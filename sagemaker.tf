# SageMaker Training Job
resource "aws_sagemaker_model" "sensor_prediction_model" {
  name               = "${var.project_name}-model-${random_string.suffix.result}"
  execution_role_arn = aws_iam_role.sagemaker_role.arn

  primary_container {
    image = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1"
    model_data_url = "s3://${aws_s3_bucket.model_bucket.bucket}/model/model.tar.gz"
  }

  depends_on = [aws_s3_object.training_script]
}

# SageMaker Endpoint Configuration
resource "aws_sagemaker_endpoint_configuration" "sensor_prediction_config" {
  name = "${var.project_name}-endpoint-config-${random_string.suffix.result}"

  production_variants {
    variant_name           = "primary"
    model_name            = aws_sagemaker_model.sensor_prediction_model.name
    initial_instance_count = 1
    instance_type         = "ml.t2.medium"  # Smallest available instance for endpoints
    initial_variant_weight = 1
  }

  depends_on = [aws_sagemaker_model.sensor_prediction_model]
}

# SageMaker Endpoint
resource "aws_sagemaker_endpoint" "sensor_prediction_endpoint" {
  name                 = "${var.project_name}-endpoint-${random_string.suffix.result}"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.sensor_prediction_config.name

  depends_on = [aws_sagemaker_endpoint_configuration.sensor_prediction_config]
}

# Upload training script to S3
resource "aws_s3_object" "training_script" {
  bucket = aws_s3_bucket.scripts_bucket.bucket
  key    = "sagemaker_scripts/train.py"
  source = "sagemaker_scripts/train.py"

  depends_on = [local_file.training_script]
}

# Create local training script
resource "local_file" "training_script" {
  content = templatefile("${path.module}/templates/train.py.tpl", {
    data_bucket  = aws_s3_bucket.data_bucket.bucket
    model_bucket = aws_s3_bucket.model_bucket.bucket
  })
  filename = "${path.module}/sagemaker_scripts/train.py"
}

# Lambda function to trigger SageMaker training after Glue job completion
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${random_string.suffix.result}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sagemaker:CreateTrainingJob",
          "sagemaker:DescribeTrainingJob",
          "iam:PassRole"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_bucket.arn,
          "${aws_s3_bucket.data_bucket.arn}/*",
          aws_s3_bucket.model_bucket.arn,
          "${aws_s3_bucket.model_bucket.arn}/*"
        ]
      }
    ]
  })
}

# Lambda function
resource "aws_lambda_function" "trigger_training" {
  filename         = "lambda_function.zip"
  function_name    = "${var.project_name}-trigger-training-${random_string.suffix.result}"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      SAGEMAKER_ROLE_ARN = aws_iam_role.sagemaker_role.arn
      DATA_BUCKET       = aws_s3_bucket.data_bucket.bucket
      MODEL_BUCKET      = aws_s3_bucket.model_bucket.bucket
      TRAINING_IMAGE    = "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1"
    }
  }

  depends_on = [data.archive_file.lambda_zip]
}

# Create Lambda deployment package
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "lambda_function.py"
  output_path = "lambda_function.zip"
  depends_on  = [local_file.lambda_function]
}

resource "local_file" "lambda_function" {
  content = templatefile("${path.module}/templates/lambda_function.py.tpl", {
    sagemaker_role_arn = aws_iam_role.sagemaker_role.arn
    data_bucket       = aws_s3_bucket.data_bucket.bucket
    model_bucket      = aws_s3_bucket.model_bucket.bucket
  })
  filename = "${path.module}/lambda_function.py"
}

# EventBridge rule to trigger Lambda when Glue job completes
resource "aws_cloudwatch_event_rule" "glue_job_completion" {
  name        = "${var.project_name}-glue-completion-${random_string.suffix.result}"
  description = "Trigger when Glue data processing job completes successfully"

  event_pattern = jsonencode({
    source      = ["aws.glue"]
    detail-type = ["Glue Job State Change"]
    detail = {
      jobName = [aws_glue_job.data_processing_job.name]
      state   = ["SUCCEEDED"]
    }
  })
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.glue_job_completion.name
  target_id = "TriggerLambda"
  arn       = aws_lambda_function.trigger_training.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trigger_training.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.glue_job_completion.arn
}

# Outputs
output "sagemaker_model_name" {
  description = "Name of the SageMaker model"
  value       = aws_sagemaker_model.sensor_prediction_model.name
}

output "sagemaker_endpoint_name" {
  description = "Name of the SageMaker endpoint"
  value       = aws_sagemaker_endpoint.sensor_prediction_endpoint.name
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.trigger_training.function_name
}