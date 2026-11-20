import glob
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
from pyspark.sql import SparkSession

os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"


class MockGlueContext:
    def __init__(self, spark_context=None):
        self.spark_session = None

    def get_logger(self):
        return Mock()


sys.modules["awsglue"] = Mock()
sys.modules["awsglue.context"] = Mock()
sys.modules["awsglue.context"].GlueContext = MockGlueContext
sys.modules["awsglue.job"] = Mock()
sys.modules["awsglue.job"].Job = Mock()
sys.modules["awsglue.utils"] = Mock()
sys.modules["awsglue.utils"].getResolvedOptions = Mock()
sys.modules["awsglue.utils"].getResolvedOptions.return_value = {
    "JOB_NAME": "test_job",
    "source_bucket": "test-source-bucket",
    "source_prefix": "test-source-prefix",
    "output_bucket": "test-output-bucket",
    "output_prefix": "test-output-prefix",
    "database_name_output": "test_database_output",
    "table_config_object": "s3://test-config-bucket/test-config-key",
    "gx_config_object": "s3://test-config-bucket/test-config-key",
    "table_name_prefix": "test_prefix",
    "target_env": "test",
}

# Import after mocking AWS Glue modules
from process_data import (  # noqa: E402
    aggregate_cloudfront_logs,
    download_s3_object,
    get_dataset_config,
    get_date_from,
    get_expected_dates,
    load_expectation_suite,
    store_validation_result,
    validate_with_gx,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_COLUMNS = [
    "date",
    "cs(referer)",
    "cs(host)",
    "x-host-header",
    "cs-uri-stem",
    "sc-status",
    "x-edge-result-type",
    "sc-bytes",
]


def log_row(
    referer,
    date="2026-10-28",
    uri="/gcds.css",
    status="200",
    result="Hit",
    sc_bytes="100",
    host="abc.cloudfront.net",
    host_header="cdn.example.ca",
):
    return (date, referer, host, host_header, uri, status, result, sc_bytes)


@pytest.fixture(scope="session")
def spark_session():
    spark = (
        SparkSession.builder.appName("GCDSProcessDataTest")
        .config("spark.master", "local[*]")
        .config("spark.sql.execution.arrow.pyspark.enabled", "false")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.adaptive.enabled", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    yield spark
    spark.stop()


def aggregate(spark_session, rows):
    df = spark_session.createDataFrame(rows, LOG_COLUMNS)
    return aggregate_cloudfront_logs(df)


def by_referrer(result):
    return {r["referrer_host"]: r for r in result.collect()}


# ===== AGGREGATION TESTS =====


def test_aggregate_sums_requests_and_bytes(spark_session):
    rows = [
        log_row("https://www.canada.ca/en.html", sc_bytes="100"),
        log_row("https://www.canada.ca/fr.html", sc_bytes="50"),
        log_row("https://www.canada.ca/en/a.html", sc_bytes="25"),
    ]
    result = aggregate(spark_session, rows)

    assert result.count() == 1
    row = result.collect()[0]
    assert row["referrer_host"] == "www.canada.ca"
    assert row["requests"] == 3
    assert row["bytes_sent"] == 175


def test_aggregate_splits_on_status_uri_and_date(spark_session):
    rows = [
        log_row("https://a.ca/", status="200"),
        log_row("https://a.ca/", status="304"),
        log_row("https://a.ca/", uri="/other.js"),
        log_row("https://a.ca/", date="2026-10-29"),
    ]
    assert aggregate(spark_session, rows).count() == 4


def test_referrer_host_is_lowercased_without_path_or_port(spark_session):
    rows = [log_row("https://WWW.Canada.CA:8443/en/page?x=1#top")]
    result = by_referrer(aggregate(spark_session, rows))

    assert list(result.keys()) == ["www.canada.ca"]


def test_blank_and_missing_referrers_are_none(spark_session):
    rows = [log_row(""), log_row("-"), log_row("  "), log_row(None)]
    result = by_referrer(aggregate(spark_session, rows))

    assert list(result.keys()) == ["(none)"]
    assert result["(none)"]["requests"] == 4
    assert result["(none)"]["is_dev_traffic"] is False


def test_unparseable_referrer_is_unknown(spark_session):
    rows = [log_row("not a url")]
    result = by_referrer(aggregate(spark_session, rows))

    assert list(result.keys()) == ["(unknown)"]


@pytest.mark.parametrize(
    "referer,expected_host,is_dev",
    [
        ("http://localhost:3000/", "localhost", True),
        ("http://127.0.0.1:8080/x", "127.0.0.1", True),
        ("http://host.docker.internal/", "host.docker.internal", True),
        ("https://my-project.ddev.site/", "my-project.ddev.site", True),
        (
            "https://design-system.alpha.canada.ca/",
            "design-system.alpha.canada.ca",
            False,
        ),
        ("https://notddev.site.example.com/", "notddev.site.example.com", False),
    ],
)
def test_dev_traffic_flag(spark_session, referer, expected_host, is_dev):
    result = by_referrer(aggregate(spark_session, [log_row(referer)]))

    assert result[expected_host]["is_dev_traffic"] is is_dev


def test_output_columns(spark_session):
    result = aggregate(spark_session, [log_row("https://a.ca/")])

    assert set(result.columns) == {
        "referrer_host",
        "is_dev_traffic",
        "distribution_domain",
        "host_header",
        "uri_stem",
        "status",
        "edge_result_type",
        "date",
        "requests",
        "bytes_sent",
    }


# ===== DATE WINDOW TESTS =====


def test_get_date_from():
    today = datetime(2026, 11, 6, 8, 30, tzinfo=timezone.utc)

    assert get_date_from(3, today) == "2026-11-03"
    assert get_date_from(0, today) == "2026-11-06"


def test_get_date_from_crosses_month_boundary():
    today = datetime(2026, 11, 1, tzinfo=timezone.utc)

    assert get_date_from(3, today) == "2026-10-29"


# ===== CONFIG TESTS =====


def test_get_dataset_config_reads_json_files(tmp_path, monkeypatch):
    tables = tmp_path / "tables"
    tables.mkdir()
    (tables / "cloudfront_daily.json").write_text(
        json.dumps(
            {
                "table_name": "cloudfront_daily",
                "partition_cols": ["date"],
                "look_back_days": 3,
            }
        )
    )
    (tables / "ignored.txt").write_text("not json")
    monkeypatch.chdir(tmp_path)

    datasets = get_dataset_config()

    assert len(datasets) == 1
    assert datasets[0]["table_name"] == "cloudfront_daily"


def test_get_dataset_config_missing_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="Tables directory not found"):
        get_dataset_config()


def test_get_dataset_config_empty_directory(tmp_path, monkeypatch):
    (tmp_path / "tables").mkdir()
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="No dataset configurations found"):
        get_dataset_config()


def test_download_s3_object_extracts_zip(tmp_path, monkeypatch):
    import zipfile

    monkeypatch.chdir(tmp_path)
    s3 = Mock()

    def fake_download(Bucket, Key, Filename):
        with zipfile.ZipFile(Filename, "w") as z:
            z.writestr("cloudfront_daily.json", "{}")

    s3.download_file.side_effect = fake_download

    download_s3_object(s3, "s3://my-bucket/path/tables.zip", "tables.zip")

    s3.download_file.assert_called_once()
    assert s3.download_file.call_args.kwargs["Bucket"] == "my-bucket"
    assert s3.download_file.call_args.kwargs["Key"] == "path/tables.zip"
    assert (tmp_path / "tables" / "cloudfront_daily.json").exists()


# ===== REPOSITORY CONFIG CONSISTENCY TESTS =====


def test_table_configs_are_valid():
    for path in glob.glob(os.path.join(BASE_DIR, "tables", "*.json")):
        with open(path) as f:
            config = json.load(f)
        assert config["table_name"] == os.path.basename(path)[: -len(".json")]
        assert config["partition_cols"] == ["date"]
        assert config["look_back_days"] >= 1


def test_every_table_has_gx_suite():
    for path in glob.glob(os.path.join(BASE_DIR, "tables", "*.json")):
        table = os.path.basename(path)[: -len(".json")]
        assert os.path.exists(
            os.path.join(BASE_DIR, "gx", "expectations", f"gcds-{table}_suite.json")
        )


def test_gx_suites_load(monkeypatch):
    """Every suite shipped in gx/expectations must load as a valid GX 1.x suite."""
    monkeypatch.chdir(BASE_DIR)
    suite_files = sorted(os.listdir(os.path.join(BASE_DIR, "gx", "expectations")))
    assert len(suite_files) > 0

    for suite_file in suite_files:
        suite_name = suite_file.replace(".json", "")
        suite = load_expectation_suite(suite_name)
        assert suite.name == suite_name
        assert len(suite.expectations) > 0


def test_gx_suite_columns_exist_in_output(spark_session):
    output_columns = set(aggregate(spark_session, [log_row("https://a.ca/")]).columns)
    suite_path = os.path.join(
        BASE_DIR, "gx", "expectations", "gcds-cloudfront_daily_suite.json"
    )
    with open(suite_path) as f:
        suite = json.load(f)

    for expectation in suite["expectations"]:
        column = expectation["kwargs"].get("column")
        if column:
            assert column in output_columns


# ===== GREAT EXPECTATIONS VALIDATION TESTS =====


@contextmanager
def mock_gx(success=True, failed_results=None):
    """
    Patch the Great Expectations module used by process_data so that the
    validation definition run returns a canned result.
    """
    result = MagicMock()
    result.success = success
    result.results = failed_results or []

    with patch("process_data.gx") as gx_mock, patch(
        "process_data.load_expectation_suite"
    ) as load_suite_mock:
        context = gx_mock.get_context.return_value
        validation_definition = context.validation_definitions.add.return_value
        validation_definition.run.return_value = result
        gx_mock.load_suite_mock = load_suite_mock
        gx_mock.validation_definition = validation_definition
        yield gx_mock


def test_validate_with_gx_success(spark_session):
    df = aggregate(spark_session, [log_row("https://a.ca/")])

    with mock_gx(success=True) as gx_mock, patch("process_data.boto3.client"):
        assert validate_with_gx(df, "test_suite") is True

        gx_mock.load_suite_mock.assert_called_once_with("test_suite")
        gx_mock.get_context.assert_called_once_with(mode="ephemeral")
        call_args = gx_mock.validation_definition.run.call_args
        assert call_args[1]["batch_parameters"] == {"dataframe": df}


def test_validate_with_gx_failure(spark_session):
    df = aggregate(spark_session, [log_row("https://a.ca/")])

    failed = MagicMock()
    failed.success = False
    failed.expectation_config.type = "expect_table_row_count_to_be_between"
    failed.expectation_config.kwargs = {"min_value": 1000}
    failed.result = {"observed_value": 0}

    with mock_gx(success=False, failed_results=[failed]), patch(
        "process_data.boto3.client"
    ):
        assert validate_with_gx(df, "test_suite") is False


def test_validate_with_gx_exception_returns_false(spark_session):
    df = aggregate(spark_session, [log_row("https://a.ca/")])

    with mock_gx() as gx_mock:
        gx_mock.get_context.side_effect = Exception("GX context error")
        assert validate_with_gx(df, "test_suite") is False


def test_validate_with_gx_missing_suite(spark_session):
    df = aggregate(spark_session, [log_row("https://a.ca/")])
    assert validate_with_gx(df, "gcds-does_not_exist_suite") is False


def test_store_validation_result_writes_to_s3():
    validation_result = MagicMock()
    validation_result.to_json_dict.return_value = {"success": True}

    with patch("process_data.boto3.client") as mock_client:
        store_validation_result(
            validation_result, "gcds-cloudfront_daily_suite", "output-bucket"
        )

        kwargs = mock_client.return_value.put_object.call_args[1]
        assert kwargs["Bucket"] == "output-bucket"
        assert kwargs["Key"].startswith(
            "platform/gc-design-system/data-validation/validations/"
            "gcds-cloudfront_daily_suite/"
        )
        assert json.loads(kwargs["Body"]) == {"success": True}


def test_store_validation_result_skipped_for_test_bucket():
    with patch("process_data.boto3.client") as mock_client:
        store_validation_result(MagicMock(), "gcds-cloudfront_daily_suite", "test-b")
        mock_client.assert_not_called()


def test_store_validation_result_does_not_raise_on_s3_failure():
    validation_result = MagicMock()
    validation_result.to_json_dict.return_value = {"success": True}

    with patch("process_data.boto3.client") as mock_client:
        mock_client.return_value.put_object.side_effect = Exception("S3 error")
        store_validation_result(
            validation_result, "gcds-cloudfront_daily_suite", "output-bucket"
        )


def test_get_expected_dates_excludes_today():
    today = datetime(2026, 11, 18, 5, 0, tzinfo=timezone.utc)
    assert get_expected_dates(3, today) == ["2026-11-15", "2026-11-16", "2026-11-17"]


def test_get_expected_dates_starts_at_date_from():
    today = datetime(2026, 11, 18, 5, 0, tzinfo=timezone.utc)
    assert get_expected_dates(3, today)[0] == get_date_from(3, today)


def window_dataframe(spark_session, dates, rows_per_date=500):
    rows = [
        (date, "(none)", "/a", "200", 1, 100)
        for date in dates
        for _ in range(rows_per_date)
    ]
    return spark_session.createDataFrame(
        rows, ["date", "referrer_host", "uri_stem", "status", "requests", "bytes_sent"]
    )


def test_suite_passes_when_every_expected_date_is_present(spark_session, monkeypatch):
    monkeypatch.chdir(BASE_DIR)
    expected = ["2026-11-03", "2026-11-04", "2026-11-05"]
    df = window_dataframe(spark_session, expected)

    assert validate_with_gx(
        df,
        "gcds-cloudfront_daily_suite",
        expectation_parameters={"expected_dates": expected},
    )


def test_suite_fails_when_a_day_in_the_window_is_missing(spark_session, monkeypatch):
    monkeypatch.chdir(BASE_DIR)
    expected = ["2026-11-03", "2026-11-04", "2026-11-05"]
    df = window_dataframe(spark_session, ["2026-11-03", "2026-11-04", "2026-11-06"])

    assert not validate_with_gx(
        df,
        "gcds-cloudfront_daily_suite",
        expectation_parameters={"expected_dates": expected},
    )
