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
    publish_metric,
    validate_with_gx,
    get_metrics,
    detect_anomalies,
    SOURCE_BUCKET,
    SOURCE_PREFIX,
    METRIC_NAMESPACE,
    METRIC_NAME,
    ANOMALY_LOOKBACK_DAYS,
    ANOMALY_STANDARD_DEVIATION,
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
        "partition_timestamp": "created_at",
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


@patch("process_data.datetime")
@patch("process_data.logger")
def test_publish_metric(mock_logger, mock_datetime):
    mock_cloudwatch = Mock()
    test_namespace = METRIC_NAMESPACE
    test_metric_name = METRIC_NAME
    test_dataset = "test-dataset"
    test_count = 100

    fixed_timestamp = datetime(2025, 3, 28, 12, 0, 0, tzinfo=timezone.utc)
    mock_datetime.now.return_value = fixed_timestamp

    publish_metric(
        mock_cloudwatch,
        test_namespace,
        test_metric_name,
        test_dataset,
        test_count,
    )

    mock_cloudwatch.put_metric_data.assert_called_once_with(
        Namespace=test_namespace,
        MetricData=[
            {
                "MetricName": test_metric_name,
                "Dimensions": [{"Name": "Dataset", "Value": test_dataset}],
                "Value": test_count,
                "Timestamp": fixed_timestamp,
                "Unit": "Count",
            },
        ],
    )

    mock_logger.info.assert_called_once_with(
        f"Published metrics for {test_dataset}: {test_count} records"
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
@patch("process_data.get_metrics")
@patch("process_data.detect_anomalies")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
@patch("boto3.client")
def test_process_data(
    mock_boto3_client,
    mock_wr_s3,
    mock_wr_catalog,
    mock_detect_anomalies,
    mock_get_metrics,
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

    mock_get_metrics.return_value = np.array([100, 110, 90])
    mock_detect_anomalies.return_value = False

    process_data()

    # Verify a call for each dataset
    assert mock_get_new_data.call_count == 5
    assert mock_wr_s3.to_parquet.call_count == 5
    assert mock_cloudwatch.put_metric_data.call_count == 5

    # Verify anomaly detection calls
    assert mock_get_metrics.call_count == 5
    assert mock_detect_anomalies.call_count == 5


@patch("process_data.download_s3_object")
@patch("process_data.get_new_data")
@patch("process_data.get_metrics")
@patch("process_data.detect_anomalies")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
@patch("boto3.client")
def test_process_data_validation_success(
    mock_boto3_client,
    mock_wr_s3,
    mock_wr_catalog,
    mock_detect_anomalies,
    mock_get_metrics,
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

    mock_get_metrics.return_value = np.array([100, 110, 90])
    mock_detect_anomalies.return_value = False

    process_data(datasets_params)

    assert mock_get_new_data.call_count == 1
    assert mock_wr_s3.to_parquet.call_count == 1
    assert mock_cloudwatch.put_metric_data.call_count == 1
    assert mock_get_metrics.call_count == 1
    assert mock_detect_anomalies.call_count == 1


@patch("process_data.download_s3_object")
@patch("process_data.get_new_data")
@patch("process_data.get_metrics")
@patch("process_data.detect_anomalies")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
@patch("boto3.client")
def test_process_data_empty_dataset(
    mock_boto3_client,
    mock_wr_s3,
    mock_wr_catalog,
    mock_detect_anomalies,
    mock_get_metrics,
    mock_get_new_data,
    mock_s3,
):
    mock_cloudwatch = Mock()
    mock_s3_client = Mock()
    mock_boto3_client.side_effect = lambda service_name, *args, **kwargs: (
        mock_cloudwatch if service_name == "cloudwatch" else mock_s3_client
    )
    mock_get_new_data.return_value = pd.DataFrame()

    mock_get_metrics.return_value = np.array([100, 110, 90])
    mock_detect_anomalies.return_value = False

    process_data()

    mock_wr_s3.to_parquet.assert_not_called()
    assert mock_cloudwatch.put_metric_data.call_count == 5
    assert mock_get_metrics.call_count == 5
    assert mock_detect_anomalies.call_count == 5


@patch("process_data.download_s3_object")
@patch("process_data.get_new_data")
@patch("process_data.get_metrics")
@patch("process_data.detect_anomalies")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
@patch("boto3.client")
def test_process_data_extra_column(
    mock_boto3_client,
    mock_wr_s3,
    mock_wr_catalog,
    mock_detect_anomalies,
    mock_get_metrics,
    mock_get_new_data,
    mock_s3,
    sample_data_df,
    datasets_params,
):

    mock_cloudwatch = Mock()

    df_added_column = sample_data_df.copy()
    df_added_column["extra_column"] = "extra_value"
    mock_get_new_data.return_value = df_added_column
    mock_get_new_data.return_value = sample_data_df

    mock_s3_client = Mock()
    mock_boto3_client.side_effect = lambda service_name, *args, **kwargs: (
        mock_cloudwatch if service_name == "cloudwatch" else mock_s3_client
    )

    mock_get_metrics.return_value = np.array([100, 110, 90])
    mock_detect_anomalies.return_value = False

    process_data(datasets_params)

    assert mock_get_new_data.call_count == 1
    assert mock_wr_s3.to_parquet.call_count == 1
    assert mock_cloudwatch.put_metric_data.call_count == 1


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
    mock_cloudwatch.put_metric_data.assert_not_called()
    mock_get_metrics.assert_not_called()
    mock_detect_anomalies.assert_not_called()
    mock_get_metrics.assert_not_called()
    mock_detect_anomalies.assert_not_called()


@patch("process_data.download_s3_object")
@patch("process_data.get_new_data")
@patch("process_data.get_metrics")
@patch("process_data.detect_anomalies")
@patch("awswrangler.catalog")
@patch("awswrangler.s3")
@patch("boto3.client")
def test_process_data_validation_failure_missing_column(
    mock_boto3_client,
    mock_wr_s3,
    mock_wr_catalog,
    mock_detect_anomalies,
    mock_get_metrics,
    mock_get_new_data,
    mock_s3,
    sample_data_df,
    datasets_params,
):
    # Mock CloudWatch client
    mock_cloudwatch = Mock()
    mock_s3_client = Mock()
    mock_boto3_client.side_effect = lambda service_name, *args, **kwargs: (
        mock_cloudwatch if service_name == "cloudwatch" else mock_s3_client
    )
    mock_get_metrics.return_value = np.array([100, 110, 90])
    mock_detect_anomalies.return_value = False

    bad_data_df = sample_data_df.drop(columns=["ispublished"])
    mock_get_new_data.return_value = bad_data_df

    with pytest.raises(ValueError):
        process_data(datasets=datasets_params)

    assert mock_get_new_data.call_count == 1
    assert mock_wr_s3.to_parquet.call_count == 0
    assert mock_cloudwatch.put_metric_data.call_count == 0
    mock_get_metrics.assert_not_called()
    mock_detect_anomalies.assert_not_called()


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
    assert mock_cloudwatch.put_metric_data.call_count == 0


@patch("process_data.datetime")
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
