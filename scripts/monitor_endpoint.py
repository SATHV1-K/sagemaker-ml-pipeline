import boto3
import time
import json
from datetime import datetime

def monitor_endpoint_deployment(endpoint_name, max_wait_minutes=15):
    """
    Monitor SageMaker endpoint deployment status
    """
    sagemaker = boto3.client('sagemaker')
    runtime = boto3.client('sagemaker-runtime')
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    print(f"Monitoring endpoint: {endpoint_name}")
    print(f"Maximum wait time: {max_wait_minutes} minutes")
    print("=" * 60)
    
    while True:
        try:
            # Get endpoint status
            response = sagemaker.describe_endpoint(EndpointName=endpoint_name)
            status = response['EndpointStatus']
            
            elapsed_time = time.time() - start_time
            elapsed_minutes = elapsed_time / 60
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Status: {status} (Elapsed: {elapsed_minutes:.1f} min)")
            
            if status == 'InService':
                print("\n🎉 Endpoint is now IN SERVICE!")
                print("=" * 60)
                
                # Test the endpoint
                print("Testing endpoint with sample data...")
                test_sample = [25.5, 68.2, 0.374, 8, 1, 217, 25.1, 67.8, 1.2, 2.1]
                csv_input = ','.join(map(str, test_sample))
                
                try:
                    prediction_response = runtime.invoke_endpoint(
                        EndpointName=endpoint_name,
                        ContentType='text/csv',
                        Body=csv_input
                    )
                    
                    prediction = prediction_response['Body'].read().decode('utf-8').strip()
                    print(f"✓ Test prediction successful: {prediction}")
                    print(f"✓ Endpoint URL: {response['EndpointArn']}")
                    
                except Exception as e:
                    print(f"❌ Test prediction failed: {str(e)}")
                
                return True
                
            elif status == 'Failed':
                print(f"\n❌ Endpoint deployment FAILED!")
                if 'FailureReason' in response:
                    print(f"Failure reason: {response['FailureReason']}")
                return False
                
            elif elapsed_time > max_wait_seconds:
                print(f"\n⏰ Timeout reached ({max_wait_minutes} minutes)")
                print("Endpoint is still creating. You can continue monitoring manually.")
                return False
            
            # Wait before next check
            time.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            print(f"Error monitoring endpoint: {str(e)}")
            return False

def get_endpoint_info(endpoint_name):
    """Get detailed endpoint information"""
    sagemaker = boto3.client('sagemaker')
    
    try:
        response = sagemaker.describe_endpoint(EndpointName=endpoint_name)
        
        print("Endpoint Details:")
        print("=" * 40)
        print(f"Name: {response['EndpointName']}")
        print(f"Status: {response['EndpointStatus']}")
        print(f"Config: {response['EndpointConfigName']}")
        print(f"Created: {response['CreationTime']}")
        print(f"Modified: {response['LastModifiedTime']}")
        
        if 'FailureReason' in response:
            print(f"Failure Reason: {response['FailureReason']}")
            
        return response
        
    except Exception as e:
        print(f"Error getting endpoint info: {str(e)}")
        return None

if __name__ == "__main__":
    import sys
    
    endpoint_name = "sensor-prediction-endpoint-20250805-124642"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--info":
            get_endpoint_info(endpoint_name)
        elif sys.argv[1] == "--monitor":
            monitor_endpoint_deployment(endpoint_name)
        else:
            endpoint_name = sys.argv[1]
            monitor_endpoint_deployment(endpoint_name)
    else:
        monitor_endpoint_deployment(endpoint_name)