import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
import boto3

# Get job parameters
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'INPUT_BUCKET', 'OUTPUT_BUCKET', 'INPUT_KEY', 'OUTPUT_KEY'])

# Initialize Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

def clean_sensor_data():
    """
    Clean sensor data by handling missing values and outliers
    """
    print("Starting data cleaning job...")
    
    # Read data from S3
    input_path = f"s3://{args['INPUT_BUCKET']}/{args['INPUT_KEY']}"
    print(f"Reading data from: {input_path}")
    
    # Read CSV file
    df = spark.read.option("header", "true").option("inferSchema", "true").csv(input_path)
    
    print(f"Initial record count: {df.count()}")
    print("Schema:")
    df.printSchema()
    
    # Convert timestamp to proper timestamp type
    df = df.withColumn("timestamp", to_timestamp(col("timestamp")))
    
    # Remove records with null timestamps
    df = df.filter(col("timestamp").isNotNull())
    
    # Handle missing temperature values - fill with median
    temp_median = df.select(percentile_approx("temperature", 0.5)).collect()[0][0]
    df = df.fillna({"temperature": temp_median})
    
    # Handle missing humidity values - fill with median
    humidity_median = df.select(percentile_approx("humidity", 0.5)).collect()[0][0]
    df = df.fillna({"humidity": humidity_median})
    
    # Remove outliers using IQR method for temperature
    temp_q1 = df.select(percentile_approx("temperature", 0.25)).collect()[0][0]
    temp_q3 = df.select(percentile_approx("temperature", 0.75)).collect()[0][0]
    temp_iqr = temp_q3 - temp_q1
    temp_lower = temp_q1 - 1.5 * temp_iqr
    temp_upper = temp_q3 + 1.5 * temp_iqr
    
    df = df.filter(
        (col("temperature") >= temp_lower) & 
        (col("temperature") <= temp_upper)
    )
    
    # Remove outliers using IQR method for humidity
    humidity_q1 = df.select(percentile_approx("humidity", 0.25)).collect()[0][0]
    humidity_q3 = df.select(percentile_approx("humidity", 0.75)).collect()[0][0]
    humidity_iqr = humidity_q3 - humidity_q1
    humidity_lower = humidity_q1 - 1.5 * humidity_iqr
    humidity_upper = humidity_q3 + 1.5 * humidity_iqr
    
    df = df.filter(
        (col("humidity") >= humidity_lower) & 
        (col("humidity") <= humidity_upper)
    )
    
    # Add data quality flags
    df = df.withColumn("data_quality_score", 
        when((col("temperature").between(10, 40)) & 
             (col("humidity").between(20, 95)), 1.0)
        .otherwise(0.8)
    )
    
    # Sort by timestamp
    df = df.orderBy("timestamp")
    
    print(f"Cleaned record count: {df.count()}")
    
    # Write cleaned data to S3 in Parquet format
    output_path = f"s3://{args['OUTPUT_BUCKET']}/{args['OUTPUT_KEY']}"
    print(f"Writing cleaned data to: {output_path}")
    
    df.coalesce(1).write.mode("overwrite").parquet(output_path)
    
    print("Data cleaning completed successfully!")
    
    return df

if __name__ == "__main__":
    try:
        clean_sensor_data()
        print("Job completed successfully")
    except Exception as e:
        print(f"Job failed with error: {str(e)}")
        raise e
    finally:
        job.commit()