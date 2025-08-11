import boto3
import time
from datetime import datetime

try:
    from ..config.config import (
        AWS_REGION, 
        SAGEMAKER_ROLE_ARN, 
        XGBOOST_CONTAINER_IMAGE,
        TRAINING_INSTANCE_TYPE,
        PROJECT_NAME
    )
except ImportError:
    print("❌ config.py not found. Please copy config.example.py to config.py and update with your AWS details.")
    exit(1)

def start_training_job(bucket_name, input_data_key='training/realistic_training_data.csv'):
    """
    Start a SageMaker training job with XGBoost
    
    Args:
        bucket_name (str): S3 bucket containing training data
        input_data_key (str): S3 key for training data file
    """
    
    # Initialize SageMaker client
    sagemaker = boto3.client('sagemaker', region_name=AWS_REGION)
    
    # Generate unique job name with timestamp
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    job_name = f'sensor-prediction-training-{timestamp}'
    
    # Training job configuration
    training_params = {
        'TrainingJobName': job_name,
        'RoleArn': SAGEMAKER_ROLE_ARN,
        'AlgorithmSpecification': {
            'TrainingImage': XGBOOST_CONTAINER_IMAGE,
            'TrainingInputMode': 'File'
        },
        'InputDataConfig': [
            {
                'ChannelName': 'training',
                'DataSource': {
                    'S3DataSource': {
                        'S3DataType': 'S3Prefix',
                        'S3Uri': f's3://{bucket_name}/{input_data_key}',
                        'S3DataDistributionType': 'FullyReplicated'
                    }
                },
                'ContentType': 'text/csv',
                'CompressionType': 'None'
            }
        ],
        'OutputDataConfig': {
            'S3OutputPath': f's3://{bucket_name}/model-artifacts/'
        },
        'ResourceConfig': {
            'InstanceType': TRAINING_INSTANCE_TYPE,
            'InstanceCount': 1,
            'VolumeSizeInGB': 30
        },
        'StoppingCondition': {
            'MaxRuntimeInSeconds': 3600  # 1 hour
        },
        'HyperParameters': {
            'objective': 'reg:squarederror',
            'num_round': '100',
            'max_depth': '6',
            'eta': '0.1',
            'subsample': '0.8',
            'colsample_bytree': '0.8',
            'min_child_weight': '1',
            'silent': '1'
        },
        'Tags': [
            {
                'Key': 'Project',
                'Value': PROJECT_NAME
            },
            {
                'Key': 'Environment',
                'Value': 'development'
            }
        ]
    }
    
    try:
        print(f"🚀 Starting training job: {job_name}")
        print(f"📊 Training data: s3://{bucket_name}/{input_data_key}")
        print(f"🤖 Container image: {XGBOOST_CONTAINER_IMAGE}")
        print(f"💻 Instance type: {TRAINING_INSTANCE_TYPE}")
        print(f"🔑 Role ARN: {SAGEMAKER_ROLE_ARN}")
        
        # Start the training job
        response = sagemaker.create_training_job(**training_params)
        
        print(f"✅ Training job started successfully!")
        print(f"📝 Job Name: {job_name}")
        print(f"🔗 Training Job ARN: {response['TrainingJobArn']}")
        
        # Wait a moment and check initial status
        time.sleep(5)
        
        status_response = sagemaker.describe_training_job(TrainingJobName=job_name)
        print(f"📊 Initial Status: {status_response['TrainingJobStatus']}")
        
        if status_response['TrainingJobStatus'] == 'Failed':
            print(f"❌ Training job failed: {status_response.get('FailureReason', 'Unknown error')}")
        else:
            print(f"\n💡 Monitor progress with:")
            print(f"   aws sagemaker describe-training-job --training-job-name {job_name}")
            print(f"\n📊 Or use the pipeline manager:")
            print(f"   python pipeline_manager_github.py --status {bucket_name}")
        
        return job_name
        
    except Exception as e:
        print(f"❌ Error starting training job: {e}")
        return None

def check_training_status(job_name):
    """
    Check the status of a training job
    
    Args:
        job_name (str): Name of the training job
    """
    sagemaker = boto3.client('sagemaker', region_name=AWS_REGION)
    
    try:
        response = sagemaker.describe_training_job(TrainingJobName=job_name)
        
        status = response['TrainingJobStatus']
        print(f"📊 Training Job Status: {status}")
        
        if status == 'Completed':
            print(f"✅ Training completed successfully!")
            print(f"📁 Model artifacts: {response['ModelArtifacts']['S3ModelArtifacts']}")
        elif status == 'Failed':
            print(f"❌ Training failed: {response.get('FailureReason', 'Unknown error')}")
        elif status == 'InProgress':
            print(f"🔄 Training in progress...")
            if 'TrainingStartTime' in response:
                start_time = response['TrainingStartTime']
                elapsed = datetime.now(start_time.tzinfo) - start_time
                print(f"⏱️  Elapsed time: {elapsed}")
        
        return status
        
    except Exception as e:
        print(f"❌ Error checking training status: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python start_training_job_github.py <bucket_name> [input_data_key]")
        print("\nExample:")
        print("python start_training_job_github.py my-data-bucket")
        print("python start_training_job_github.py my-data-bucket training/my_data.csv")
        sys.exit(1)
    
    bucket_name = sys.argv[1]
    input_data_key = sys.argv[2] if len(sys.argv) > 2 else 'training/realistic_training_data.csv'
    
    print("=" * 60)
    print("🚀 SAGEMAKER TRAINING JOB STARTER")
    print("=" * 60)
    
    job_name = start_training_job(bucket_name, input_data_key)
    
    if job_name:
        print(f"\n🎯 Training job '{job_name}' has been started!")
        print(f"\n💡 To check status later, run:")
        print(f"   python start_training_job_github.py --status {job_name}")
    
    # Handle status check
    if len(sys.argv) > 1 and sys.argv[1] == "--status" and len(sys.argv) > 2:
        job_name = sys.argv[2]
        print(f"\n📊 Checking status for: {job_name}")
        check_training_status(job_name)