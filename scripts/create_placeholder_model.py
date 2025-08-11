#!/usr/bin/env python3
"""
Script to create a placeholder model file for initial SageMaker deployment.
This allows the infrastructure to be deployed before any actual training occurs.
"""

import boto3
import tarfile
import tempfile
import os
import pickle
import xgboost as xgb
import numpy as np

def create_placeholder_model():
    """
    Create a simple placeholder model and upload it to S3
    """
    # Create a simple placeholder XGBoost model
    # Create some dummy training data to fit the model
    X_dummy = np.random.rand(100, 4)  # 4 features to match our sensor data
    y_dummy = np.random.rand(100)     # Random target values
    
    # Create DMatrix for XGBoost
    dtrain = xgb.DMatrix(X_dummy, label=y_dummy)
    
    # Train a simple XGBoost model
    params = {
        'objective': 'reg:squarederror',
        'max_depth': 3,
        'eta': 0.1,
        'seed': 42
    }
    model = xgb.train(params, dtrain, num_boost_round=10)
    
    # Create files in current directory instead of temp
    model_path = 'model.pkl'
    tar_path = 'model.tar.gz'
    
    try:
        # Save the model in XGBoost format
        model.save_model(model_path)
        
        # Create model.tar.gz
        with tarfile.open(tar_path, 'w:gz') as tar:
            tar.add(model_path, arcname='model.pkl')
        
        # Clean up the pickle file
        os.remove(model_path)
        
        return tar_path
    except Exception as e:
        # Clean up on error
        if os.path.exists(model_path):
            os.remove(model_path)
        if os.path.exists(tar_path):
            os.remove(tar_path)
        raise e

def upload_to_s3(local_file_path, bucket_name, s3_key):
    """
    Upload the model file to S3
    """
    s3_client = boto3.client('s3')
    
    try:
        s3_client.upload_file(local_file_path, bucket_name, s3_key)
        print(f"Successfully uploaded {local_file_path} to s3://{bucket_name}/{s3_key}")
        return True
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return False

def main():
    """
    Main function to create and upload placeholder model
    """
    # Get bucket name from Terraform output or environment
    import subprocess
    import json
    
    try:
        # Get the model bucket name from terraform output
        result = subprocess.run(['terraform', 'output', '-json'], 
                              capture_output=True, text=True, check=True)
        outputs = json.loads(result.stdout)
        model_bucket = outputs['model_bucket_name']['value']
        
        print(f"Using model bucket: {model_bucket}")
        
        # Create placeholder model
        print("Creating placeholder model...")
        model_file = create_placeholder_model()
        
        # Upload to S3
        print("Uploading to S3...")
        success = upload_to_s3(model_file, model_bucket, 'model/model.tar.gz')
        
        # Clean up the local tar file
        if os.path.exists(model_file):
            os.remove(model_file)
        
        if success:
            print("Placeholder model created and uploaded successfully!")
            print("You can now proceed with terraform apply.")
        else:
            print("Failed to upload placeholder model.")
            
    except subprocess.CalledProcessError as e:
        print(f"Error getting terraform outputs: {e}")
        print("Make sure terraform has been applied successfully first.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()