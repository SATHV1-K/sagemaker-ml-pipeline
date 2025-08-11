# Configuration file for AWS SageMaker ML Pipeline
# Copy this file to config.py and update with your AWS details

import os

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID', 'YOUR_ACCOUNT_ID_HERE')

# SageMaker Configuration
SAGEMAKER_ROLE_NAME = os.getenv('SAGEMAKER_ROLE_NAME', 'sagemaker-ml-pipeline-sagemaker-role')
SAGEMAKER_ROLE_ARN = f'arn:aws:iam::{AWS_ACCOUNT_ID}:role/{SAGEMAKER_ROLE_NAME}'

# XGBoost Container Image (region-specific)
XGBOOST_CONTAINER_IMAGES = {
    'us-east-1': '683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1',
    'us-west-2': '246618743249.dkr.ecr.us-west-2.amazonaws.com/sagemaker-xgboost:1.7-1',
    'eu-west-1': '141502667606.dkr.ecr.eu-west-1.amazonaws.com/sagemaker-xgboost:1.7-1',
    'ap-southeast-1': '121021644041.dkr.ecr.ap-southeast-1.amazonaws.com/sagemaker-xgboost:1.7-1'
}

XGBOOST_CONTAINER_IMAGE = XGBOOST_CONTAINER_IMAGES.get(AWS_REGION, XGBOOST_CONTAINER_IMAGES['us-east-1'])

# S3 Bucket Names (will be created with random suffix)
PROJECT_NAME = os.getenv('PROJECT_NAME', 'sagemaker-ml-pipeline')
DATA_BUCKET_PREFIX = f'{PROJECT_NAME}-data'
SCRIPTS_BUCKET_PREFIX = f'{PROJECT_NAME}-scripts'

# Training Configuration
TRAINING_INSTANCE_TYPE = os.getenv('TRAINING_INSTANCE_TYPE', 'ml.m5.large')
ENDPOINT_INSTANCE_TYPE = os.getenv('ENDPOINT_INSTANCE_TYPE', 'ml.t2.medium')

# Glue Configuration
GLUE_WORKER_TYPE = os.getenv('GLUE_WORKER_TYPE', 'G.1X')
GLUE_NUMBER_OF_WORKERS = int(os.getenv('GLUE_NUMBER_OF_WORKERS', '2'))