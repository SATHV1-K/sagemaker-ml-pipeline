import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_sample_data(num_records=10000):
    """
    Generate sample IoT sensor data with timestamp, temperature, and humidity
    """
    # Generate timestamps for the last 7 days with 1-minute intervals
    start_time = datetime.now() - timedelta(days=7)
    timestamps = [start_time + timedelta(minutes=i) for i in range(num_records)]
    
    # Generate realistic temperature data (15-35°C with some noise)
    base_temp = 25
    temperature = np.random.normal(base_temp, 5, num_records)
    temperature = np.clip(temperature, 10, 40)  # Realistic temperature range
    
    # Generate realistic humidity data (30-90% with some correlation to temperature)
    # Higher temperature tends to have lower humidity
    humidity = 80 - (temperature - 20) * 1.5 + np.random.normal(0, 10, num_records)
    humidity = np.clip(humidity, 20, 95)  # Realistic humidity range
    
    # Create DataFrame
    data = pd.DataFrame({
        'timestamp': timestamps,
        'temperature': np.round(temperature, 2),
        'humidity': np.round(humidity, 2)
    })
    
    # Add some missing values to simulate real-world data issues
    missing_indices = np.random.choice(data.index, size=int(0.02 * len(data)), replace=False)
    data.loc[missing_indices, 'temperature'] = np.nan
    
    missing_indices = np.random.choice(data.index, size=int(0.015 * len(data)), replace=False)
    data.loc[missing_indices, 'humidity'] = np.nan
    
    return data

if __name__ == "__main__":
    # Generate sample data
    print("Generating sample IoT sensor data...")
    df = generate_sample_data()
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Save to CSV
    output_file = 'data/sensor_data_raw.csv'
    df.to_csv(output_file, index=False)
    
    print(f"Sample data generated and saved to {output_file}")
    print(f"Total records: {len(df)}")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print("\nFirst 5 rows:")
    print(df.head())
    print("\nData info:")
    print(df.info())