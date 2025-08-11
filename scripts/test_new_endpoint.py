import boto3
import json
import numpy as np

def test_latest_endpoint():
    """
    Test the latest endpoint with realistic predictions
    """
    runtime = boto3.client('sagemaker-runtime')
    
    # Use the latest endpoint
    endpoint_name = 'sensor-prediction-endpoint-20250805-155734'
    
    print(f"Testing endpoint: {endpoint_name}")
    print("=" * 60)
    
    # Test samples with realistic sensor data
    test_samples = [
        {
            'description': 'Morning cool temperature',
            'features': [18.5, 75.2, 0.247, 7, 1, 217, 18.2, 76.1, 1.1, 1.8]
        },
        {
            'description': 'Afternoon warm temperature', 
            'features': [28.3, 58.4, 0.485, 14, 1, 217, 27.9, 59.2, 2.2, 2.9]
        },
        {
            'description': 'Evening moderate temperature',
            'features': [22.7, 68.9, 0.329, 19, 1, 217, 23.1, 67.5, 1.7, 2.3]
        },
        {
            'description': 'Night cool temperature',
            'features': [16.2, 82.1, 0.197, 23, 1, 217, 16.8, 81.3, 1.3, 2.1]
        },
        {
            'description': 'Hot summer day',
            'features': [35.1, 45.3, 0.775, 13, 2, 218, 34.7, 46.1, 2.8, 3.4]
        }
    ]
    
    for i, sample in enumerate(test_samples, 1):
        try:
            # Prepare input data
            input_data = ','.join(map(str, sample['features']))
            
            # Make prediction
            response = runtime.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType='text/csv',
                Body=input_data
            )
            
            # Parse result
            result = json.loads(response['Body'].read().decode())
            predicted_temp = float(result)
            
            current_temp = sample['features'][0]
            temp_change = predicted_temp - current_temp
            
            print(f"Test Sample {i}: {sample['description']}")
            print(f"  Current temperature: {current_temp}°C")
            print(f"  Predicted next temperature: {predicted_temp:.2f}°C")
            print(f"  Temperature change: {temp_change:+.2f}°C")
            print(f"  Prediction seems: {'✅ Realistic' if 10 <= predicted_temp <= 40 and abs(temp_change) <= 10 else '❌ Unrealistic'}")
            print()
            
        except Exception as e:
            print(f"❌ Error testing sample {i}: {str(e)}")
            print()
    
    print("=" * 60)
    print("Endpoint testing completed!")

if __name__ == "__main__":
    test_latest_endpoint()