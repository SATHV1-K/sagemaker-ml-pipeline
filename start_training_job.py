import boto3
import json
from datetime import datetime

def start_training_job():
    """
    Directly start a SageMaker training job
    """
    sagemaker = boto3.client('sagemaker')
    
    # Generate unique job name
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    job_name = f'sensor-prediction-training-{timestamp}'
    
    # Training job parameters
    training_params = {
        'TrainingJobName': job_name,
        'RoleArn': 'arn:aws:iam::296062569059:role/sagemaker-ml-pipeline-sagemaker-role-f5ofrag0',
        'AlgorithmSpecification': {
            'TrainingImage': '683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1',
            'TrainingInputMode': 'File'
        },
        'InputDataConfig': [
            {
                'ChannelName': 'train',
                'DataSource': {
                    'S3DataSource': {
                        'S3DataType': 'S3Prefix',
                        'S3Uri': 's3://sagemaker-ml-pipeline-data-f5ofrag0/training/realistic_training_data.csv',
                        'S3DataDistributionType': 'FullyReplicated'
                    }
                },
                'ContentType': 'text/csv',
                'CompressionType': 'None'
            }
        ],
        'OutputDataConfig': {
            'S3OutputPath': 's3://sagemaker-ml-pipeline-models-f5ofrag0/output/'
        },
        'ResourceConfig': {
            'InstanceType': 'ml.m5.large',
            'InstanceCount': 1,
            'VolumeSizeInGB': 10
        },
        'StoppingCondition': {
            'MaxRuntimeInSeconds': 3600
        },
        'HyperParameters': {
            'max_depth': '6',
            'eta': '0.3',
            'gamma': '4',
            'min_child_weight': '6',
            'subsample': '0.8',
            'objective': 'reg:squarederror',
            'num_round': '100'
        }
    }
    
    try:
        print(f"Starting SageMaker training job: {job_name}")
        response = sagemaker.create_training_job(**training_params)
        print(f"Training job started successfully!")
        print(f"Training Job ARN: {response['TrainingJobArn']}")
        return job_name
    except Exception as e:
        print(f"Error starting training job: {str(e)}")
        return None

if __name__ == "__main__":
    job_name = start_training_job()
    if job_name:
        print(f"\nTo check status, run:")
        print(f"aws sagemaker describe-training-job --training-job-name {job_name}")