import pytest
import os
import json
import pandas as pd

from unittest.mock import Mock, patch, mock_open, ANY

# Set environment variables for testing
os.environ["SOURCE_LOCAL_PATH"] = "/tmp/test_source"
os.environ["TRANSFORMED_S3_PATH"] = "s3://test-transformed-bucket/test-prefix"
os.environ["GLUE_TABLE_NAME_PREFIX"] = "test_prefix"
os.environ["GLUE_DATABASE_NAME_TRANSFORMED"] = "test_database"

# Import the module after setting environment variables
# flake8: noqa: E402
from initial_load import (
    validate_schema,
    postgres_to_pandas_type,
    is_type_compatible,
    parse_dates,
    load_data,
    get_dataset_config,
    initial_load,
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
        "initial_load.is_type_compatible",
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
    assert isinstance(postgres_to_pandas_type("boolean"), pd.BooleanDtype)
    assert postgres_to_pandas_type("timestamp") == "datetime64[ns]"
    assert isinstance(postgres_to_pandas_type("notification_type"), pd.StringDtype)


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


@patch("initial_load.glob.glob")
@patch("initial_load.pq.ParquetFile")
@patch("initial_load.validate_schema")
@patch("initial_load.wr.s3.to_parquet")
@patch("pyarrow.Table")
def test_load_data(
    mock_pa_table,
    mock_to_parquet,
    mock_validate_schema,
    mock_parquet_file,
    mock_glob,
    sample_dataframe,
    sample_fields,
):
    """Test the load_data function."""
    mock_glob.return_value = ["/tmp/test_source/public.test_table/data.parquet"]
    mock_batch = Mock()
    mock_table = Mock()
    mock_table.to_pandas.return_value = sample_dataframe
    mock_batch_iter = Mock(return_value=[mock_batch])
    mock_parquet_file.return_value.iter_batches = mock_batch_iter
    mock_validate_schema.return_value = True

    mock_pa_table.from_batches.return_value = mock_table

    result = load_data(
        "test_table",
        "/tmp/test_source/public.test_table",
        sample_fields,
        "created_at",
        ["year", "month", "day"],
    )

    assert result == len(sample_dataframe)
    mock_validate_schema.assert_called_once()
    mock_to_parquet.assert_called_once()

    args, kwargs = mock_to_parquet.call_args
    assert "partition_cols" in kwargs
    assert kwargs["partition_cols"] == ["year", "month", "day"]


@patch("initial_load.glob.glob")
@patch("initial_load.pq")
@patch("initial_load.pa")
def test_load_data_validation_failure(
    mock_pa, mock_pq, mock_glob, sample_dataframe, sample_fields
):
    """Test load_data when schema validation fails."""
    mock_glob.return_value = ["/tmp/test_source/public.test_table/data.parquet"]
    mock_table = Mock()
    mock_table.to_pandas.return_value = sample_dataframe
    mock_pa.Table.from_batches.return_value = mock_table

    mock_batch = Mock()
    mock_batch_iter = Mock(return_value=[mock_batch])
    mock_parquet_file = Mock()
    mock_parquet_file.iter_batches = mock_batch_iter
    mock_pq.ParquetFile.return_value = mock_parquet_file

    with patch("initial_load.validate_schema", return_value=False):
        with pytest.raises(ValueError, match="Schema validation failed"):
            load_data("test_table", "/tmp/test_source/public.test_table", sample_fields)


@patch("builtins.open", new_callable=mock_open)
@patch("os.getcwd")
@patch("os.listdir")
def test_get_dataset_config(
    mock_listdir, mock_getcwd, mock_file, sample_dataset_config
):
    """Test loading dataset configurations."""
    mock_getcwd.return_value = (
        "/workspaces/data-lake/terragrunt/aws/glue/etl/platform/gc_notify"
    )
    mock_listdir.return_value = ["notifications.json", "templates.json"]
    mock_file.return_value.__enter__.return_value.read.side_effect = [
        json.dumps(sample_dataset_config[0]),
        json.dumps(sample_dataset_config[1]),
    ]

    result = get_dataset_config()

    # Assert results
    assert len(result) == 2
    assert result[0]["table_name"] == "notifications"
    assert result[1]["table_name"] == "templates"

    mock_file.assert_any_call(
        "/workspaces/data-lake/terragrunt/aws/glue/etl/platform/gc_notify/tables/notifications.json",
        "r",
    )
    mock_file.assert_any_call(
        "/workspaces/data-lake/terragrunt/aws/glue/etl/platform/gc_notify/tables/templates.json",
        "r",
    )


@patch("os.listdir")
@patch("os.getcwd")
def test_get_dataset_config_no_files(mock_getcwd, mock_listdir):
    """Test get_dataset_config when no config files are found."""
    mock_getcwd.return_value = (
        "/workspaces/data-lake/terragrunt/aws/glue/etl/platform/gc_notify"
    )
    mock_listdir.return_value = []

    with pytest.raises(ValueError, match="No dataset configurations found"):
        get_dataset_config()


@patch("os.listdir")
@patch("os.getcwd")
def test_get_dataset_config_dir_not_found(mock_getcwd, mock_listdir):
    """Test get_dataset_config when tables directory is not found."""
    mock_getcwd.return_value = (
        "/workspaces/data-lake/terragrunt/aws/glue/etl/platform/gc_notify"
    )
    mock_listdir.side_effect = FileNotFoundError

    with pytest.raises(ValueError, match="Tables directory not found"):
        get_dataset_config()


@patch("initial_load.get_dataset_config")
@patch("initial_load.load_data")
@patch("initial_load.time.time")
def test_initial_load(
    mock_time, mock_load_data, mock_get_dataset_config, sample_dataset_config
):
    """Test the main initial_load function."""
    mock_get_dataset_config.return_value = sample_dataset_config
    mock_load_data.side_effect = [100, 200]
    # Use return_value instead of side_effect to avoid StopIteration issues
    mock_time.return_value = 1000.0

    initial_load()

    assert mock_load_data.call_count == 2

    mock_load_data.assert_any_call(
        "notifications",
        f"{os.environ['SOURCE_LOCAL_PATH']}/public.notifications",
        sample_dataset_config[0]["fields"],
        sample_dataset_config[0]["partition_timestamp"],
        sample_dataset_config[0]["partition_cols"],
    )

    mock_load_data.assert_any_call(
        "templates",
        f"{os.environ['SOURCE_LOCAL_PATH']}/public.templates",
        sample_dataset_config[1]["fields"],
        sample_dataset_config[1]["partition_timestamp"],
        sample_dataset_config[1]["partition_cols"],
    )
