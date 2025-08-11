import boto3
import pandas as pd
import pyarrow.parquet as pq
import io

def convert_parquet_to_csv():
    """
    Convert the parquet training data to CSV format for XGBoost
    """
    s3 = boto3.client('s3')
    bucket = 'sagemaker-ml-pipeline-data-f5ofrag0'
    
    try:
        # List parquet files in training folder
        response = s3.list_objects_v2(Bucket=bucket, Prefix='training/')
        
        if 'Contents' not in response:
            print("No training data found")
            return
            
        for obj in response['Contents']:
            if obj['Key'].endswith('.parquet'):
                print(f"Converting {obj['Key']} to CSV...")
                
                # Download parquet file
                parquet_obj = s3.get_object(Bucket=bucket, Key=obj['Key'])
                parquet_data = parquet_obj['Body'].read()
                
                # Read parquet data
                df = pd.read_parquet(io.BytesIO(parquet_data))
                
                # Convert to CSV
                csv_key = obj['Key'].replace('.parquet', '.csv')
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False, header=False)  # XGBoost expects no header
                
                # Upload CSV to S3
                s3.put_object(
                    Bucket=bucket,
                    Key=csv_key,
                    Body=csv_buffer.getvalue()
                )
                
                print(f"Uploaded {csv_key}")
                
        print("Conversion completed successfully!")
        
    except Exception as e:
        print(f"Error converting data: {str(e)}")

if __name__ == "__main__":
    convert_parquet_to_csv()