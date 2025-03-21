import pytest
import sys

from datetime import datetime, UTC
from unittest.mock import Mock, patch

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
}

# Mock the AWS Glue and PySpark modules
mock_glue_utils = Mock()
mock_glue_utils.getResolvedOptions.return_value = mock_args
sys.modules["awsglue.utils"] = mock_glue_utils

# flake8: noqa: E402
from process_tickets import (
    validate_schema,
    is_type_compatible,
    merge_tickets,
    process_tickets,
    get_days_tickets,
)


# Sample test data fixtures
@pytest.fixture
def sample_tickets_df():
    return pd.DataFrame(
        {
            "id": ["1", "2", "3"],
            "subject": ["Test 1", "Test 2", "Test 3"],
            "created_at": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "updated_at": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "due_by": pd.to_datetime(["2024-01-05", "2024-01-06", "2024-01-07"]),
            "fr_due_by": pd.to_datetime(["2024-01-04", "2024-01-05", "2024-01-06"]),
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
                "subject",
                "created_at",
                "updated_at",
                "due_by",
                "fr_due_by",
                "status",
                "priority",
            ],
            "Type": [
                "string",
                "string",
                "timestamp",
                "timestamp",
                "timestamp",
                "timestamp",
                "string",
                "int",
            ],
        }
    )


def test_validate_schema_valid(sample_tickets_df, glue_table_schema):
    assert validate_schema(sample_tickets_df, glue_table_schema) is True


def test_validate_schema_missing_column(sample_tickets_df, glue_table_schema):
    df_missing_column = sample_tickets_df.drop("status", axis=1)
    assert validate_schema(df_missing_column, glue_table_schema) is False


def test_validate_schema_wrong_type(sample_tickets_df, glue_table_schema):
    df_wrong_type = sample_tickets_df.copy()
    df_wrong_type["priority"] = pd.to_datetime(
        ["2024-01-04", "2024-01-05", "2024-01-06"]
    )
    assert validate_schema(df_wrong_type, glue_table_schema) is False


def test_is_type_compatible():
    assert is_type_compatible(pd.Series(["a", "b", "c"]), "string") is True
    assert is_type_compatible(pd.Series([1, 2, 3]), "int") is True
    assert is_type_compatible(pd.Series([1.1, 2.2, 3.3]), "double") is True
    assert is_type_compatible(pd.Series([True, False]), "boolean") is True
    assert is_type_compatible(pd.Series(["a", "b", "c"]), "int") is False
    assert is_type_compatible(pd.Series(["a", "b", "c"]), "foobar") is False


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
@patch("awswrangler.s3")
@patch("awswrangler.catalog")
def test_process_tickets(
    mock_wr_catalog, mock_wr_s3, sample_tickets_df, glue_table_schema
):
    # Mock AWS Wrangler responses
    mock_wr_s3.read_json.return_value = sample_tickets_df
    mock_wr_catalog.table.return_value = glue_table_schema
    mock_wr_s3.read_parquet.return_value = sample_tickets_df

    # Run the process
    process_tickets()

    # Verify the write operation was called
    mock_wr_s3.to_parquet.assert_called_once()


# Test error handling
@patch("awswrangler.s3")
@patch("awswrangler.catalog")
def test_process_tickets_no_new_data(mock_wr_catalog, mock_wr_s3, glue_table_schema):
    # Mock empty response from S3
    mock_wr_s3.read_json.side_effect = NoFilesFound("Simulate no file for read_json")
    mock_wr_catalog.table.return_value = glue_table_schema

    # Run the process
    process_tickets()

    # Verify no write operation was attempted
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
