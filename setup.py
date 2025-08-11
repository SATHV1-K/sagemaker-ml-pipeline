#!/usr/bin/env python3
"""
Setup and validation script for AWS ML Pipeline
"""

import subprocess
import sys
import os
import boto3
import json
from pathlib import Path

def check_python_version():
    """
    Check if Python version is compatible
    """
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("   Required: Python 3.8 or higher")
        return False

def check_aws_cli():
    """
    Check if AWS CLI is installed and configured
    """
    print("\n☁️ Checking AWS CLI...")
    try:
        # Check if AWS CLI is installed
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ AWS CLI installed: {result.stdout.strip()}")
        else:
            print("❌ AWS CLI not found")
            return False
        
        # Check if credentials are configured
        try:
            session = boto3.Session()
            credentials = session.get_credentials()
            if credentials is None:
                print("❌ AWS credentials not configured")
                print("   Run: aws configure")
                return False
            
            # Test credentials
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            print(f"✅ AWS credentials configured for account: {identity['Account']}")
            return True
            
        except Exception as e:
            print(f"❌ Error checking AWS credentials: {e}")
            return False
            
    except FileNotFoundError:
        print("❌ AWS CLI not found")
        print("   Install from: https://aws.amazon.com/cli/")
        return False

def check_terraform():
    """
    Check if Terraform is installed
    """
    print("\n🏗️ Checking Terraform...")
    try:
        result = subprocess.run(['terraform', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ Terraform installed: {version_line}")
            return True
        else:
            print("❌ Terraform not found")
            return False
    except FileNotFoundError:
        print("❌ Terraform not found")
        print("   Install from: https://www.terraform.io/downloads")
        return False

def install_python_dependencies():
    """
    Install required Python packages
    """
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        print("✅ Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False

def check_aws_permissions():
    """
    Check if the current AWS user has necessary permissions
    """
    print("\n🔐 Checking AWS permissions...")
    
    required_services = {
        's3': 'S3 (Simple Storage Service)',
        'iam': 'IAM (Identity and Access Management)',
        'glue': 'AWS Glue',
        'sagemaker': 'Amazon SageMaker',
        'lambda': 'AWS Lambda',
        'events': 'Amazon EventBridge',
        'logs': 'CloudWatch Logs'
    }
    
    permissions_ok = True
    
    for service, description in required_services.items():
        try:
            client = boto3.client(service)
            
            # Test basic operations for each service
            if service == 's3':
                client.list_buckets()
            elif service == 'iam':
                client.list_roles(MaxItems=1)
            elif service == 'glue':
                client.list_jobs(MaxResults=1)
            elif service == 'sagemaker':
                client.list_models(MaxResults=1)
            elif service == 'lambda':
                client.list_functions(MaxItems=1)
            elif service == 'events':
                client.list_rules(Limit=1)
            elif service == 'logs':
                client.describe_log_groups(limit=1)
            
            print(f"✅ {description} - Access OK")
            
        except Exception as e:
            print(f"❌ {description} - Access denied or error: {str(e)[:100]}...")
            permissions_ok = False
    
    return permissions_ok

def check_aws_quotas():
    """
    Check relevant AWS service quotas
    """
    print("\n📊 Checking AWS service quotas...")
    
    try:
        # Check SageMaker quotas
        sagemaker = boto3.client('sagemaker')
        
        # List current endpoints to check quota usage
        endpoints = sagemaker.list_endpoints()['Endpoints']
        print(f"✅ Current SageMaker endpoints: {len(endpoints)}")
        
        # Check Glue jobs
        glue = boto3.client('glue')
        jobs = glue.list_jobs()['JobNames']
        print(f"✅ Current Glue jobs: {len(jobs)}")
        
        # Check S3 buckets
        s3 = boto3.client('s3')
        buckets = s3.list_buckets()['Buckets']
        print(f"✅ Current S3 buckets: {len(buckets)}")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Could not check quotas: {e}")
        return True  # Don't fail setup for quota check issues

def validate_project_structure():
    """
    Validate that all required files are present
    """
    print("\n📁 Validating project structure...")
    
    required_files = [
        'main.tf',
        'glue_jobs.tf',
        'sagemaker.tf',
        'generate_sample_data.py',
        'deploy.py',
        'requirements.txt',
        'templates/data_cleaning.py.tpl',
        'templates/data_processing.py.tpl',
        'templates/train.py.tpl',
        'templates/lambda_function.py.tpl'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - Missing")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files")
        return False
    else:
        print("\n✅ All required files present")
        return True

def estimate_costs():
    """
    Provide cost estimates for the AWS resources
    """
    print("\n💰 Estimated AWS Costs (Monthly):")
    print("   📊 AWS Glue:")
    print("      - G.1X workers (2 workers): ~$0.44/hour when running")
    print("      - Estimated monthly: $10-20 (depends on job frequency)")
    print("   🤖 SageMaker:")
    print("      - Training (ml.m5.large): ~$0.115/hour when training")
    print("      - Endpoint (ml.t2.medium): ~$0.065/hour = ~$47/month")
    print("   💾 S3 Storage:")
    print("      - Standard storage: ~$0.023/GB/month")
    print("      - Estimated: $1-5/month for sample data")
    print("   ⚡ Lambda:")
    print("      - Pay per execution: ~$0.0000002/request")
    print("      - Estimated: <$1/month")
    print("   📝 CloudWatch Logs:")
    print("      - $0.50/GB ingested, $0.03/GB stored")
    print("      - Estimated: $1-3/month")
    print("\n   🎯 Total Estimated Monthly Cost: $60-80")
    print("   ⚠️  Note: Costs depend on usage patterns and data volume")

def main():
    """
    Main setup function
    """
    print("🚀 AWS ML Pipeline Setup & Validation")
    print("====================================\n")
    
    checks_passed = 0
    total_checks = 6
    
    # Run all checks
    if check_python_version():
        checks_passed += 1
    
    if check_aws_cli():
        checks_passed += 1
    
    if check_terraform():
        checks_passed += 1
    
    if install_python_dependencies():
        checks_passed += 1
    
    if check_aws_permissions():
        checks_passed += 1
    
    if validate_project_structure():
        checks_passed += 1
    
    # Optional checks (don't count towards pass/fail)
    check_aws_quotas()
    
    # Summary
    print(f"\n📋 Setup Summary: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("\n🎉 Setup completed successfully!")
        print("\n📖 Next steps:")
        print("   1. Review the cost estimates below")
        print("   2. Run: python deploy.py (for automated deployment)")
        print("   3. Or run: terraform init && terraform apply (for manual deployment)")
        
        estimate_costs()
        
    else:
        print("\n❌ Setup incomplete. Please fix the issues above before proceeding.")
        print("\n🔧 Common solutions:")
        print("   - Install missing tools (AWS CLI, Terraform)")
        print("   - Configure AWS credentials: aws configure")
        print("   - Check AWS permissions with your administrator")
        
        sys.exit(1)

if __name__ == "__main__":
    main()