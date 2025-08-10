# Glue Job 1: Data Cleaning
resource "aws_glue_job" "data_cleaning_job" {
  name         = "${var.project_name}-data-cleaning-${random_string.suffix.result}"
  role_arn     = aws_iam_role.glue_role.arn
  glue_version = "4.0"
  worker_type  = "G.1X"
  number_of_workers = 2
  timeout      = 60

  command {
    script_location = "s3://${aws_s3_bucket.scripts_bucket.bucket}/glue_scripts/data_cleaning.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-disable"
    "--enable-metrics"                   = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.scripts_bucket.bucket}/spark-logs/"
    "--enable-job-insights"              = "true"
    "--enable-glue-datacatalog"          = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--INPUT_BUCKET"                     = aws_s3_bucket.data_bucket.bucket
    "--OUTPUT_BUCKET"                    = aws_s3_bucket.data_bucket.bucket
    "--INPUT_KEY"                        = "raw/sensor_data_raw.csv"
    "--OUTPUT_KEY"                       = "cleaned/"
  }

  depends_on = [aws_s3_object.data_cleaning_script]
}

# Glue Job 2: Data Processing and Aggregation
resource "aws_glue_job" "data_processing_job" {
  name         = "${var.project_name}-data-processing-${random_string.suffix.result}"
  role_arn     = aws_iam_role.glue_role.arn
  glue_version = "4.0"
  worker_type  = "G.1X"
  number_of_workers = 2
  timeout      = 60

  command {
    script_location = "s3://${aws_s3_bucket.scripts_bucket.bucket}/glue_scripts/data_processing.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-disable"
    "--enable-metrics"                   = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.scripts_bucket.bucket}/spark-logs/"
    "--enable-job-insights"              = "true"
    "--enable-glue-datacatalog"          = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--INPUT_BUCKET"                     = aws_s3_bucket.data_bucket.bucket
    "--OUTPUT_BUCKET"                    = aws_s3_bucket.data_bucket.bucket
    "--INPUT_KEY"                        = "cleaned/"
    "--OUTPUT_KEY"                       = "processed/"
  }

  depends_on = [aws_s3_object.data_processing_script]
}

# Glue Workflow to orchestrate jobs
resource "aws_glue_workflow" "ml_pipeline_workflow" {
  name        = "${var.project_name}-workflow-${random_string.suffix.result}"
  description = "ML Pipeline workflow for data cleaning and processing"
}

# Glue Trigger for Job 1 (Manual start)
resource "aws_glue_trigger" "start_data_cleaning" {
  name         = "${var.project_name}-start-cleaning-${random_string.suffix.result}"
  type         = "ON_DEMAND"
  workflow_name = aws_glue_workflow.ml_pipeline_workflow.name

  actions {
    job_name = aws_glue_job.data_cleaning_job.name
  }
}

# Glue Trigger for Job 2 (Triggered after Job 1 success)
resource "aws_glue_trigger" "start_data_processing" {
  name         = "${var.project_name}-start-processing-${random_string.suffix.result}"
  type         = "CONDITIONAL"
  workflow_name = aws_glue_workflow.ml_pipeline_workflow.name

  predicate {
    conditions {
      job_name = aws_glue_job.data_cleaning_job.name
      state    = "SUCCEEDED"
    }
  }

  actions {
    job_name = aws_glue_job.data_processing_job.name
  }
}

# Upload Glue scripts to S3
resource "aws_s3_object" "data_cleaning_script" {
  bucket = aws_s3_bucket.scripts_bucket.bucket
  key    = "glue_scripts/data_cleaning.py"
  source = "glue_scripts/data_cleaning.py"

  depends_on = [local_file.data_cleaning_script]
}

resource "aws_s3_object" "data_processing_script" {
  bucket = aws_s3_bucket.scripts_bucket.bucket
  key    = "glue_scripts/data_processing.py"
  source = "glue_scripts/data_processing.py"

  depends_on = [local_file.data_processing_script]
}

# Create local files for Glue scripts
resource "local_file" "data_cleaning_script" {
  content  = file("${path.module}/templates/data_cleaning.py.tpl")
  filename = "${path.module}/glue_scripts/data_cleaning.py"
}

resource "local_file" "data_processing_script" {
  content  = file("${path.module}/templates/data_processing.py.tpl")
  filename = "${path.module}/glue_scripts/data_processing.py"
}

# Outputs for Glue jobs
output "glue_job_1_name" {
  description = "Name of the data cleaning Glue job"
  value       = aws_glue_job.data_cleaning_job.name
}

output "glue_job_2_name" {
  description = "Name of the data processing Glue job"
  value       = aws_glue_job.data_processing_job.name
}

output "glue_workflow_name" {
  description = "Name of the Glue workflow"
  value       = aws_glue_workflow.ml_pipeline_workflow.name
}