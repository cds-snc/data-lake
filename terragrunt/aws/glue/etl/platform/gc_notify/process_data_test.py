import pytest
import json
import pandas as pd
import datetime
import sys
from unittest.mock import Mock, patch, mock_open, ANY

sys.modules["pyspark"] = Mock()
sys.modules["pyspark.context"] = Mock()
sys.modules["pyspark.context"].SparkContext = Mock()
sys.modules["pyspark.context"].SparkContext.getOrCreate = Mock(return_value=Mock())

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
    validate_schema,
    postgres_to_pandas_type,
    is_type_compatible,
    parse_dates,
    get_new_data,
    publish_metric,
    get_dataset_config,
    download_s3_object,
    get_incremental_load_date_from,
    process_data,
    Field,
)


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "id": ["1", "2", "3"],
            "created_at": [
                "2024-01-01 12:30:45.123",
                "2024-01-02 10:15:30",
                "2024-01-03 08:45:20.456",
            ],
            "updated_at": [
                "2024-01-01 14:20:15.789",
                "2024-01-02 16:40:10",
                "2024-01-03 18:05:25.321",
            ],
            "status": ["active", "inactive", "pending"],
            "count": [10, 20, 30],
            "is_valid": [True, False, True],
            "amount": [125.45, 230.75, 350.25],
        }
    )


@pytest.fixture
def sample_fields():
    """Sample field definitions for testing."""
    return [
        {"name": "id", "type": "uuid"},
        {"name": "created_at", "type": "timestamp"},
        {"name": "updated_at", "type": "timestamp"},
        {"name": "status", "type": "text"},
        {"name": "count", "type": "integer"},
        {"name": "is_valid", "type": "boolean"},
        {"name": "amount", "type": "numeric"},
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
            "retention_days": 90,
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
            "retention_days": 0,
        },
    ]


def test_validate_schema_valid(sample_dataframe, sample_fields):
    """Test schema validation with valid data."""
    assert validate_schema(sample_dataframe, sample_fields) is True


def test_validate_schema_missing_column(sample_dataframe, sample_fields):
    """Test schema validation with a missing column."""
    df_missing_column = sample_dataframe.drop("status", axis=1)
    assert validate_schema(df_missing_column, sample_fields) is False


def test_validate_schema_type_mismatch(sample_dataframe, sample_fields):
    """Test schema validation with a type mismatch."""
    df_type_mismatch = sample_dataframe.copy()

    with patch(
        "process_data.is_type_compatible",
        side_effect=lambda series, field_type: (
            False if field_type == "integer" else True
        ),
    ):
        assert validate_schema(df_type_mismatch, sample_fields) is False


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


def test_is_type_compatible():
    """Test type compatibility checking."""
    assert is_type_compatible(pd.Series(["a", "b", "c"]), "text") is True
    assert is_type_compatible(pd.Series([1, 2, 3]), "integer") is True
    assert is_type_compatible(pd.Series([1.1, 2.2, 3.3]), "numeric") is True
    assert is_type_compatible(pd.Series([True, False, True]), "boolean") is True
    assert is_type_compatible(pd.Series(["a", "b", "c"]), "integer") is False
    assert is_type_compatible(pd.Series([1, 2, 3]), "boolean") is False
    assert is_type_compatible(pd.Series(["a", "b", "c"]), "unknown_type") is False


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
            "created_at",
            "updated_at",
            "status",
            "count",
            "is_valid",
            "amount",
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

    publish_metric(mock_cloudwatch, "test_dataset", 100, 5.5)

    mock_cloudwatch.put_metric_data.assert_called_once()
    put_metric_args = mock_cloudwatch.put_metric_data.call_args[1]
    assert put_metric_args["Namespace"] == "data-lake/etl/gc-notify"

    metric_data = put_metric_args["MetricData"]
    assert len(metric_data) == 2

    record_count_metric = metric_data[0]
    assert record_count_metric["MetricName"] == "ProcessedRecordCount"
    assert record_count_metric["Dimensions"][0]["Name"] == "Dataset"
    assert record_count_metric["Dimensions"][0]["Value"] == "test_dataset"
    assert record_count_metric["Value"] == 100
    assert record_count_metric["Unit"] == "Count"

    processing_time_metric = metric_data[1]
    assert processing_time_metric["MetricName"] == "ProcessingTime"
    assert processing_time_metric["Dimensions"][0]["Name"] == "Dataset"
    assert processing_time_metric["Dimensions"][0]["Value"] == "test_dataset"
    assert processing_time_metric["Value"] == 5.5
    assert processing_time_metric["Unit"] == "Seconds"


@patch("process_data.zipfile.ZipFile")
@patch("process_data.os.listdir")
@patch("process_data.os.getcwd")
@patch("builtins.open", new_callable=mock_open)
def test_get_dataset_config(
    mock_file, mock_getcwd, mock_listdir, mock_zipfile, sample_dataset_config
):
    """Test loading dataset configurations."""
    mock_getcwd.return_value = "/workspaces/test"
    mock_listdir.return_value = ["notifications.json", "templates.json"]
    mock_file.return_value.__enter__.return_value.read.side_effect = [
        json.dumps(sample_dataset_config[0]),
        json.dumps(sample_dataset_config[1]),
    ]

    result = get_dataset_config()

    mock_zipfile.assert_called_once_with("/workspaces/test/tables.zip", "r")
    mock_zipfile.return_value.__enter__.return_value.extractall.assert_called_once_with(
        "/workspaces/test/tables"
    )

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


def test_download_s3_object():
    """Test the S3 object download function."""
    mock_s3 = Mock()
    s3_url = "s3://test-bucket/path/to/object.zip"

    with patch("os.path.join", return_value="/workspaces/test/tables.zip"):
        with patch("os.getcwd", return_value="/workspaces/test"):
            download_s3_object(mock_s3, s3_url, "tables.zip")

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
@patch("process_data.validate_schema")
@patch("process_data.wr.s3.to_parquet")
@patch("process_data.time.time")
@patch("process_data.datetime")
@patch("process_data.Job")
def test_process_data(
    mock_job,
    mock_datetime,
    mock_time,
    mock_to_parquet,
    mock_validate_schema,
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
    mock_time.side_effect = [1000, 1050, 1100, 1150]

    mock_s3 = Mock()
    mock_cloudwatch = Mock()
    mock_boto3_client.side_effect = [mock_cloudwatch, mock_s3]

    mock_get_dataset_config.return_value = sample_dataset_config
    mock_get_new_data.side_effect = [sample_dataframe, pd.DataFrame()]
    mock_validate_schema.return_value = True

    process_data()

    mock_download_s3_object.assert_called_once_with(
        mock_s3, "s3://test-config-bucket/test-config-key", "tables.zip"
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

    mock_validate_schema.assert_called_once_with(
        sample_dataframe, sample_dataset_config[0]["fields"]
    )
    mock_to_parquet.assert_called_once()

    assert mock_cloudwatch.put_metric_data.call_count == 2


@patch("process_data.get_dataset_config")
@patch("process_data.get_new_data")
@patch("process_data.validate_schema")
@patch("process_data.boto3.client")
@patch("process_data.download_s3_object")
@patch("process_data.Job")
def test_process_data_schema_validation_failure(
    mock_job,
    mock_download_s3_object,
    mock_boto3_client,
    mock_validate_schema,
    mock_get_new_data,
    mock_get_dataset_config,
    sample_dataset_config,
    sample_dataframe,
):
    """Test process_data when schema validation fails."""
    mock_s3 = Mock()
    mock_cloudwatch = Mock()
    mock_boto3_client.side_effect = [mock_cloudwatch, mock_s3]

    mock_get_dataset_config.return_value = [sample_dataset_config[0]]
    mock_get_new_data.return_value = sample_dataframe
    mock_validate_schema.return_value = False

    with pytest.raises(ValueError, match="Schema validation failed for notifications"):
        process_data()
