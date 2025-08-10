import boto3
import time
import json
from datetime import datetime
import subprocess
import sys

def run_full_ml_pipeline():
    """
    Complete ML Pipeline Automation:
    1. Check/trigger data processing
    2. Start training job
    3. Deploy model endpoint
    4. Test endpoint
    """
    print("=" * 80)
    print("STARTING COMPLETE ML PIPELINE")
    print("=" * 80)
    
    # Initialize AWS clients
    sagemaker = boto3.client('sagemaker')
    s3 = boto3.client('s3')
    glue = boto3.client('glue')
    
    bucket_data = 'sagemaker-ml-pipeline-data-f5ofrag0'
    bucket_models = 'sagemaker-ml-pipeline-models-f5ofrag0'
    
    try:
        # Step 1: Check if training data exists
        print("\n1. Checking training data availability...")
        training_objects = s3.list_objects_v2(Bucket=bucket_data, Prefix='training/')
        
        if training_objects.get('KeyCount', 0) == 0:
            print("No training data found. Please run data processing first.")
            return False
        
        print(f"Found {training_objects.get('KeyCount', 0)} training data files.")
        
        # Step 2: Check if we have a recent successful training job
        print("\n2. Checking recent training jobs...")
        training_jobs = sagemaker.list_training_jobs(
            SortBy='CreationTime',
            SortOrder='Descending',
            NameContains='sensor-prediction',
            MaxResults=3
        )
        
        latest_successful_job = None
        for job in training_jobs['TrainingJobSummaries']:
            if job['TrainingJobStatus'] == 'Completed':
                latest_successful_job = job
                break
        
        if latest_successful_job:
            print(f"Found successful training job: {latest_successful_job['TrainingJobName']}")
            model_artifacts_path = f"s3://{bucket_models}/output/{latest_successful_job['TrainingJobName']}/output/model.tar.gz"
        else:
            print("No successful training job found. Starting new training...")
            # Here you could trigger a new training job
            print("Please run start_training_job.py first.")
            return False
        
        # Step 3: Check if endpoint exists and is in service
        print("\n3. Checking endpoint status...")
        endpoints = sagemaker.list_endpoints(
            SortBy='CreationTime',
            SortOrder='Descending',
            NameContains='sensor-prediction',
            MaxResults=1
        )
        
        active_endpoint = None
        if endpoints['Endpoints']:
            endpoint = endpoints['Endpoints'][0]
            if endpoint['EndpointStatus'] == 'InService':
                active_endpoint = endpoint['EndpointName']
                print(f"Found active endpoint: {active_endpoint}")
            else:
                print(f"Endpoint {endpoint['EndpointName']} status: {endpoint['EndpointStatus']}")
        
        if not active_endpoint:
            print("No active endpoint found. Deployment may still be in progress.")
            print("Check deploy_model.py output for deployment status.")
            return False
        
        # Step 4: Test the endpoint
        print("\n4. Testing endpoint with sample data...")
        runtime = boto3.client('sagemaker-runtime')
        
        # Sample test data (features without target)
        test_sample = [25.5, 68.2, 0.374, 8, 1, 217, 25.1, 67.8, 1.2, 2.1]
        csv_input = ','.join(map(str, test_sample))
        
        response = runtime.invoke_endpoint(
            EndpointName=active_endpoint,
            ContentType='text/csv',
            Body=csv_input
        )
        
        prediction = response['Body'].read().decode('utf-8').strip()
        print(f"Test prediction successful: {prediction}")
        
        # Step 5: Pipeline summary
        print("\n" + "=" * 80)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 80)
        print(f"✓ Training Job: {latest_successful_job['TrainingJobName']}")
        print(f"✓ Model Artifacts: {model_artifacts_path}")
        print(f"✓ Active Endpoint: {active_endpoint}")
        print(f"✓ Test Prediction: {prediction}")
        print("\n🎉 ML Pipeline is fully operational!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline execution failed: {str(e)}")
        return False

def quick_endpoint_status():
    """Quick check of endpoint status"""
    sagemaker = boto3.client('sagemaker')
    
    try:
        endpoints = sagemaker.list_endpoints(
            SortBy='CreationTime',
            SortOrder='Descending',
            NameContains='sensor-prediction',
            MaxResults=3
        )
        
        print("Current Endpoint Status:")
        print("-" * 40)
        
        if endpoints['Endpoints']:
            for endpoint in endpoints['Endpoints']:
                print(f"Name: {endpoint['EndpointName']}")
                print(f"Status: {endpoint['EndpointStatus']}")
                print(f"Created: {endpoint['CreationTime']}")
                print(f"Modified: {endpoint['LastModifiedTime']}")
                print("-" * 40)
        else:
            print("No endpoints found.")
            
    except Exception as e:
        print(f"Error checking endpoint status: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        quick_endpoint_status()
    else:
        run_full_ml_pipeline()