# GitHub Deployment Guide

This guide will help you safely upload your SageMaker ML Pipeline project to GitHub without exposing sensitive information.

## 🔒 Security First - What NOT to Upload

### ❌ NEVER commit these files:
- `config.py` (contains AWS account ID and region)
- `terraform.tfvars` (contains AWS configuration)
- `.aws/` directory (AWS credentials)
- `terraform.tfstate*` (Terraform state files)
- `.terraform/` directory
- Any files with actual AWS keys, passwords, or account IDs

### ✅ Safe to upload:
- All `*_github.py` files (sanitized versions)
- `config.example.py` (template file)
- `terraform.tfvars.example` (template file)
- `setup_github.py` (setup script for users)
- `README_GITHUB.md` (GitHub-specific documentation)
- `.gitignore_github` (comprehensive gitignore)

## 📋 Pre-Upload Checklist

### 1. Verify Sensitive Information is Removed
```bash
# Search for potential sensitive data
findstr /s /i "296062569059" *.py *.tf *.md
findstr /s /i "us-east-1" *.py *.tf *.md
findstr /s /i "arn:aws" *.py *.tf *.md
```

### 2. Check GitHub-Ready Files
Ensure these files exist and are properly configured:
- [ ] `config.example.py`
- [ ] `terraform.tfvars.example`
- [ ] `setup_github.py`
- [ ] `README_GITHUB.md`
- [ ] `.gitignore_github`
- [ ] All `*_github.py` files

### 3. Test the Setup Process
Run the setup script to ensure it works:
```bash
python setup_github.py
```

## 🚀 GitHub Upload Steps

### Step 1: Initialize Git Repository
```bash
# Navigate to your project directory
cd C:\Users\sathv\Desktop\Sagemaker_Proj

# Initialize git (if not already done)
git init

# Copy the GitHub gitignore
copy .gitignore_github .gitignore
```

### Step 2: Stage Safe Files Only
```bash
# Add template and example files
git add config.example.py
git add terraform.tfvars.example
git add setup_github.py
git add README_GITHUB.md
git add .gitignore

# Add all GitHub-specific files
git add *_github.py

# Add Terraform templates (without sensitive data)
git add *.tf
git add templates/

# Add documentation
git add GITHUB_DEPLOYMENT_GUIDE.md
git add requirements.txt

# Add other safe files
git add glue_scripts/.gitkeep
git add sagemaker_scripts/.gitkeep
```

### Step 3: Verify What's Being Committed
```bash
# Check staged files
git status

# Review changes
git diff --cached

# Make sure no sensitive files are staged
git ls-files | findstr config.py
git ls-files | findstr terraform.tfvars
```

### Step 4: Commit and Push
```bash
# Commit changes
git commit -m "Initial commit: SageMaker ML Pipeline for GitHub"

# Add remote repository (replace with your GitHub repo URL)
git remote add origin https://github.com/yourusername/sagemaker-ml-pipeline.git

# Push to GitHub
git push -u origin main
```

## 📁 Recommended Repository Structure for GitHub

```
sagemaker-ml-pipeline/
├── README.md                          # Rename README_GITHUB.md to this
├── .gitignore                         # Use .gitignore_github
├── requirements.txt
├── setup.py                           # GitHub setup script
├── config.example.py                  # Configuration template
├── terraform.tfvars.example           # Terraform variables template
├── 
├── # Core Infrastructure
├── main.tf
├── sagemaker.tf
├── glue_jobs.tf
├── lambda_function.py.tpl
├── 
├── # GitHub-Safe Python Scripts
├── pipeline_manager_github.py
├── start_training_job_github.py
├── deploy_model_github.py
├── test_endpoint_predictions_github.py
├── 
├── # Templates
├── templates/
│   ├── data_cleaning.py.tpl
│   ├── data_processing.py.tpl
│   └── lambda_function.py.tpl
├── 
├── # Utility Scripts
├── generate_training_data.py
├── cleanup_failed_resources.py
├── run_full_pipeline.py
├── 
└── # Documentation
    ├── GITHUB_DEPLOYMENT_GUIDE.md
    └── architecture_diagram.png
```

## 🔧 Post-Upload Instructions for Users

Include these instructions in your GitHub README:

### For New Users:
1. Clone the repository
2. Run `python setup.py` (the GitHub version)
3. Configure AWS credentials
4. Update `config.py` with their AWS details
5. Update `terraform.tfvars` with their preferences
6. Deploy infrastructure with `terraform apply`
7. Run the ML pipeline

## ⚠️ Important Security Notes

### Before Each Commit:
1. **Double-check** no sensitive files are staged
2. **Review** all changes with `git diff --cached`
3. **Verify** .gitignore is working properly
4. **Test** that example files work for new users

### Regular Maintenance:
1. **Update** .gitignore as needed
2. **Review** commits for accidentally added sensitive data
3. **Keep** example files up to date
4. **Document** any new configuration requirements

## 🆘 Emergency: Sensitive Data Accidentally Committed

If you accidentally commit sensitive data:

1. **Immediately** remove the sensitive data
2. **Force push** to overwrite history (if repository is private and you're the only contributor)
3. **Consider** creating a new repository if data was exposed publicly
4. **Rotate** any exposed credentials immediately

```bash
# Remove sensitive file from history
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch config.py' --prune-empty --tag-name-filter cat -- --all

# Force push (DANGEROUS - only if you're sure)
git push origin --force --all
```

## 📞 Support

For questions about this deployment process:
1. Check the main README_GITHUB.md
2. Review the setup_github.py script
3. Ensure all example files are properly configured

---

**Remember: Security is paramount. When in doubt, don't commit!**