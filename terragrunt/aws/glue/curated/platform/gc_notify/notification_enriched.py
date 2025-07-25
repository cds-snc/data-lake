import sys
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from pyspark.sql import DataFrame as SparkDataFrame

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext

args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "transformed_bucket",
        "transformed_prefix",
        "database_name_transformed",
        "target_env",
        "start_month",
        "end_month",
    ],
)

JOB_NAME = args["JOB_NAME"]
TRANSFORMED_BUCKET = args["transformed_bucket"]
TRANSFORMED_PREFIX = args["transformed_prefix"]
DATABASE_NAME_TRANSFORMED = args["database_name_transformed"]
TARGET_ENV = args["target_env"]
START_MONTH = args["start_month"]
END_MONTH = args["end_month"]

# Handle date parameters - default to current and previous month if not provided
now = datetime.now(timezone.utc)
current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
previous_month_start = current_month_start - relativedelta(months=1)

# Parse start_month and end_month parameters


if START_MONTH and START_MONTH.strip():
    start_date = datetime.strptime(START_MONTH, "%Y-%m").replace(
        day=1, tzinfo=timezone.utc
    )
else:
    start_date = previous_month_start

if END_MONTH and END_MONTH.strip():
    end_date = datetime.strptime(END_MONTH, "%Y-%m").replace(day=1, tzinfo=timezone.utc)
else:
    end_date = current_month_start

# Initialize Spark and Glue
sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(JOB_NAME, args)
logger = glueContext.get_logger()

# Configure Spark to handle schema evolution and empty partitions
if spark is not None:
    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")


def execute_enrichment_query(
    start_month_str: str, end_month_str: str
) -> SparkDataFrame:  # Changed return type
    """Execute the SQL query to create enriched notification dataset."""
    logger.info(f"Processing month range: {start_month_str} to {end_month_str}")

    sql_query = f"""
    WITH notification_data AS (
      SELECT
        id AS notification_id,
        billable_units AS notification_billable_units,
        created_at AS notification_created_at,
        queue_name AS notification_queue_name,
        sent_at AS notification_sent_at,
        notification_status,
        notification_type,
        updated_at AS notification_updated_at,
        job_id,
        api_key_id,
        key_type AS api_key_type,
        service_id,
        template_id,
        reference AS notification_reference,
        sms_total_message_price,
        sms_total_carrier_fee,
        sms_iso_country_code,
        sms_carrier_name,
        sms_message_encoding,
        sms_origination_phone_number,
        year,
        month
      FROM {DATABASE_NAME_TRANSFORMED}.platform_gc_notify_notifications
      WHERE month >= '{start_month_str}' AND month <= '{end_month_str}'

      UNION

      SELECT
        id AS notification_id,
        billable_units AS notification_billable_units,
        created_at AS notification_created_at,
        queue_name AS notification_queue_name,
        sent_at AS notification_sent_at,
        notification_status,
        notification_type,
        updated_at AS notification_updated_at,
        job_id,
        api_key_id,
        key_type AS api_key_type,
        service_id,
        template_id,
        reference AS notification_reference,
        sms_total_message_price,
        sms_total_carrier_fee,
        sms_iso_country_code,
        sms_carrier_name,
        sms_message_encoding,
        sms_origination_phone_number,
        year,
        month
      FROM {DATABASE_NAME_TRANSFORMED}.platform_gc_notify_notification_history
      WHERE month >= '{start_month_str}' AND month <= '{end_month_str}'
    ),

    service_data AS (
      SELECT
        s.id AS service_id,
        s.active AS service_active,
        s.count_as_live AS service_count_as_live,
        s.go_live_at AS service_go_live_at,
        s.name AS service_name,
        s.message_limit AS service_message_limit,
        s.rate_limit AS service_rate_limit,
        s.sms_daily_limit AS service_sms_daily_limit,
        s.organisation_id,
        o.name AS organisation_name
      FROM {DATABASE_NAME_TRANSFORMED}.platform_gc_notify_services s
      LEFT JOIN {DATABASE_NAME_TRANSFORMED}.platform_gc_notify_organisation o
        ON s.organisation_id = o.id
    ),

    template_data AS (
      SELECT
        t.id AS template_id,
        t.created_at AS template_created_at,
        t.name AS template_name,
        t.updated_at AS template_updated_at,
        t.version AS template_version,
        t.template_category_id,
        tc.name_en AS tc_name_en,
        tc.name_fr AS tc_name_fr,
        tc.email_process_type AS tc_email_process_type,
        tc.sms_process_type AS tc_sms_process_type,
        tc.sms_sending_vehicle AS tc_sms_sending_vehicle
      FROM {DATABASE_NAME_TRANSFORMED}.platform_gc_notify_templates t
      LEFT JOIN {DATABASE_NAME_TRANSFORMED}.platform_gc_notify_template_categories tc
        ON t.template_category_id = tc.id
    )

    SELECT
      nd.*,
      sd.service_active,
      sd.service_count_as_live,
      sd.service_go_live_at,
      sd.service_name,
      sd.service_message_limit,
      sd.service_rate_limit,
      sd.service_sms_daily_limit,
      sd.organisation_id,
      sd.organisation_name,
      td.template_created_at,
      td.template_name,
      td.template_updated_at,
      td.template_version,
      td.template_category_id,
      td.tc_name_en,
      td.tc_name_fr,
      td.tc_email_process_type,
      td.tc_sms_process_type,
      td.tc_sms_sending_vehicle
    FROM notification_data nd
    INNER JOIN service_data sd
      ON nd.service_id = sd.service_id
    INNER JOIN template_data td
      ON nd.template_id = td.template_id
    """

    logger.info("Executing enrichment SQL query using Spark")
    df = spark.sql(sql_query)

    row_count = df.count()
    logger.info(f"Query returned {row_count} rows")
    return df


def write_to_curated(df: SparkDataFrame, table_name: str):
    """Write the enriched dataset to the curated bucket with partitioning and overwrite."""
    try:
        row_count = df.count()
        # Remove 'platform_gc_notify_' prefix from table name for S3 path
        s3_subdir = table_name
        if s3_subdir.startswith("platform_gc_notify_"):
            s3_subdir = s3_subdir[len("platform_gc_notify_"):]
        s3_path = f"s3://{TRANSFORMED_BUCKET}/{TRANSFORMED_PREFIX}/{s3_subdir}/"

        logger.info(f"Writing {row_count} rows to {s3_path}")
        logger.info("Partitioning by: year, month")

        df.write.mode("overwrite").partitionBy("year", "month").parquet(s3_path)

        # Create/update the Glue table separately to ensure it exists
        logger.info(
            f"Creating/updating Glue table {DATABASE_NAME_TRANSFORMED}.{table_name}"
        )

        # Create temp view from the original DataFrame (no extra read needed)
        df.limit(0).createOrReplaceTempView("temp_table_for_registration")

        # Register table in Glue Data Catalog using Spark SQL
        # Drop table if exists to avoid schema drift
        spark.sql(f"DROP TABLE IF EXISTS {DATABASE_NAME_TRANSFORMED}.{table_name}")
        
        # Create the table in Glue Data Catalog using the original DataFrame's schema
        spark.sql(
            f"""
            CREATE TABLE IF NOT EXISTS {DATABASE_NAME_TRANSFORMED}.{table_name}
            USING PARQUET
            LOCATION '{s3_path}'
            PARTITIONED BY (year, month)
            AS SELECT * FROM temp_table_for_registration WHERE 1=0
        """
        )

        # Refresh partitions to ensure Glue knows about the new partitions
        spark.sql(f"MSCK REPAIR TABLE {DATABASE_NAME_TRANSFORMED}.{table_name}")

        logger.info(
            f"Successfully wrote data to {s3_path} and registered table {table_name}"
        )

    except Exception as e:
        logger.error(f"Error writing to curated bucket: {str(e)}")
        raise


def main():
    """Main execution function."""
    try:
        logger.info("Starting notification enrichment job")

        # Convert dates to YYYY-MM format for filtering
        start_month_str = start_date.strftime("%Y-%m")
        end_month_str = end_date.strftime("%Y-%m")

        logger.info(f"Processing date range: {start_month_str} to {end_month_str}")

        # Execute SQL query to create enriched dataset
        enriched_df = execute_enrichment_query(start_month_str, end_month_str)

        # Write to curated bucket with partition overwrite
        table_name = "platform_gc_notify_notifications_enriched"
        write_to_curated(enriched_df, table_name)

        logger.info("Notification enrichment job completed successfully")

    except Exception as e:
        logger.error(f"Job failed: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        main()
    finally:
        job.commit()
