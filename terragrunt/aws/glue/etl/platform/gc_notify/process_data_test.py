import pytest
import json
import pandas as pd
import numpy as np
import datetime
import sys
from unittest.mock import Mock, patch, mock_open, ANY, call


class MockPysparkDataFrame:
    pass


sys.modules["pyspark"] = Mock()
sys.modules["pyspark.context"] = Mock()
sys.modules["pyspark.context"].SparkContext = Mock()
sys.modules["pyspark.context"].SparkContext.getOrCreate = Mock(return_value=Mock())
sys.modules["pyspark.sql"] = Mock()
sys.modules["pyspark.sql"].DataFrame = MockPysparkDataFrame


sys.modules["awsglue"] = Mock()
sys.modules["awsglue.context"] = Mock()
sys.modules["awsglue.context"].GlueContext = Mock()
sys.modules["awsglue.job"] = Mock()
sys.modules["awsglue.job"].Job = Mock()


sys.modules["awsglue.utils"] = Mock()
sys.modules["awsglue.utils"].getResolvedOptions = Mock()
sys.modules["awsglue.utils"].getResolvedOptions.return_value = {
    "JOB_NAME": "test_job",
    "source_bucket": "test-source-bucket",
    "source_prefix": "test-source-prefix",
    "transformed_bucket": "test-transformed-bucket",
    "transformed_prefix": "test-transformed-prefix",
    "database_name_transformed": "test_database_transformed",
    "table_config_object": "s3://test-config-bucket/test-config-key",
    "gx_config_object": "s3://test-config-bucket/test-config-key",
    "table_name_prefix": "test_prefix",
    "target_env": "test",
}


class MockNoFilesFound(Exception):
    """Mock exception for NoFilesFound"""

    pass


sys.modules["awswrangler"] = Mock()
sys.modules["awswrangler"].exceptions = Mock()
sys.modules["awswrangler"].exceptions.NoFilesFound = MockNoFilesFound

# Import the module after mocking dependencies
# flake8: noqa: E402
from process_data import (
    validate_with_gx,
    postgres_to_pandas_type,
    parse_dates,
    get_new_data,
    publish_metric,
    get_dataset_config,
    download_s3_object,
    get_incremental_load_date_from,
    get_metrics,
    detect_anomalies,
    process_data,
    Field,
    METRIC_NAMESPACE,
    METRIC_NAME,
    ANOMALY_LOOKBACK_DAYS,
    ANOMALY_STANDARD_DEVIATION,
)


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "id": [
                "11111111-1234-abde-abde-aaabbbccc123",
                "11111111-1234-abde-abde-aaabbbccc124",
                "11111111-1234-abde-abde-aaabbbccc125",
            ],
            "original_file_name": [
                "message_gcnotify",
                "message_gcnotify",
                "message_gcnotify",
            ],
            "service_id": [
                "11111111-1234-abde-abde-aaabbbccc123",
                "11111111-1234-abde-abde-aaabbbccc124",
                "11111111-1234-abde-abde-aaabbbccc125",
            ],
            "template_id": [
                "11111111-1234-abde-abde-aaabbbccc123",
                "11111111-1234-abde-abde-aaabbbccc124",
                "11111111-1234-abde-abde-aaabbbccc125",
            ],
            "created_at": [
                pd.Timestamp("2024-09-19 12:46:02.268903"),
                pd.Timestamp("2024-09-19 12:46:18.002539"),
                pd.Timestamp("2024-09-19 12:46:32.720726"),
            ],
            "updated_at": [
                pd.Timestamp("2024-09-27 09:07:57.236219"),
                pd.Timestamp("2024-09-27 09:07:57.236219"),
                pd.Timestamp("2024-09-27 09:07:57.236220"),
            ],
            "notification_count": [1, 1, 1],
            "notifications_sent": [0, 0, 0],
            "processing_started": [
                pd.Timestamp("2024-09-19 12:46:02.334265"),
                pd.Timestamp("2024-09-19 12:46:18.059370"),
                pd.Timestamp("2024-09-19 12:46:32.782187"),
            ],
            "processing_finished": [
                pd.Timestamp("2024-09-19 12:47:00.161073"),
                pd.Timestamp("2024-09-19 12:47:00.583338"),
                pd.Timestamp("2024-09-19 12:47:01.010010"),
            ],
            "created_by_id": [
                "6af522d0-2915-4e52-83a3-3690455a5fe6",
                "6af522d0-2915-4e52-83a3-3690455a5fe6",
                "6af522d0-2915-4e52-83a3-3690455a5fe6",
            ],
            "template_version": [8, 8, 8],
            "notifications_delivered": [0, 0, 0],
            "notifications_failed": [0, 0, 0],
            "job_status": ["finished", "finished", "finished"],
            "scheduled_for": [pd.NaT, pd.NaT, pd.NaT],
            "archived": [True, True, True],
            "api_key_id": [
                "11111111-1234-abde-abde-aaabbbccc123",
                "11111111-1234-abde-abde-aaabbbccc124",
                "11111111-1234-abde-abde-aaabbbccc153",
            ],
            "sender_id": [None, None, None],
            "data_modified": [
                pd.Timestamp("2025-05-29 00:33:29"),
                pd.Timestamp("2025-05-29 00:33:29"),
                pd.Timestamp("2025-05-29 00:33:29"),
            ],
            "year": ["2024", "2024", "2024"],
            "month": ["2024-09", "2024-09", "2024-09"],
        }
    )


@pytest.fixture
def sample_fields():
    """Sample field definitions for testing."""
    return [
        {"name": "id", "type": "uuid"},
        {"name": "original_file_name", "type": "varchar"},
        {"name": "service_id", "type": "uuid"},
        {"name": "template_id", "type": "uuid"},
        {"name": "created_at", "type": "timestamp"},
        {"name": "updated_at", "type": "timestamp"},
        {"name": "notification_count", "type": "integer"},
        {"name": "notifications_sent", "type": "integer"},
        {"name": "processing_started", "type": "timestamp"},
        {"name": "processing_finished", "type": "timestamp"},
        {"name": "created_by_id", "type": "uuid"},
        {"name": "template_version", "type": "integer"},
        {"name": "notifications_delivered", "type": "integer"},
        {"name": "notifications_failed", "type": "integer"},
        {"name": "job_status", "type": "varchar"},
        {"name": "scheduled_for", "type": "timestamp"},
        {"name": "archived", "type": "boolean"},
        {"name": "api_key_id", "type": "uuid"},
        {"name": "sender_id", "type": "uuid"},
    ]


@pytest.fixture
def sample_dataset_config():
    """Sample dataset configuration for testing."""
    return [
        {
            "table_name": "notifications",
            "partition_timestamp": "created_at",
            "partition_cols": ["year", "month", "day"],
            "fields": [
                {"name": "id", "type": "uuid"},
                {"name": "created_at", "type": "timestamp"},
                {"name": "updated_at", "type": "timestamp"},
                {"name": "status", "type": "text"},
            ],
            "incremental_load": True,
            "look_back_days": 90,
        },
        {
            "table_name": "templates",
            "partition_timestamp": None,
            "partition_cols": None,
            "fields": [
                {"name": "id", "type": "uuid"},
                {"name": "name", "type": "text"},
                {"name": "created_at", "type": "timestamp"},
            ],
            "incremental_load": False,
            "look_back_days": 0,
        },
    ]


def test_validate_with_gx_valid(
    sample_dataframe,
):
    """Test schema validation with valid data."""
    gx_checkpoint = "notify-jobs_checkpoint"
    assert validate_with_gx(sample_dataframe, gx_checkpoint) is True


def test_validate_with_gx_missing_column(sample_dataframe):
    """Test schema validation with a missing column."""
    df_missing_column = sample_dataframe.drop("job_status", axis=1)
    gx_checkpoint = "notify-jobs_checkpoint"
    assert validate_with_gx(df_missing_column, gx_checkpoint) is False


def test_validate_with_gx_type_mismatch(sample_dataframe, sample_fields):
    """Test schema validation with a type mismatch."""
    df_type_mismatch = sample_dataframe.copy()
    df_type_mismatch["scheduled_for"] = True
    gx_checkpoint = "notify-jobs_checkpoint"
    assert validate_with_gx(df_type_mismatch, gx_checkpoint) is False


def test_postgres_to_pandas_type():
    """Test conversion from PostgreSQL types to pandas types."""
    assert isinstance(postgres_to_pandas_type("uuid"), pd.StringDtype)
    assert isinstance(postgres_to_pandas_type("text"), pd.StringDtype)
    assert isinstance(postgres_to_pandas_type("varchar"), pd.StringDtype)
    assert isinstance(postgres_to_pandas_type("integer"), pd.Int64Dtype)
    assert isinstance(postgres_to_pandas_type("int"), pd.Int64Dtype)
    assert isinstance(postgres_to_pandas_type("numeric"), pd.Float64Dtype)
    assert isinstance(postgres_to_pandas_type("float"), pd.Float64Dtype)
    assert isinstance(postgres_to_pandas_type("boolean"), pd.BooleanDtype)
    assert isinstance(postgres_to_pandas_type("bool"), pd.BooleanDtype)
    assert postgres_to_pandas_type("timestamp") == "datetime64[ns]"
    assert isinstance(postgres_to_pandas_type("notification_type"), pd.StringDtype)
    assert isinstance(postgres_to_pandas_type("template_type"), pd.StringDtype)
    assert isinstance(postgres_to_pandas_type("sms_sending_vehicle"), pd.StringDtype)
    assert postgres_to_pandas_type("unknown_type") is None


def test_parse_dates():
    """Test date parsing function."""
    dates = pd.Series(
        ["2024-01-01 12:30:45.123", "2024-01-02 10:15:30", "2024-01-03 08:45:20.456"]
    )

    result = parse_dates(dates)

    assert pd.isna(result).sum() == 0

    assert result[0] == pd.Timestamp("2024-01-01 12:30:45.123")
    assert result[1] == pd.Timestamp("2024-01-02 10:15:30")
    assert result[2] == pd.Timestamp("2024-01-03 08:45:20.456")


@patch("process_data.ds")
@patch("process_data.wr.s3.read_parquet")
def test_get_new_data_full_load(
    mock_read_parquet, mock_ds, sample_dataframe, sample_fields
):
    """Test the get_new_data function for a full load."""
    mock_read_parquet.return_value = sample_dataframe

    result = get_new_data("test_path", sample_fields)

    mock_read_parquet.assert_called_once()
    assert len(result) == len(sample_dataframe)


@patch("process_data.ds")
def test_get_new_data_incremental_load(mock_ds, sample_dataframe, sample_fields):
    """Test the get_new_data function for an incremental load."""
    mock_dataset = Mock()
    mock_scanner = Mock()
    mock_table = Mock()
    mock_table.to_pandas.return_value = sample_dataframe
    mock_scanner.to_table.return_value = mock_table
    mock_dataset.scanner.return_value = mock_scanner
    mock_ds.dataset.return_value = mock_dataset
    mock_ds.field.return_value = "timestamp_filter"

    result = get_new_data(
        "test_path",
        sample_fields,
        partition_timestamp="created_at",
        partition_cols=["year", "month", "day"],
        date_from="2024-01-01 00:00:00",
    )

    mock_ds.dataset.assert_called_once()
    mock_ds.field.assert_called_with("created_at")
    mock_dataset.scanner.assert_called_once_with(
        filter=True,
        columns=[
            "id",
            "original_file_name",
            "service_id",
            "template_id",
            "created_at",
            "updated_at",
            "notification_count",
            "notifications_sent",
            "processing_started",
            "processing_finished",
            "created_by_id",
            "template_version",
            "notifications_delivered",
            "notifications_failed",
            "job_status",
            "scheduled_for",
            "archived",
            "api_key_id",
            "sender_id",
        ],
    )
    assert len(result) == len(sample_dataframe)
    assert "year" in result.columns
    assert "month" in result.columns
    assert "day" in result.columns


@patch("process_data.wr.s3.read_parquet")
def test_get_new_data_no_files_found(mock_read_parquet, sample_fields):
    """Test the get_new_data function when no files are found."""
    from process_data import wr

    original_exception = wr.exceptions.NoFilesFound
    wr.exceptions.NoFilesFound = MockNoFilesFound
    mock_read_parquet.side_effect = wr.exceptions.NoFilesFound()

    try:
        result = get_new_data("test_path", sample_fields)
        assert result.empty
        mock_read_parquet.assert_called_once()
    finally:
        wr.exceptions.NoFilesFound = original_exception


@patch("process_data.datetime")
def test_publish_metric(mock_datetime):
    """Test the publish_metric function."""
    mock_datetime.now.return_value = datetime.datetime(
        2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc
    )
    mock_cloudwatch = Mock()

    publish_metric(
        mock_cloudwatch, METRIC_NAMESPACE, "ProcessedRecordCount", "test_dataset", 100
    )

    mock_cloudwatch.put_metric_data.assert_called_once()
    put_metric_args = mock_cloudwatch.put_metric_data.call_args[1]
    assert put_metric_args["Namespace"] == METRIC_NAMESPACE

    metric_data = put_metric_args["MetricData"]
    assert len(metric_data) == 1

    record_metric = metric_data[0]
    assert record_metric["MetricName"] == "ProcessedRecordCount"
    assert record_metric["Dimensions"][0]["Name"] == "Dataset"
    assert record_metric["Dimensions"][0]["Value"] == "test_dataset"
    assert record_metric["Value"] == 100
    assert record_metric["Unit"] == "Count"


@patch("process_data.os.listdir")
@patch("process_data.os.getcwd")
@patch("builtins.open", new_callable=mock_open)
def test_get_dataset_config(
    mock_file, mock_getcwd, mock_listdir, sample_dataset_config
):
    """Test loading dataset configurations."""
    mock_getcwd.return_value = "/workspaces/test"
    mock_listdir.return_value = ["notifications.json", "templates.json"]
    mock_file.return_value.__enter__.return_value.read.side_effect = [
        json.dumps(sample_dataset_config[0]),
        json.dumps(sample_dataset_config[1]),
    ]

    result = get_dataset_config()

    assert len(result) == 2
    assert result[0]["table_name"] == "notifications"
    assert result[1]["table_name"] == "templates"

    mock_file.assert_any_call("/workspaces/test/tables/notifications.json", "r")
    mock_file.assert_any_call("/workspaces/test/tables/templates.json", "r")


@patch("process_data.os.listdir")
@patch("process_data.os.getcwd")
@patch("process_data.zipfile.ZipFile")
def test_get_dataset_config_no_files(mock_zipfile, mock_getcwd, mock_listdir):
    """Test get_dataset_config when no config files are found."""
    mock_getcwd.return_value = "/workspaces/test"
    mock_listdir.return_value = []

    with pytest.raises(ValueError, match="No dataset configurations found"):
        get_dataset_config()


@patch("process_data.os.listdir")
@patch("process_data.os.getcwd")
@patch("process_data.zipfile.ZipFile")
def test_get_dataset_config_dir_not_found(mock_zipfile, mock_getcwd, mock_listdir):
    """Test get_dataset_config when tables directory is not found."""
    mock_getcwd.return_value = "/workspaces/test"
    mock_listdir.side_effect = FileNotFoundError

    with pytest.raises(ValueError, match="Tables directory not found"):
        get_dataset_config()


@patch("process_data.zipfile.ZipFile")
def test_download_s3_object(mock_zipfile):
    """Test the S3 object download function."""
    mock_s3 = Mock()
    s3_url = "s3://test-bucket/path/to/object.zip"

    with patch("os.getcwd", return_value="/workspaces/test"):
        download_s3_object(mock_s3, s3_url, "tables.zip")

    mock_zipfile.assert_called_once_with("/workspaces/test/tables.zip", "r")
    mock_zipfile.return_value.__enter__.return_value.extractall.assert_called_once_with(
        "/workspaces/test/tables"
    )

    mock_s3.download_file.assert_called_once_with(
        Bucket="test-bucket",
        Key="path/to/object.zip",
        Filename="/workspaces/test/tables.zip",
    )


@patch("process_data.pd.Timestamp")
def test_get_incremental_load_date_from(mock_timestamp):
    """Test the function that gets the date for incremental loads."""
    mock_now = Mock()
    mock_now.normalize.return_value = pd.Timestamp("2024-05-15")
    mock_timestamp.now.return_value = mock_now

    result = get_incremental_load_date_from(90)

    mock_now.normalize.assert_called_once()
    assert result.startswith("2024-02-01")

    mock_now.normalize.reset_mock()
    result = get_incremental_load_date_from(30)
    mock_now.normalize.assert_called_once()
    assert result.startswith("2024-04-01")


@patch("process_data.boto3.client")
@patch("process_data.download_s3_object")
@patch("process_data.get_dataset_config")
@patch("process_data.get_new_data")
@patch("process_data.validate_with_gx")
@patch("process_data.get_metrics")
@patch("process_data.detect_anomalies")
@patch("process_data.wr.s3.to_parquet")
@patch("process_data.datetime")
@patch("process_data.Job")
def test_process_data(
    mock_job,
    mock_datetime,
    mock_to_parquet,
    mock_detect_anomalies,
    mock_get_metrics,
    mock_validate_with_gx,
    mock_get_new_data,
    mock_get_dataset_config,
    mock_download_s3_object,
    mock_boto3_client,
    sample_dataset_config,
    sample_dataframe,
):
    """Test the main process_data function."""
    mock_datetime_obj = Mock()
    mock_datetime_obj.strftime.return_value = "2024-05-15"
    mock_datetime.now.return_value = mock_datetime_obj

    mock_s3 = Mock()
    mock_cloudwatch = Mock()
    mock_boto3_client.side_effect = [mock_cloudwatch, mock_s3]
    mock_get_metrics.return_value = np.array([100, 110, 90])
    mock_detect_anomalies.return_value = False

    mock_get_dataset_config.return_value = sample_dataset_config
    mock_get_new_data.side_effect = [sample_dataframe, pd.DataFrame()]
    mock_validate_with_gx.return_value = True

    process_data()

    mock_download_s3_object.assert_has_calls(
        [
            call(mock_s3, "s3://test-config-bucket/test-config-key", "tables.zip"),
            call(mock_s3, "s3://test-config-bucket/test-config-key", "gx.zip"),
        ]
    )

    assert mock_get_new_data.call_count == 2

    mock_get_new_data.assert_any_call(
        f"notification-canada-ca-test-cluster-2024-05-15/NotificationCanadaCatest/public.notifications",
        sample_dataset_config[0]["fields"],
        sample_dataset_config[0]["partition_timestamp"],
        sample_dataset_config[0]["partition_cols"],
        date_from=ANY,
    )

    mock_get_new_data.assert_any_call(
        f"notification-canada-ca-test-cluster-2024-05-15/NotificationCanadaCatest/public.templates",
        sample_dataset_config[1]["fields"],
        sample_dataset_config[1]["partition_timestamp"],
        sample_dataset_config[1]["partition_cols"],
        date_from=None,
    )

    mock_validate_with_gx.assert_called_once_with(
        sample_dataframe,
        "notify-" + sample_dataset_config[0]["table_name"] + "_checkpoint",
    )
    mock_to_parquet.assert_called_once()

    assert mock_get_metrics.call_count == 2
    mock_get_metrics.assert_any_call(
        mock_cloudwatch,
        METRIC_NAMESPACE,
        METRIC_NAME,
        "notifications",
        ANOMALY_LOOKBACK_DAYS,
    )
    mock_get_metrics.assert_any_call(
        mock_cloudwatch,
        METRIC_NAMESPACE,
        METRIC_NAME,
        "templates",
        ANOMALY_LOOKBACK_DAYS,
    )

    assert mock_detect_anomalies.call_count == 2

    call_args_list = mock_detect_anomalies.call_args_list

    assert call_args_list[0][0][0] == len(sample_dataframe)
    assert np.array_equal(call_args_list[0][0][1], np.array([100, 110, 90]))
    assert call_args_list[0][0][2] == ANOMALY_STANDARD_DEVIATION

    assert call_args_list[1][0][0] == 0
    assert np.array_equal(call_args_list[1][0][1], np.array([100, 110, 90]))
    assert call_args_list[1][0][2] == ANOMALY_STANDARD_DEVIATION

    assert mock_cloudwatch.put_metric_data.call_count == 2


@patch("process_data.get_dataset_config")
@patch("process_data.get_new_data")
@patch("process_data.validate_with_gx")
@patch("process_data.get_metrics")
@patch("process_data.detect_anomalies")
@patch("process_data.boto3.client")
@patch("process_data.download_s3_object")
@patch("process_data.Job")
def test_process_data_schema_validation_failure(
    mock_job,
    mock_download_s3_object,
    mock_boto3_client,
    mock_detect_anomalies,
    mock_get_metrics,
    mock_validate_with_gx,
    mock_get_new_data,
    mock_get_dataset_config,
    sample_dataset_config,
    sample_dataframe,
):
    """Test process_data when schema validation fails."""
    mock_s3 = Mock()
    mock_cloudwatch = Mock()
    mock_boto3_client.side_effect = [mock_cloudwatch, mock_s3]
    mock_get_metrics.return_value = np.array([100, 110, 90])
    mock_detect_anomalies.return_value = False

    mock_get_dataset_config.return_value = [sample_dataset_config[0]]
    mock_get_new_data.return_value = sample_dataframe
    mock_validate_with_gx.return_value = False

    with pytest.raises(
        ValueError,
        match="Great Expectations validation failed for notifications. Aborting ETL process.",
    ):
        process_data()


@patch("process_data.datetime")
def test_get_metrics(mock_datetime):
    fixed_now = datetime.datetime(2025, 5, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)
    fixed_start = datetime.datetime(2025, 5, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
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


@patch("process_data.logger")
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


@patch("process_data.logger")
def test_detect_anomalies_outlier(mock_logger):
    historical_data = np.array([100, 110, 105, 95, 108])
    row_count = 200

    result = detect_anomalies(row_count, historical_data, 2.0)

    assert result == True
    mock_logger.error.assert_called_once()
    assert "Anomaly: Latest value" in mock_logger.error.call_args[0][0]


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
