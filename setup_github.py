#!/usr/bin/env python3
"""
SageMaker ML Pipeline Setup Script for GitHub

This script helps users set up the ML pipeline project from GitHub.
It checks prerequisites, configures AWS settings, and guides through deployment.
"""

import os
import sys
import boto3
import json
import subprocess
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def print_step(step_num, title):
    """Print a formatted step"""
    print(f"\n📋 Step {step_num}: {title}")
    print("-" * 40)

def check_prerequisites():
    """Check if required tools are installed"""
    print_step(1, "Checking Prerequisites")
    
    required_tools = {
        'python': 'python --version',
        'aws': 'aws --version',
        'terraform': 'terraform --version'
    }
    
    missing_tools = []
    
    for tool, command in required_tools.items():
        try:
            result = subprocess.run(command.split(), capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print(f"✅ {tool}: {version}")
            else:
                print(f"❌ {tool}: Not found")
                missing_tools.append(tool)
        except FileNotFoundError:
            print(f"❌ {tool}: Not found")
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"\n❌ Missing required tools: {', '.join(missing_tools)}")
        print("\n📝 Installation instructions:")
        if 'python' in missing_tools:
            print("   - Python: https://www.python.org/downloads/")
        if 'aws' in missing_tools:
            print("   - AWS CLI: https://aws.amazon.com/cli/")
        if 'terraform' in missing_tools:
            print("   - Terraform: https://www.terraform.io/downloads")
        return False
    
    return True

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    print_step(2, "Checking AWS Credentials")
    
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials is None:
            print("❌ AWS credentials not configured")
            print("\n📝 Configure AWS credentials:")
            print("   aws configure")
            print("\n   You'll need:")
            print("   - AWS Access Key ID")
            print("   - AWS Secret Access Key")
            print("   - Default region (e.g., us-east-1)")
            return False
        
        # Test credentials
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        print(f"✅ AWS credentials configured")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User/Role: {identity['Arn'].split('/')[-1]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking AWS credentials: {e}")
        return False

def setup_configuration():
    """Set up configuration files"""
    print_step(3, "Setting Up Configuration")
    
    # Check if config.py exists
    if os.path.exists('config.py'):
        print("✅ config.py already exists")
        return True
    
    # Check if config.example.py exists
    if not os.path.exists('config.example.py'):
        print("❌ config.example.py not found")
        return False
    
    print("📝 Creating config.py from config.example.py...")
    
    try:
        # Get AWS account ID
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        account_id = identity['Account']
        
        # Get current region
        session = boto3.Session()
        region = session.region_name or 'us-east-1'
        
        # Read template
        with open('config.example.py', 'r') as f:
            config_content = f.read()
        
        # Replace placeholders
        config_content = config_content.replace('YOUR_ACCOUNT_ID_HERE', account_id)
        config_content = config_content.replace("os.getenv('AWS_REGION', 'us-east-1')", f"os.getenv('AWS_REGION', '{region}')")
        
        # Write config.py
        with open('config.py', 'w') as f:
            f.write(config_content)
        
        print(f"✅ config.py created with:")
        print(f"   Account ID: {account_id}")
        print(f"   Region: {region}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating config.py: {e}")
        return False

def setup_terraform():
    """Set up Terraform configuration"""
    print_step(4, "Setting Up Terraform")
    
    # Check if terraform.tfvars exists
    if os.path.exists('terraform.tfvars'):
        print("✅ terraform.tfvars already exists")
        return True
    
    # Check if terraform.tfvars.example exists
    if not os.path.exists('terraform.tfvars.example'):
        print("❌ terraform.tfvars.example not found")
        return False
    
    print("📝 Creating terraform.tfvars from terraform.tfvars.example...")
    
    try:
        # Get current region
        session = boto3.Session()
        region = session.region_name or 'us-east-1'
        
        # Read template
        with open('terraform.tfvars.example', 'r') as f:
            tfvars_content = f.read()
        
        # Update region
        tfvars_content = tfvars_content.replace('aws_region = "us-east-1"', f'aws_region = "{region}"')
        
        # Write terraform.tfvars
        with open('terraform.tfvars', 'w') as f:
            f.write(tfvars_content)
        
        print(f"✅ terraform.tfvars created with region: {region}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating terraform.tfvars: {e}")
        return False

def install_python_dependencies():
    """Install Python dependencies"""
    print_step(5, "Installing Python Dependencies")
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found")
        return False
    
    try:
        print("📦 Installing Python packages...")
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Python dependencies installed successfully")
            return True
        else:
            print(f"❌ Error installing dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def initialize_terraform():
    """Initialize Terraform"""
    print_step(6, "Initializing Terraform")
    
    try:
        print("🔧 Running terraform init...")
        result = subprocess.run(['terraform', 'init'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Terraform initialized successfully")
            return True
        else:
            print(f"❌ Terraform init failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing Terraform: {e}")
        return False

def show_next_steps():
    """Show next steps to the user"""
    print_step(7, "Next Steps")
    
    print("🎉 Setup completed successfully!")
    print("\n📋 What to do next:")
    print("\n1. 🏗️  Deploy Infrastructure:")
    print("   terraform plan")
    print("   terraform apply")
    
    print("\n2. 📊 Generate Training Data:")
    print("   python create_realistic_training_data.py")
    
    print("\n3. 🚀 Start Training Job:")
    print("   python start_training_job_github.py <your-data-bucket-name>")
    
    print("\n4. 🤖 Deploy Model:")
    print("   python deploy_model_github.py <s3-model-artifacts-path>")
    
    print("\n5. 🧪 Test Predictions:")
    print("   python test_endpoint_predictions_github.py <endpoint-name>")
    
    print("\n📚 Useful Commands:")
    print("   - Check pipeline status: python pipeline_manager_github.py --status")
    print("   - List endpoints: python test_endpoint_predictions_github.py --list")
    print("   - Clean up resources: terraform destroy")
    
    print("\n💡 Tips:")
    print("   - Monitor AWS costs in the billing dashboard")
    print("   - Use smallest instance types for development")
    print("   - Check CloudWatch logs for debugging")
    
    print("\n🔗 Documentation:")
    print("   - README.md for detailed instructions")
    print("   - AWS SageMaker documentation")
    print("   - Terraform AWS provider documentation")

def main():
    """Main setup function"""
    print_header("SageMaker ML Pipeline Setup")
    
    print("Welcome to the SageMaker ML Pipeline setup!")
    print("This script will help you configure and deploy the project.")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Please install missing tools and run setup again.")
        sys.exit(1)
    
    # Check AWS credentials
    if not check_aws_credentials():
        print("\n❌ Please configure AWS credentials and run setup again.")
        sys.exit(1)
    
    # Set up configuration
    if not setup_configuration():
        print("\n❌ Failed to set up configuration.")
        sys.exit(1)
    
    # Set up Terraform
    if not setup_terraform():
        print("\n❌ Failed to set up Terraform configuration.")
        sys.exit(1)
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("\n❌ Failed to install Python dependencies.")
        sys.exit(1)
    
    # Initialize Terraform
    if not initialize_terraform():
        print("\n❌ Failed to initialize Terraform.")
        sys.exit(1)
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()