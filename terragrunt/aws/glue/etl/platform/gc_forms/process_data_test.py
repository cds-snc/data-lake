import pytest

from unittest.mock import patch

import pandas as pd

from awswrangler.exceptions import NoFilesFound

# flake8: noqa: E402
from process_data import (
    validate_schema,
    is_type_compatible,
    get_new_data,
    process_data,
    SOURCE_BUCKET,
    SOURCE_PREFIX,
)


# Sample test data fixtures
@pytest.fixture
def sample_data_df():
    return pd.DataFrame(
        {
            "id": ["1", "2", "3"],
            "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "created_at": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "updated_at": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "text_field": ["Test 1", "Test 2", "Test 3"],
            "status": ["open", "pending", "closed"],
            "priority": [1, 2, 3],
        }
    )


@pytest.fixture
def glue_table_schema():
    return pd.DataFrame(
        {
            "Column Name": [
                "id",
                "date",
                "timestamp",
                "created_at",
                "updated_at",
                "text_field",
                "status",
                "priority",
            ],
            "Type": [
                "string",
                "timestamp",
                "timestamp",
                "timestamp",
                "timestamp",
                "string",
                "string",
                "int",
            ],
        }
    )


def test_validate_schema_valid(sample_data_df, glue_table_schema):
    assert validate_schema(sample_data_df, None, glue_table_schema) is True


def test_validate_schema_missing_column(sample_data_df, glue_table_schema):
    df_missing_column = sample_data_df.drop("status", axis=1)
    assert validate_schema(df_missing_column, None, glue_table_schema) is False


def test_validate_schema_partition_column(sample_data_df, glue_table_schema):
    df_with_parition_column = sample_data_df.copy()
    df_with_parition_column["month"] = pd.to_datetime(
        ["2024-01-01", "2024-01-02", "2024-01-03"]
    )
    assert (
        validate_schema(df_with_parition_column, ["month"], glue_table_schema) is True
    )


def test_validate_schema_wrong_type(sample_data_df, glue_table_schema):
    df_wrong_type = sample_data_df.copy()
    df_wrong_type["priority"] = pd.to_datetime(
        ["2024-01-04", "2024-01-05", "2024-01-06"]
    )
    assert validate_schema(df_wrong_type, None, glue_table_schema) is False


def test_is_type_compatible():
    assert is_type_compatible(pd.Series(["a", "b", "c"]), "string") is True
    assert is_type_compatible(pd.Series([1, 2, 3]), "int") is True
    assert is_type_compatible(pd.Series([1.1, 2.2, 3.3]), "double") is True
    assert is_type_compatible(pd.Series([True, False]), "boolean") is True
    assert (
        is_type_compatible(pd.Series(pd.to_datetime(["2024-01-01"])), "timestamp")
        is True
    )
    assert is_type_compatible(pd.Series(["a", "b", "c"]), "int") is False
    assert is_type_compatible(pd.Series(["a", "b", "c"]), "unknown_type") is False


@patch("awswrangler.s3")
def test_get_new_data(mock_wr_s3, sample_data_df):
    # Mock AWS Wrangler response
    mock_wr_s3.read_parquet.return_value = sample_data_df

    result = get_new_data(
        path="test-path",
        date_columns=["date", "timestamp", "created_at"],
        sort_columns=["id"],
        partition_created_column="created_at",
    )

    # Verify S3 path was constructed correctly
    mock_wr_s3.read_parquet.assert_called_with(
        path=f"s3://{SOURCE_BUCKET}/{SOURCE_PREFIX}/test-path/",
        use_threads=True,
        dataset=True,
    )

    # Verify data is processed correctly
    assert "month" in result.columns
    assert len(result) == len(sample_data_df)

    # Test date columns TZ localization
    for date_column in ["date", "timestamp", "created_at"]:
        assert result[date_column].dt.tz is None


@patch("awswrangler.s3")
def test_get_new_data_with_sorting(mock_wr_s3):
    # Create data with duplicates to test sorting and deduplication
    data_with_dupes = pd.DataFrame(
        {
            "id": ["1", "2", "1"],  # Duplicate ID 1
            "timestamp": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        }
    )
    mock_wr_s3.read_parquet.return_value = data_with_dupes

    result = get_new_data(
        path="test-path",
        date_columns=["date", "timestamp"],
        sort_columns=["id"],
        partition_created_column=None,
    )

    # Should have dropped the duplicate with older timestamp
    assert len(result) == 2
    assert result[result["id"] == "1"]["timestamp"].iloc[0] == pd.Timestamp(
        "2024-01-03"
    )


@patch("awswrangler.s3")
def test_get_new_data_no_files(mock_wr_s3):
    # Mock no files found exception
    mock_wr_s3.read_parquet.side_effect = NoFilesFound("No files found")

    result = get_new_data(
        path="test-path",
        date_columns=["date"],
        sort_columns=["id"],
        partition_created_column="date",
    )

    # Verify result is empty DataFrame
    assert isinstance(result, pd.DataFrame)
    assert result.empty


@patch("process_data.get_new_data")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
def test_process_data(
    mock_wr_s3, mock_wr_catalog, mock_get_new_data, sample_data_df, glue_table_schema
):
    mock_get_new_data.return_value = sample_data_df
    mock_wr_catalog.table.return_value = glue_table_schema

    process_data()

    # Verify a call for each dataset
    assert mock_get_new_data.call_count == 4
    assert mock_wr_s3.to_parquet.call_count == 4


@patch("process_data.get_new_data")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
def test_process_data_empty_dataset(
    mock_wr_s3, mock_wr_catalog, mock_get_new_data, glue_table_schema
):
    mock_get_new_data.return_value = pd.DataFrame()
    mock_wr_catalog.table.return_value = glue_table_schema

    process_data()

    mock_wr_s3.to_parquet.assert_not_called()


@patch("process_data.get_new_data")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
def test_process_data_validation_failure(
    mock_wr_s3, mock_wr_catalog, mock_get_new_data, sample_data_df, glue_table_schema
):
    # Mock get_new_data to return sample data
    mock_get_new_data.return_value = sample_data_df

    # Mock table schema that will cause validation to fail (missing required column)
    invalid_schema = glue_table_schema.drop(0)  # Remove the first column from schema
    mock_wr_catalog.table.return_value = invalid_schema

    # Run the process, expect a ValueError due to schema validation failure
    with pytest.raises(ValueError):
        process_data()

    # Verify to_parquet was not called
    mock_wr_s3.to_parquet.assert_not_called()
