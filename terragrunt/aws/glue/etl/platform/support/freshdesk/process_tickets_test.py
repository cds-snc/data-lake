import pytest
import sys

from datetime import datetime, timezone, UTC
from unittest.mock import Mock, patch, MagicMock

import numpy as np
import pandas as pd

from awswrangler.exceptions import NoFilesFound

# Create mock for getResolvedOptions that returns test arguments
mock_args = {
    "JOB_NAME": "test_job",
    "source_bucket": "test-source-bucket",
    "source_prefix": "test-source-prefix/",
    "transformed_bucket": "test-transformed-bucket",
    "transformed_prefix": "test-transformed-prefix/",
    "database_name_raw": "test_raw_db",
    "database_name_transformed": "test_transformed_db",
    "table_name": "test_table",
    "gx_config_object": "s3://test-config-bucket/test-config-key",
}

# Mock the AWS Glue and PySpark modules
mock_glue_utils = Mock()
mock_glue_utils.getResolvedOptions.return_value = mock_args
sys.modules["awsglue.utils"] = mock_glue_utils

# flake8: noqa: E402
from process_tickets import (
    validate_with_gx,
    merge_tickets,
    process_tickets,
    get_days_tickets,
)


# Sample test data fixtures
@pytest.fixture
def sample_tickets_df():
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "status": [5, 5, 5],
            "status_label": ["Closed", "Closed", "Closed"],
            "priority": [2, 1, 1],
            "priority_label": ["Medium", "Low", "Low"],
            "source": [10, 2, 2],
            "source_label": ["Outbound Email", "Portal", "Portal"],
            "created_at": [
                pd.Timestamp("2022-09-28 18:01:02"),
                pd.Timestamp("2022-11-03 22:54:16"),
                pd.Timestamp("2022-11-01 15:35:02"),
            ],
            "updated_at": [
                pd.Timestamp("2022-11-28 19:42:07"),
                pd.Timestamp("2022-11-04 13:42:43"),
                pd.Timestamp("2022-11-04 14:55:28"),
            ],
            "month": ["2022-11", "2022-11", "2022-11"],
            "due_by": [
                pd.Timestamp("2024-03-22 14:13:52"),
                pd.Timestamp("2024-01-26 14:24:43"),
                pd.Timestamp("2024-01-26 14:42:28"),
            ],
            "fr_due_by": [
                pd.Timestamp("2022-11-25 15:13:52"),
                pd.Timestamp("2022-11-04 21:00:00"),
                pd.Timestamp("2022-11-02 15:35:02"),
            ],
            "is_escalated": [False, False, False],
            "tags": [
                ["Notify_Dev"],
                [
                    "received-out-of-hours",
                    "z_sent-reply-if-urgent",
                    "Notify_Usability_ReceiverUX",
                ],
                ["z_sent-confirm-reception", "Notify_request_UserAccountConf"],
            ],
            "spam": [False, False, False],
            "requester_email_suffix": ["cyber.gc.ca", "external", "dfo-mpo.gc.ca"],
            "type": ["Problem", "Question", "Feature Request"],
            "product_id": [61000000046.0, 61000000046.0, 61000000046.0],
            "product_name": [
                "GC Notify | Notification GC",
                "GC Notify | Notification GC",
                "GC Notify | Notification GC",
            ],
            "conversations_total_count": [3, 3, 3],
            "conversations_reply_count": [3, 1, 1],
            "conversations_note_count": [3, 2, 2],
            "language": ["English", "Français", "English"],
            "province_or_territory": [None, None, None],
            "organization": [None, None, None],
        }
    )


def test_validate_schema_valid(
    sample_tickets_df,
):
    assert validate_with_gx(sample_tickets_df) is True


def test_validate_schema_missing_column(sample_tickets_df):
    df_missing_column = sample_tickets_df.drop("status", axis=1)
    assert validate_with_gx(df_missing_column) is False


def test_validate_schema_wrong_type(sample_tickets_df):
    df_wrong_type = sample_tickets_df.copy()
    df_wrong_type["priority"] = pd.to_datetime(
        ["2024-01-04", "2024-01-05", "2024-01-06"]
    )
    assert validate_with_gx(df_wrong_type) is False


# Test ticket merging functionality
def test_merge_tickets_empty_existing(sample_tickets_df):
    existing_tickets = pd.DataFrame()
    merged = merge_tickets(existing_tickets, sample_tickets_df)

    assert len(merged) == len(sample_tickets_df)
    assert all(merged["id"] == sample_tickets_df["id"])


def test_merge_tickets_with_duplicates():
    # Create existing tickets with some overlap
    existing_tickets = pd.DataFrame(
        {
            "id": ["1", "2"],
            "subject": ["Old 1", "Old 2"],
            "updated_at": pd.to_datetime(["2024-01-01", "2024-01-02"]),
        }
    )

    # Create new tickets with updated information for id=1
    new_tickets = pd.DataFrame(
        {
            "id": ["1", "3"],
            "subject": ["Updated 1", "New 3"],
            "updated_at": pd.to_datetime(["2024-01-03", "2024-01-03"]),
        }
    )

    merged = merge_tickets(existing_tickets, new_tickets)

    assert len(merged) == 3  # Should have 3 unique tickets
    assert (
        merged[merged["id"] == "1"]["subject"].iloc[0] == "Updated 1"
    )  # Should keep newer version


# Test the main process with mocked AWS services
@patch("boto3.client")
@patch("awswrangler.s3")
@patch("process_tickets.download_s3_object")
def test_process_tickets(
    mock_s3_download, mock_wr_s3, mock_boto3_client, sample_tickets_df
):
    # Mock AWS Wrangler responses
    mock_wr_s3.read_json.return_value = sample_tickets_df
    mock_wr_s3.read_parquet.return_value = sample_tickets_df

    # Mock CloudWatch client
    mock_cloudwatch = MagicMock()
    mock_boto3_client.return_value = mock_cloudwatch

    # Mock metrics
    with patch("process_tickets.get_metrics") as mock_get_metrics:
        mock_get_metrics.return_value = [10, 15, 20]  # Some sample historical data

        # Run the process
        process_tickets()

        # Verify the write operation was called
        mock_wr_s3.to_parquet.assert_called_once()

        # Verify CloudWatch metrics were published
        mock_cloudwatch.put_metric_data.assert_called()

        # Get all calls to put_metric_data
        call_args_list = mock_cloudwatch.put_metric_data.call_args_list

        # Ensure we have the right namespace for metrics
        assert any(
            call[1]["Namespace"] == "data-lake/etl/freshdesk" for call in call_args_list
        )

        # Verify metric for new ticket count was published
        found_record_count_metric = False
        for call in call_args_list:
            metrics = call[1]["MetricData"]
            for metric in metrics:
                if (
                    metric["MetricName"] == "ProcessedRecordCount"
                    and metric["Dimensions"][0]["Value"] == "new_tickets"
                ):
                    found_record_count_metric = True
                    break
            if found_record_count_metric:
                break

        assert (
            found_record_count_metric
        ), "ProcessedRecordCount metric for new_tickets not found"


# Test error handling
@patch("boto3.client")
@patch("awswrangler.s3")
@patch("process_tickets.download_s3_object")
def test_process_tickets_no_new_data(mock_s3_download, mock_wr_s3, mock_boto3_client):
    # Mock empty response from S3
    mock_wr_s3.read_json.side_effect = NoFilesFound("Simulate no file for read_json")

    # Mock CloudWatch client
    mock_cloudwatch = MagicMock()
    mock_boto3_client.return_value = mock_cloudwatch
    process_tickets()
    mock_wr_s3.to_parquet.assert_not_called()


# Test date handling
def test_get_days_tickets_date_handling():
    test_date = datetime(2024, 1, 1, tzinfo=UTC)

    with patch("awswrangler.s3.read_json") as mock_read_json:
        # Create test data with timezone-aware timestamps
        test_data = pd.DataFrame(
            {
                "created_at": [pd.Timestamp("2024-01-01 10:00:00+00:00")],
                "updated_at": [pd.Timestamp("2024-01-01 11:00:00+00:00")],
                "due_by": [pd.Timestamp("2024-01-02 10:00:00+00:00")],
                "fr_due_by": [pd.Timestamp("2024-01-02 11:00:00+00:00")],
            }
        )
        mock_read_json.return_value = test_data

        result = get_days_tickets(test_date)

        # Verify all datetime columns are timezone-naive
        assert result["created_at"].dt.tz is None
        assert result["updated_at"].dt.tz is None
        assert result["due_by"].dt.tz is None
        assert result["fr_due_by"].dt.tz is None


