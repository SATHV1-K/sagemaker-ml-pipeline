#!/usr/bin/env python3
"""
Deployment script for AWS ML Pipeline using Terraform
"""

import subprocess
import sys
import os
import boto3
import time
import json
from pathlib import Path

def run_command(command, cwd=None):
    """
    Run a shell command and return the result
    """
    print(f"Running: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

def check_aws_credentials():
    """
    Check if AWS credentials are configured
    """
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials is None:
            print("❌ AWS credentials not found. Please configure AWS CLI first.")
            print("Run: aws configure")
            sys.exit(1)
        
        # Test credentials by making a simple API call
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials configured for account: {identity['Account']}")
        print(f"   User/Role: {identity['Arn']}")
        
    except Exception as e:
        print(f"❌ Error checking AWS credentials: {e}")
        sys.exit(1)

def check_terraform():
    """
    Check if Terraform is installed
    """
    try:
        result = subprocess.run(['terraform', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Terraform is installed: {result.stdout.split()[1]}")
        else:
            print("❌ Terraform not found. Please install Terraform first.")
            sys.exit(1)
    except FileNotFoundError:
        print("❌ Terraform not found. Please install Terraform first.")
        sys.exit(1)

def generate_sample_data():
    """
    Generate sample sensor data
    """
    print("\n📊 Generating sample sensor data...")
    run_command("python generate_sample_data.py")
    print("✅ Sample data generated successfully")

def deploy_infrastructure():
    """
    Deploy AWS infrastructure using Terraform
    """
    print("\n🚀 Deploying AWS infrastructure with Terraform...")
    
    # Initialize Terraform
    print("Initializing Terraform...")
    run_command("terraform init")
    
    # Plan deployment
    print("Planning Terraform deployment...")
    run_command("terraform plan")
    
    # Apply deployment
    print("Applying Terraform deployment...")
    run_command("terraform apply -auto-approve")
    
    # Get outputs
    print("Getting Terraform outputs...")
    outputs = run_command("terraform output -json")
    return json.loads(outputs)

def upload_data_to_s3(bucket_name):
    """
    Upload sample data to S3
    """
    print(f"\n📤 Uploading sample data to S3 bucket: {bucket_name}")
    
    s3 = boto3.client('s3')
    
    # Upload raw data
    data_file = 'data/sensor_data_raw.csv'
    if os.path.exists(data_file):
        s3.upload_file(data_file, bucket_name, 'raw/sensor_data_raw.csv')
        print(f"✅ Uploaded {data_file} to s3://{bucket_name}/raw/")
    else:
        print(f"❌ Data file {data_file} not found")
        sys.exit(1)

def run_glue_workflow(workflow_name):
    """
    Start the Glue workflow
    """
    print(f"\n⚙️ Starting Glue workflow: {workflow_name}")
    
    glue = boto3.client('glue')
    
    try:
        # Start workflow
        response = glue.start_workflow_run(Name=workflow_name)
        run_id = response['RunId']
        print(f"✅ Workflow started with run ID: {run_id}")
        
        # Monitor workflow progress
        print("Monitoring workflow progress...")
        while True:
            response = glue.get_workflow_run(Name=workflow_name, RunId=run_id)
            status = response['Run']['WorkflowRunProperties'].get('Status', 'RUNNING')
            
            print(f"Workflow status: {status}")
            
            if status == 'COMPLETED':
                print("✅ Workflow completed successfully")
                break
            elif status == 'FAILED':
                print("❌ Workflow failed")
                sys.exit(1)
            
            time.sleep(30)  # Wait 30 seconds before checking again
            
    except Exception as e:
        print(f"❌ Error running Glue workflow: {e}")
        sys.exit(1)

def check_sagemaker_endpoint(endpoint_name):
    """
    Check if SageMaker endpoint is ready
    """
    print(f"\n🤖 Checking SageMaker endpoint: {endpoint_name}")
    
    sagemaker = boto3.client('sagemaker')
    
    try:
        response = sagemaker.describe_endpoint(EndpointName=endpoint_name)
        status = response['EndpointStatus']
        
        print(f"Endpoint status: {status}")
        
        if status == 'InService':
            print("✅ SageMaker endpoint is ready for predictions")
            return True
        else:
            print(f"⏳ Endpoint is still {status}. Please wait...")
            return False
            
    except Exception as e:
        print(f"❌ Error checking endpoint: {e}")
        return False

def test_endpoint(endpoint_name):
    """
    Test the SageMaker endpoint with sample data
    """
    print(f"\n🧪 Testing SageMaker endpoint: {endpoint_name}")
    
    runtime = boto3.client('sagemaker-runtime')
    
    # Sample test data (features for prediction)
    test_data = "25.5,65.2,0.391,2.1,15.3,14,3,180,50,0.95"
    
    try:
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='text/csv',
            Body=test_data
        )
        
        result = response['Body'].read().decode()
        print(f"✅ Prediction result: {result}")
        
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")

def main():
    """
    Main deployment function
    """
    print("🚀 AWS ML Pipeline Deployment Script")
    print("====================================\n")
    
    # Check prerequisites
    print("🔍 Checking prerequisites...")
    check_aws_credentials()
    check_terraform()
    
    # Generate sample data
    generate_sample_data()
    
    # Deploy infrastructure
    outputs = deploy_infrastructure()
    
    # Extract important values from outputs
    data_bucket = outputs['data_bucket_name']['value']
    workflow_name = outputs['glue_workflow_name']['value']
    endpoint_name = outputs['sagemaker_endpoint_name']['value']
    
    print(f"\n📋 Deployment Summary:")
    print(f"   Data Bucket: {data_bucket}")
    print(f"   Glue Workflow: {workflow_name}")
    print(f"   SageMaker Endpoint: {endpoint_name}")
    
    # Upload data to S3
    upload_data_to_s3(data_bucket)
    
    # Run Glue workflow
    run_glue_workflow(workflow_name)
    
    # Wait for SageMaker endpoint to be ready
    print("\n⏳ Waiting for SageMaker endpoint to be ready...")
    while not check_sagemaker_endpoint(endpoint_name):
        time.sleep(60)  # Wait 1 minute before checking again
    
    # Test the endpoint
    test_endpoint(endpoint_name)
    
    print("\n🎉 Deployment completed successfully!")
    print("\n📖 Next steps:")
    print(f"   1. Monitor your resources in AWS Console")
    print(f"   2. Use the SageMaker endpoint for predictions: {endpoint_name}")
    print(f"   3. Check processed data in S3 bucket: {data_bucket}")
    print(f"   4. To destroy resources: terraform destroy")

if __name__ == "__main__":
    main()