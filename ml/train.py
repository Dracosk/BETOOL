import os
import xgboost as xgb
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss, mean_absolute_error
from ml.features import create_feature, load_results
from utils.s3_tool import upload_to_s3

def train_models():
    
    raw_df = load_results()
    dataset, X_cols = create_feature(raw_df, window=5)

    dataset = dataset.sort_values(by=['game_date', 'game_id']).reset_index(drop=True)

    split_idx = int(len(dataset) * 0.8)
    train_df = dataset.iloc[:split_idx]
    test_df = dataset.iloc[split_idx:]

    X_train = train_df[X_cols]
    X_test = test_df[X_cols]

    models_dir = os.path.join("ml", "models")
    os.makedirs(models_dir, exist_ok=True)

    target_binary = [
        'target_dc_1x','target_dc_2x', 'target_ou_o15', 'target_ou_o25', 'target_btts',
        'target_corners_o65', 'target_corners_o75', 'target_corners_o85', 'target_dc_12'
    ]

    #print(f"{'market':<22} | {'accuracy':<20} | {'quality (LogLoss/MAE)'}")
    #print("-" * 70)

    y_train_1x2 = train_df['target_1x2'].astype('int')
    y_test_1x2 = test_df['target_1x2'].astype('int')

    model_1x2 = xgb.XGBClassifier(
        objective='multi:softprob',
        num_class=3,
        eval_metric='mlogloss',
        min_child_weight=5,
        reg_lambda=2.0,
        n_estimators=150,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        
    )

    model_1x2.fit(X_train, y_train_1x2)

    preds_1x2 = model_1x2.predict(X_test)
    probs_1x2 = model_1x2.predict_proba(X_test)
    accuracy_1x2 = accuracy_score(y_test_1x2, preds_1x2)
    loss_1x2 = log_loss(y_test_1x2, probs_1x2)
    #print(f"{'1X2':<22} | {accuracy_1x2:<20.4f} | {loss_1x2:.4f}")
    model_1x2.save_model(os.path.join(models_dir, 'model_target_1x2.json'))

    for target in target_binary:
        y_train = train_df[target].astype('int')
        y_test = test_df[target].astype('int')

        model = xgb.XGBClassifier(
            objective='binary:logistic',
            eval_metric='logloss',
            n_estimators=150,
            max_depth=3,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            min_child_weight=5,
            reg_lambda=2.0
        )

        model.fit(X_train, y_train)

        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)[:, 1]
        accuracy = accuracy_score(y_test, preds)
        loss = log_loss(y_test, probs)
        mae = mean_absolute_error(y_test, probs)

        #print(f"{target:<22} | {accuracy:<20.4f} | {loss:.4f}/{mae:.4f}")
        model.save_model(os.path.join(models_dir, f'model_{target}.json'))

    y_train_reg = train_df['target_total_corners'].astype('float')
    y_test_reg = test_df['target_total_corners'].astype('float')

    model_reg = xgb.XGBRegressor(
        objective='reg:squarederror',
        eval_metric='mae',
        n_estimators=150,
        max_depth=3,
        learning_rate=0.03,
        subsample=0.8,
        reg_lambda=2.0,
        min_child_weight=5,
        colsample_bytree=0.8,
        random_state=42
    )
    model_reg.fit(X_train, y_train_reg)

    preds_reg = model_reg.predict(X_test)
    mae_reg = mean_absolute_error(y_test_reg, preds_reg)
    #print(f"{'total Corners':<22} | {'N/A':<20} | {mae_reg:.4f}")
    model_reg.save_model(os.path.join(models_dir, 'model_target_total_corners.json'))
    
    names = ['target_1x2', 'target_total_corners'] + target_binary
    for name in names:
        achive_name = f'ml/models/model_{name}.json'
        upload_to_s3('ml_models', achive_name)

    return model_1x2, model, model_reg

if __name__ == "__main__":
    train_models()


    
    
    
    
    