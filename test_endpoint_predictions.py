import boto3
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def test_endpoint_predictions(endpoint_name):
    """
    Test the deployed SageMaker endpoint with sample sensor data
    """
    runtime = boto3.client('sagemaker-runtime')
    
    # Create sample test data (same format as training data)
    # Features: temperature, humidity, temp_humidity_ratio, hour_of_day, day_of_week, 
    #          day_of_year, temp_rolling_mean, humidity_rolling_mean, temp_rolling_std, humidity_rolling_std
    
    test_samples = [
        # Sample 1: Morning data
        [25.5, 68.2, 0.374, 8, 1, 217, 25.1, 67.8, 1.2, 2.1],
        # Sample 2: Afternoon data  
        [32.1, 55.3, 0.581, 14, 1, 217, 31.8, 56.1, 2.1, 3.2],
        # Sample 3: Evening data
        [28.7, 72.4, 0.396, 19, 1, 217, 28.9, 71.2, 1.8, 2.8],
        # Sample 4: Night data
        [22.3, 78.1, 0.286, 23, 1, 217, 22.8, 77.5, 1.5, 2.4],
        # Sample 5: High temperature scenario
        [35.2, 45.8, 0.769, 12, 2, 218, 34.8, 46.2, 2.5, 3.1]
    ]
    
    print(f"Testing endpoint: {endpoint_name}")
    print("=" * 60)
    
    for i, sample in enumerate(test_samples, 1):
        try:
            # Convert to CSV format (no target column for prediction)
            csv_input = ','.join(map(str, sample))
            
            print(f"\nTest Sample {i}:")
            print(f"Input features: {sample}")
            print(f"Temperature: {sample[0]}°C, Humidity: {sample[1]}%")
            print(f"Time: Hour {sample[3]}, Day of week {sample[4]}")
            
            # Make prediction
            response = runtime.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType='text/csv',
                Body=csv_input
            )
            
            # Parse prediction result
            result = response['Body'].read().decode('utf-8').strip()
            predicted_temp = float(result)
            
            print(f"Predicted next temperature: {predicted_temp:.2f}°C")
            
            # Provide interpretation
            temp_diff = predicted_temp - sample[0]
            if abs(temp_diff) < 1:
                trend = "stable"
            elif temp_diff > 0:
                trend = "increasing"
            else:
                trend = "decreasing"
            
            print(f"Temperature trend: {trend} ({temp_diff:+.2f}°C change)")
            
        except Exception as e:
            print(f"Error making prediction for sample {i}: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Endpoint testing completed!")

def get_latest_endpoint():
    """
    Get the most recently created endpoint
    """
    sagemaker = boto3.client('sagemaker')
    
    try:
        # List endpoints and find the latest sensor prediction endpoint
        response = sagemaker.list_endpoints(
            SortBy='CreationTime',
            SortOrder='Descending',
            NameContains='sensor-prediction-endpoint'
        )
        
        if response['Endpoints']:
            latest_endpoint = response['Endpoints'][0]
            endpoint_name = latest_endpoint['EndpointName']
            status = latest_endpoint['EndpointStatus']
            
            print(f"Found endpoint: {endpoint_name}")
            print(f"Status: {status}")
            
            if status == 'InService':
                return endpoint_name
            else:
                print(f"Endpoint is not ready yet. Current status: {status}")
                return None
        else:
            print("No sensor prediction endpoints found.")
            return None
            
    except Exception as e:
        print(f"Error finding endpoint: {str(e)}")
        return None

if __name__ == "__main__":
    # Use the latest working endpoint
    endpoint_name = 'sensor-prediction-endpoint-20250805-155734'
    
    if endpoint_name:
        test_endpoint_predictions(endpoint_name)
    else:
        print("Please provide the endpoint name manually:")
        print("python test_endpoint_predictions.py")
        print("Or wait for the endpoint deployment to complete.")