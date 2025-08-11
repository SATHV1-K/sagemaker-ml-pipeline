import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import boto3
import io

def create_realistic_training_data(num_records=10000):
    """
    Create realistic training data for temperature prediction
    Target: next temperature reading (shifted by 1 time step)
    """
    print("Generating realistic sensor training data...")
    
    # Generate timestamps for the last 7 days with 1-minute intervals
    start_time = datetime.now() - timedelta(days=7)
    timestamps = [start_time + timedelta(minutes=i) for i in range(num_records)]
    
    # Generate realistic temperature data with daily patterns
    hours = np.array([ts.hour for ts in timestamps])
    days = np.array([ts.day for ts in timestamps])
    
    # Base temperature with daily cycle (cooler at night, warmer during day)
    base_temp = 25 + 8 * np.sin(2 * np.pi * (hours - 6) / 24)
    
    # Add weekly variation
    weekly_variation = 3 * np.sin(2 * np.pi * days / 7)
    
    # Add random noise
    noise = np.random.normal(0, 2, num_records)
    
    # Combine all components
    temperature = base_temp + weekly_variation + noise
    temperature = np.clip(temperature, 10, 40)  # Realistic range
    
    # Generate humidity inversely correlated with temperature
    humidity = 80 - (temperature - 25) * 1.2 + np.random.normal(0, 8, num_records)
    humidity = np.clip(humidity, 20, 95)
    
    # Create DataFrame
    data = pd.DataFrame({
        'timestamp': timestamps,
        'temperature': np.round(temperature, 2),
        'humidity': np.round(humidity, 2)
    })
    
    # Create features
    data['temp_humidity_ratio'] = data['temperature'] / data['humidity']
    data['hour_of_day'] = data['timestamp'].dt.hour
    data['day_of_week'] = data['timestamp'].dt.dayofweek
    data['day_of_year'] = data['timestamp'].dt.dayofyear
    
    # Create rolling features (5-minute windows)
    data = data.sort_values('timestamp')
    data['temp_rolling_mean'] = data['temperature'].rolling(window=5, min_periods=1).mean()
    data['humidity_rolling_mean'] = data['humidity'].rolling(window=5, min_periods=1).mean()
    data['temp_rolling_std'] = data['temperature'].rolling(window=5, min_periods=1).std().fillna(0)
    data['humidity_rolling_std'] = data['humidity'].rolling(window=5, min_periods=1).std().fillna(0)
    
    # Create target: next temperature reading (shifted by 1)
    data['target'] = data['temperature'].shift(-1)
    
    # Remove the last row (no target available)
    data = data[:-1].copy()
    
    # Remove any rows with NaN values
    data = data.dropna()
    
    # Select features for training (target first for XGBoost)
    training_features = data[[
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
    
    print(f"Training data shape: {training_features.shape}")
    print(f"Target statistics:")
    print(f"  Min: {training_features['target'].min():.2f}°C")
    print(f"  Max: {training_features['target'].max():.2f}°C")
    print(f"  Mean: {training_features['target'].mean():.2f}°C")
    print(f"  Std: {training_features['target'].std():.2f}°C")
    
    return training_features

def upload_to_s3(training_data):
    """
    Upload the training data to S3
    """
    s3 = boto3.client('s3')
    bucket_name = 'sagemaker-ml-pipeline-data-f5ofrag0'
    
    # Save to CSV without headers and index (XGBoost format)
    csv_buffer = io.StringIO()
    training_data.to_csv(csv_buffer, index=False, header=False)
    csv_content = csv_buffer.getvalue()
    
    # Upload the training data
    s3.put_object(
        Bucket=bucket_name,
        Key='training/realistic_training_data.csv',
        Body=csv_content.encode('utf-8')
    )
    
    print(f"\nRealistic training data uploaded to s3://{bucket_name}/training/realistic_training_data.csv")
    print(f"Data format: {training_data.shape[1]} columns, {training_data.shape[0]} rows")
    print("Target column is first, no headers included.")

def save_local_copy(training_data):
    """
    Save a local copy for reference
    """
    # Save with headers for local reference
    training_data.to_csv('realistic_training_data.csv', index=False)
    print(f"\nLocal copy saved as 'realistic_training_data.csv'")
    
    # Show sample data
    print("\nSample training data:")
    print(training_data.head(10))

if __name__ == "__main__":
    # Generate realistic training data
    training_data = create_realistic_training_data()
    
    # Save local copy
    save_local_copy(training_data)
    
    # Upload to S3
    upload_to_s3(training_data)
    
    print("\n✅ Realistic training data created successfully!")
    print("Next steps:")
    print("1. Retrain the model with: python start_training_job.py")
    print("2. Deploy the new model")
    print("3. Test predictions")