import pytest
import sys

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pandas as pd
import numpy as np
import os

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
    "table_name_prefix": "test_table",
    "gx_config_object": "s3://test-config-bucket/test-config-key",
}

# Mock the AWS Glue and PySpark modules
mock_glue_utils = Mock()
mock_glue_utils.getResolvedOptions.return_value = mock_args
sys.modules["awsglue.utils"] = mock_glue_utils

# flake8: noqa: E402
from process_data import (
    get_new_data,
    process_data,
    validate_with_gx,
    SOURCE_BUCKET,
    SOURCE_PREFIX,
)


@pytest.fixture
def datasets_params():
    datasets_params = {
        "path": "processed-data/template",
        "date_columns": [
            "ttl",
            "api_created_at",
            "timestamp",
            "closingdate",
            "created_at",
            "updated_at",
        ],
        "field_count_columns": [
            "checkbox_count",
            "combobox_count",
            "dropdown_count",
            "dynamicrow_count",
            "fileinput_count",
            "formatteddate_count",
            "radio_count",
            "richtext_count",
            "textarea_count",
            "textfield_count",
            "addresscomplete_count",
        ],
        "partition_timestamp": "timestamp",
        "partition_columns": ["year", "month"],
        "email_columns": ["deliveryemaildestination"],
        "gx_checkpoint": "forms-template_checkpoint",
    }
    return datasets_params


# Sample test data fixtures
@pytest.fixture
def sample_data_df():
    return pd.DataFrame(
        {
            "id": [
                "aaaa1bbbb03f8ymf83jd75nd3",
                "aaaa1bbbb03f8ymf83jd75nd4",
                "aaaa1bbbb03f8ymf83jd75nd5",
            ],
            "ttl": [pd.Timestamp("2025-03-30 19:47:26.804000"), pd.NaT, pd.NaT],
            "ispublished": [True, False, False],
            "created_at": [
                pd.Timestamp("2023-08-30 17:54:56"),
                pd.Timestamp("2024-01-30 15:31:12"),
                pd.Timestamp("2024-06-05 18:49:43"),
            ],
            "updated_at": [
                pd.Timestamp("2023-10-25 15:38:24"),
                pd.Timestamp("2024-01-30 15:31:12"),
                pd.Timestamp("2024-06-05 18:52:17"),
            ],
            "name": [
                "Questionnaire à l’intention des ministères et organismes fédéraux",
                "",
                "Test Form",
            ],
            "securityattribute": ["Protected A", "Protected A", "Protected A"],
            "closingdate": [pd.NaT, pd.NaT, pd.NaT],
            "formpurpose": ["TEST", "", ""],
            "publishdesc": ["TEST", "", ""],
            "publishformtype": ["TEST", "", ""],
            "publishreason": ["TEST", "", ""],
            "closeddetails": ["TEST", "", ""],
            "saveandresume": [False, False, False],
            "deliveryemaildestination": ["foo.bar@bar.com", "barbaz@baz.com", None],
            "api_created_at": [
                pd.NaT,
                pd.NaT,
                pd.NaT,
            ],
            "api_id": ["TEST", "", ""],
            "deliveryoption": [0, 0, 0],
            "timestamp": [
                pd.Timestamp("2025-01-01 00:01:58"),
                pd.Timestamp("2025-01-01 00:01:55"),
                pd.Timestamp("2025-01-02 00:01:47"),
            ],
            "titleen": [
                "Request for Information \nfor Language Training Services",
                "National Security Tip Intake",
                "Test Form",
            ],
            "titlefr": [
                "Federal Government Department and Agency Questionnaire",
                "",
                "",
            ],
            "brand": [
                "Demande de renseignements \nsur les services de formation linguistique.",
                "",
                "",
            ],
            "checkbox_count": [63, 0, 0],
            "combobox_count": [0, 0, 0],
            "dropdown_count": [0, 0, 0],
            "dynamicrow_count": [0, 0, 0],
            "fileinput_count": [0, 0, 0],
            "formatteddate_count": [0, 0, 0],
            "radio_count": [1, 1, 2],
            "richtext_count": [1, 0, 1],
            "textarea_count": [61, 0, 0],
            "textfield_count": [4, 0, 2],
            "addresscomplete_count": [0, 0, 0],
            "notificationsinterval": [None, None, 0],
            "year": ["2023", "2024", "2024"],
            "month": ["2023-08", "2024-01", "2024-06"],
        }
    )


def test_validate_schema_valid(sample_data_df, datasets_params):
    assert validate_with_gx(sample_data_df, datasets_params["gx_checkpoint"]) is True


def test_validate_schema_missing_column(sample_data_df, datasets_params):
    df_missing_column = sample_data_df.drop("ispublished", axis=1)
    assert (
        validate_with_gx(df_missing_column, datasets_params["gx_checkpoint"]) is False
    )


def test_validate_schema_extra_column(sample_data_df, datasets_params):
    df_added_column = sample_data_df.copy()
    df_added_column["stuff"] = True
    assert validate_with_gx(df_added_column, datasets_params["gx_checkpoint"]) is True


def test_validate_schema_wrong_type(sample_data_df, datasets_params):
    df_wrong_type = sample_data_df.copy()
    df_wrong_type["ispublished"] = pd.to_datetime(
        ["2024-01-04", "2024-01-05", "2024-01-06"]
    )
    assert validate_with_gx(df_wrong_type, datasets_params["gx_checkpoint"]) is False


@patch("pandas.Timestamp")
@patch("awswrangler.s3")
def test_get_new_data(mock_wr_s3, mock_timestamp, sample_data_df):

    fixed_date = datetime(1970, 1, 2)
    fixed_date_yesterday = datetime(1970, 1, 1)
    mock_timestamp.today.return_value = fixed_date

    # This data has timestamp of jan 1st
    mock_wr_s3.read_parquet.return_value = sample_data_df

    result = get_new_data(
        path="test-path",
        date_columns=["ttl", "timestamp", "created_at"],
        drop_columns=["ispublished"],
        field_count_columns=["checkbox_count", "muffin_count"],
        email_columns=["deliveryemaildestination"],
        partition_columns=["year", "month"],
        partition_timestamp="timestamp",
    )

    # Verify S3 path was constructed correctly
    mock_wr_s3.read_parquet.assert_called_with(
        path=f"s3://{SOURCE_BUCKET}/{SOURCE_PREFIX}/test-path/",
        use_threads=True,
        dataset=True,
        last_modified_begin=fixed_date_yesterday,
    )

    # Verify data is processed correctly
    assert "month" in result.columns
    assert "year" in result.columns
    assert "ispublished" not in result.columns

    # One row is dropped because its dated after the job run date
    assert len(result) == len(sample_data_df)

    # Verify email columns are processed correctly
    assert (
        result["deliveryemaildestination"].values == ["bar.com", "baz.com", None]
    ).all()

    # Verify field count columns are processed correctly
    assert (result["checkbox_count"].values == [63, 0, 0]).all()
    assert (result["muffin_count"].values == [0, 0, 0]).all()

    # Test date columns TZ localization
    for date_column in ["ttl", "timestamp", "created_at"]:
        assert result[date_column].dt.tz is None


@patch("pandas.Timestamp")
@patch("awswrangler.s3")
def test_get_new_data_historical(mock_wr_s3, mock_timestamp, sample_data_df):

    fixed_date = datetime(1970, 1, 2)
    fixed_date_yesterday = datetime(1970, 1, 1)
    mock_timestamp.today.return_value = fixed_date

    mock_wr_s3.read_parquet.return_value = sample_data_df

    result = get_new_data(
        path="test-path",
        date_columns=["ttl", "timestamp", "created_at"],
        drop_columns=["ispublished"],
        field_count_columns=["checkbox_count", "muffin_count"],
        email_columns=["deliveryemaildestination"],
        partition_columns=["year", "month"],
        partition_timestamp="timestamp",
    )

    # Verify S3 path was constructed correctly
    mock_wr_s3.read_parquet.assert_called_with(
        path=f"s3://{SOURCE_BUCKET}/{SOURCE_PREFIX}/test-path/",
        use_threads=True,
        dataset=True,
        last_modified_begin=fixed_date_yesterday,
    )

    # Verify data is processed correctly
    assert "month" in result.columns
    assert "year" in result.columns
    assert "ispublished" not in result.columns

    assert len(result) == len(sample_data_df)

    # Verify email columns are processed correctly
    assert (
        result["deliveryemaildestination"].values == ["bar.com", "baz.com", None]
    ).all()

    # Verify field count columns are processed correctly
    assert (result["checkbox_count"].values == [63, 0, 0]).all()
    assert (result["muffin_count"].values == [0, 0, 0]).all()

    # Test date columns TZ localization
    for date_column in ["ttl", "timestamp", "created_at"]:
        assert result[date_column].dt.tz is None


@patch("awswrangler.s3")
def test_get_new_data_no_files(mock_wr_s3):
    # Mock no files found exception
    mock_wr_s3.read_parquet.side_effect = NoFilesFound("No files found")

    result = get_new_data(
        path="test-path",
        date_columns=["timestamp"],
        drop_columns=None,
        field_count_columns=None,
        email_columns=None,
        partition_columns=None,
        partition_timestamp=None,
    )

    # Verify result is empty DataFrame
    assert isinstance(result, pd.DataFrame)
    assert result.empty


@patch("process_data.download_s3_object")
@patch("process_data.validate_with_gx", return_value=True)
@patch("process_data.get_new_data")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
@patch("boto3.client")
def test_process_data(
    mock_boto3_client,
    mock_wr_s3,
    mock_wr_catalog,
    mock_get_new_data,
    mock_validate_with_gx,
    mock_s3,
    sample_data_df,
    datasets_params,
):
    mock_cloudwatch = Mock()
    mock_s3_client = Mock()
    mock_boto3_client.side_effect = lambda service_name: (
        mock_cloudwatch if service_name == "cloudwatch" else mock_s3_client
    )
    mock_get_new_data.return_value = sample_data_df

    process_data()

    # Verify a call for each dataset
    assert mock_get_new_data.call_count == 6
    assert mock_wr_s3.to_parquet.call_count == 6


@patch("process_data.download_s3_object")
@patch("process_data.get_new_data")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
@patch("boto3.client")
def test_process_data_validation_success(
    mock_boto3_client,
    mock_wr_s3,
    mock_wr_catalog,
    mock_get_new_data,
    mock_s3,
    sample_data_df,
    datasets_params,
):
    mock_cloudwatch = Mock()
    mock_s3_client = Mock()
    mock_boto3_client.side_effect = lambda service_name, *args, **kwargs: (
        mock_cloudwatch if service_name == "cloudwatch" else mock_s3_client
    )
    mock_get_new_data.return_value = sample_data_df

    process_data(datasets_params)

    assert mock_get_new_data.call_count == 1
    assert mock_wr_s3.to_parquet.call_count == 1


@patch("process_data.download_s3_object")
@patch("process_data.get_new_data")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
@patch("boto3.client")
def test_process_data_empty_dataset(
    mock_boto3_client,
    mock_wr_s3,
    mock_wr_catalog,
    mock_get_new_data,
    mock_s3,
):
    mock_cloudwatch = Mock()
    mock_s3_client = Mock()
    mock_boto3_client.side_effect = lambda service_name, *args, **kwargs: (
        mock_cloudwatch if service_name == "cloudwatch" else mock_s3_client
    )
    mock_get_new_data.return_value = pd.DataFrame()

    process_data()

    mock_wr_s3.to_parquet.assert_not_called()


@patch("process_data.download_s3_object")
@patch("process_data.get_new_data")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
@patch("boto3.client")
def test_process_data_extra_column(
    mock_boto3_client,
    mock_wr_s3,
    mock_wr_catalog,
    mock_get_new_data,
    mock_s3,
    sample_data_df,
    datasets_params,
):

    mock_cloudwatch = Mock()

    df_added_column = sample_data_df.copy()
    df_added_column["extra_column"] = "extra_value"
    mock_get_new_data.return_value = df_added_column

    mock_s3_client = Mock()
    mock_boto3_client.side_effect = lambda service_name, *args, **kwargs: (
        mock_cloudwatch if service_name == "cloudwatch" else mock_s3_client
    )

    process_data(datasets_params)

    assert mock_get_new_data.call_count == 1
    assert mock_wr_s3.to_parquet.call_count == 1


@patch("process_data.download_s3_object")
@patch("process_data.get_new_data")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
@patch("boto3.client")
def test_process_data_validation_failure_missing_column(
    mock_boto3_client,
    mock_wr_s3,
    mock_wr_catalog,
    mock_get_new_data,
    mock_s3,
    sample_data_df,
    datasets_params,
):
    # Mock CloudWatch client
    mock_cloudwatch = Mock()
    mock_boto3_client.return_value = mock_cloudwatch

    bad_data_df = sample_data_df.drop(columns=["ispublished"])
    mock_get_new_data.return_value = bad_data_df

    with pytest.raises(ValueError):
        process_data(datasets_params)

    assert mock_get_new_data.call_count == 1
    mock_wr_s3.to_parquet.assert_not_called()


@patch("process_data.download_s3_object")
@patch("process_data.get_new_data")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
@patch("boto3.client")
def test_process_data_validation_bad_format(
    mock_boto3_client,
    mock_wr_s3,
    mock_wr_catalog,
    mock_get_new_data,
    mock_s3,
    sample_data_df,
    datasets_params,
):
    mock_cloudwatch = Mock()
    mock_boto3_client.return_value = mock_cloudwatch

    bad_data_df = sample_data_df.copy()
    bad_data_df["checkbox_count"] = "foo"  # string value
    mock_get_new_data.return_value = bad_data_df

    with pytest.raises(ValueError):
        process_data(datasets_params)

    assert mock_get_new_data.call_count == 1
    assert mock_wr_s3.to_parquet.call_count == 0
