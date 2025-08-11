import argparse
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import joblib
import boto3
from io import StringIO

def model_fn(model_dir):
    """
    Load model for inference
    """
    model = joblib.load(os.path.join(model_dir, "model.joblib"))
    return model

def input_fn(request_body, content_type='text/csv'):
    """
    Parse input data for inference
    """
    if content_type == 'text/csv':
        df = pd.read_csv(StringIO(request_body))
        return df.values
    else:
        raise ValueError(f"Unsupported content type: {content_type}")

def predict_fn(input_data, model):
    """
    Make predictions
    """
    predictions = model.predict(input_data)
    return predictions

def output_fn(prediction, accept='text/csv'):
    """
    Format predictions for output
    """
    if accept == 'text/csv':
        return ','.join(map(str, prediction))
    else:
        raise ValueError(f"Unsupported accept type: {accept}")

def load_data_from_s3(bucket, key):
    """
    Load training data from S3
    """
    s3 = boto3.client('s3')
    
    # List objects to find the actual CSV file
    response = s3.list_objects_v2(Bucket=bucket, Prefix=key)
    
    csv_file = None
    for obj in response.get('Contents', []):
        if obj['Key'].endswith('.csv'):
            csv_file = obj['Key']
            break
    
    if not csv_file:
        raise ValueError(f"No CSV file found in s3://{bucket}/{key}")
    
    print(f"Loading data from s3://{bucket}/{csv_file}")
    
    # Download and read the CSV file
    obj = s3.get_object(Bucket=bucket, Key=csv_file)
    df = pd.read_csv(obj['Body'])
    
    return df

def train():
    """
    Train XGBoost model for temperature prediction
    """
    parser = argparse.ArgumentParser()
    
    # SageMaker specific arguments
    parser.add_argument('--model-dir', type=str, default=os.environ.get('SM_MODEL_DIR'))
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAIN'))
    parser.add_argument('--validation', type=str, default=os.environ.get('SM_CHANNEL_VALIDATION'))
    
    # Custom arguments
    parser.add_argument('--data-bucket', type=str, default='${data_bucket}')
    parser.add_argument('--model-bucket', type=str, default='${model_bucket}')
    parser.add_argument('--max-depth', type=int, default=6)
    parser.add_argument('--eta', type=float, default=0.3)
    parser.add_argument('--gamma', type=int, default=4)
    parser.add_argument('--min-child-weight', type=int, default=6)
    parser.add_argument('--subsample', type=float, default=0.8)
    parser.add_argument('--silent', type=int, default=0)
    parser.add_argument('--objective', type=str, default='reg:squarederror')
    parser.add_argument('--num-round', type=int, default=100)
    
    args = parser.parse_args()
    
    print("Starting model training...")
    print(f"Arguments: {args}")
    
    try:
        # Load training data from S3
        df = load_data_from_s3(args.data_bucket, 'training/')
        
        print(f"Loaded {len(df)} training samples")
        print(f"Columns: {list(df.columns)}")
        print("\nFirst 5 rows:")
        print(df.head())
        
        # Prepare features and target
        feature_columns = [
            'avg_temperature', 'avg_humidity', 'temp_humidity_ratio',
            'temp_range', 'humidity_range', 'hour_of_day', 'day_of_week',
            'day_of_year', 'record_count', 'avg_data_quality'
        ]
        
        X = df[feature_columns]
        y = df['target_temp']
        
        print(f"Feature matrix shape: {X.shape}")
        print(f"Target vector shape: {y.shape}")
        
        # Handle missing values
        X = X.fillna(X.mean())
        y = y.fillna(y.mean())
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"Training set size: {X_train.shape[0]}")
        print(f"Test set size: {X_test.shape[0]}")
        
        # Create DMatrix for XGBoost
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dtest = xgb.DMatrix(X_test, label=y_test)
        
        # Set XGBoost parameters
        params = {
            'max_depth': args.max_depth,
            'eta': args.eta,
            'gamma': args.gamma,
            'min_child_weight': args.min_child_weight,
            'subsample': args.subsample,
            'silent': args.silent,
            'objective': args.objective,
            'eval_metric': 'rmse'
        }
        
        print(f"XGBoost parameters: {params}")
        
        # Train model
        watchlist = [(dtrain, 'train'), (dtest, 'validation')]
        model = xgb.train(
            params=params,
            dtrain=dtrain,
            num_boost_round=args.num_round,
            evals=watchlist,
            early_stopping_rounds=10,
            verbose_eval=10
        )
        
        # Make predictions
        y_pred = model.predict(dtest)
        
        # Calculate metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"\nModel Performance:")
        print(f"RMSE: {rmse:.4f}")
        print(f"MAE: {mae:.4f}")
        print(f"R²: {r2:.4f}")
        
        # Feature importance
        importance = model.get_score(importance_type='weight')
        print(f"\nFeature Importance:")
        for feature, score in sorted(importance.items(), key=lambda x: x[1], reverse=True):
            print(f"{feature}: {score}")
        
        # Save model
        model_path = os.path.join(args.model_dir, "model.joblib")
        joblib.dump(model, model_path)
        print(f"Model saved to {model_path}")
        
        # Save feature names for inference
        feature_names_path = os.path.join(args.model_dir, "feature_names.txt")
        with open(feature_names_path, 'w') as f:
            f.write(','.join(feature_columns))
        
        # Save model metrics
        metrics_path = os.path.join(args.model_dir, "metrics.txt")
        with open(metrics_path, 'w') as f:
            f.write(f"RMSE: {rmse:.4f}\n")
            f.write(f"MAE: {mae:.4f}\n")
            f.write(f"R²: {r2:.4f}\n")
        
        print("Training completed successfully!")
        
    except Exception as e:
        print(f"Training failed with error: {str(e)}")
        raise e

if __name__ == '__main__':
    train()