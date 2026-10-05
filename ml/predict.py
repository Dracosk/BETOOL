import os
import pandas as pd
import xgboost as xgb
import numpy as np
import boto3
import awswrangler as wr

def query_athena(query):
    """
    Execute a SQL query on AWS Athena and return the result as a pandas DataFrame.
    
    Args:
        query (str): The SQL query to execute.
        database (str): The Athena database to query.
        s3_output (str): The S3 path where the query results will be stored."""
    session = boto3.Session(region_name='us-east-2')
    df = wr.athena.read_sql_query(
        query, 
        database='db_betool', 
        ctas_approach=False, 
        s3_output='s3://betool-dl/query_results/',
        boto3_session=session)
    return df
def check_models_exist():
    """
    Check if the required machine learning models exist in the S3 bucket.
    
    Returns:
        bool: True if all models exist, False otherwise."""
    s3 = boto3.client('s3')
    bucket_name = 'betool-dl'
    os.makedirs('ml/models', exist_ok=True)
    model_names = [
        'model_target_1x2.json',
        'model_target_total_corners.json',
        'model_target_dc_1x.json',
        'model_target_dc_2x.json',
        'model_target_ou_o15.json',
        'model_target_ou_o25.json',
        'model_target_btts.json',
        'model_target_corners_o65.json',
        'model_target_corners_o75.json',
        'model_target_corners_o85.json',
        'model_target_dc_12.json'
    ]
    for model_name in model_names:
        local_path = f'ml/models/{model_name}'
        if not os.path.exists(local_path):
            try:
                s3.download_file(bucket_name, f'ml_models/ml/models/{model_name}', local_path)
            except Exception as e:
                print(f"Error downloading {model_name} from S3: {e}")
                return False
    return True
            
def build_fixtures_features(df_matches, df_fixtures,window=5):
    """
    Build features for match fixtures by querying the necessary data from Athena.
    
    Returns:
        pd.DataFrame: A DataFrame containing the features for match fixtures."""
    
    df = df_matches.copy()
    df['game_date'] = pd.to_datetime(df['game_date'])

    home_poss = df['home_possession'].astype(str).str.replace('%', '', regex=False).astype(int)
    away_poss = df['away_possession'].astype(str).str.replace('%', '', regex=False).astype(int)

    num_cols = [
        'home_score', 'away_score','home_possession', 'away_possession',
        'home_total_shots', 'away_total_shots','home_shots_in_target', 'away_shots_in_target',
        'home_corners', 'away_corners']

    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    home_pts = np.where(df['home_score'] > df['away_score'], 3,
                       np.where(df['home_score'] == df['away_score'], 1, 0))
    away_pts = np.where(df['home_score'] < df['away_score'], 3,
                       np.where(df['home_score'] == df['away_score'], 1, 0))

    df_home = pd.DataFrame({
        'game_id': df['game_id'],
        'game_date': df['game_date'],
        'team_id': df['home_id'],
        'pts': home_pts,
        'gf': df['home_score'],
        'ga': df['away_score'],
        'possession': home_poss,
        'shots': df['home_total_shots'],
        'shots_target': df['home_shots_in_target'],
        'corners': df['home_corners']
    })

    df_away = pd.DataFrame({
        'game_id': df['game_id'],
        'game_date': df['game_date'],
        'team_id': df['away_id'],
        'pts': away_pts,
        'gf': df['away_score'],
        'ga': df['home_score'],
        'possession': away_poss,
        'shots': df['away_total_shots'],
        'shots_target': df['away_shots_in_target'],
        'corners': df['away_corners']
    })

    df_home.sort_values(by=['team_id', 'game_date', 'game_id'], inplace=True)
    df_away.sort_values(by=['team_id', 'game_date', 'game_id'], inplace=True)

    v_metrics = ['pts', 'gf', 'ga']
    for m in v_metrics:
        df_home[f'home_only_{m}'] = (
            df_home.groupby('team_id')[m]
            .transform(lambda x: x.rolling(window=window, min_periods=2).mean())
        )
        df_away[f'away_only_{m}'] = (
            df_away.groupby('team_id')[m]
            .transform(lambda x: x.rolling(window=window, min_periods=2).mean())
        )
    home_only_form = df_home.groupby('team_id')[['home_only_pts', 'home_only_gf', 'home_only_ga']].last().reset_index()
    away_only_form = df_away.groupby('team_id')[['away_only_pts', 'away_only_gf', 'away_only_ga']].last().reset_index()

    df_combined = pd.concat([df_home, df_away], ignore_index=True)
    df_combined.sort_values(by=['team_id', 'game_date', 'game_id'], inplace=True)

    metrics = ['pts', 'gf', 'ga', 'possession', 'shots', 'shots_target', 'corners']
    for m in metrics:
        df_combined[f'{m}_rolling_mean'] = (
            df_combined.groupby('team_id')[m]
            .transform(lambda x: x.rolling(window=window, min_periods=2).mean())
        )

    rolling_metrics = [f'{m}_rolling_mean' for m in metrics]
    general_form = df_combined.groupby('team_id')[rolling_metrics].last().reset_index()

    df_merged = df_fixtures.merge(general_form, left_on='home_id', right_on='team_id', how='left').rename(columns={col: f'home_{col}' for col in rolling_metrics}).drop(columns=['team_id'])
    df_merged = df_merged.merge(general_form, left_on='away_id', right_on='team_id', how='left').rename(columns={col: f'away_{col}' for col in rolling_metrics}).drop(columns=['team_id'])

    df_merged = df_merged.merge(home_only_form, left_on='home_id', right_on='team_id', how='left').drop(columns=['team_id'])
    df_merged = df_merged.merge(away_only_form, left_on='away_id', right_on='team_id', how='left').drop(columns=['team_id'])

    df_merged['home_gd_rolling'] = df_merged['home_gf_rolling_mean'] - df_merged['home_ga_rolling_mean']
    df_merged['away_gd_rolling'] = df_merged['away_gf_rolling_mean'] - df_merged['away_ga_rolling_mean']

    df_merged['diff_pts'] = df_merged['home_pts_rolling_mean'] - df_merged['away_pts_rolling_mean']
    df_merged['diff_gd'] = df_merged['home_gd_rolling'] - df_merged['away_gd_rolling']
    df_merged['diff_gf'] = df_merged['home_gf_rolling_mean'] - df_merged['away_gf_rolling_mean']
    df_merged['diff_ga'] = df_merged['home_ga_rolling_mean'] - df_merged['away_ga_rolling_mean']
    df_merged['diff_shots_target'] = df_merged['home_shots_target_rolling_mean'] - df_merged['away_shots_target_rolling_mean']
    df_merged['diff_possession'] = df_merged['home_possession_rolling_mean'] - df_merged['away_possession_rolling_mean']
    df_merged['diff_corners'] = df_merged['home_corners_rolling_mean'] - df_merged['away_corners_rolling_mean']

    df_merged['venue_diff_pts'] = df_merged['home_only_pts'] - df_merged['away_only_pts']
    df_merged['venue_diff_gf'] = df_merged['home_only_gf'] - df_merged['away_only_gf']

    df_merged['home_effec'] = df_merged['home_gf_rolling_mean'] / (df_merged['home_shots_target_rolling_mean'] + 0.001)
    df_merged['away_effec'] = df_merged['away_gf_rolling_mean'] / (df_merged['away_shots_target_rolling_mean'] + 0.001)

    df_merged['sum_gf'] = df_merged['home_gf_rolling_mean'] + df_merged['away_gf_rolling_mean']
    df_merged['sum_ga'] = df_merged['home_ga_rolling_mean'] + df_merged['away_ga_rolling_mean']
    df_merged['sum_shots_target'] = df_merged['home_shots_target_rolling_mean'] + df_merged['away_shots_target_rolling_mean']
    df_merged['sum_corners'] = df_merged['home_corners_rolling_mean'] + df_merged['away_corners_rolling_mean']

    extra_cols = [
        'home_only_pts', 'home_only_gf', 'home_only_ga',
        'away_only_pts', 'away_only_gf', 'away_only_ga',
        'home_gd_rolling', 'away_gd_rolling',
        'diff_pts', 'diff_gd', 'diff_gf', 'diff_ga',
        'diff_shots_target', 'diff_possession', 'diff_corners',
        'venue_diff_pts', 'venue_diff_gf',
        'home_effec', 'away_effec',
        'sum_gf', 'sum_ga', 'sum_shots_target', 'sum_corners'
    ]
    features_columns = [f'home_{m}' for m in rolling_metrics] + [f'away_{m}' for m in rolling_metrics] + extra_cols
    df_final = df_merged.dropna(subset=features_columns).reset_index(drop=True)
    return df_final, features_columns

def calculate_kelly_stake(prob, odd, kelly_fraction=0.05, min_ev=0.04, max_stake=3.0):
    """
    Calculate the Kelly stake based on the probability of winning and the odds.
    
    Args:
        prob (float): The probability of winning (between 0 and 1).
        odd (float): The decimal odds for the bet.
        kelly_fraction (float): The fraction of the Kelly stake to use (default is 0.25).
        min_ev (float): The minimum expected value to consider a bet (default is 0.04).
        max_stake (float): The maximum stake to use (default is 5.0)."""
    if prob < 0.45:
        return 0.0, 0.0
    if odd > 3.2 or odd <= 1.15:
        return 0.0, 0.0
    
    ev = (prob * odd) - 1
    if ev < min_ev or ev > 0.25:
        return 0.0, round(ev * 100, 2)

    kelly_pct = (ev / (odd - 1)) * 100
    stake_pct = min(kelly_pct * kelly_fraction, max_stake)
    return round(stake_pct, 2), round(ev * 100, 2)

def prediction_run():
    check_models_exist()
    df_matches = query_athena("SELECT * FROM db_betool.v_matches")
    df_fixtures = query_athena("SELECT * FROM db_betool.v_fixtures")
    df_odds = query_athena("SELECT * FROM db_betool.v_odds")
    df_teams = query_athena("SELECT team_id, team_name FROM db_betool.dim_teams")

    df_fixtures['game_date'] = pd.to_datetime(df_fixtures['game_date'])
    df_odds['odd'] = pd.to_numeric(df_odds['odd'], errors='coerce')
    
    today = pd.Timestamp.now().normalize()
    df_upcoming = df_fixtures[df_fixtures['game_date'] >= today].copy()

    df_pred, _ = build_fixtures_features(df_matches, df_upcoming, window=5)

    models_dir = os.path.join("ml", "models")
    model_1x2 = xgb.XGBClassifier()
    model_1x2.load_model(os.path.join(models_dir, 'model_target_1x2.json'))
    expected_cols = model_1x2.get_booster().feature_names
    X_upcoming = df_pred[expected_cols]

    probs_1x2 = model_1x2.predict_proba(X_upcoming)
    df_pred['prob_1'] = probs_1x2[:, 0]
    df_pred['prob_X'] = probs_1x2[:, 1]
    df_pred['prob_2'] = probs_1x2[:, 2]

    binary_targets = ['target_dc_1x', 'target_dc_2x', 'target_dc_12', 'target_ou_o15', 'target_ou_o25', 'target_btts', 'target_corners_o65', 'target_corners_o75', 'target_corners_o85']
    for target in binary_targets:
        m = xgb.XGBClassifier()
        m.load_model(os.path.join(models_dir, f'model_{target}.json'))
        df_pred[f'prob_{target}'] = m.predict_proba(X_upcoming)[:, 1]

    model_reg = xgb.XGBRegressor()
    model_reg.load_model(os.path.join(models_dir, 'model_target_total_corners.json'))
    df_pred['expected_corners'] = model_reg.predict(X_upcoming)

    records= []
    for _, row in df_pred.iterrows():
        gid = row['game_id']
        gdate = row['game_date'].strftime('%Y-%m-%d')
        hom, awy = row['home_id'], row['away_id']

        markets_map = [
            ('resultado del partido', '1', row['prob_1']),
            ('resultado del partido', 'x', row['prob_X']),
            ('resultado del partido', '2', row['prob_2']),
            ('doble oportunidad', '1X', row['prob_target_dc_1x']),
            ('doble oportunidad', '2X', row['prob_target_dc_2x']),
            ('doble oportunidad', '12', row['prob_target_dc_12']),
            ('goles totales mas/menos', 'mas de 1.5', row['prob_target_ou_o15']),
            ('goles totales mas/menos', 'menos de 1.5', 1 - row['prob_target_ou_o15']),
            ('goles totales mas/menos', 'mas de 2.5', row['prob_target_ou_o25']),
            ('goles totales mas/menos', 'menos de 2.5', 1 - row['prob_target_ou_o25']),
            ('ambos equipos anotan', 'si', row['prob_target_btts']),
            ('ambos equipos anotan', 'no', 1 - row['prob_target_btts']),
            ('corners mas/menos', 'mas de 6.5 córners', row['prob_target_corners_o65']),
            ('corners mas/menos', 'mas de 7.5 córners', row['prob_target_corners_o75']),
            ('corners mas/menos', 'mas de 8.5 córners', row['prob_target_corners_o85'])
        ]
        for mkt, bname, prob in markets_map:
            records.append({
                'game_id': gid,
                'game_date': gdate,
                'home_id': hom,
                'away_id': awy,
                'market': mkt,
                'bet_name': bname,
                'model_prob': round(float(prob), 4)
        })
    df_long_prob = pd.DataFrame(records)

    df_value = df_long_prob.merge(df_odds[['game_id', 'market', 'bet_name', 'odd']], on=['game_id', 'market', 'bet_name'], how='inner')

    stake_evs = df_value.apply(lambda row: calculate_kelly_stake(row['model_prob'], row['odd']), axis=1)
    df_value['bank'] = [x[0] for x in stake_evs]
    df_value['ev'] = [x[1] for x in stake_evs]

    df_best_bets = df_value[df_value['bank'] > 0].sort_values(by='ev', ascending=False).reset_index(drop=True)
    df_best_bets = df_best_bets.merge(df_teams, left_on='home_id', right_on='team_id', how='left')
    df_best_bets.rename(columns={'team_name': 'home'}, inplace=True)
    df_best_bets.drop(columns=['team_id'], inplace=True)

    df_best_bets = df_best_bets.merge(df_teams, left_on='away_id', right_on='team_id', how='left')
    df_best_bets.rename(columns={'team_name': 'away'}, inplace=True)
    df_best_bets.drop(columns=['team_id'], inplace=True)
    df_best_bets = df_best_bets.loc[df_best_bets.groupby('game_id')['ev'].idxmax()].reset_index(drop=True)
    df_best_bets = df_best_bets.sort_values(by='ev', ascending=False)
    
    return df_best_bets