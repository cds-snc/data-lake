import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import (
    year, month, to_timestamp, col, current_timestamp, 
    when, lit, struct, count, sum
)
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, \
    BooleanType, ArrayType, TimestampType
import boto3
from datetime import datetime
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FreshdeskETL:
    def __init__(self):
        # Initialize AWS Glue context
        self.args = getResolvedOptions(sys.argv, [
            'JOB_NAME', 
            'input_path', 
            'output_path',
            'cloudwatch_namespace',
            'validation_threshold'
        ])
        self.sc = SparkContext()
        self.glue_context = GlueContext(self.sc)
        self.spark = self.glue_context.spark_session
        self.job = Job(self.glue_context)
        self.job.init(self.args['JOB_NAME'], self.args)
        
        # Initialize metrics client
        self.cloudwatch = boto3.client('cloudwatch')
        
        # Define expected schema
        self.expected_schema = StructType([
            StructField("id", IntegerType(), False),
            StructField("status", IntegerType(), True),
            StructField("status_label", StringType(), True),
            StructField("priority", IntegerType(), True),
            StructField("priority_label", StringType(), True),
            StructField("source", IntegerType(), True),
            StructField("source_label", StringType(), True),
            StructField("created_at", StringType(), True),
            StructField("updated_at", StringType(), True),
            StructField("due_by", StringType(), True),
            StructField("fr_due_by", StringType(), True),
            StructField("is_escalated", BooleanType(), True),
            StructField("tags", ArrayType(StringType()), True),
            StructField("spam", BooleanType(), True),
            StructField("requester_email_suffix", StringType(), True),
            StructField("type", StringType(), True),
            StructField("product_id", IntegerType(), True),
            StructField("product_name", StringType(), True),
            StructField("converstations", StructType([
                StructField("total_count", IntegerType(), True),
                StructField("reply_count", IntegerType(), True),
                StructField("note_count", IntegerType(), True)
            ]), True),
            StructField("custom_fields", StructType([
                StructField("language", StringType(), True),
                StructField("province_or_territory", StringType(), True),
                StructField("organization", StringType(), True)
            ]), True)
        ])

    def publish_metric(self, metric_name, value, unit='Count'):
        """Publish metrics to CloudWatch"""
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.args['cloudwatch_namespace'],
                MetricData=[{
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Timestamp': datetime.now()
                }]
            )
        except Exception as e:
            logger.error(f"Failed to publish metric {metric_name}: {str(e)}")

    def validate_data(self, df):
        """Perform data validation checks"""
        validation_results = []
        
        # Check for nulls in required fields
        required_fields = ['id', 'created_at', 'updated_at']
        for field in required_fields:
            null_count = df.filter(col(field).isNull()).count()
            validation_results.append({
                'check': f'null_{field}',
                'passed': null_count == 0,
                'details': f'Found {null_count} null values in {field}'
            })
        
        # Validate date formats
        date_fields = ['created_at', 'updated_at', 'due_by', 'fr_due_by']
        for field in date_fields:
            invalid_dates = df.filter(
                ~col(field).rlike('^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$')
            ).count()
            validation_results.append({
                'check': f'date_format_{field}',
                'passed': invalid_dates == 0,
                'details': f'Found {invalid_dates} invalid date formats in {field}'
            })
        
        # Validate data relationships
        invalid_updates = df.filter(col('updated_at') < col('created_at')).count()
        validation_results.append({
            'check': 'update_date_relationship',
            'passed': invalid_updates == 0,
            'details': f'Found {invalid_updates} records where updated_at < created_at'
        })
        
        # Calculate overall validation score
        total_checks = len(validation_results)
        passed_checks = sum(1 for r in validation_results if r['passed'])
        validation_score = passed_checks / total_checks
        
        # Log validation results
        logger.info(f"Validation Results: {json.dumps(validation_results, indent=2)}")
        self.publish_metric('ValidationScore', validation_score, 'None')
        
        # Fail if validation score is below threshold
        threshold = float(self.args['validation_threshold'])
        if validation_score < threshold:
            raise ValueError(
                f"Data validation score {validation_score} below threshold {threshold}"
            )
        
        return df

    def optimize_performance(self, df):
        """Apply performance optimizations"""
        # Repartition based on data size
        record_count = df.count()
        partition_count = max(1, record_count // 100000)  # 1 partition per 100k records
        df = df.repartition(partition_count)
        
        # Cache frequently accessed data
        df = df.cache()
        
        return df

    def handle_schema_evolution(self, existing_df, new_df):
        """Handle schema differences between existing and new data"""
        if existing_df is None:
            return new_df
            
        # Get all columns from both dataframes
        existing_columns = set(existing_df.columns)
        new_columns = set(new_df.columns)
        
        # Add missing columns to each dataframe with null values
        for col_name in existing_columns - new_columns:
            new_df = new_df.withColumn(col_name, lit(None))
            
        for col_name in new_columns - existing_columns:
            existing_df = existing_df.withColumn(col_name, lit(None))
            
        # Align column order
        all_columns = sorted(existing_columns.union(new_columns))
        existing_df = existing_df.select(all_columns)
        new_df = new_df.select(all_columns)
        
        return existing_df.unionByName(new_df)

    def process(self):
        """Main ETL process"""
        try:
            # Read input data
            logger.info(f"Reading input data from {self.args['input_path']}")
            input_dyf = self.glue_context.create_dynamic_frame.from_options(
                connection_type="s3",
                connection_options={"paths": [self.args['input_path']]},
                format="json",
                schema=self.expected_schema
            )
            
            # Convert to DataFrame
            input_df = input_dyf.toDF()
            initial_count = input_df.count()
            self.publish_metric('InputRecordCount', initial_count)
            
            # Validate data
            logger.info("Validating input data")
            input_df = self.validate_data(input_df)
            
            # Transform timestamps
            logger.info("Transforming timestamps")
            timestamp_columns = ['created_at', 'updated_at', 'due_by', 'fr_due_by']
            for col_name in timestamp_columns:
                input_df = input_df.withColumn(col_name, to_timestamp(col_name))
            
            # Add partition columns
            input_df = input_df.withColumn("year", year("created_at")) \
                              .withColumn("month", month("created_at"))
            
            # Read existing data if available
            existing_df = None
            try:
                logger.info(f"Reading existing data from {self.args['output_path']}")
                existing_df = self.spark.read.parquet(self.args['output_path'])
                self.publish_metric('ExistingRecordCount', existing_df.count())
            except Exception as e:
                logger.warning(f"No existing data found: {str(e)}")
            
            # Handle schema evolution and combine data
            logger.info("Combining new and existing data")
            combined_df = self.handle_schema_evolution(existing_df, input_df)
            
            # Deduplicate and keep latest versions
            combined_df = combined_df \
                .orderBy("id", "updated_at") \
                .dropDuplicates(["id"])
            
            # Optimize performance
            logger.info("Applying performance optimizations")
            combined_df = self.optimize_performance(combined_df)
            
            # Write output
            logger.info(f"Writing output to {self.args['output_path']}")
            combined_df.write \
                .mode("overwrite") \
                .partitionBy("year", "month") \
                .parquet(self.args['output_path'])
            
            # Publish final metrics
            final_count = combined_df.count()
            self.publish_metric('OutputRecordCount', final_count)
            self.publish_metric('DuplicatesRemoved', initial_count - final_count)
            
            logger.info("ETL job completed successfully")
            
        except Exception as e:
            logger.error(f"ETL job failed: {str(e)}")
            raise
        finally:
            # Clean up
            self.job.commit()

if __name__ == "__main__":
    etl = FreshdeskETL()
    etl.process()