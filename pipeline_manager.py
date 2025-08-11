import boto3
import json
import time
from datetime import datetime, timedelta
import pandas as pd

class MLPipelineManager:
    def __init__(self):
        self.sagemaker = boto3.client('sagemaker')
        self.s3 = boto3.client('s3')
        self.glue = boto3.client('glue')
        self.lambda_client = boto3.client('lambda')
        
        # Configuration
        self.bucket_data = 'sagemaker-ml-pipeline-data-f5ofrag0'
        self.bucket_models = 'sagemaker-ml-pipeline-models-f5ofrag0'
        self.workflow_name = 'sagemaker-ml-pipeline-workflow-f5ofrag0'
        self.role_arn = 'arn:aws:iam::296062569059:role/sagemaker-ml-pipeline-sagemaker-role-f5ofrag0'
    
    def check_data_pipeline_status(self):
        """Check the status of the data processing pipeline"""
        print("=== Data Pipeline Status ===")
        
        try:
            # Check Glue workflow status
            response = self.glue.get_workflow_runs(Name=self.workflow_name, MaxResults=1)
            if response['Runs']:
                latest_run = response['Runs'][0]
                print(f"Glue Workflow Status: {latest_run['WorkflowRunProperties']['Status']}")
                print(f"Last Run: {latest_run['StartedOn']}")
            
            # Check S3 data availability
            print("\nData Availability:")
            
            # Raw data
            raw_objects = self.s3.list_objects_v2(Bucket=self.bucket_data, Prefix='raw/')
            print(f"Raw data files: {raw_objects.get('KeyCount', 0)}")
            
            # Cleaned data
            cleaned_objects = self.s3.list_objects_v2(Bucket=self.bucket_data, Prefix='cleaned/')
            print(f"Cleaned data files: {cleaned_objects.get('KeyCount', 0)}")
            
            # Training data
            training_objects = self.s3.list_objects_v2(Bucket=self.bucket_data, Prefix='training/')
            print(f"Training data files: {training_objects.get('KeyCount', 0)}")
            
            if training_objects.get('KeyCount', 0) > 0:
                for obj in training_objects.get('Contents', []):
                    print(f"  - {obj['Key']} ({obj['Size']} bytes, {obj['LastModified']})")
            
        except Exception as e:
            print(f"Error checking data pipeline: {str(e)}")
    
    def check_training_jobs(self):
        """Check recent training job status"""
        print("\n=== Training Jobs Status ===")
        
        try:
            response = self.sagemaker.list_training_jobs(
                SortBy='CreationTime',
                SortOrder='Descending',
                NameContains='sensor-prediction',
                MaxResults=5
            )
            
            if response['TrainingJobSummaries']:
                for job in response['TrainingJobSummaries']:
                    print(f"Job: {job['TrainingJobName']}")
                    print(f"  Status: {job['TrainingJobStatus']}")
                    print(f"  Created: {job['CreationTime']}")
                    if job['TrainingJobStatus'] == 'Completed':
                        print(f"  Ended: {job.get('TrainingEndTime', 'N/A')}")
                    print()
            else:
                print("No training jobs found.")
                
        except Exception as e:
            print(f"Error checking training jobs: {str(e)}")
    
    def check_models_and_endpoints(self):
        """Check deployed models and endpoints"""
        print("=== Models and Endpoints Status ===")
        
        try:
            # Check models
            models_response = self.sagemaker.list_models(
                SortBy='CreationTime',
                SortOrder='Descending',
                NameContains='sensor-prediction',
                MaxResults=5
            )
            
            print("Models:")
            if models_response['Models']:
                for model in models_response['Models']:
                    print(f"  - {model['ModelName']} (Created: {model['CreationTime']})")
            else:
                print("  No models found.")
            
            # Check endpoints
            endpoints_response = self.sagemaker.list_endpoints(
                SortBy='CreationTime',
                SortOrder='Descending',
                NameContains='sensor-prediction',
                MaxResults=5
            )
            
            print("\nEndpoints:")
            if endpoints_response['Endpoints']:
                for endpoint in endpoints_response['Endpoints']:
                    print(f"  - {endpoint['EndpointName']}")
                    print(f"    Status: {endpoint['EndpointStatus']}")
                    print(f"    Created: {endpoint['CreationTime']}")
                    print(f"    Last Modified: {endpoint['LastModifiedTime']}")
                    print()
            else:
                print("  No endpoints found.")
                
        except Exception as e:
            print(f"Error checking models and endpoints: {str(e)}")
    
    def get_model_artifacts(self):
        """List available model artifacts"""
        print("\n=== Model Artifacts ===")
        
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_models,
                Prefix='output/'
            )
            
            if response.get('Contents'):
                print("Available model artifacts:")
                for obj in response['Contents']:
                    if obj['Key'].endswith('.tar.gz'):
                        print(f"  - {obj['Key']}")
                        print(f"    Size: {obj['Size']} bytes")
                        print(f"    Last Modified: {obj['LastModified']}")
                        print()
            else:
                print("No model artifacts found.")
                
        except Exception as e:
            print(f"Error checking model artifacts: {str(e)}")
    
    def cleanup_old_resources(self, days_old=7):
        """Clean up old training jobs, models, and endpoints"""
        print(f"\n=== Cleanup (resources older than {days_old} days) ===")
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        try:
            # List old endpoints
            endpoints_response = self.sagemaker.list_endpoints(
                SortBy='CreationTime',
                SortOrder='Ascending',
                NameContains='sensor-prediction'
            )
            
            old_endpoints = []
            for endpoint in endpoints_response['Endpoints']:
                if endpoint['CreationTime'].replace(tzinfo=None) < cutoff_date:
                    old_endpoints.append(endpoint['EndpointName'])
            
            if old_endpoints:
                print(f"Found {len(old_endpoints)} old endpoints to clean up:")
                for endpoint_name in old_endpoints:
                    print(f"  - {endpoint_name}")
                    # Uncomment to actually delete:
                    # self.sagemaker.delete_endpoint(EndpointName=endpoint_name)
                    # print(f"    Deleted: {endpoint_name}")
                print("(Cleanup is disabled by default - uncomment code to enable)")
            else:
                print("No old endpoints found for cleanup.")
                
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
    
    def generate_pipeline_report(self):
        """Generate a comprehensive pipeline status report"""
        print("\n" + "=" * 80)
        print(f"ML PIPELINE STATUS REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        self.check_data_pipeline_status()
        self.check_training_jobs()
        self.check_models_and_endpoints()
        self.get_model_artifacts()
        self.cleanup_old_resources()
        
        print("\n" + "=" * 80)
        print("REPORT COMPLETED")
        print("=" * 80)

def main():
    manager = MLPipelineManager()
    manager.generate_pipeline_report()

if __name__ == "__main__":
    main()