import boto3
import time
from datetime import datetime

try:
    from ..config.config import AWS_REGION, SAGEMAKER_ROLE_ARN
except ImportError:
    print("❌ config.py not found. Please copy config.example.py to config.py and update with your AWS details.")
    exit(1)

class PipelineManager:
    def __init__(self):
        self.sagemaker = boto3.client('sagemaker', region_name=AWS_REGION)
        self.s3 = boto3.client('s3', region_name=AWS_REGION)
        self.glue = boto3.client('glue', region_name=AWS_REGION)
        
        # Get the actual role ARN from your AWS account
        # This will be set from config.py
        self.role_arn = SAGEMAKER_ROLE_ARN
        
        # Get workflow name from Terraform outputs or set manually
        self.workflow_name = None  # Will be set dynamically
    
    def get_workflow_status(self):
        """Get the status of the latest Glue workflow run"""
        if not self.workflow_name:
            print("❌ Workflow name not set. Please run Terraform first.")
            return
            
        try:
            # Check Glue workflow status
            response = self.glue.get_workflow_runs(Name=self.workflow_name, MaxResults=1)
            if response['Runs']:
                latest_run = response['Runs'][0]
                print(f"Glue Workflow Status: {latest_run['WorkflowRunProperties']['Status']}")
            else:
                print("No workflow runs found")
        except Exception as e:
            print(f"Error getting workflow status: {e}")
    
    def check_s3_data(self, bucket_name):
        """Check S3 data availability"""
        try:
            # Check raw data
            raw_objects = self.s3.list_objects_v2(Bucket=bucket_name, Prefix='raw/')
            print(f"Raw data files: {raw_objects.get('KeyCount', 0)}")
            
            # Check cleaned data
            cleaned_objects = self.s3.list_objects_v2(Bucket=bucket_name, Prefix='cleaned/')
            print(f"Cleaned data files: {cleaned_objects.get('KeyCount', 0)}")
            
            # Check training data
            training_objects = self.s3.list_objects_v2(Bucket=bucket_name, Prefix='training/')
            print(f"Training data files: {training_objects.get('KeyCount', 0)}")
            
            if training_objects.get('KeyCount', 0) > 0:
                print("Training data files:")
                for obj in training_objects.get('Contents', []):
                    print(f"  - {obj['Key']} ({obj['Size']} bytes, {obj['LastModified']})")
                    
        except Exception as e:
            print(f"Error checking S3 data: {e}")
    
    def list_training_jobs(self, max_results=10):
        """List recent SageMaker training jobs"""
        try:
            response = self.sagemaker.list_training_jobs(
                SortBy='CreationTime',
                SortOrder='Descending',
                MaxResults=max_results
            )
            
            print(f"\n📊 Recent Training Jobs ({len(response['TrainingJobSummaries'])}):")            
            for job in response['TrainingJobSummaries']:
                status_emoji = {
                    'Completed': '✅',
                    'Failed': '❌', 
                    'InProgress': '🔄',
                    'Stopped': '⏹️'
                }.get(job['TrainingJobStatus'], '❓')
                
                print(f"  {status_emoji} {job['TrainingJobName']} - {job['TrainingJobStatus']} ({job['CreationTime'].strftime('%Y-%m-%d %H:%M')})")
                
        except Exception as e:
            print(f"Error listing training jobs: {e}")
    
    def list_models(self, max_results=10):
        """List SageMaker models"""
        try:
            response = self.sagemaker.list_models(
                SortBy='CreationTime',
                SortOrder='Descending',
                MaxResults=max_results
            )
            
            print(f"\n🤖 Recent Models ({len(response['Models'])}):")            
            for model in response['Models']:
                print(f"  📦 {model['ModelName']} ({model['CreationTime'].strftime('%Y-%m-%d %H:%M')})")
                
        except Exception as e:
            print(f"Error listing models: {e}")
    
    def list_endpoints(self, max_results=10):
        """List SageMaker endpoints"""
        try:
            response = self.sagemaker.list_endpoints(
                SortBy='CreationTime',
                SortOrder='Descending',
                MaxResults=max_results
            )
            
            print(f"\n🚀 Recent Endpoints ({len(response['Endpoints'])}):")            
            for endpoint in response['Endpoints']:
                status_emoji = {
                    'InService': '✅',
                    'Failed': '❌',
                    'Creating': '🔄',
                    'Updating': '🔄',
                    'Deleting': '🗑️'
                }.get(endpoint['EndpointStatus'], '❓')
                
                print(f"  {status_emoji} {endpoint['EndpointName']} - {endpoint['EndpointStatus']} ({endpoint['CreationTime'].strftime('%Y-%m-%d %H:%M')})")
                
        except Exception as e:
            print(f"Error listing endpoints: {e}")
    
    def check_model_artifacts(self, bucket_name):
        """Check model artifacts in S3"""
        try:
            response = self.s3.list_objects_v2(Bucket=bucket_name, Prefix='model-artifacts/')
            
            print(f"\n📁 Model Artifacts ({response.get('KeyCount', 0)} files):")            
            if response.get('KeyCount', 0) > 0:
                for obj in response.get('Contents', []):
                    if obj['Key'].endswith('.tar.gz'):
                        print(f"  - {obj['Key']}")
            else:
                print("  No model artifacts found")
                
        except Exception as e:
            print(f"Error checking model artifacts: {e}")
    
    def get_pipeline_status(self, bucket_name=None, workflow_name=None):
        """Get comprehensive pipeline status"""
        print("=" * 60)
        print("🔍 ML PIPELINE STATUS")
        print("=" * 60)
        
        if workflow_name:
            self.workflow_name = workflow_name
            self.get_workflow_status()
        
        if bucket_name:
            self.check_s3_data(bucket_name)
            self.check_model_artifacts(bucket_name)
        
        self.list_training_jobs()
        self.list_models()
        self.list_endpoints()
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    import sys
    
    manager = PipelineManager()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--status":
            # Get bucket and workflow names from command line or use defaults
            bucket_name = sys.argv[2] if len(sys.argv) > 2 else None
            workflow_name = sys.argv[3] if len(sys.argv) > 3 else None
            manager.get_pipeline_status(bucket_name, workflow_name)
        else:
            print("Usage: python pipeline_manager_github.py --status [bucket_name] [workflow_name]")
    else:
        print("Usage: python pipeline_manager_github.py --status [bucket_name] [workflow_name]")
        print("\nExample:")
        print("python pipeline_manager_github.py --status my-data-bucket my-workflow")