import boto3
import time
from datetime import datetime

try:
    from ..config.config import (
        AWS_REGION, 
        SAGEMAKER_ROLE_ARN, 
        XGBOOST_CONTAINER_IMAGE,
        ENDPOINT_INSTANCE_TYPE,
        PROJECT_NAME
    )
except ImportError:
    print("❌ config.py not found. Please copy config.example.py to config.py and update with your AWS details.")
    exit(1)

def deploy_model(model_artifacts_s3_path, model_name=None, endpoint_name=None):
    """
    Deploy a trained model to a SageMaker endpoint
    
    Args:
        model_artifacts_s3_path (str): S3 path to model artifacts (model.tar.gz)
        model_name (str): Optional custom model name
        endpoint_name (str): Optional custom endpoint name
    """
    
    # Initialize SageMaker client
    sagemaker = boto3.client('sagemaker', region_name=AWS_REGION)
    
    # Generate unique names with timestamp
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    
    if not model_name:
        model_name = f'sensor-prediction-model-{timestamp}'
    if not endpoint_name:
        endpoint_name = f'sensor-prediction-endpoint-{timestamp}'
    
    endpoint_config_name = f'sensor-prediction-config-{timestamp}'
    
    try:
        print(f"🤖 Creating SageMaker model: {model_name}")
        print(f"📁 Model artifacts: {model_artifacts_s3_path}")
        print(f"🔑 Role ARN: {SAGEMAKER_ROLE_ARN}")
        print(f"🐳 Container image: {XGBOOST_CONTAINER_IMAGE}")
        
        # Step 1: Create SageMaker Model
        model_response = sagemaker.create_model(
            ModelName=model_name,
            PrimaryContainer={
                'Image': XGBOOST_CONTAINER_IMAGE,
                'ModelDataUrl': model_artifacts_s3_path,
                'Environment': {
                    'SAGEMAKER_PROGRAM': 'inference.py',
                    'SAGEMAKER_SUBMIT_DIRECTORY': '/opt/ml/code'
                }
            },
            ExecutionRoleArn=SAGEMAKER_ROLE_ARN,
            Tags=[
                {
                    'Key': 'Project',
                    'Value': PROJECT_NAME
                },
                {
                    'Key': 'Environment', 
                    'Value': 'development'
                }
            ]
        )
        
        print(f"✅ Model created: {model_response['ModelArn']}")
        
        # Step 2: Create Endpoint Configuration
        print(f"⚙️ Creating endpoint configuration: {endpoint_config_name}")
        print(f"💻 Instance type: {ENDPOINT_INSTANCE_TYPE}")
        
        config_response = sagemaker.create_endpoint_config(
            EndpointConfigName=endpoint_config_name,
            ProductionVariants=[
                {
                    'VariantName': 'primary',
                    'ModelName': model_name,
                    'InitialInstanceCount': 1,
                    'InstanceType': ENDPOINT_INSTANCE_TYPE,
                    'InitialVariantWeight': 1.0
                }
            ],
            Tags=[
                {
                    'Key': 'Project',
                    'Value': PROJECT_NAME
                },
                {
                    'Key': 'Environment',
                    'Value': 'development'
                }
            ]
        )
        
        print(f"✅ Endpoint configuration created: {config_response['EndpointConfigArn']}")
        
        # Step 3: Create Endpoint
        print(f"🚀 Creating endpoint: {endpoint_name}")
        print(f"⏳ This may take 5-10 minutes...")
        
        endpoint_response = sagemaker.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name,
            Tags=[
                {
                    'Key': 'Project',
                    'Value': PROJECT_NAME
                },
                {
                    'Key': 'Environment',
                    'Value': 'development'
                }
            ]
        )
        
        print(f"✅ Endpoint creation initiated: {endpoint_response['EndpointArn']}")
        
        # Wait for endpoint to be in service
        print(f"⏳ Waiting for endpoint to be in service...")
        
        waiter = sagemaker.get_waiter('endpoint_in_service')
        waiter.wait(
            EndpointName=endpoint_name,
            WaiterConfig={
                'Delay': 30,  # Check every 30 seconds
                'MaxAttempts': 20  # Wait up to 10 minutes
            }
        )
        
        # Check final status
        endpoint_desc = sagemaker.describe_endpoint(EndpointName=endpoint_name)
        
        if endpoint_desc['EndpointStatus'] == 'InService':
            print(f"🎉 Endpoint is now in service!")
            print(f"🔗 Endpoint Name: {endpoint_name}")
            print(f"📊 Status: {endpoint_desc['EndpointStatus']}")
            print(f"🕐 Creation Time: {endpoint_desc['CreationTime']}")
            
            print(f"\n💡 Test your endpoint with:")
            print(f"   python test_endpoint_predictions_github.py {endpoint_name}")
            
            return endpoint_name
        else:
            print(f"❌ Endpoint failed to start: {endpoint_desc['EndpointStatus']}")
            if 'FailureReason' in endpoint_desc:
                print(f"   Reason: {endpoint_desc['FailureReason']}")
            return None
            
    except Exception as e:
        print(f"❌ Error deploying model: {e}")
        return None

def check_endpoint_status(endpoint_name):
    """
    Check the status of an endpoint
    
    Args:
        endpoint_name (str): Name of the endpoint
    """
    sagemaker = boto3.client('sagemaker', region_name=AWS_REGION)
    
    try:
        response = sagemaker.describe_endpoint(EndpointName=endpoint_name)
        
        status = response['EndpointStatus']
        print(f"📊 Endpoint Status: {status}")
        print(f"🔗 Endpoint Name: {endpoint_name}")
        print(f"🕐 Creation Time: {response['CreationTime']}")
        
        if status == 'InService':
            print(f"✅ Endpoint is ready for predictions!")
        elif status == 'Failed':
            print(f"❌ Endpoint failed: {response.get('FailureReason', 'Unknown error')}")
        elif status in ['Creating', 'Updating']:
            print(f"🔄 Endpoint is {status.lower()}...")
        
        return status
        
    except Exception as e:
        print(f"❌ Error checking endpoint status: {e}")
        return None

def list_recent_training_jobs(max_results=5):
    """
    List recent training jobs to help find model artifacts
    """
    sagemaker = boto3.client('sagemaker', region_name=AWS_REGION)
    
    try:
        response = sagemaker.list_training_jobs(
            SortBy='CreationTime',
            SortOrder='Descending',
            MaxResults=max_results
        )
        
        print(f"\n📊 Recent Training Jobs:")
        for i, job in enumerate(response['TrainingJobSummaries'], 1):
            status_emoji = {
                'Completed': '✅',
                'Failed': '❌',
                'InProgress': '🔄'
            }.get(job['TrainingJobStatus'], '❓')
            
            print(f"  {i}. {status_emoji} {job['TrainingJobName']} - {job['TrainingJobStatus']}")
            
            if job['TrainingJobStatus'] == 'Completed':
                # Get model artifacts path
                job_details = sagemaker.describe_training_job(TrainingJobName=job['TrainingJobName'])
                artifacts_path = job_details['ModelArtifacts']['S3ModelArtifacts']
                print(f"     📁 Model artifacts: {artifacts_path}")
        
        return response['TrainingJobSummaries']
        
    except Exception as e:
        print(f"❌ Error listing training jobs: {e}")
        return []

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("🚀 SAGEMAKER MODEL DEPLOYMENT")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\n📋 Usage Options:")
        print("1. Deploy with model artifacts path:")
        print("   python deploy_model_github.py <s3_model_artifacts_path>")
        print("\n2. Check endpoint status:")
        print("   python deploy_model_github.py --status <endpoint_name>")
        print("\n3. List recent training jobs:")
        print("   python deploy_model_github.py --list-jobs")
        print("\n📝 Examples:")
        print("   python deploy_model_github.py s3://my-bucket/model-artifacts/job-name/output/model.tar.gz")
        print("   python deploy_model_github.py --status my-endpoint-name")
        print("   python deploy_model_github.py --list-jobs")
        sys.exit(1)
    
    if sys.argv[1] == "--status" and len(sys.argv) > 2:
        endpoint_name = sys.argv[2]
        print(f"📊 Checking status for endpoint: {endpoint_name}")
        check_endpoint_status(endpoint_name)
        
    elif sys.argv[1] == "--list-jobs":
        print("📋 Listing recent training jobs...")
        jobs = list_recent_training_jobs(10)
        
        if jobs:
            print(f"\n💡 To deploy a completed model, use:")
            print(f"   python deploy_model_github.py <model_artifacts_s3_path>")
        
    else:
        model_artifacts_path = sys.argv[1]
        
        if not model_artifacts_path.startswith('s3://'):
            print("❌ Model artifacts path must be an S3 URI (s3://...)")
            sys.exit(1)
        
        print(f"🚀 Deploying model from: {model_artifacts_path}")
        
        endpoint_name = deploy_model(model_artifacts_path)
        
        if endpoint_name:
            print(f"\n🎉 Deployment successful!")
            print(f"🔗 Endpoint Name: {endpoint_name}")
            print(f"\n💡 Next steps:")
            print(f"   1. Test predictions: python test_endpoint_predictions_github.py {endpoint_name}")
            print(f"   2. Monitor endpoint: python deploy_model_github.py --status {endpoint_name}")
        else:
            print(f"\n❌ Deployment failed. Check the logs above for details.")