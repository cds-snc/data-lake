import os
import datetime
import logging

import boto3

from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DB_CLUSTER_IDENTIFIER = os.environ["DB_CLUSTER_IDENTIFIER"]
IAM_ROLE_ARN = os.environ["IAM_ROLE_ARN"]
KMS_KEY_ID = os.environ["KMS_KEY_ID"]
TABLE_SCHEMA = os.environ["TABLE_SCHEMA"]
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
S3_EXPORT_PREFIX = os.environ["S3_EXPORT_PREFIX"]

# Only the following tables will be exported
EXPORT_TABLES = [
    "jobs",
    "login_events",
    "notification_history",
    "notifications",
    "organisation",
    "permissions",
    "services",
    "services_history",
    "template_categories",
    "templates",
    "templates_history",
    "user_to_organisation",
    "user_to_service",
    "users",
]


def assume_role(role_arn):
    """Assume the specified IAM role and return temporary credentials"""
    try:
        sts_client = boto3.client("sts")
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn, RoleSessionName="DataLakeExportSession"
        )

        credentials = assumed_role["Credentials"]
        logger.info(f"Successfully assumed role: {role_arn}")

        return {
            "aws_access_key_id": credentials["AccessKeyId"],
            "aws_secret_access_key": credentials["SecretAccessKey"],
            "aws_session_token": credentials["SessionToken"],
        }
    except ClientError as e:
        logger.error(f"Error assuming role: {e}")
        raise


def get_latest_snapshot(rds_client, db_cluster_identifier):
    """Get the latest automated snapshot ARN for the specified DB cluster"""
    try:
        response = rds_client.describe_db_cluster_snapshots(
            DBClusterIdentifier=db_cluster_identifier, SnapshotType="automated"
        )

        if not response["DBClusterSnapshots"]:
            logger.error(
                f"Error no snapshots found for cluster {db_cluster_identifier}"
            )
            return None

        # Get the last snapshot in the list (most recent is last)
        latest_snapshot = response["DBClusterSnapshots"][-1]
        logger.info(
            f"Latest snapshot: {latest_snapshot['DBClusterSnapshotIdentifier']} created at {latest_snapshot['SnapshotCreateTime']}"
        )
        return latest_snapshot["DBClusterSnapshotArn"]

    except ClientError as e:
        logger.error(f"Error getting snapshots: {e}")
        return None


def start_export_task(rds_client, snapshot_arn, table_schema, export_tables):
    """Start an export task for the specified snapshot ARN"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
        export_task_identifier = f"{DB_CLUSTER_IDENTIFIER}-{timestamp}"

        response = rds_client.start_export_task(
            ExportTaskIdentifier=export_task_identifier,
            SourceArn=snapshot_arn,
            S3BucketName=S3_BUCKET_NAME,
            S3Prefix=S3_EXPORT_PREFIX,
            IamRoleArn=IAM_ROLE_ARN,
            KmsKeyId=KMS_KEY_ID,
            ExportOnly=[f"{table_schema}.{table}" for table in export_tables],
        )

        logger.info(f"Export task started: {export_task_identifier}")
        return response["ExportTaskIdentifier"]

    except ClientError as e:
        logger.error(f"Error starting export task: {e}")
        return None


def handler(_event, _context):
    """Retrieve the latest snapshot and start an export task"""

    response = {
        "statusCode": 500,
        "body": "Export task failed to start",
    }
    try:
        assumed_credentials = assume_role(IAM_ROLE_ARN)
        rds_client = boto3.client("rds", **assumed_credentials)

        snapshot_arn = get_latest_snapshot(rds_client, DB_CLUSTER_IDENTIFIER)
        if snapshot_arn:
            export_task_id = start_export_task(
                rds_client, snapshot_arn, TABLE_SCHEMA, EXPORT_TABLES
            )
            if export_task_id:
                logger.info(f"Successfully started export: {export_task_id}")
                response = {
                    "statusCode": 200,
                    "body": f"Export task started: {export_task_id}",
                }

    except Exception as e:
        logger.error(f"Unexpected Error: {e}")

    return response
