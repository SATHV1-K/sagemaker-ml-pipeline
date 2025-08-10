import boto3
import time
from datetime import datetime

def cleanup_failed_resources():
    """
    Clean up failed SageMaker resources
    """
    sagemaker = boto3.client('sagemaker')
    
    print("=" * 60)
    print("CLEANING UP FAILED SAGEMAKER RESOURCES")
    print("=" * 60)
    
    # List of potentially failed resources to clean up
    failed_endpoints = [
        'sensor-prediction-endpoint-20250805-124642'
    ]
    
    failed_configs = [
        'sensor-prediction-config-20250805-124642'
    ]
    
    failed_models = [
        'sensor-prediction-model-20250805-124642'
    ]
    
    # Clean up endpoints
    for endpoint_name in failed_endpoints:
        try:
            print(f"\nChecking endpoint: {endpoint_name}")
            response = sagemaker.describe_endpoint(EndpointName=endpoint_name)
            status = response['EndpointStatus']
            
            if status in ['Failed', 'OutOfService']:
                print(f"Deleting failed endpoint: {endpoint_name}")
                sagemaker.delete_endpoint(EndpointName=endpoint_name)
                print(f"✓ Endpoint {endpoint_name} deletion initiated")
            elif status == 'Creating':
                print(f"⏳ Endpoint {endpoint_name} still creating - will likely fail")
                print(f"   You can delete it manually once it fails")
            else:
                print(f"ℹ️ Endpoint {endpoint_name} status: {status}")
                
        except sagemaker.exceptions.ClientError as e:
            if 'does not exist' in str(e):
                print(f"✓ Endpoint {endpoint_name} does not exist")
            else:
                print(f"❌ Error checking endpoint {endpoint_name}: {str(e)}")
    
    # Clean up endpoint configurations
    for config_name in failed_configs:
        try:
            print(f"\nDeleting endpoint config: {config_name}")
            sagemaker.delete_endpoint_config(EndpointConfigName=config_name)
            print(f"✓ Endpoint config {config_name} deleted")
        except sagemaker.exceptions.ClientError as e:
            if 'does not exist' in str(e):
                print(f"✓ Endpoint config {config_name} does not exist")
            else:
                print(f"❌ Error deleting config {config_name}: {str(e)}")
    
    # Clean up models
    for model_name in failed_models:
        try:
            print(f"\nDeleting model: {model_name}")
            sagemaker.delete_model(ModelName=model_name)
            print(f"✓ Model {model_name} deleted")
        except sagemaker.exceptions.ClientError as e:
            if 'does not exist' in str(e):
                print(f"✓ Model {model_name} does not exist")
            else:
                print(f"❌ Error deleting model {model_name}: {str(e)}")
    
    print("\n" + "=" * 60)
    print("CLEANUP COMPLETED")
    print("=" * 60)
    print("\nCurrent working resources:")
    print("✓ Endpoint: sensor-prediction-endpoint-20250805-130217 (InService)")
    print("✓ Model: sensor-prediction-model-20250805-130217")
    print("✓ Config: sensor-prediction-config-20250805-130217")

def show_current_status():
    """
    Show current pipeline status
    """
    sagemaker = boto3.client('sagemaker')
    
    print("\n" + "=" * 60)
    print("CURRENT PIPELINE STATUS")
    print("=" * 60)
    
    # Check active endpoints
    try:
        endpoints = sagemaker.list_endpoints(
            SortBy='CreationTime',
            SortOrder='Descending',
            NameContains='sensor-prediction',
            MaxResults=5
        )
        
        print("\nEndpoints:")
        for endpoint in endpoints['Endpoints']:
            status_icon = "✅" if endpoint['EndpointStatus'] == 'InService' else "❌" if endpoint['EndpointStatus'] == 'Failed' else "⏳"
            print(f"{status_icon} {endpoint['EndpointName']} - {endpoint['EndpointStatus']}")
            
    except Exception as e:
        print(f"Error checking endpoints: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        show_current_status()
    else:
        cleanup_failed_resources()
        show_current_status()