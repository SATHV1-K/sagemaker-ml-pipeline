import boto3
import time
from datetime import datetime

def deploy_model():
    sagemaker = boto3.client('sagemaker')
    
    # Configuration
    model_name = f"sensor-prediction-model-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    endpoint_config_name = f"sensor-prediction-config-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    endpoint_name = f"sensor-prediction-endpoint-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    role_arn = 'arn:aws:iam::296062569059:role/sagemaker-ml-pipeline-sagemaker-role-f5ofrag0'
    model_artifacts = 's3://sagemaker-ml-pipeline-models-f5ofrag0/output/sensor-prediction-training-20250805-153525/output/model.tar.gz'
    container_image = '683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1'
    
    try:
        # Step 1: Create SageMaker Model
        print(f"Creating SageMaker model: {model_name}")
        create_model_response = sagemaker.create_model(
            ModelName=model_name,
            PrimaryContainer={
                'Image': container_image,
                'ModelDataUrl': model_artifacts
            },
            ExecutionRoleArn=role_arn
        )
        print(f"Model created: {create_model_response['ModelArn']}")
        
        # Step 2: Create Endpoint Configuration
        print(f"Creating endpoint configuration: {endpoint_config_name}")
        create_config_response = sagemaker.create_endpoint_config(
            EndpointConfigName=endpoint_config_name,
            ProductionVariants=[
                {
                    'VariantName': 'primary',
                    'ModelName': model_name,
                    'InitialInstanceCount': 1,
                    'InstanceType': 'ml.t2.medium',
                    'InitialVariantWeight': 1.0
                }
            ]
        )
        print(f"Endpoint configuration created: {create_config_response['EndpointConfigArn']}")
        
        # Step 3: Create Endpoint
        print(f"Creating endpoint: {endpoint_name}")
        create_endpoint_response = sagemaker.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name
        )
        print(f"Endpoint creation initiated: {create_endpoint_response['EndpointArn']}")
        
        # Step 4: Wait for endpoint to be in service
        print("Waiting for endpoint to be in service...")
        waiter = sagemaker.get_waiter('endpoint_in_service')
        waiter.wait(
            EndpointName=endpoint_name,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 20
            }
        )
        
        # Get endpoint status
        endpoint_response = sagemaker.describe_endpoint(EndpointName=endpoint_name)
        print(f"\nEndpoint Status: {endpoint_response['EndpointStatus']}")
        print(f"Endpoint Name: {endpoint_name}")
        print(f"Endpoint ARN: {endpoint_response['EndpointArn']}")
        
        return {
            'model_name': model_name,
            'endpoint_config_name': endpoint_config_name,
            'endpoint_name': endpoint_name,
            'endpoint_arn': endpoint_response['EndpointArn']
        }
        
    except Exception as e:
        print(f"Error during deployment: {str(e)}")
        raise e

if __name__ == "__main__":
    result = deploy_model()
    print(f"\nDeployment completed successfully!")
    print(f"Endpoint name: {result['endpoint_name']}")
    print(f"You can now use this endpoint for real-time predictions.")