# 🚀 SageMaker ML Pipeline - GitHub Edition

A complete end-to-end machine learning pipeline using AWS SageMaker, Glue, and Terraform for sensor data prediction.

## 🎯 What This Project Does

This project creates a production-ready ML pipeline that:
- 📊 Processes IoT sensor data (temperature, humidity)
- 🧠 Trains XGBoost models to predict next temperature readings
- 🚀 Deploys models to real-time prediction endpoints
- 📈 Provides realistic temperature forecasts (not constant 1.0°C!)

## 🏗️ Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Raw Data  │───▶│ Glue Job 1  │───▶│ Glue Job 2  │───▶│  SageMaker  │
│  (S3 CSV)   │    │(Data Clean) │    │(Processing) │    │  Training   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                   │
                                                                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │◀───│  Endpoint   │◀───│   Model     │◀───│   Model     │
│Predictions  │    │(Real-time)  │    │Deployment   │    │ Artifacts   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Terraform** >= 1.0
4. **Python** >= 3.8
5. **Git** for cloning the repository

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd sagemaker-ml-pipeline

# Run the automated setup
python setup_github.py
```

The setup script will:
- ✅ Check prerequisites
- ✅ Verify AWS credentials
- ✅ Create configuration files
- ✅ Install Python dependencies
- ✅ Initialize Terraform

### Step 2: Deploy Infrastructure

```bash
# Review the deployment plan
terraform plan

# Deploy AWS resources
terraform apply
```

This creates:
- S3 buckets for data and scripts
- IAM roles and policies
- Glue jobs and workflows
- SageMaker training job configuration
- Lambda functions for automation

### Step 3: Generate Training Data

```bash
# Generate realistic sensor training data
python create_realistic_training_data.py
```

This creates 10,000 realistic sensor readings with proper target values (10-40°C range).

### Step 4: Train the Model

```bash
# Start SageMaker training job
python start_training_job_github.py <your-data-bucket-name>

# Check training status
python pipeline_manager_github.py --status <bucket-name>
```

### Step 5: Deploy the Model

```bash
# List completed training jobs
python deploy_model_github.py --list-jobs

# Deploy the latest model
python deploy_model_github.py <s3-model-artifacts-path>
```

### Step 6: Test Predictions

```bash
# Test the deployed endpoint
python test_endpoint_predictions_github.py <endpoint-name>

# List available endpoints
python test_endpoint_predictions_github.py --list
```

## 📁 Project Structure

```
├── 🔧 Configuration
│   ├── config.example.py              # AWS configuration template
│   ├── terraform.tfvars.example       # Terraform variables template
│   └── requirements.txt               # Python dependencies
│
├── 🏗️ Infrastructure (Terraform)
│   ├── main.tf                        # Main Terraform configuration
│   ├── sagemaker.tf                   # SageMaker resources
│   ├── glue_jobs.tf                   # Glue jobs and workflows
│   └── templates/                     # Script templates
│
├── 🚀 GitHub-Ready Scripts
│   ├── setup_github.py                # Automated setup script
│   ├── pipeline_manager_github.py     # Pipeline status management
│   ├── start_training_job_github.py   # Start training jobs
│   ├── deploy_model_github.py         # Deploy trained models
│   └── test_endpoint_predictions_github.py  # Test predictions
│
├── 📊 Data Processing
│   ├── create_realistic_training_data.py    # Generate training data
│   ├── generate_sample_data.py              # Generate sample sensor data
│   └── glue_scripts/                        # Glue ETL scripts
│
└── 📚 Documentation
    ├── README_GITHUB.md               # This file
    └── README.md                      # Original project README
```

## ⚙️ Configuration

### AWS Configuration

The project uses `config.py` for AWS settings:

```python
# Automatically configured by setup_github.py
AWS_REGION = 'us-east-1'              # Your AWS region
AWS_ACCOUNT_ID = '123456789012'       # Your AWS account ID
SAGEMAKER_ROLE_ARN = 'arn:aws:iam::...'  # SageMaker execution role
```

### Terraform Variables

Customize deployment in `terraform.tfvars`:

```hcl
aws_region = "us-east-1"
project_name = "my-ml-pipeline"
sagemaker_instance_type = "ml.m5.large"
endpoint_instance_type = "ml.t2.medium"
```

## 🧪 Testing and Validation

### Test Realistic Predictions

```bash
# Test with sample data
python test_endpoint_predictions_github.py sensor-prediction-endpoint-20250805-155734
```

Expected output:
```
Test Sample 1:
Temperature: 25.5°C, Humidity: 68.2%
Predicted next temperature: 26.51°C
Temperature trend: increasing (+1.01°C change)
✅ Prediction looks reasonable
```

### Monitor Pipeline Status

```bash
# Check overall pipeline status
python pipeline_manager_github.py --status my-data-bucket my-workflow
```

## 💰 Cost Optimization

This project is designed for cost-effectiveness:

- **SageMaker Training**: ml.m5.large (on-demand, short duration)
- **SageMaker Endpoints**: ml.t2.medium (lowest cost for real-time inference)
- **Glue Jobs**: G.1X workers (smallest available) with 2 workers
- **S3 Storage**: Standard tier with lifecycle policies

**Estimated Monthly Cost**: $50-100 for development usage

## 🔧 Troubleshooting

### Common Issues

1. **"config.py not found"**
   ```bash
   # Run setup script to create config files
   python setup_github.py
   ```

2. **"AWS credentials not configured"**
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret, and region
   ```

3. **"Endpoint not found"**
   ```bash
   # List available endpoints
   python test_endpoint_predictions_github.py --list
   ```

4. **"Training job failed"**
   ```bash
   # Check training job status
   python pipeline_manager_github.py --status
   ```

### Debug Commands

```bash
# Check AWS credentials
aws sts get-caller-identity

# List S3 buckets
aws s3 ls

# Check SageMaker endpoints
aws sagemaker list-endpoints

# View CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix /aws/sagemaker
```

## 🔒 Security Best Practices

- ✅ No hardcoded credentials in code
- ✅ IAM roles with minimal required permissions
- ✅ Environment-based configuration
- ✅ Encrypted S3 buckets
- ✅ VPC endpoints for private communication

## 🚀 Advanced Usage

### Custom Training Data

```python
# Modify create_realistic_training_data.py
# Adjust temperature ranges, features, or data volume
TEMP_RANGE = (5, 45)  # Custom temperature range
NUM_SAMPLES = 50000   # More training data
```

### Different ML Algorithms

```python
# Update container image in config.py
XGBOOST_CONTAINER_IMAGE = 'your-custom-algorithm-image'
```

### Production Deployment

```hcl
# Update terraform.tfvars for production
sagemaker_instance_type = "ml.m5.xlarge"
endpoint_instance_type = "ml.m5.large"
glue_number_of_workers = 10
```

## 🧹 Cleanup

```bash
# Destroy all AWS resources
terraform destroy

# Confirm deletion
# Type 'yes' when prompted
```

## 📚 Additional Resources

- [AWS SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
- [AWS Glue Documentation](https://docs.aws.amazon.com/glue/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [XGBoost Algorithm](https://xgboost.readthedocs.io/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review AWS CloudWatch logs
3. Verify AWS permissions and quotas
4. Open an issue with detailed error messages

---

**Happy ML Pipeline Building! 🚀🤖**