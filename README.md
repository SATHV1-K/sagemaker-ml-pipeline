# 🚀 SageMaker ML Pipeline

A complete end-to-end machine learning pipeline using AWS SageMaker, Glue, and Terraform for sensor data prediction.

## 📁 Repository Structure

```
📁 sagemaker-ml-pipeline/
├── 📁 config/           # Configuration files and templates
│   ├── config.example.py
│   └── terraform.tfvars.example
├── 📁 docs/             # Documentation and guides
│   ├── README.md        # Detailed setup and usage guide
│   ├── GITHUB_DEPLOYMENT_GUIDE.md
│   └── GITHUB_FILES_SUMMARY.md
├── 📁 infrastructure/   # Terraform infrastructure code
│   ├── main.tf
│   ├── sagemaker.tf
│   └── glue_jobs.tf
├── 📁 scripts/          # All Python scripts and utilities
│   ├── setup_github.py # Main setup script
│   ├── pipeline_manager_github.py
│   ├── deploy_model_github.py
│   ├── templates/       # Code templates
│   └── ... (all other Python files)
├── 📁 data/             # Data storage (created during setup)
├── 📁 glue_scripts/     # Generated Glue job scripts
├── 📁 sagemaker_scripts/ # Generated SageMaker scripts
└── requirements.txt     # Python dependencies
```

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd sagemaker-ml-pipeline
   ```

2. **Run the setup script**
   ```bash
   python scripts/setup_github.py
   ```

3. **Follow the detailed guide**
   See [docs/README.md](docs/README.md) for complete setup instructions and usage guide.

## 📖 Documentation

- **[Complete Setup Guide](docs/README.md)** - Detailed installation and usage instructions
- **[GitHub Deployment Guide](docs/GITHUB_DEPLOYMENT_GUIDE.md)** - Step-by-step deployment process
- **[Files Summary](docs/GITHUB_FILES_SUMMARY.md)** - Overview of all project files

## 🎯 What This Project Does

- 📊 Processes IoT sensor data (temperature, humidity)
- 🧠 Trains XGBoost models to predict next temperature readings
- 🚀 Deploys models to real-time prediction endpoints
- 📈 Provides realistic temperature forecasts

## 🛠️ Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured with credentials
- Terraform >= 1.0
- Python >= 3.8

---

**Ready to get started?** Run `python scripts/setup_github.py` and follow the prompts!