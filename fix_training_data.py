import boto3
import pandas as pd
import io

def fix_training_data():
    s3 = boto3.client('s3')
    bucket_name = 'sagemaker-ml-pipeline-data-f5ofrag0'
    
    # Download the current training data
    response = s3.get_object(Bucket=bucket_name, Key='training/part-00000-427b3c4d-3180-4f0e-ab3f-7637d3318878-c000.snappy.csv')
    csv_content = response['Body'].read().decode('utf-8')
    
    # Read into pandas DataFrame
    df = pd.read_csv(io.StringIO(csv_content))
    
    print(f"Original data shape: {df.shape}")
    print(f"Original columns: {df.columns.tolist()}")
    print("First few rows:")
    print(df.head())
    
    # Check if this is the raw data or processed data
    if len(df.columns) == 4:  # Raw data: timestamp, temp, humidity, target
        print("Detected raw data format. Creating proper training features...")
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df.iloc[:, 0])
        df['temperature'] = df.iloc[:, 1]
        df['humidity'] = df.iloc[:, 2]
        df['target'] = df.iloc[:, 3]
        
        # Create features
        df['temp_humidity_ratio'] = df['temperature'] / df['humidity']
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_year'] = df['timestamp'].dt.dayofyear
        
        # Create rolling features (5-minute windows)
        df = df.sort_values('timestamp')
        df['temp_rolling_mean'] = df['temperature'].rolling(window=5, min_periods=1).mean()
        df['humidity_rolling_mean'] = df['humidity'].rolling(window=5, min_periods=1).mean()
        df['temp_rolling_std'] = df['temperature'].rolling(window=5, min_periods=1).std().fillna(0)
        df['humidity_rolling_std'] = df['humidity'].rolling(window=5, min_periods=1).std().fillna(0)
        
        # Select features for training (target first for XGBoost)
        training_features = df[[
            'target',  # Target column first
            'temperature',
            'humidity', 
            'temp_humidity_ratio',
            'hour_of_day',
            'day_of_week',
            'day_of_year',
            'temp_rolling_mean',
            'humidity_rolling_mean',
            'temp_rolling_std',
            'humidity_rolling_std'
        ]].copy()
        
    else:  # Processed data from Glue
        print("Detected processed data format. Reordering columns...")
        
        # Assuming the last column is the target
        feature_cols = df.columns[:-1].tolist()
        target_col = df.columns[-1]
        
        # Reorder: target first, then features
        training_features = df[[target_col] + feature_cols].copy()
    
    # Remove any rows with NaN values
    training_features = training_features.dropna()
    
    print(f"\nFinal training data shape: {training_features.shape}")
    print(f"Final columns: {training_features.columns.tolist()}")
    print("First few rows of final data:")
    print(training_features.head())
    
    # Save to CSV without headers and index
    csv_buffer = io.StringIO()
    training_features.to_csv(csv_buffer, index=False, header=False)
    csv_content = csv_buffer.getvalue()
    
    # Upload the fixed training data
    s3.put_object(
        Bucket=bucket_name,
        Key='training/training_data_fixed.csv',
        Body=csv_content.encode('utf-8')
    )
    
    print(f"\nFixed training data uploaded to s3://{bucket_name}/training/training_data_fixed.csv")
    print(f"Data format: {training_features.shape[1]} columns, {training_features.shape[0]} rows")
    print("Target column is first, no headers included.")

if __name__ == "__main__":
    fix_training_data()