import pytest
import datetime
import os
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

os.environ["DB_CLUSTER_IDENTIFIER"] = "test-cluster"
os.environ["IAM_ROLE_ARN"] = "test-role-arn"
os.environ["KMS_KEY_ID"] = "test-kms-key"
os.environ["TABLE_SCHEMA"] = "test-schema"
os.environ["S3_BUCKET_NAME"] = "test-bucket"
os.environ["S3_EXPORT_PREFIX"] = "test/prefix"

from main import (
    assume_role,
    get_latest_snapshot,
    start_export_task,
    handler,
    EXPORT_TABLES,
)


class TestGCNotifyExport:
    @pytest.fixture
    def mock_sts_client(self):
        with patch("boto3.client") as mock_client:
            mock_sts = Mock()
            mock_sts.assume_role.return_value = {
                "Credentials": {
                    "AccessKeyId": "test-access-key",
                    "SecretAccessKey": "test-secret-key",
                    "SessionToken": "test-session-token",
                }
            }
            mock_client.return_value = mock_sts
            yield mock_client, mock_sts

    @pytest.fixture
    def mock_rds_client(self):
        with patch("boto3.client") as mock_client:
            mock_rds = Mock()
            mock_client.return_value = mock_rds
            yield mock_client, mock_rds

    def test_assume_role(self, mock_sts_client):
        mock_client, mock_sts = mock_sts_client

        result = assume_role("test-role-arn")

        mock_sts.assume_role.assert_called_once_with(
            RoleArn="test-role-arn", RoleSessionName="DataLakeExportSession"
        )

        assert result["aws_access_key_id"] == "test-access-key"
        assert result["aws_secret_access_key"] == "test-secret-key"
        assert result["aws_session_token"] == "test-session-token"

    def test_assume_role_error(self, mock_sts_client):
        mock_client, mock_sts = mock_sts_client
        mock_sts.assume_role.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "AssumeRole",
        )

        with pytest.raises(ClientError):
            assume_role("test-role-arn")

    def test_get_latest_snapshot(self, mock_rds_client):
        mock_client, mock_rds = mock_rds_client
        mock_rds.describe_db_cluster_snapshots.return_value = {
            "DBClusterSnapshots": [
                {
                    "DBClusterSnapshotIdentifier": "snapshot-1",
                    "SnapshotCreateTime": "2023-01-01T00:00:00Z",
                    "DBClusterSnapshotArn": "arn:aws:rds:region:account:snapshot/snapshot-1",
                },
                {
                    "DBClusterSnapshotIdentifier": "snapshot-2",
                    "SnapshotCreateTime": "2023-01-02T00:00:00Z",
                    "DBClusterSnapshotArn": "arn:aws:rds:region:account:snapshot/snapshot-2",
                },
            ]
        }

        result = get_latest_snapshot(mock_rds, "test-cluster")

        mock_rds.describe_db_cluster_snapshots.assert_called_once_with(
            DBClusterIdentifier="test-cluster", SnapshotType="automated"
        )
        assert result == "arn:aws:rds:region:account:snapshot/snapshot-2"

    def test_get_latest_snapshot_no_snapshots(self, mock_rds_client):
        mock_client, mock_rds = mock_rds_client
        mock_rds.describe_db_cluster_snapshots.return_value = {"DBClusterSnapshots": []}

        result = get_latest_snapshot(mock_rds, "test-cluster")

        assert result is None

    def test_get_latest_snapshot_error(self, mock_rds_client):
        mock_client, mock_rds = mock_rds_client
        mock_rds.describe_db_cluster_snapshots.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFound",
                    "Message": "Cluster not found",
                }
            },
            "DescribeDBClusterSnapshots",
        )

        result = get_latest_snapshot(mock_rds, "test-cluster")

        assert result is None

    def test_start_export_task(self, mock_rds_client):
        mock_client, mock_rds = mock_rds_client
        mock_rds.start_export_task.return_value = {
            "ExportTaskIdentifier": "test-cluster-2023-01-01"
        }

        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime.datetime(2023, 1, 1)

            result = start_export_task(
                mock_rds, "snapshot-arn", "test-schema", ["table1", "table2"]
            )

            assert result == "test-cluster-2023-01-01"
            mock_rds.start_export_task.assert_called_once()
            args = mock_rds.start_export_task.call_args[1]
            assert "test-schema.table1" in args["ExportOnly"]
            assert "test-schema.table2" in args["ExportOnly"]

    def test_start_export_task_error(self, mock_rds_client):
        mock_client, mock_rds = mock_rds_client
        mock_rds.start_export_task.side_effect = ClientError(
            {
                "Error": {
                    "Code": "InvalidParameterValue",
                    "Message": "Invalid parameter",
                }
            },
            "StartExportTask",
        )

        result = start_export_task(
            mock_rds, "snapshot-arn", "test-schema", ["table1", "table2"]
        )

        assert result is None

    def test_handler_success(self):
        with patch("main.assume_role") as mock_assume_role, patch(
            "boto3.client"
        ) as mock_boto3_client, patch(
            "main.get_latest_snapshot"
        ) as mock_get_snapshot, patch(
            "main.start_export_task"
        ) as mock_start_export:

            mock_assume_role.return_value = {
                "aws_access_key_id": "test-key",
                "aws_secret_access_key": "test-secret",
                "aws_session_token": "test-token",
            }
            mock_rds = Mock()
            mock_boto3_client.return_value = mock_rds
            mock_get_snapshot.return_value = "test-snapshot-arn"
            mock_start_export.return_value = "test-export-id"

            response = handler({}, {})

            mock_assume_role.assert_called_once()
            mock_get_snapshot.assert_called_once()
            mock_start_export.assert_called_once()
            assert response.get("statusCode") == 200

    def test_handler_no_snapshots(self):
        with patch("main.assume_role") as mock_assume_role, patch(
            "boto3.client"
        ) as mock_boto3_client, patch(
            "main.get_latest_snapshot"
        ) as mock_get_snapshot, patch(
            "main.start_export_task"
        ) as mock_start_export:

            mock_assume_role.return_value = {
                "aws_access_key_id": "test-key",
                "aws_secret_access_key": "test-secret",
                "aws_session_token": "test-token",
            }
            mock_get_snapshot.return_value = None

            response = handler({}, {})

            mock_start_export.assert_not_called()
            assert response.get("statusCode") == 500

    def test_handler_export_task_failure(self):
        with patch("main.assume_role") as mock_assume_role, patch(
            "boto3.client"
        ) as mock_boto3_client, patch(
            "main.get_latest_snapshot"
        ) as mock_get_snapshot, patch(
            "main.start_export_task"
        ) as mock_start_export, patch(
            "main.logger"
        ) as mock_logger:

            mock_assume_role.return_value = {
                "aws_access_key_id": "test-key",
                "aws_secret_access_key": "test-secret",
                "aws_session_token": "test-token",
            }
            mock_get_snapshot.return_value = "test-snapshot-arn"
            mock_start_export.return_value = None

            response = handler({}, {})

            assert response.get("statusCode") == 500

    def test_handler_exception(self):
        with patch("main.assume_role") as mock_assume_role:
            mock_assume_role.side_effect = Exception("Test error")

            response = handler({}, {})

            assert response.get("statusCode") == 500
