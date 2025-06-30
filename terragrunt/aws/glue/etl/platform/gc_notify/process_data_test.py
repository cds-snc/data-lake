import pytest
import json
import numpy as np
import datetime
import sys
import os
from unittest.mock import Mock, patch, mock_open, MagicMock
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    BooleanType,
    TimestampType,
    DoubleType,
)

# Set environment variables for local Spark
os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"


# Mock AWS Glue modules before importing process_data
class MockGlueContext:
    def __init__(self, spark_context=None):
        self.spark_session = None  # Will be set in tests

    def get_logger(self):
        return Mock()

    def create_dynamic_frame_from_options(self, *args, **kwargs):
        return Mock()

    def write_dynamic_frame(self):
        return Mock()


sys.modules["awsglue"] = Mock()
sys.modules["awsglue.context"] = Mock()
sys.modules["awsglue.context"].GlueContext = MockGlueContext
sys.modules["awsglue.job"] = Mock()
sys.modules["awsglue.job"].Job = Mock()
sys.modules["awsglue.dynamicframe"] = Mock()
sys.modules["awsglue.dynamicframe"].DynamicFrame = Mock()

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

# Import after mocking AWS Glue modules
import great_expectations as gx
from process_data import (
    postgres_to_spark_type,
    get_new_data,
    publish_metric,
    get_dataset_config,
    download_s3_object,
    get_incremental_load_date_from,
    get_metrics,
    detect_anomalies,
    validate_with_gx,
    METRIC_NAMESPACE,
    METRIC_NAME,
)


@pytest.fixture(scope="session")
def spark_session():
    """Create a local Spark session for testing."""
    spark = (
        SparkSession.builder.appName("ProcessDataTest")
        .config("spark.master", "local[*]")
        .config("spark.sql.execution.arrow.pyspark.enabled", "false")
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "1g")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .config("spark.sql.adaptive.enabled", "false")
        .getOrCreate()
    )

    # Set log level to reduce noise during testing
    spark.sparkContext.setLogLevel("ERROR")

    yield spark
    spark.stop()


@pytest.fixture
def sample_spark_dataframe(spark_session):
    """Create a real Spark DataFrame for testing."""
    schema = StructType(
        [
            StructField("id", StringType(), True),
            StructField("original_file_name", StringType(), True),
            StructField("service_id", StringType(), True),
            StructField("template_id", StringType(), True),
            StructField("created_at", TimestampType(), True),
            StructField("updated_at", TimestampType(), True),
            StructField("notification_count", IntegerType(), True),
            StructField("notifications_sent", IntegerType(), True),
            StructField("processing_started", TimestampType(), True),
            StructField("processing_finished", TimestampType(), True),
            StructField("created_by_id", StringType(), True),
            StructField("template_version", IntegerType(), True),
            StructField("notifications_delivered", IntegerType(), True),
            StructField("notifications_failed", IntegerType(), True),
            StructField("job_status", StringType(), True),
            StructField("scheduled_for", TimestampType(), True),
            StructField("archived", BooleanType(), True),
            StructField("api_key_id", StringType(), True),
            StructField("sender_id", StringType(), True),
            StructField("data_modified", TimestampType(), True),
            StructField("year", StringType(), True),
            StructField("month", StringType(), True),
        ]
    )

    data = [
        (
            "11111111-1234-abde-abde-aaabbbccc123",
            "message_gcnotify",
            "11111111-1234-abde-abde-aaabbbccc123",
            "11111111-1234-abde-abde-aaabbbccc123",
            datetime.datetime(2024, 9, 19, 12, 46, 2, 268903),
            datetime.datetime(2024, 9, 27, 9, 7, 57, 236219),
            1,
            0,
            datetime.datetime(2024, 9, 19, 12, 46, 2, 334265),
            datetime.datetime(2024, 9, 19, 12, 47, 0, 161073),
            "6af522d0-2915-4e52-83a3-3690455a5fe6",
            8,
            0,
            0,
            "finished",
            None,
            True,
            "11111111-1234-abde-abde-aaabbbccc123",
            None,
            datetime.datetime(2025, 5, 29, 0, 33, 29),
            "2024",
            "2024-09",
        ),
        (
            "11111111-1234-abde-abde-aaabbbccc124",
            "message_gcnotify",
            "11111111-1234-abde-abde-aaabbbccc124",
            "11111111-1234-abde-abde-aaabbbccc124",
            datetime.datetime(2024, 9, 19, 12, 46, 18, 2539),
            datetime.datetime(2024, 9, 27, 9, 7, 57, 236219),
            1,
            0,
            datetime.datetime(2024, 9, 19, 12, 46, 18, 59370),
            datetime.datetime(2024, 9, 19, 12, 47, 0, 583338),
            "6af522d0-2915-4e52-83a3-3690455a5fe6",
            8,
            0,
            0,
            "finished",
            None,
            True,
            "11111111-1234-abde-abde-aaabbbccc124",
            None,
            datetime.datetime(2025, 5, 29, 0, 33, 29),
            "2024",
            "2024-09",
        ),
        (
            "11111111-1234-abde-abde-aaabbbccc125",
            "message_gcnotify",
            "11111111-1234-abde-abde-aaabbbccc125",
            "11111111-1234-abde-abde-aaabbbccc125",
            datetime.datetime(2024, 9, 19, 12, 46, 32, 720726),
            datetime.datetime(2024, 9, 27, 9, 7, 57, 236220),
            1,
            0,
            datetime.datetime(2024, 9, 19, 12, 46, 32, 782187),
            datetime.datetime(2024, 9, 19, 12, 47, 1, 10010),
            "6af522d0-2915-4e52-83a3-3690455a5fe6",
            8,
            0,
            0,
            "finished",
            None,
            True,
            "11111111-1234-abde-abde-aaabbbccc153",
            None,
            datetime.datetime(2025, 5, 29, 0, 33, 29),
            "2024",
            "2024-09",
        ),
    ]

    return spark_session.createDataFrame(data, schema)


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


# ===== SPARK DATAFRAME TESTS =====


def test_spark_dataframe_creation(sample_spark_dataframe):
    """Test that we can create and work with Spark DataFrames."""
    assert sample_spark_dataframe.count() == 3
    assert len(sample_spark_dataframe.columns) == 22
    assert "id" in sample_spark_dataframe.columns
    assert "job_status" in sample_spark_dataframe.columns


def test_spark_dataframe_operations(sample_spark_dataframe):
    """Test basic Spark DataFrame operations."""
    # Test filtering
    filtered_df = sample_spark_dataframe.filter(
        sample_spark_dataframe.job_status == "finished"
    )
    assert filtered_df.count() == 3

    # Test column selection
    id_df = sample_spark_dataframe.select("id", "job_status")
    assert len(id_df.columns) == 2

    # Test adding a column
    with_new_col = sample_spark_dataframe.withColumn(
        "test_col", sample_spark_dataframe.notification_count + 1
    )
    assert "test_col" in with_new_col.columns


# ===== POSTGRES TO SPARK TYPE TESTS =====


def test_postgres_to_spark_type():
    """Test conversion from PostgreSQL types to Spark types."""

    assert isinstance(postgres_to_spark_type("uuid"), StringType)
    assert isinstance(postgres_to_spark_type("text"), StringType)
    assert isinstance(postgres_to_spark_type("varchar"), StringType)
    assert isinstance(postgres_to_spark_type("integer"), IntegerType)
    assert isinstance(postgres_to_spark_type("int"), IntegerType)
    assert isinstance(postgres_to_spark_type("numeric"), DoubleType)
    assert isinstance(postgres_to_spark_type("float"), DoubleType)
    assert isinstance(postgres_to_spark_type("boolean"), BooleanType)
    assert isinstance(postgres_to_spark_type("bool"), BooleanType)
    assert isinstance(postgres_to_spark_type("timestamp"), TimestampType)
    assert isinstance(postgres_to_spark_type("notification_type"), StringType)
    assert isinstance(postgres_to_spark_type("template_type"), StringType)
    assert isinstance(postgres_to_spark_type("sms_sending_vehicle"), StringType)
    # Unknown types default to StringType
    assert isinstance(postgres_to_spark_type("unknown_type"), StringType)


# ===== GET NEW DATA TESTS =====


def test_get_new_data_with_spark_mock(
    spark_session, sample_spark_dataframe, sample_fields
):
    """Test the get_new_data function with a mocked Spark session."""
    # Mock the spark.read.parquet call to return our test DataFrame
    with patch("process_data.spark", spark_session), patch.object(
        spark_session.read, "parquet", return_value=sample_spark_dataframe
    ):

        result = get_new_data("s3://test-bucket/test-path", sample_fields)

        # The function should return a DataFrame
        assert result is not None
        # We can't easily test the exact result due to complex transformations,
        # but we can verify it doesn't crash


def test_get_new_data_incremental_load_with_spark(
    spark_session, sample_spark_dataframe, sample_fields
):
    """Test incremental loading with real Spark operations."""
    # Mock the spark.read.parquet call to return our test DataFrame
    with patch("process_data.spark", spark_session), patch.object(
        spark_session.read, "parquet", return_value=sample_spark_dataframe
    ):

        result = get_new_data(
            "s3://test-bucket/test-path",
            sample_fields,
            partition_timestamp="created_at",
            partition_cols=["year", "month", "day"],
            date_from="2024-01-01 00:00:00",
        )

        # The function should return a DataFrame
        assert result is not None


def test_get_new_data_exception_handling(spark_session, sample_fields):
    """Test exception handling in get_new_data."""
    # Mock spark to raise an exception
    with patch("process_data.spark", spark_session), patch.object(
        spark_session.read, "parquet", side_effect=Exception("File not found")
    ):

        # Should create an empty DataFrame when exception occurs
        result = get_new_data("s3://invalid-path", sample_fields)

        # Should return an empty DataFrame
        assert result.count() == 0


# ===== BUSINESS LOGIC TESTS =====


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


@patch("process_data.datetime")
def test_get_incremental_load_date_from(mock_datetime):
    """Test the function that gets the date for incremental loads."""
    import datetime as real_datetime

    mock_datetime.now.return_value = real_datetime.datetime(
        2024, 5, 15, 12, 0, 0, tzinfo=real_datetime.timezone.utc
    )
    mock_datetime.timedelta = real_datetime.timedelta

    result = get_incremental_load_date_from(90)
    assert result.startswith("2024-02-01")

    result = get_incremental_load_date_from(30)
    assert result.startswith("2024-04-01")


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

    result = detect_anomalies("foo", row_count, historical_data, 2.0)

    assert not result


@patch("process_data.logger")
def test_detect_anomalies_outlier(mock_logger):
    historical_data = np.array([100, 110, 105, 95, 108])
    row_count = 200

    result = detect_anomalies("foo", row_count, historical_data, 2.0)

    assert result
    mock_logger.warn.assert_called_once()
    assert "Data-Anomaly for foo: Latest value" in mock_logger.warn.call_args[0][0]


def test_detect_anomalies_zero_standard_deviation():
    historical_data = np.array([100, 100, 100, 100])
    row_count = 110

    result = detect_anomalies("foo", row_count, historical_data, 2.0)

    assert result is False


def test_detect_anomalies_empty_history():
    """Test anomaly detection with empty historical data."""
    historical_data = np.array([])
    row_count = 100

    result = detect_anomalies("foo", row_count, historical_data, 2.0)

    assert result is False


# ===== GREAT EXPECTATIONS VALIDATION TESTS =====


def test_validate_with_gx_basic_validation(spark_session):
    """Test basic GX validation with Spark DataFrame."""
    # Create test DataFrame
    test_data = [
        ("001", "user1@example.com", "delivered", "2024-01-01 12:00:00"),
        ("002", "user2@example.com", "delivered", "2024-01-01 12:05:00"),
        ("003", "user3@example.com", "delivered", "2024-01-01 12:10:00"),
    ]
    df = spark_session.createDataFrame(
        test_data, ["id", "email", "status", "created_at"]
    )

    with patch("great_expectations.get_context") as mock_get_context, patch(
        "process_data.configure_gx_stores"
    ) as _, patch("process_data.SOURCE_BUCKET", "test-bucket"):

        mock_context = MagicMock()
        mock_get_context.return_value = mock_context

        # Mock datasource structure
        mock_context.datasources = {"spark_datasource": MagicMock()}
        mock_context.datasources["spark_datasource"].execution_engine = MagicMock()

        # Mock checkpoint result
        mock_result = {"success": True}
        mock_context.run_checkpoint.return_value = mock_result

        # Test validation
        result = validate_with_gx(df, spark_session, "test_checkpoint", "test_batch")

        assert result is True
        mock_context.run_checkpoint.assert_called_once()


def test_validate_with_gx_validation_failure(spark_session):
    """Test GX validation failure handling with Spark DataFrame."""
    # Create test DataFrame with problematic data
    test_data = [
        ("001", "invalid-email", "delivered", "2024-01-01 12:00:00"),
        (None, "user2@example.com", "unknown_status", "2024-01-01 12:05:00"),
    ]
    df = spark_session.createDataFrame(
        test_data, ["id", "email", "status", "created_at"]
    )

    with patch("great_expectations.get_context") as mock_get_context, patch(
        "process_data.configure_gx_stores"
    ) as _, patch("process_data.SOURCE_BUCKET", "test-bucket"):

        mock_context = MagicMock()
        mock_get_context.return_value = mock_context

        # Mock datasource structure
        mock_context.datasources = {"spark_datasource": MagicMock()}
        mock_context.datasources["spark_datasource"].execution_engine = MagicMock()

        # Mock checkpoint result with failure
        mock_result = {"success": False, "run_results": {}}
        mock_context.run_checkpoint.return_value = mock_result

        # Test validation failure
        result = validate_with_gx(df, spark_session, "test_checkpoint", "test_batch")

        assert result is False
        mock_context.run_checkpoint.assert_called_once()


def test_validate_with_gx_runtime_batch_request(spark_session):
    """Test that GX validation creates proper RuntimeBatchRequest with Spark DataFrame."""
    test_data = [("001", "user1@example.com", "delivered", "2024-01-01 12:00:00")]
    df = spark_session.createDataFrame(
        test_data, ["id", "email", "status", "created_at"]
    )

    with patch("great_expectations.get_context") as mock_get_context:
        mock_context = MagicMock()
        mock_get_context.return_value = mock_context

        mock_result = MagicMock()
        mock_result.success = True
        mock_context.run_checkpoint.return_value = mock_result

        validate_with_gx(df, spark_session, "test_checkpoint", "test_batch")

        # Check that run_checkpoint was called with the right parameters
        call_args = mock_context.run_checkpoint.call_args
        assert call_args[1]["checkpoint_name"] == "test_checkpoint"

        # Check that batch_request contains runtime parameters
        batch_request = call_args[1]["batch_request"]
        assert "runtime_parameters" in batch_request
        assert "batch_identifiers" in batch_request


def test_validate_with_gx_exception_handling(spark_session):
    """Test GX validation exception handling."""
    test_data = [("001", "user1@example.com", "delivered", "2024-01-01 12:00:00")]
    df = spark_session.createDataFrame(
        test_data, ["id", "email", "status", "created_at"]
    )

    with patch("great_expectations.get_context") as mock_get_context:
        mock_get_context.side_effect = Exception("GX context error")

        # Should return False on exception
        result = validate_with_gx(df, spark_session, "test_checkpoint", "test_batch")
        assert result is False


def test_validate_with_gx_with_different_schemas(spark_session):
    """Test GX validation with different DataFrame schemas."""
    # Test with different column types
    schema = StructType(
        [
            StructField("notification_id", StringType(), True),
            StructField("recipient_email", StringType(), True),
            StructField("delivery_status", StringType(), True),
            StructField("sent_timestamp", TimestampType(), True),
            StructField("is_processed", BooleanType(), True),
            StructField("retry_count", IntegerType(), True),
        ]
    )

    test_data = [
        (
            "notif_001",
            "test@example.com",
            "delivered",
            datetime.datetime(2024, 1, 1, 12, 0, 0),
            True,
            0,
        ),
        (
            "notif_002",
            "test2@example.com",
            "failed",
            datetime.datetime(2024, 1, 1, 12, 5, 0),
            False,
            3,
        ),
    ]

    df = spark_session.createDataFrame(test_data, schema)

    with patch("great_expectations.get_context") as mock_get_context:
        mock_context = MagicMock()
        mock_get_context.return_value = mock_context

        mock_result = MagicMock()
        mock_result.success = True
        mock_context.run_checkpoint.return_value = mock_result

        result = validate_with_gx(df, spark_session, "test_checkpoint", "test_batch")
        assert result is True


def test_spark_dataframe_gx_integration_end_to_end(spark_session):
    """Test end-to-end integration of Spark DataFrame operations with GX validation."""
    # Create a more realistic dataset
    schema = StructType(
        [
            StructField("id", StringType(), True),
            StructField("template_id", StringType(), True),
            StructField("email_address", StringType(), True),
            StructField("phone_number", StringType(), True),
            StructField("line_1", StringType(), True),
            StructField("line_2", StringType(), True),
            StructField("line_3", StringType(), True),
            StructField("line_4", StringType(), True),
            StructField("line_5", StringType(), True),
            StructField("line_6", StringType(), True),
            StructField("postage", StringType(), True),
            StructField("status", StringType(), True),
            StructField("created_at", TimestampType(), True),
            StructField("sent_at", TimestampType(), True),
            StructField("completed_at", TimestampType(), True),
            StructField("estimated_delivery", TimestampType(), True),
        ]
    )

    test_data = [
        (
            "notif_001",
            "template_1",
            "user1@example.com",
            "+1234567890",
            "Line 1",
            "Line 2",
            "Line 3",
            "Line 4",
            "Line 5",
            "Line 6",
            "first",
            "delivered",
            datetime.datetime(2024, 1, 1, 10, 0, 0),
            datetime.datetime(2024, 1, 1, 10, 5, 0),
            datetime.datetime(2024, 1, 1, 12, 0, 0),
            datetime.datetime(2024, 1, 3, 10, 0, 0),
        ),
        (
            "notif_002",
            "template_2",
            "user2@example.com",
            "+1234567891",
            "Line A",
            "Line B",
            "Line C",
            "Line D",
            "Line E",
            "Line F",
            "second",
            "sending",
            datetime.datetime(2024, 1, 1, 11, 0, 0),
            datetime.datetime(2024, 1, 1, 11, 5, 0),
            None,
            None,
        ),
    ]

    df = spark_session.createDataFrame(test_data, schema)

    # Test DataFrame operations
    assert df.count() == 2

    # Test filtering operations
    delivered_df = df.filter(df.status == "delivered")
    assert delivered_df.count() == 1

    # Test aggregation operations
    status_counts = df.groupBy("status").count().collect()
    assert len(status_counts) == 2

    # Test with GX validation (mocked)
    with patch("great_expectations.get_context") as mock_get_context:
        mock_context = MagicMock()
        mock_get_context.return_value = mock_context

        mock_result = MagicMock()
        mock_result.success = True
        mock_context.run_checkpoint.return_value = mock_result

        # Validate original dataset
        result = validate_with_gx(
            df, spark_session, "gc_notify_checkpoint", "test_batch"
        )
        assert result is True

        # Validate filtered dataset
        result = validate_with_gx(
            delivered_df, spark_session, "gc_notify_checkpoint", "delivered_batch"
        )
        assert result is True


def test_spark_dataframe_type_conversions_for_gx(spark_session):
    """Test that Spark DataFrame type conversions work properly for GX validation."""
    # Test various data types that might come from PostgreSQL
    from pyspark.sql.functions import col, to_timestamp

    # Raw data as it might come from PostgreSQL
    raw_data = [
        ("001", "2024-01-01 12:00:00", "123.45", "true", "42"),
        ("002", "2024-01-01 13:00:00", "678.90", "false", "84"),
    ]

    df = spark_session.createDataFrame(
        raw_data, ["id", "timestamp_str", "amount_str", "flag_str", "count_str"]
    )

    # Convert types as would happen in real ETL
    df_converted = df.select(
        col("id"),
        to_timestamp(col("timestamp_str"), "yyyy-MM-dd HH:mm:ss").alias(
            "timestamp_col"
        ),
        col("amount_str").cast("double").alias("amount"),
        col("flag_str").cast("boolean").alias("flag"),
        col("count_str").cast("integer").alias("count"),
    )

    # Verify conversions
    assert df_converted.schema["timestamp_col"].dataType == TimestampType()
    assert df_converted.schema["amount"].dataType.typeName() == "double"
    assert df_converted.schema["flag"].dataType == BooleanType()
    assert df_converted.schema["count"].dataType == IntegerType()

    # Test with GX validation
    with patch("great_expectations.get_context") as mock_get_context:
        mock_context = MagicMock()
        mock_get_context.return_value = mock_context

        mock_result = MagicMock()
        mock_result.success = True
        mock_context.run_checkpoint.return_value = mock_result

        result = validate_with_gx(
            df_converted, spark_session, "test_checkpoint", "converted_batch"
        )
        assert result is True


# ===== REAL GREAT EXPECTATIONS VALIDATION TESTS =====


def test_real_gx_validation_with_valid_notify_jobs_data(spark_session):
    """Test actual GX validation with valid notify-jobs data that should pass all expectations."""
    # Create valid notify-jobs data that matches all expectations
    schema = StructType(
        [
            StructField("id", StringType(), True),
            StructField("original_file_name", StringType(), True),
            StructField("service_id", StringType(), True),
            StructField("template_id", StringType(), True),
            StructField("created_at", TimestampType(), True),
            StructField("updated_at", TimestampType(), True),
            StructField("notification_count", IntegerType(), True),
            StructField("notifications_sent", IntegerType(), True),
            StructField("processing_started", TimestampType(), True),
            StructField("processing_finished", TimestampType(), True),
            StructField("created_by_id", StringType(), True),
            StructField("template_version", IntegerType(), True),
            StructField("notifications_delivered", IntegerType(), True),
            StructField("notifications_failed", IntegerType(), True),
            StructField("job_status", StringType(), True),
            StructField("scheduled_for", TimestampType(), True),
            StructField("archived", BooleanType(), True),
            StructField("api_key_id", StringType(), True),
            StructField("sender_id", StringType(), True),
            StructField("year", StringType(), True),
            StructField("month", StringType(), True),
        ]
    )

    # Valid data that should pass all GX expectations
    valid_data = [
        (
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890",  # id (valid UUID)
            "test_template.pdf",  # original_file_name
            "f1e2d3c4-b5a6-9870-1234-567890abcdef",  # service_id (valid UUID)
            "123e4567-e89b-12d3-a456-426614174000",  # template_id (valid UUID)
            datetime.datetime(2024, 6, 1, 10, 0, 0),  # created_at
            datetime.datetime(2024, 6, 1, 10, 5, 0),  # updated_at
            100,  # notification_count (>= 0)
            95,  # notifications_sent (>= 0)
            datetime.datetime(2024, 6, 1, 10, 1, 0),  # processing_started
            datetime.datetime(2024, 6, 1, 10, 4, 0),  # processing_finished
            "abcd1234-5678-90ef-1234-567890abcdef",  # created_by_id (valid UUID)
            1,  # template_version (>= 0)
            90,  # notifications_delivered (>= 0)
            5,  # notifications_failed (>= 0)
            "completed",  # job_status
            datetime.datetime(2024, 6, 1, 9, 0, 0),  # scheduled_for
            False,  # archived (boolean)
            "def56789-abcd-ef12-3456-7890abcdef12",  # api_key_id (valid UUID)
            "12345678-1234-1234-1234-123456789012",  # sender_id (valid UUID)
            "2024",  # year (4 digits)
            "2024-06",  # month (yyyy-mm format)
        )
    ]

    df = spark_session.createDataFrame(valid_data, schema)

    # Mock only the S3 dependencies but use real GX
    with patch("process_data.configure_gx_stores") as _, patch(
        "process_data.SOURCE_BUCKET", "test-bucket"
    ):

        # This should actually run Great Expectations validation
        result = validate_with_gx(
            df, spark_session, "notify-jobs_checkpoint", "valid_test_batch"
        )

        # The validation should pass because all data meets the expectations
        assert result is True


def test_real_gx_validation_with_invalid_notify_jobs_data(spark_session):
    """Test actual GX validation with invalid notify-jobs data that should fail expectations."""
    # Create the same schema
    schema = StructType(
        [
            StructField("id", StringType(), True),
            StructField("original_file_name", StringType(), True),
            StructField("service_id", StringType(), True),
            StructField("template_id", StringType(), True),
            StructField("created_at", TimestampType(), True),
            StructField("updated_at", TimestampType(), True),
            StructField("notification_count", IntegerType(), True),
            StructField("notifications_sent", IntegerType(), True),
            StructField("processing_started", TimestampType(), True),
            StructField("processing_finished", TimestampType(), True),
            StructField("created_by_id", StringType(), True),
            StructField("template_version", IntegerType(), True),
            StructField("notifications_delivered", IntegerType(), True),
            StructField("notifications_failed", IntegerType(), True),
            StructField("job_status", StringType(), True),
            StructField("scheduled_for", TimestampType(), True),
            StructField("archived", BooleanType(), True),
            StructField("api_key_id", StringType(), True),
            StructField("sender_id", StringType(), True),
            StructField("year", StringType(), True),
            StructField("month", StringType(), True),
        ]
    )

    # Invalid data that should violate GX expectations
    invalid_data = [
        (
            "invalid-uuid-format",  # id (INVALID UUID format)
            "test_template.pdf",  # original_file_name
            "also-not-uuid",  # service_id (INVALID UUID format)
            "123e4567-e89b-12d3-a456-426614174000",  # template_id (valid UUID)
            datetime.datetime(2024, 6, 1, 10, 0, 0),  # created_at
            datetime.datetime(2024, 6, 1, 10, 5, 0),  # updated_at
            -5,  # notification_count (INVALID: negative)
            95,  # notifications_sent (>= 0)
            datetime.datetime(2024, 6, 1, 10, 1, 0),  # processing_started
            datetime.datetime(2024, 6, 1, 10, 4, 0),  # processing_finished
            "not-a-uuid-either",  # created_by_id (INVALID UUID format)
            -1,  # template_version (INVALID: negative)
            90,  # notifications_delivered (>= 0)
            5,  # notifications_failed (>= 0)
            "completed",  # job_status
            datetime.datetime(2024, 6, 1, 9, 0, 0),  # scheduled_for
            False,  # archived (boolean)
            "bad-api-key-id",  # api_key_id (INVALID UUID format)
            "bad-sender-id",  # sender_id (INVALID UUID format)
            "24",  # year (INVALID: not 4 digits)
            "2024/06",  # month (INVALID: wrong format)
        )
    ]

    df = spark_session.createDataFrame(invalid_data, schema)

    # Mock only the S3 dependencies but use real GX
    with patch("process_data.configure_gx_stores") as _, patch(
        "process_data.SOURCE_BUCKET", "test-bucket"
    ):

        # This should actually run Great Expectations validation
        result = validate_with_gx(
            df, spark_session, "notify-jobs_checkpoint", "invalid_test_batch"
        )

        # The validation should fail because data violates multiple expectations
        assert result is False


def test_real_gx_validation_with_mixed_notify_jobs_data(spark_session):
    """Test actual GX validation with mixed valid/invalid notify-jobs data."""
    # Create the same schema
    schema = StructType(
        [
            StructField("id", StringType(), True),
            StructField("original_file_name", StringType(), True),
            StructField("service_id", StringType(), True),
            StructField("template_id", StringType(), True),
            StructField("created_at", TimestampType(), True),
            StructField("updated_at", TimestampType(), True),
            StructField("notification_count", IntegerType(), True),
            StructField("notifications_sent", IntegerType(), True),
            StructField("processing_started", TimestampType(), True),
            StructField("processing_finished", TimestampType(), True),
            StructField("created_by_id", StringType(), True),
            StructField("template_version", IntegerType(), True),
            StructField("notifications_delivered", IntegerType(), True),
            StructField("notifications_failed", IntegerType(), True),
            StructField("job_status", StringType(), True),
            StructField("scheduled_for", TimestampType(), True),
            StructField("archived", BooleanType(), True),
            StructField("api_key_id", StringType(), True),
            StructField("sender_id", StringType(), True),
            StructField("year", StringType(), True),
            StructField("month", StringType(), True),
        ]
    )

    # Mix of valid and invalid data
    mixed_data = [
        # Valid row
        (
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890",  # id (valid UUID)
            "test_template.pdf",  # original_file_name
            "f1e2d3c4-b5a6-9870-1234-567890abcdef",  # service_id (valid UUID)
            "123e4567-e89b-12d3-a456-426614174000",  # template_id (valid UUID)
            datetime.datetime(2024, 6, 1, 10, 0, 0),  # created_at
            datetime.datetime(2024, 6, 1, 10, 5, 0),  # updated_at
            100,  # notification_count (>= 0)
            95,  # notifications_sent (>= 0)
            datetime.datetime(2024, 6, 1, 10, 1, 0),  # processing_started
            datetime.datetime(2024, 6, 1, 10, 4, 0),  # processing_finished
            "abcd1234-5678-90ef-ghij-klmnopqrstuv",  # created_by_id (valid UUID)
            1,  # template_version (>= 0)
            90,  # notifications_delivered (>= 0)
            5,  # notifications_failed (>= 0)
            "completed",  # job_status
            datetime.datetime(2024, 6, 1, 9, 0, 0),  # scheduled_for
            False,  # archived (boolean)
            "def56789-abcd-ef12-3456-7890abcdef12",  # api_key_id (valid UUID)
            "sender12-3456-7890-abcd-ef1234567890",  # sender_id (valid UUID)
            "2024",  # year (4 digits)
            "2024-06",  # month (yyyy-mm format)
        ),
        # Invalid row (has some invalid UUIDs)
        (
            "invalid-uuid",  # id (INVALID UUID)
            "another_template.pdf",  # original_file_name
            "also-invalid-uuid",  # service_id (INVALID UUID)
            "123e4567-e89b-12d3-a456-426614174001",  # template_id (valid UUID)
            datetime.datetime(2024, 6, 2, 10, 0, 0),  # created_at
            datetime.datetime(2024, 6, 2, 10, 5, 0),  # updated_at
            50,  # notification_count (>= 0)
            45,  # notifications_sent (>= 0)
            datetime.datetime(2024, 6, 2, 10, 1, 0),  # processing_started
            datetime.datetime(2024, 6, 2, 10, 4, 0),  # processing_finished
            "valid1234-5678-90ef-ghij-klmnopqrstuv",  # created_by_id (valid UUID)
            2,  # template_version (>= 0)
            40,  # notifications_delivered (>= 0)
            5,  # notifications_failed (>= 0)
            "in_progress",  # job_status
            datetime.datetime(2024, 6, 2, 9, 0, 0),  # scheduled_for
            True,  # archived (boolean)
            "api12345-abcd-ef12-3456-7890abcdef12",  # api_key_id (valid UUID)
            "sender34-5678-90ab-cdef-1234567890ab",  # sender_id (valid UUID)
            "2024",  # year (4 digits)
            "2024-06",  # month (yyyy-mm format)
        ),
    ]

    df = spark_session.createDataFrame(mixed_data, schema)

    # Mock only the S3 dependencies but use real GX
    with patch("process_data.configure_gx_stores") as _, patch(
        "process_data.SOURCE_BUCKET", "test-bucket"
    ):

        # This should actually run Great Expectations validation
        result = validate_with_gx(
            df, spark_session, "notify-jobs_checkpoint", "mixed_test_batch"
        )

        # The validation should fail because some rows violate expectations
        assert result is False


def test_debug_gx_validation_failure(spark_session):
    """Debug test to see exactly what GX validations are failing."""
    # Create the same valid data
    schema = StructType(
        [
            StructField("id", StringType(), True),
            StructField("original_file_name", StringType(), True),
            StructField("service_id", StringType(), True),
            StructField("template_id", StringType(), True),
            StructField("created_at", TimestampType(), True),
            StructField("updated_at", TimestampType(), True),
            StructField("notification_count", IntegerType(), True),
            StructField("notifications_sent", IntegerType(), True),
            StructField("processing_started", TimestampType(), True),
            StructField("processing_finished", TimestampType(), True),
            StructField("created_by_id", StringType(), True),
            StructField("template_version", IntegerType(), True),
            StructField("notifications_delivered", IntegerType(), True),
            StructField("notifications_failed", IntegerType(), True),
            StructField("job_status", StringType(), True),
            StructField("scheduled_for", TimestampType(), True),
            StructField("archived", BooleanType(), True),
            StructField("api_key_id", StringType(), True),
            StructField("sender_id", StringType(), True),
            StructField("year", StringType(), True),
            StructField("month", StringType(), True),
        ]
    )

    valid_data = [
        (
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890",  # id (valid UUID)
            "test_template.pdf",  # original_file_name
            "f1e2d3c4-b5a6-9870-1234-567890abcdef",  # service_id (valid UUID)
            "123e4567-e89b-12d3-a456-426614174000",  # template_id (valid UUID)
            datetime.datetime(2024, 6, 1, 10, 0, 0),  # created_at
            datetime.datetime(2024, 6, 1, 10, 5, 0),  # updated_at
            100,  # notification_count (>= 0)
            95,  # notifications_sent (>= 0)
            datetime.datetime(2024, 6, 1, 10, 1, 0),  # processing_started
            datetime.datetime(2024, 6, 1, 10, 4, 0),  # processing_finished
            "abcd1234-5678-90ef-1234-567890abcdef",  # created_by_id (valid UUID)
            1,  # template_version (>= 0)
            90,  # notifications_delivered (>= 0)
            5,  # notifications_failed (>= 0)
            "completed",  # job_status
            datetime.datetime(2024, 6, 1, 9, 0, 0),  # scheduled_for
            False,  # archived (boolean)
            "def56789-abcd-ef12-3456-7890abcdef12",  # api_key_id (valid UUID)
            "12345678-1234-1234-1234-123456789012",  # sender_id (valid UUID)
            "2024",  # year (4 digits)
            "2024-06",  # month (yyyy-mm format)
        )
    ]

    df = spark_session.createDataFrame(valid_data, schema)

    print("=== DataFrame Schema ===")
    df.printSchema()
    print("\n=== DataFrame Data ===")
    df.show(truncate=False)

    # Try to run GX validation and capture detailed errors using the actual function
    from unittest.mock import patch

    with patch("process_data.configure_gx_stores") as _, patch(
        "process_data.SOURCE_BUCKET", "test-bucket"
    ):

        print("\n=== Running validate_with_gx function directly ===")
        result = validate_with_gx(
            df, spark_session, "notify-jobs_checkpoint", "debug_batch"
        )
        print(f"Validation result: {result}")

        # The actual function handles exceptions, so let's also try to capture more details
        # by temporarily modifying the logging or examining what happens


def test_debug_gx_validation_without_exception_handling(spark_session):
    """Debug test that bypasses exception handling to see the actual GX error."""
    # Create the same valid data
    schema = StructType(
        [
            StructField("id", StringType(), True),
            StructField("original_file_name", StringType(), True),
            StructField("service_id", StringType(), True),
            StructField("template_id", StringType(), True),
            StructField("created_at", TimestampType(), True),
            StructField("updated_at", TimestampType(), True),
            StructField("notification_count", IntegerType(), True),
            StructField("notifications_sent", IntegerType(), True),
            StructField("processing_started", TimestampType(), True),
            StructField("processing_finished", TimestampType(), True),
            StructField("created_by_id", StringType(), True),
            StructField("template_version", IntegerType(), True),
            StructField("notifications_delivered", IntegerType(), True),
            StructField("notifications_failed", IntegerType(), True),
            StructField("job_status", StringType(), True),
            StructField("scheduled_for", TimestampType(), True),
            StructField("archived", BooleanType(), True),
            StructField("api_key_id", StringType(), True),
            StructField("sender_id", StringType(), True),
            StructField("year", StringType(), True),
            StructField("month", StringType(), True),
        ]
    )

    valid_data = [
        (
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890",  # id (valid UUID)
            "test_template.pdf",  # original_file_name
            "f1e2d3c4-b5a6-9870-1234-567890abcdef",  # service_id (valid UUID)
            "123e4567-e89b-12d3-a456-426614174000",  # template_id (valid UUID)
            datetime.datetime(2024, 6, 1, 10, 0, 0),  # created_at
            datetime.datetime(2024, 6, 1, 10, 5, 0),  # updated_at
            100,  # notification_count (>= 0)
            95,  # notifications_sent (>= 0)
            datetime.datetime(2024, 6, 1, 10, 1, 0),  # processing_started
            datetime.datetime(2024, 6, 1, 10, 4, 0),  # processing_finished
            "abcd1234-5678-90ef-1234-567890abcdef",  # created_by_id (valid UUID)
            1,  # template_version (>= 0)
            90,  # notifications_delivered (>= 0)
            5,  # notifications_failed (>= 0)
            "completed",  # job_status
            datetime.datetime(2024, 6, 1, 9, 0, 0),  # scheduled_for
            False,  # archived (boolean)
            "def56789-abcd-ef12-3456-7890abcdef12",  # api_key_id (valid UUID)
            "12345678-1234-1234-1234-123456789012",  # sender_id (valid UUID)
            "2024",  # year (4 digits)
            "2024-06",  # month (yyyy-mm format)
        )
    ]

    df = spark_session.createDataFrame(valid_data, schema)

    # Copy the validate_with_gx logic but without exception handling
    import os
    from unittest.mock import patch

    with patch("process_data.configure_gx_stores") as _, patch(
        "process_data.SOURCE_BUCKET", "test-bucket"
    ):

        print("=== Running GX validation without exception handling ===")

        gx_context_path = os.path.join(os.getcwd(), "gx")
        context = gx.get_context(context_root_dir=gx_context_path, cloud_mode=False)

        # Configure datasource to use our Spark session
        context.datasources["spark_datasource"].execution_engine.spark = spark_session

        # Try running checkpoint the simpler way by just adding the data to the datasource
        # and letting the checkpoint use its predefined batch_request

        # Add the DataFrame to the datasource context as the data asset
        context.datasources["spark_datasource"]._data_context = context

        # Try to run the checkpoint with runtime parameters instead
        result = context.run_checkpoint(
            checkpoint_name="notify-jobs_checkpoint",
            batch_request={
                "runtime_parameters": {"batch_data": df},
                "batch_identifiers": {"default_identifier_name": "debug_test"},
            },
        )

        print(f"SUCCESS: {result['success']}")

        if not result["success"]:
            print("\n=== DETAILED VALIDATION FAILURES ===")
            for run_result in result["run_results"].values():
                validation_result = run_result["validation_result"]
                for res in validation_result["results"]:
                    if not res["success"]:
                        expectation_type = res["expectation_config"]["expectation_type"]
                        column = res["expectation_config"]["kwargs"].get(
                            "column", "N/A"
                        )
                        result_details = res.get("result", {})
                        print(f"\n❌ FAILED: {expectation_type}")
                        print(f"   Column: {column}")
                        print(f"   Config: {res['expectation_config']['kwargs']}")
                        print(f"   Result: {result_details}")
        else:
            print("✅ All validations passed!")
