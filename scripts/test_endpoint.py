#!/usr/bin/env python3
"""
Test script for SageMaker endpoint
"""

import boto3
import json
import pandas as pd
import numpy as np
from datetime import datetime

def get_endpoint_name():
    """
    Get the SageMaker endpoint name from Terraform outputs
    """
    try:
        import subprocess
        result = subprocess.run(
            ['terraform', 'output', '-json'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        outputs = json.loads(result.stdout)
        return outputs['sagemaker_endpoint_name']['value']
    except Exception as e:
        print(f"Error getting endpoint name: {e}")
        print("Please provide the endpoint name manually.")
        return input("Enter SageMaker endpoint name: ")

def test_single_prediction(endpoint_name, runtime_client):
    """
    Test a single prediction
    """
    print("\n🧪 Testing single prediction...")
    
    # Sample input features:
    # avg_temperature, avg_humidity, temp_humidity_ratio, temp_range, humidity_range,
    # hour_of_day, day_of_week, day_of_year, record_count, avg_data_quality
    test_data = "25.5,65.2,0.391,2.1,15.3,14,3,180,50,0.95"
    
    try:
        response = runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='text/csv',
            Body=test_data
        )
        
        result = response['Body'].read().decode()
        print(f"✅ Input features: {test_data}")
        print(f"✅ Predicted temperature: {result}°C")
        return float(result)
        
    except Exception as e:
        print(f"❌ Error making prediction: {e}")
        return None

def test_batch_predictions(endpoint_name, runtime_client, num_samples=5):
    """
    Test multiple predictions with random data
    """
    print(f"\n🧪 Testing {num_samples} batch predictions...")
    
    predictions = []
    
    for i in range(num_samples):
        # Generate random but realistic sensor data
        avg_temp = np.random.normal(25, 5)  # 25°C ± 5°C
        avg_humidity = np.random.normal(60, 15)  # 60% ± 15%
        temp_humidity_ratio = avg_temp / avg_humidity
        temp_range = np.random.uniform(1, 5)
        humidity_range = np.random.uniform(5, 20)
        hour_of_day = np.random.randint(0, 24)
        day_of_week = np.random.randint(1, 8)
        day_of_year = np.random.randint(1, 366)
        record_count = np.random.randint(40, 60)  # Records in 5-min window
        data_quality = np.random.uniform(0.8, 1.0)
        
        # Format as CSV string
        test_data = f"{avg_temp:.2f},{avg_humidity:.2f},{temp_humidity_ratio:.4f},{temp_range:.2f},{humidity_range:.2f},{hour_of_day},{day_of_week},{day_of_year},{record_count},{data_quality:.3f}"
        
        try:
            response = runtime_client.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType='text/csv',
                Body=test_data
            )
            
            result = response['Body'].read().decode()
            prediction = float(result)
            
            predictions.append({
                'sample': i + 1,
                'input_temp': avg_temp,
                'input_humidity': avg_humidity,
                'predicted_temp': prediction,
                'difference': prediction - avg_temp
            })
            
            print(f"Sample {i+1}: Input={avg_temp:.2f}°C, Predicted={prediction:.2f}°C, Diff={prediction-avg_temp:.2f}°C")
            
        except Exception as e:
            print(f"❌ Error in sample {i+1}: {e}")
    
    return predictions

def analyze_predictions(predictions):
    """
    Analyze the prediction results
    """
    if not predictions:
        print("❌ No predictions to analyze")
        return
    
    print("\n📊 Prediction Analysis:")
    
    df = pd.DataFrame(predictions)
    
    print(f"   Average input temperature: {df['input_temp'].mean():.2f}°C")
    print(f"   Average predicted temperature: {df['predicted_temp'].mean():.2f}°C")
    print(f"   Average difference: {df['difference'].mean():.2f}°C")
    print(f"   Standard deviation of differences: {df['difference'].std():.2f}°C")
    print(f"   Min difference: {df['difference'].min():.2f}°C")
    print(f"   Max difference: {df['difference'].max():.2f}°C")
    
    # Check if predictions are reasonable
    reasonable_predictions = df[(df['difference'].abs() < 5)].shape[0]
    total_predictions = len(df)
    
    print(f"   Reasonable predictions (±5°C): {reasonable_predictions}/{total_predictions} ({reasonable_predictions/total_predictions*100:.1f}%)")

def check_endpoint_status(endpoint_name, sagemaker_client):
    """
    Check if the endpoint is ready
    """
    try:
        response = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        status = response['EndpointStatus']
        
        print(f"📊 Endpoint Status: {status}")
        
        if status == 'InService':
            print("✅ Endpoint is ready for predictions")
            return True
        else:
            print(f"⏳ Endpoint is {status}. Please wait for it to be InService.")
            return False
            
    except Exception as e:
        print(f"❌ Error checking endpoint status: {e}")
        return False

def main():
    """
    Main test function
    """
    print("🧪 SageMaker Endpoint Testing Script")
    print("===================================\n")
    
    # Initialize AWS clients
    try:
        sagemaker_client = boto3.client('sagemaker')
        runtime_client = boto3.client('sagemaker-runtime')
        print("✅ AWS clients initialized")
    except Exception as e:
        print(f"❌ Error initializing AWS clients: {e}")
        print("Please check your AWS credentials and region.")
        return
    
    # Get endpoint name
    endpoint_name = get_endpoint_name()
    print(f"🎯 Testing endpoint: {endpoint_name}")
    
    # Check endpoint status
    if not check_endpoint_status(endpoint_name, sagemaker_client):
        return
    
    # Test single prediction
    single_result = test_single_prediction(endpoint_name, runtime_client)
    
    if single_result is not None:
        # Test batch predictions
        batch_results = test_batch_predictions(endpoint_name, runtime_client, 10)
        
        # Analyze results
        analyze_predictions(batch_results)
        
        print("\n🎉 Testing completed successfully!")
        print("\n📖 Next steps:")
        print("   1. Integrate the endpoint into your application")
        print("   2. Monitor endpoint performance in AWS Console")
        print("   3. Set up CloudWatch alarms for monitoring")
        print("   4. Consider auto-scaling for production workloads")
    else:
        print("❌ Testing failed. Please check the endpoint and try again.")

if __name__ == "__main__":
    main()