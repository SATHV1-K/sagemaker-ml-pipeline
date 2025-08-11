#!/usr/bin/env python3
"""
Test script to verify the XGBoost model works correctly
"""

import boto3
import tarfile
import tempfile
import os
import xgboost as xgb
import numpy as np

def test_model_from_s3():
    """
    Download and test the XGBoost model from S3
    """
    # Get S3 client
    s3 = boto3.client('s3')
    
    # Get bucket name from terraform output
    try:
        import subprocess
        result = subprocess.run(['terraform', 'output', '-json'], 
                              capture_output=True, text=True, check=True)
        import json
        outputs = json.loads(result.stdout)
        bucket_name = outputs['model_bucket_name']['value']
    except Exception as e:
        print(f"Error getting terraform outputs: {e}")
        print("Using default bucket name...")
        bucket_name = "sagemaker-ml-pipeline-models-f5ofrag0"
    
    print(f"Testing model from bucket: {bucket_name}")
    
    # Download model from S3
    with tempfile.TemporaryDirectory() as temp_dir:
        model_tar_path = os.path.join(temp_dir, 'model.tar.gz')
        model_path = os.path.join(temp_dir, 'model.pkl')
        
        try:
            # Download the model
            s3.download_file(bucket_name, 'model/model.tar.gz', model_tar_path)
            print("Model downloaded successfully")
            
            # Extract the model
            with tarfile.open(model_tar_path, 'r:gz') as tar:
                tar.extractall(temp_dir)
            print("Model extracted successfully")
            
            # Load the XGBoost model
            model = xgb.Booster()
            model.load_model(model_path)
            print("Model loaded successfully")
            
            # Test prediction
            test_data = np.random.rand(5, 4)  # 5 samples, 4 features
            dtest = xgb.DMatrix(test_data)
            predictions = model.predict(dtest)
            
            print(f"Test predictions: {predictions}")
            print("Model test completed successfully!")
            
            return True
            
        except Exception as e:
            print(f"Error testing model: {e}")
            return False

if __name__ == "__main__":
    success = test_model_from_s3()
    if success:
        print("\n✅ XGBoost model is working correctly!")
    else:
        print("\n❌ XGBoost model test failed!")