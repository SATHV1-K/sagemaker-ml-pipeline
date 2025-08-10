import boto3
import json
import numpy as np
from datetime import datetime, timedelta

try:
    from config import AWS_REGION
except ImportError:
    print("❌ config.py not found. Please copy config.example.py to config.py and update with your AWS details.")
    exit(1)

def create_test_samples():
    """
    Create realistic test samples for sensor prediction
    
    Returns:
        list: List of test samples with feature vectors
    """
    
    test_samples = [
        {
            'description': 'Morning temperature rise',
            'features': [25.5, 68.2, 0.374, 8, 1, 217, 25.1, 67.8, 1.2, 2.1],
            'context': {
                'temperature': 25.5,
                'humidity': 68.2,
                'hour': 8,
                'day_of_week': 1,
                'day_of_year': 217
            }
        },
        {
            'description': 'Afternoon peak temperature',
            'features': [32.1, 55.3, 0.581, 14, 1, 217, 31.8, 56.1, 2.1, 3.2],
            'context': {
                'temperature': 32.1,
                'humidity': 55.3,
                'hour': 14,
                'day_of_week': 1,
                'day_of_year': 217
            }
        },
        {
            'description': 'Evening cooling',
            'features': [28.7, 72.4, 0.396, 19, 1, 217, 28.9, 71.2, 1.8, 2.8],
            'context': {
                'temperature': 28.7,
                'humidity': 72.4,
                'hour': 19,
                'day_of_week': 1,
                'day_of_year': 217
            }
        },
        {
            'description': 'Late night temperature drop',
            'features': [22.3, 78.1, 0.286, 23, 1, 217, 22.8, 77.5, 1.5, 2.4],
            'context': {
                'temperature': 22.3,
                'humidity': 78.1,
                'hour': 23,
                'day_of_week': 1,
                'day_of_year': 217
            }
        },
        {
            'description': 'Hot summer day',
            'features': [35.2, 45.8, 0.769, 12, 2, 218, 34.8, 46.2, 2.5, 3.1],
            'context': {
                'temperature': 35.2,
                'humidity': 45.8,
                'hour': 12,
                'day_of_week': 2,
                'day_of_year': 218
            }
        }
    ]
    
    return test_samples

def predict_temperature(endpoint_name, features):
    """
    Make a prediction using the SageMaker endpoint
    
    Args:
        endpoint_name (str): Name of the SageMaker endpoint
        features (list): List of feature values
    
    Returns:
        float: Predicted temperature
    """
    
    # Initialize SageMaker runtime client
    runtime = boto3.client('sagemaker-runtime', region_name=AWS_REGION)
    
    try:
        # Convert features to CSV format (XGBoost expects CSV)
        csv_data = ','.join(map(str, features))
        
        # Make prediction
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='text/csv',
            Body=csv_data
        )
        
        # Parse response
        result = response['Body'].read().decode('utf-8')
        prediction = float(result.strip())
        
        return prediction
        
    except Exception as e:
        print(f"❌ Error making prediction: {e}")
        return None

def analyze_prediction(current_temp, predicted_temp):
    """
    Analyze the prediction and provide insights
    
    Args:
        current_temp (float): Current temperature
        predicted_temp (float): Predicted next temperature
    
    Returns:
        dict: Analysis results
    """
    
    temp_change = predicted_temp - current_temp
    
    if abs(temp_change) < 0.5:
        trend = "stable"
        trend_emoji = "➡️"
    elif temp_change > 0:
        trend = "increasing"
        trend_emoji = "📈"
    else:
        trend = "decreasing"
        trend_emoji = "📉"
    
    return {
        'change': temp_change,
        'trend': trend,
        'trend_emoji': trend_emoji,
        'change_description': f"{temp_change:+.2f}°C change"
    }

def test_endpoint(endpoint_name):
    """
    Test the endpoint with multiple samples
    
    Args:
        endpoint_name (str): Name of the SageMaker endpoint
    """
    
    print(f"Testing endpoint: {endpoint_name}")
    print("=" * 60)
    
    test_samples = create_test_samples()
    
    for i, sample in enumerate(test_samples, 1):
        print(f"\nTest Sample {i}:")
        print(f"Input features: {sample['features']}")
        
        context = sample['context']
        print(f"Temperature: {context['temperature']}°C, Humidity: {context['humidity']}%")
        print(f"Time: Hour {context['hour']}, Day of week {context['day_of_week']}")
        
        # Make prediction
        prediction = predict_temperature(endpoint_name, sample['features'])
        
        if prediction is not None:
            print(f"Predicted next temperature: {prediction:.2f}°C")
            
            # Analyze the prediction
            analysis = analyze_prediction(context['temperature'], prediction)
            print(f"Temperature trend: {analysis['trend']} ({analysis['change_description']})")
            
            # Validate prediction reasonableness
            if 5.0 <= prediction <= 50.0:  # Reasonable temperature range
                if abs(analysis['change']) <= 5.0:  # Reasonable change
                    print("✅ Prediction looks reasonable")
                else:
                    print(f"⚠️  Large temperature change: {analysis['change']:+.2f}°C")
            else:
                print(f"❌ Unrealistic prediction: {prediction:.2f}°C")
        else:
            print("❌ Failed to get prediction")
    
    print("\n" + "=" * 60)
    print("Endpoint testing completed!")

def check_endpoint_exists(endpoint_name):
    """
    Check if the endpoint exists and is in service
    
    Args:
        endpoint_name (str): Name of the endpoint
    
    Returns:
        bool: True if endpoint exists and is in service
    """
    
    sagemaker = boto3.client('sagemaker', region_name=AWS_REGION)
    
    try:
        response = sagemaker.describe_endpoint(EndpointName=endpoint_name)
        status = response['EndpointStatus']
        
        if status == 'InService':
            print(f"✅ Endpoint '{endpoint_name}' is in service")
            return True
        else:
            print(f"❌ Endpoint '{endpoint_name}' status: {status}")
            return False
            
    except sagemaker.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ValidationException':
            print(f"❌ Endpoint '{endpoint_name}' does not exist")
        else:
            print(f"❌ Error checking endpoint: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking endpoint: {e}")
        return False

def list_available_endpoints():
    """
    List available endpoints
    
    Returns:
        list: List of endpoint names
    """
    
    sagemaker = boto3.client('sagemaker', region_name=AWS_REGION)
    
    try:
        response = sagemaker.list_endpoints(
            SortBy='CreationTime',
            SortOrder='Descending',
            MaxResults=10
        )
        
        endpoints = []
        print("\n📋 Available Endpoints:")
        
        for endpoint in response['Endpoints']:
            status_emoji = {
                'InService': '✅',
                'Failed': '❌',
                'Creating': '🔄',
                'Updating': '🔄',
                'Deleting': '🗑️'
            }.get(endpoint['EndpointStatus'], '❓')
            
            print(f"  {status_emoji} {endpoint['EndpointName']} - {endpoint['EndpointStatus']}")
            
            if endpoint['EndpointStatus'] == 'InService':
                endpoints.append(endpoint['EndpointName'])
        
        return endpoints
        
    except Exception as e:
        print(f"❌ Error listing endpoints: {e}")
        return []

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("🧪 SAGEMAKER ENDPOINT TESTING")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\n📋 Usage:")
        print("   python test_endpoint_predictions_github.py <endpoint_name>")
        print("   python test_endpoint_predictions_github.py --list")
        print("\n📝 Examples:")
        print("   python test_endpoint_predictions_github.py sensor-prediction-endpoint-20250805-155734")
        print("   python test_endpoint_predictions_github.py --list")
        
        # Show available endpoints
        available_endpoints = list_available_endpoints()
        
        if available_endpoints:
            print(f"\n💡 Try testing one of these endpoints:")
            for endpoint in available_endpoints[:3]:  # Show top 3
                print(f"   python test_endpoint_predictions_github.py {endpoint}")
        
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_available_endpoints()
        sys.exit(0)
    
    endpoint_name = sys.argv[1]
    
    # Check if endpoint exists and is in service
    if not check_endpoint_exists(endpoint_name):
        print(f"\n💡 Available endpoints:")
        list_available_endpoints()
        sys.exit(1)
    
    # Test the endpoint
    print(f"\n🧪 Testing endpoint: {endpoint_name}")
    test_endpoint(endpoint_name)
    
    print(f"\n💡 Tips:")
    print(f"   - Realistic predictions should be between 10-40°C")
    print(f"   - Temperature changes should typically be < 5°C")
    print(f"   - Check AWS CloudWatch for endpoint metrics")
    print(f"   - Monitor costs in AWS Billing dashboard")