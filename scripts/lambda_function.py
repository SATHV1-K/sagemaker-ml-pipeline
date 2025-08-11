import json
import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    """
    Lambda function to trigger SageMaker training job when Glue job completes
    """
    print(f"Received event: {json.dumps(event)}")
    
    # Initialize SageMaker client
    sagemaker = boto3.client('sagemaker')
    
    try:
        # Get environment variables
        sagemaker_role_arn = os.environ['SAGEMAKER_ROLE_ARN']
        data_bucket = os.environ['DATA_BUCKET']
        model_bucket = os.environ['MODEL_BUCKET']
        training_image = os.environ['TRAINING_IMAGE']
        
        # Create unique job name with timestamp
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        job_name = f"sensor-prediction-training-{timestamp}"
        
        # Define training job parameters
        training_params = {
            'TrainingJobName': job_name,
            'RoleArn': sagemaker_role_arn,
            'AlgorithmSpecification': {
                'TrainingImage': training_image,
                'TrainingInputMode': 'File'
            },
            'InputDataConfig': [
                {
                    'ChannelName': 'train',
                    'DataSource': {
                        'S3DataSource': {
                            'S3DataType': 'S3Prefix',
                            'S3Uri': f's3://{data_bucket}/training/',
                            'S3DataDistributionType': 'FullyReplicated'
                        }
                    },
                    'ContentType': 'text/csv',
                    'CompressionType': 'None'
                }
            ],
            'OutputDataConfig': {
                'S3OutputPath': f's3://{model_bucket}/model/'
            },
            'ResourceConfig': {
                'InstanceType': 'ml.m5.large',  # Smallest training instance
                'InstanceCount': 1,
                'VolumeSizeInGB': 10
            },
            'StoppingCondition': {
                'MaxRuntimeInSeconds': 3600  # 1 hour max
            },
            'HyperParameters': {
                'max_depth': '6',
                'eta': '0.3',
                'gamma': '4',
                'min_child_weight': '6',
                'subsample': '0.8',
                'objective': 'reg:squarederror',
                'num_round': '100',
                'data_bucket': data_bucket,
                'model_bucket': model_bucket
            },
            'Tags': [
                {
                    'Key': 'Project',
                    'Value': 'SensorPrediction'
                },
                {
                    'Key': 'Environment',
                    'Value': 'Development'
                }
            ]
        }
        
        print(f"Starting SageMaker training job: {job_name}")
        print(f"Training parameters: {json.dumps(training_params, indent=2, default=str)}")
        
        # Start the training job
        response = sagemaker.create_training_job(**training_params)
        
        print(f"Training job started successfully: {response['TrainingJobArn']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'SageMaker training job started successfully',
                'trainingJobName': job_name,
                'trainingJobArn': response['TrainingJobArn']
            })
        }
        
    except Exception as e:
        print(f"Error starting training job: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to start SageMaker training job'
            })
        }

def check_training_status(job_name):
    """
    Helper function to check training job status
    """
    sagemaker = boto3.client('sagemaker')
    
    try:
        response = sagemaker.describe_training_job(TrainingJobName=job_name)
        return response['TrainingJobStatus']
    except Exception as e:
        print(f"Error checking training status: {str(e)}")
        return None