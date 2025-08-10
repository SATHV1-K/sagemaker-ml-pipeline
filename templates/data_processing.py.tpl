import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
import boto3

# Get job parameters
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'INPUT_BUCKET', 'OUTPUT_BUCKET', 'INPUT_KEY', 'OUTPUT_KEY'])

# Initialize Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

def process_sensor_data():
    """
    Process cleaned sensor data with 5-minute window aggregations
    """
    print("Starting data processing job...")
    
    # Read cleaned data from S3
    input_path = f"s3://{args['INPUT_BUCKET']}/{args['INPUT_KEY']}"
    print(f"Reading cleaned data from: {input_path}")
    
    # Read Parquet files
    df = spark.read.parquet(input_path)
    
    print(f"Input record count: {df.count()}")
    print("Schema:")
    df.printSchema()
    
    # Create 5-minute time windows
    df_windowed = df.withColumn(
        "window_start", 
        date_trunc("minute", col("timestamp")) - 
        expr("INTERVAL " + (minute(col("timestamp")) % 5).cast("string") + " MINUTES")
    )
    
    df_windowed = df_windowed.withColumn(
        "window_end",
        col("window_start") + expr("INTERVAL 5 MINUTES")
    )
    
    # Aggregate data by 5-minute windows
    aggregated_df = df_windowed.groupBy("window_start", "window_end").agg(
        avg("temperature").alias("avg_temperature"),
        avg("humidity").alias("avg_humidity"),
        min("temperature").alias("min_temperature"),
        max("temperature").alias("max_temperature"),
        min("humidity").alias("min_humidity"),
        max("humidity").alias("max_humidity"),
        count("*").alias("record_count"),
        avg("data_quality_score").alias("avg_data_quality")
    )
    
    # Round aggregated values to 2 decimal places
    aggregated_df = aggregated_df.select(
        col("window_start"),
        col("window_end"),
        round(col("avg_temperature"), 2).alias("avg_temperature"),
        round(col("avg_humidity"), 2).alias("avg_humidity"),
        round(col("min_temperature"), 2).alias("min_temperature"),
        round(col("max_temperature"), 2).alias("max_temperature"),
        round(col("min_humidity"), 2).alias("min_humidity"),
        round(col("max_humidity"), 2).alias("max_humidity"),
        col("record_count"),
        round(col("avg_data_quality"), 3).alias("avg_data_quality")
    )
    
    # Add derived features for ML
    aggregated_df = aggregated_df.withColumn(
        "temp_humidity_ratio",
        round(col("avg_temperature") / col("avg_humidity"), 4)
    )
    
    aggregated_df = aggregated_df.withColumn(
        "temp_range",
        round(col("max_temperature") - col("min_temperature"), 2)
    )
    
    aggregated_df = aggregated_df.withColumn(
        "humidity_range",
        round(col("max_humidity") - col("min_humidity"), 2)
    )
    
    # Add time-based features
    aggregated_df = aggregated_df.withColumn("hour_of_day", hour(col("window_start")))
    aggregated_df = aggregated_df.withColumn("day_of_week", dayofweek(col("window_start")))
    aggregated_df = aggregated_df.withColumn("day_of_year", dayofyear(col("window_start")))
    
    # Sort by window start time
    aggregated_df = aggregated_df.orderBy("window_start")
    
    print(f"Processed record count: {aggregated_df.count()}")
    
    # Show sample of processed data
    print("Sample of processed data:")
    aggregated_df.show(10, truncate=False)
    
    # Write processed data to S3 in both Parquet and CSV formats
    output_path_parquet = f"s3://{args['OUTPUT_BUCKET']}/{args['OUTPUT_KEY']}parquet/"
    output_path_csv = f"s3://{args['OUTPUT_BUCKET']}/{args['OUTPUT_KEY']}csv/"
    
    print(f"Writing processed data to: {output_path_parquet}")
    aggregated_df.coalesce(1).write.mode("overwrite").parquet(output_path_parquet)
    
    print(f"Writing processed data to: {output_path_csv}")
    aggregated_df.coalesce(1).write.mode("overwrite").option("header", "true").csv(output_path_csv)
    
    # Create a training dataset (features for ML)
    training_df = aggregated_df.select(
        col("avg_temperature"),
        col("avg_humidity"),
        col("temp_humidity_ratio"),
        col("temp_range"),
        col("humidity_range"),
        col("hour_of_day"),
        col("day_of_week"),
        col("day_of_year"),
        col("record_count"),
        col("avg_data_quality")
    )
    
    # Add target variable (predict next window's average temperature)
    window_spec = Window.orderBy("window_start")
    training_df_with_target = aggregated_df.withColumn(
        "target_temp",
        lead(col("avg_temperature"), 1).over(window_spec)
    ).filter(col("target_temp").isNotNull())
    
    training_features = training_df_with_target.select(
        col("avg_temperature"),
        col("avg_humidity"),
        col("temp_humidity_ratio"),
        col("temp_range"),
        col("humidity_range"),
        col("hour_of_day"),
        col("day_of_week"),
        col("day_of_year"),
        col("record_count"),
        col("avg_data_quality"),
        col("target_temp")
    )
    
    # Write training data
    training_path = f"s3://{args['OUTPUT_BUCKET']}/training/"
    print(f"Writing training data to: {training_path}")
    training_features.coalesce(1).write.mode("overwrite").option("header", "true").csv(training_path)
    
    print("Data processing completed successfully!")
    
    return aggregated_df

if __name__ == "__main__":
    try:
        process_sensor_data()
        print("Job completed successfully")
    except Exception as e:
        print(f"Job failed with error: {str(e)}")
        raise e
    finally:
        job.commit()