import pytest
import sys

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pandas as pd
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
    validate_schema,
    is_type_compatible,
    get_new_data,
    process_data,
    publish_metric,
    configure_gx_stores,
    SOURCE_BUCKET,
    SOURCE_PREFIX,
)


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
                pd.Timestamp("2025-04-09 00:01:58"),
                pd.Timestamp("2025-03-02 00:01:55"),
                pd.Timestamp("2025-04-24 00:01:47"),
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


@pytest.fixture
def glue_table_schema():
    return pd.DataFrame(
        {
            "Column Name": [
                "id",
                "ttl",
                "ispublished",
                "created_at",
                "updated_at",
                "name",
                "securityattribute",
                "closingdate",
                "formpurpose",
                "publishdesc",
                "publishformtype",
                "publishreason",
                "closeddetails",
                "saveandresume",
                "deliveryemaildestination",
                "api_created_at",
                "api_id",
                "deliveryoption",
                "timestamp",
                "titleen",
                "titlefr",
                "brand",
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
                "notificationsinterval",
                "year",
                "month",
            ],
            "Type": [
                "string",  # id
                "timestamp",  # ttl
                "boolean",  # ispublished
                "timestamp",  # created_at
                "timestamp",  # updated_at
                "string",  # name
                "string",  # securityattribute
                "timestamp",  # closingdate
                "string",  # formpurpose
                "string",  # publishdesc
                "string",  # publishformtype
                "string",  # publishreason
                "string",  # closeddetails
                "boolean",  # saveandresume
                "string",  # deliveryemaildestination
                "timestamp",  # api_created_at
                "string",  # api_id
                "int",  # deliveryoption
                "timestamp",  # timestamp
                "string",  # titleen
                "string",  # titlefr
                "string",  # brand
                "bigint",  # checkbox_count
                "bigint",  # combobox_count
                "bigint",  # dropdown_count
                "bigint",  # dynamicrow_count
                "bigint",  # fileinput_count
                "bigint",  # formatteddate_count
                "bigint",  # radio_count
                "bigint",  # richtext_count
                "bigint",  # textarea_count
                "bigint",  # textfield_count
                "bigint",  # addresscomplete_count
                "int",  # notificationsinterval
                "string",  # year
                "string",  # month
            ],
        }
    )


def test_validate_schema_valid(sample_data_df, glue_table_schema):
    assert validate_schema(sample_data_df, None, None, glue_table_schema) is True


def test_validate_schema_missing_column(sample_data_df, glue_table_schema):
    df_missing_column = sample_data_df.drop("ispublished", axis=1)
    assert validate_schema(df_missing_column, None, None, glue_table_schema) is False


def test_validate_schema_partition_column(sample_data_df, glue_table_schema):
    df_with_partition_column = sample_data_df.copy()
    df_with_partition_column["month"] = pd.to_datetime(
        ["2024-01-01", "2024-01-02", "2024-01-03"]
    )
    assert (
        validate_schema(df_with_partition_column, None, ["month"], glue_table_schema)
        is True
    )


def test_validate_schema_dropped_column(sample_data_df, glue_table_schema):
    df_dropped_column = sample_data_df.drop("ispublished", axis=1)
    assert (
        validate_schema(
            df_dropped_column, ["ispublished"], ["month"], glue_table_schema
        )
        is True
    )


def test_validate_schema_wrong_type(sample_data_df, glue_table_schema):
    df_wrong_type = sample_data_df.copy()
    df_wrong_type["ispublished"] = pd.to_datetime(
        ["2024-01-04", "2024-01-05", "2024-01-06"]
    )
    assert validate_schema(df_wrong_type, None, None, glue_table_schema) is False


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


@patch("process_data.datetime")
@patch("process_data.logger")
def test_publish_metric(mock_logger, mock_datetime):
    mock_cloudwatch = Mock()
    test_dataset = "test-dataset"
    test_count = 100
    test_processing_time = 5.25

    fixed_timestamp = datetime(2025, 3, 28, 12, 0, 0, tzinfo=timezone.utc)
    mock_datetime.now.return_value = fixed_timestamp

    publish_metric(mock_cloudwatch, test_dataset, test_count, test_processing_time)

    mock_cloudwatch.put_metric_data.assert_called_once_with(
        Namespace="data-lake/etl/gc-forms",
        MetricData=[
            {
                "MetricName": "ProcessedRecordCount",
                "Dimensions": [{"Name": "Dataset", "Value": test_dataset}],
                "Value": test_count,
                "Timestamp": fixed_timestamp,
                "Unit": "Count",
            },
            {
                "MetricName": "ProcessingTime",
                "Dimensions": [{"Name": "Dataset", "Value": test_dataset}],
                "Value": test_processing_time,
                "Timestamp": fixed_timestamp,
                "Unit": "Seconds",
            },
        ],
    )

    mock_logger.info.assert_called_once_with(
        f"Published metrics for {test_dataset}: {test_count} records in {test_processing_time:.2f}s"
    )


@patch("pandas.Timestamp")
@patch("awswrangler.s3")
def test_get_new_data(mock_wr_s3, mock_timestamp, sample_data_df):
    # Mock AWS Wrangler response
    mock_wr_s3.read_parquet.return_value = sample_data_df
    fixed_date = datetime(1970, 1, 2)
    fixed_date_yesterday = datetime(1970, 1, 1)
    mock_timestamp.today.return_value = fixed_date

    result = get_new_data(
        path="test-path",
        date_columns=["ttl", "timestamp", "created_at"],
        drop_columns=["ispublished"],
        field_count_columns=["checkbox_count", "muffin_count"],
        email_columns=["deliveryemaildestination"],
        partition_columns=["year", "month"],
        partition_timestamp="created_at",
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
    glue_table_schema,
):
    mock_cloudwatch = Mock()
    mock_boto3_client.return_value = mock_cloudwatch
    mock_get_new_data.return_value = sample_data_df
    mock_wr_catalog.table.return_value = glue_table_schema

    process_data()

    # Verify a call for each dataset
    assert mock_get_new_data.call_count == 5
    assert mock_wr_s3.to_parquet.call_count == 5
    assert mock_cloudwatch.put_metric_data.call_count == 5


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
    glue_table_schema,
):
    mock_cloudwatch = Mock()
    mock_boto3_client.return_value = mock_cloudwatch
    mock_get_new_data.return_value = sample_data_df
    mock_wr_catalog.table.return_value = glue_table_schema

    process_data(
        datasets=[
            {
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
                "partition_timestamp": "created_at",
                "partition_columns": ["year", "month"],
                "email_columns": ["deliveryemaildestination"],
                "gx_checkpoint": "forms-template_checkpoint",
            }
        ]
    )

    assert mock_get_new_data.call_count == 1
    assert mock_wr_s3.to_parquet.call_count == 1
    assert mock_cloudwatch.put_metric_data.call_count == 1


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
    glue_table_schema,
):
    mock_cloudwatch = Mock()
    mock_boto3_client.return_value = mock_cloudwatch
    mock_get_new_data.return_value = pd.DataFrame()
    mock_wr_catalog.table.return_value = glue_table_schema

    process_data()

    mock_wr_s3.to_parquet.assert_not_called()
    assert mock_cloudwatch.put_metric_data.call_count == 5


@patch("process_data.download_s3_object")
@patch("process_data.validate_with_gx", return_value=True)
@patch("process_data.get_new_data")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
@patch("boto3.client")
def test_process_data_validation_failure(
    mock_boto3_client,
    mock_wr_s3,
    mock_wr_catalog,
    mock_get_new_data,
    mock_validate_with_gx,
    mock_s3,
    sample_data_df,
    glue_table_schema,
):
    mock_cloudwatch = Mock()
    mock_boto3_client.return_value = mock_cloudwatch
    mock_get_new_data.return_value = sample_data_df

    # Mock table schema that will cause validation to fail (missing required column)
    invalid_schema = glue_table_schema.drop(0)  # Remove the first column from schema
    mock_wr_catalog.table.return_value = invalid_schema

    # Run the process, expect a ValueError due to schema validation failure
    with pytest.raises(ValueError):
        process_data()

    # Verify to_parquet was not called
    mock_wr_s3.to_parquet.assert_not_called()
    mock_cloudwatch.put_metric_data.assert_not_called()


@patch("process_data.download_s3_object")
@patch("process_data.get_new_data")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
@patch("boto3.client")
def test_process_data_validation_failure_great_expectations_missing_column(
    mock_boto3_client,
    mock_wr_s3,
    mock_wr_catalog,
    mock_get_new_data,
    mock_s3,
    sample_data_df,
    glue_table_schema,
):
    # Mock CloudWatch client
    mock_cloudwatch = Mock()
    mock_boto3_client.return_value = mock_cloudwatch

    bad_data_df = sample_data_df.drop(columns=["ispublished"])
    mock_get_new_data.return_value = bad_data_df
    mock_wr_catalog.table.return_value = glue_table_schema

    with pytest.raises(ValueError):
        process_data(
            datasets=[
                {
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
                    "partition_timestamp": "created_at",
                    "partition_columns": ["year", "month"],
                    "email_columns": ["deliveryemaildestination"],
                    "gx_checkpoint": "forms-template_checkpoint",
                }
            ]
        )

    assert mock_get_new_data.call_count == 1
    assert mock_wr_s3.to_parquet.call_count == 0
    assert mock_cloudwatch.put_metric_data.call_count == 0


@patch("process_data.download_s3_object")
@patch("process_data.get_new_data")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
@patch("boto3.client")
def test_process_data_validation_failure_great_expectations_bad_schema_str_count(
    mock_boto3_client,
    mock_wr_s3,
    mock_wr_catalog,
    mock_get_new_data,
    mock_s3,
    sample_data_df,
    glue_table_schema,
):
    mock_cloudwatch = Mock()
    mock_boto3_client.return_value = mock_cloudwatch

    bad_data_df = sample_data_df.copy()
    bad_data_df["checkbox_count"] = "1"  # string value
    mock_get_new_data.return_value = bad_data_df
    mock_wr_catalog.table.return_value = glue_table_schema

    with pytest.raises(ValueError):
        process_data(
            datasets=[
                {
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
                    "partition_timestamp": "created_at",
                    "partition_columns": ["year", "month"],
                    "email_columns": ["deliveryemaildestination"],
                    "gx_checkpoint": "forms-template_checkpoint",
                }
            ]
        )

    assert mock_get_new_data.call_count == 1
    assert mock_wr_s3.to_parquet.call_count == 0
    assert mock_cloudwatch.put_metric_data.call_count == 0
