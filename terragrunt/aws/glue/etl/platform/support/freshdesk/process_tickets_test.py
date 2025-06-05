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
    publish_metric,
    get_metrics,
    detect_anomalies,
    METRIC_NAMESPACE,
    METRIC_NAME,
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

    # Mock metrics
    with patch("process_tickets.get_metrics") as mock_get_metrics:
        mock_get_metrics.return_value = [5, 8, 12]  # Some sample historical data

        # Run the process
        process_tickets()

        # Verify no write operation was attempted
        mock_wr_s3.to_parquet.assert_not_called()

        # Verify CloudWatch metrics were published
        mock_cloudwatch.put_metric_data.assert_called()

        # Find the call for new_tickets metric
        found_zero_count = False
        for call in mock_cloudwatch.put_metric_data.call_args_list:
            metrics = call[1]["MetricData"]
            for metric in metrics:
                if (
                    metric["MetricName"] == "ProcessedRecordCount"
                    and metric["Dimensions"][0]["Value"] == "new_tickets"
                    and metric["Value"] == 0
                ):
                    found_zero_count = True
                    break
            if found_zero_count:
                break

        assert (
            found_zero_count
        ), "Expected to find ProcessedRecordCount metric with value 0 for new_tickets"


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


# Test CloudWatch metrics functionality
def test_publish_metric():
    # Mock the CloudWatch client
    mock_cloudwatch = MagicMock()

    # Call the function with test parameters
    metric_namespace = "data-lake/etl/freshdesk"
    metric_name = "ProcessedRecordCount"
    dataset_name = "test-dataset"
    count = 42

    # Execute the function with our test parameters
    publish_metric(mock_cloudwatch, metric_namespace, metric_name, dataset_name, count)

    # Assert CloudWatch client was called with correct parameters
    mock_cloudwatch.put_metric_data.assert_called_once()

    # Get the actual call arguments
    call_args = mock_cloudwatch.put_metric_data.call_args[1]

    # Verify namespace is correct
    assert call_args["Namespace"] == "data-lake/etl/freshdesk"

    # Verify metrics data
    metric_data = call_args["MetricData"]
    assert len(metric_data) == 1  # Should be one metric

    # Verify record count metric
    record_metric = metric_data[0]
    assert record_metric["MetricName"] == metric_name
    assert record_metric["Value"] == count
    assert record_metric["Unit"] == "Count"
    assert record_metric["Dimensions"][0]["Name"] == "Dataset"
    assert record_metric["Dimensions"][0]["Value"] == dataset_name


def test_publish_metric_with_mocked_timestamp():
    # Mock the CloudWatch client
    mock_cloudwatch = MagicMock()

    # Mock datetime.now to return a fixed time
    fixed_datetime = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

    with patch("process_tickets.datetime") as mock_datetime:
        # Configure the mock to return our fixed datetime
        mock_datetime.now.return_value = fixed_datetime
        # Pass through the timezone attribute
        mock_datetime.timezone = UTC

        # Call the function with test parameters
        metric_namespace = "data-lake/etl/freshdesk"
        metric_name = "ProcessedRecordCount"
        dataset_name = "test-dataset"
        count = 100

        # Execute the function
        publish_metric(
            mock_cloudwatch, metric_namespace, metric_name, dataset_name, count
        )

        # Verify CloudWatch client was called with correct parameters
        mock_cloudwatch.put_metric_data.assert_called_once()

        # Get the actual call arguments
        call_args = mock_cloudwatch.put_metric_data.call_args[1]
        metric_data = call_args["MetricData"]

        # Verify the timestamps match our fixed datetime
        assert metric_data[0]["Timestamp"] == fixed_datetime


@patch("process_tickets.datetime")
def test_get_metrics(mock_datetime):
    fixed_now = datetime(2025, 5, 15, 12, 0, 0, tzinfo=timezone.utc)
    fixed_start = datetime(2025, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
    mock_datetime.now.return_value = fixed_now
    mock_datetime.timedelta.return_value = fixed_now - fixed_start

    mock_cloudwatch = Mock()
    mock_cloudwatch.get_metric_statistics.return_value = {
        "Datapoints": [
            {"Timestamp": "2025-05-01T00:00:00Z", "Maximum": 100},
            {"Timestamp": "2025-05-02T00:00:00Z", "Maximum": 150},
            {"Timestamp": "2025-05-03T00:00:00Z", "Maximum": 125},
        ]
    }

    result = get_metrics(
        mock_cloudwatch, METRIC_NAMESPACE, METRIC_NAME, "test_table", 14
    )

    mock_cloudwatch.get_metric_statistics.assert_called_once_with(
        Namespace=METRIC_NAMESPACE,
        MetricName=METRIC_NAME,
        Dimensions=[{"Name": "Dataset", "Value": "test_table"}],
        StartTime=fixed_now - mock_datetime.timedelta(),
        EndTime=fixed_now,
        Period=86400,
        Statistics=["Maximum"],
    )

    # Check the result contains the expected values
    assert isinstance(result, np.ndarray)
    assert list(result) == [100, 150, 125]


@patch("process_tickets.logger")
def test_get_metrics_exception_handling(mock_logger):
    mock_cloudwatch = Mock()
    mock_cloudwatch.get_metric_statistics.side_effect = Exception("Test exception")

    result = get_metrics(
        mock_cloudwatch, METRIC_NAMESPACE, METRIC_NAME, "test_table", 14
    )

    mock_logger.error.assert_called_once()
    assert "Error fetching CloudWatch metric data" in mock_logger.error.call_args[0][0]
    assert result is None


def test_detect_anomalies_normal_data():
    historical_data = np.array([100, 110, 105, 95, 108])
    row_count = 107

    result = detect_anomalies(row_count, historical_data, 2.0)

    assert result == False


@patch("process_tickets.logger")
def test_detect_anomalies_outlier(mock_logger):
    historical_data = np.array([100, 110, 105, 95, 108])
    row_count = 200

    result = detect_anomalies(row_count, historical_data, 2.0)

    assert result == True
    mock_logger.warning.assert_called_once()
    assert "Data-Anomaly: Latest value" in mock_logger.warning.call_args[0][0]


def test_detect_anomalies_zero_standard_deviation():
    historical_data = np.array([100, 100, 100, 100])
    row_count = 110

    result = detect_anomalies(row_count, historical_data, 2.0)

    assert result == False


def test_detect_anomalies_empty_history():
    """Test anomaly detection with empty historical data."""
    historical_data = np.array([])
    row_count = 100

    result = detect_anomalies(row_count, historical_data, 2.0)

    assert result == False
