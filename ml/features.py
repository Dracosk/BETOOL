import boto3
import awswrangler as wr
import pandas as pd
import numpy as np

def load_results():
    """
    Load the results data from S3 and return a DataFrame.
    
    Returns:
        pd.DataFrame: A DataFrame containing the results data.
    """
    session = boto3.Session(region_name='us-east-2')
    query = 'SELECT * FROM db_betool.v_matches'
    df = wr.athena.read_sql_query(
        query, 
        database='db_betool', 
        ctas_approach=False, 
        s3_output='s3://betool-dl/query_results/',
        boto3_session=session)
    return df

def create_feature(df, window=5):
    """
    Create features for the given DataFrame.
    
    Args:
        df (pd.DataFrame): The input DataFrame containing match results.
        window (int): The rolling window size for feature calculation."""
    home_poss = df['home_possesion'].astype(str).str.replace('%', '', regex=False).astype(int)
    away_poss = df['away_possesion'].astype(str).str.replace('%', '', regex=False).astype(int)

    num_cols = [
        'local_score', 'away_score', 
        'home_possesion', 'away_possesion',
        'home_total_shots', 'away_total_shots', 
        'home_shots_in_target', 'away_shots_in_target', 
        'home_corners', 'away_corners'
    ]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    home_pts = np.where(df['local_score'] > df['away_score'], 3,
                       np.where(df['local_score'] == df['away_score'], 1, 0))
    away_pts = np.where(df['local_score'] < df['away_score'], 3,
                       np.where(df['local_score'] == df['away_score'], 1, 0))

    df_home = pd.DataFrame({
        'game_id': df['game_id'],
        'game_date': df['game_date'],
        'team_id': df['local_id'],
        'pts': home_pts,
        'gf': df['local_score'],
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
        'ga': df['local_score'],
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
            .transform(lambda x: x.shift(1).rolling(window=window, min_periods=2).mean())
        )

        df_away[f'away_only_{m}'] = (
            df_away.groupby('team_id')[m]
            .transform(lambda x: x.shift(1).rolling(window=window, min_periods=2).mean())
        )
    # Df with only the rolling metrics for home and away teams
    home_v_clean = df_home[['game_id', 'team_id', 'home_only_pts', 'home_only_gf', 'home_only_ga']]
    away_v_clean = df_away[['game_id', 'team_id', 'away_only_pts', 'away_only_gf', 'away_only_ga']] 
    
    df_combined = pd.concat([df_home, df_away], ignore_index=True)
    df_combined.sort_values(by=['team_id', 'game_date', 'game_id'], inplace=True)

    metrics = ['pts', 'gf', 'ga', 'possession', 'shots', 'shots_target', 'corners']

    for metric in metrics:
        df_combined[f'{metric}_rolling_mean'] = df_combined.groupby('team_id')[metric].transform(lambda x: x.shift(1).rolling(window=window, min_periods=3).mean())

    rolling_metrics = [f'{metric}_rolling_mean' for metric in metrics]
    features_clean = df_combined[['game_id', 'team_id'] + rolling_metrics]


    df_merged = df.merge(features_clean, left_on=['game_id', 'local_id'], right_on=['game_id', 'team_id'], how='left').rename(columns={metric: f'local_{metric}' for metric in rolling_metrics}).drop(columns=['team_id'])
    df_merged = df_merged.merge(features_clean, left_on=['game_id', 'away_id'], right_on=['game_id', 'team_id'], how='left').rename(columns={metric: f'away_{metric}' for metric in rolling_metrics}).drop(columns=['team_id'])


    df_merged = df_merged.merge(home_v_clean, left_on=['game_id', 'local_id'], right_on=['game_id', 'team_id'], how='left').drop(columns=['team_id'])
    df_merged = df_merged.merge(away_v_clean, left_on=['game_id', 'away_id'], right_on=['game_id', 'team_id'], how='left').drop(columns=['team_id'])
    # New variables for target creation
    df_merged['local_gd_rolling'] = df_merged['local_gf_rolling_mean'] - df_merged['local_ga_rolling_mean']
    df_merged['away_gd_rolling'] = df_merged['away_gf_rolling_mean'] - df_merged['away_ga_rolling_mean']
    # Variables for feature creation
    df_merged['diff_pts'] = df_merged['local_pts_rolling_mean'] - df_merged['away_pts_rolling_mean']
    df_merged['diff_gd'] = df_merged['local_gd_rolling'] - df_merged['away_gd_rolling']
    df_merged['diff_gf'] = df_merged['local_gf_rolling_mean'] - df_merged['away_gf_rolling_mean']
    df_merged['diff_ga'] = df_merged['local_ga_rolling_mean'] - df_merged['away_ga_rolling_mean']
    df_merged['diff_shots_target'] = df_merged['local_shots_target_rolling_mean'] - df_merged['away_shots_target_rolling_mean']
    df_merged['diff_possession'] = df_merged['local_possession_rolling_mean'] - df_merged['away_possession_rolling_mean']
    df_merged['diff_corners'] = df_merged['local_corners_rolling_mean'] - df_merged['away_corners_rolling_mean']
    # Additional features for venue advantage
    df_merged['venue_diff_pts'] = df_merged['home_only_pts'] - df_merged['away_only_pts']
    df_merged['venue_diff_gf'] = df_merged['home_only_gf'] - df_merged['away_only_gf']
    # Efficiency metrics
    df_merged['local_effec'] = df_merged['local_gf_rolling_mean'] / (df_merged['local_shots_target_rolling_mean'] + 0.001)
    df_merged['away_effec'] = df_merged['away_gf_rolling_mean'] / (df_merged['away_shots_target_rolling_mean'] + 0.001)
    # Additional features
    df_merged['sum_gf'] = df_merged['local_gf_rolling_mean'] + df_merged['away_gf_rolling_mean']
    df_merged['sum_ga'] = df_merged['local_ga_rolling_mean'] + df_merged['away_ga_rolling_mean']
    df_merged['sum_shots_target'] = df_merged['local_shots_target_rolling_mean'] + df_merged['away_shots_target_rolling_mean']
    df_merged['sum_corners'] = df_merged['local_corners_rolling_mean'] + df_merged['away_corners_rolling_mean']
    # Target variables
    df_merged['target_1x2'] = np.where(df_merged['local_score'] > df_merged['away_score'], 0,
                                        np.where(df_merged['local_score'] == df_merged['away_score'], 1, 2))
    df_merged['target_dc_1x'] = np.where(df_merged['local_score'] >= df_merged['away_score'], 1, 0)
    df_merged['target_dc_2x'] = np.where(df_merged['local_score'] <= df_merged['away_score'], 1, 0)
    df_merged['target_dc_12'] = np.where(df_merged['local_score'] != df_merged['away_score'], 1, 0)
    df_merged['target_ou_o15'] = np.where((df_merged['local_score'] + df_merged['away_score']) > 1.5, 1, 0)
    df_merged['target_ou_o25'] = np.where((df_merged['local_score'] + df_merged['away_score']) > 2.5, 1, 0)
    df_merged['target_btts'] = np.where((df_merged['local_score'] > 0) & (df_merged['away_score'] > 0), 1, 0)
    df_merged['target_corners_o65'] = np.where((df_merged['home_corners'] + df_merged['away_corners']) > 6.5, 1, 0)
    df_merged['target_corners_o75'] = np.where((df_merged['home_corners'] + df_merged['away_corners']) > 7.5, 1, 0)
    df_merged['target_corners_o85'] = np.where((df_merged['home_corners'] + df_merged['away_corners']) > 8.5, 1, 0)
    df_merged['target_total_corners'] = df_merged['home_corners'] + df_merged['away_corners']

    extra_cols = ['local_gd_rolling', 'away_gd_rolling', 'diff_pts', 'diff_gd', 'diff_gf', 'diff_ga', 'diff_shots_target', 'diff_possession', 'diff_corners', 'venue_diff_pts', 'venue_diff_gf', 'local_effec', 'away_effec',
                  'sum_gf', 'sum_ga', 'sum_shots_target', 'sum_corners']

    features_columns = [f'local_{metric}' for metric in rolling_metrics] + [f'away_{metric}' for metric in rolling_metrics] + extra_cols
    df_final = df_merged.dropna(subset=features_columns).reset_index(drop=True)

    return df_final, features_columns


    
   