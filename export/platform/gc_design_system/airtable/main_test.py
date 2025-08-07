import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock

# Set test environment variables to match main.py
os.environ["AIRTABLE_API_KEY_PARAMETER_NAME"] = "/test/airtable-api-key"
os.environ["S3_BUCKET_NAME_TRANSFORMED"] = "test-bucket-transformed"
os.environ["S3_BUCKET_NAME_RAW"] = "test-bucket-raw"
os.environ["S3_OBJECT_PREFIX"] = "test/prefix"

from main import handler, fetch_all_records, get_airtable_api_key


class TestGCDesignSystemExport:
    @pytest.fixture
    def mock_boto3_client(self):
        with patch("main.boto3.client") as mock_client:
            # Create separate mock instances for SSM and S3
            mock_ssm = Mock()
            mock_s3 = Mock()

            # Configure the client to return the appropriate mock based on service
            def client_side_effect(service_name):
                if service_name == "ssm":
                    return mock_ssm
                elif service_name == "s3":
                    return mock_s3
                else:
                    return Mock()

            mock_client.side_effect = client_side_effect
            yield mock_client, mock_ssm, mock_s3

    @pytest.fixture
    def mock_requests_get(self):
        with patch("main.requests.get") as mock_get:
            yield mock_get

    @pytest.fixture
    def sample_airtable_response(self):
        return {
            "records": [
                {
                    "id": "rec123",
                    "fields": {"name": "Test Client", "status": "Active"},
                    "createdTime": "2024-01-01T00:00:00.000Z",
                },
                {
                    "id": "rec456",
                    "fields": {"name": "Another Client", "status": "Inactive"},
                    "createdTime": "2024-01-02T00:00:00.000Z",
                },
            ]
        }

    def test_get_airtable_api_key_success(self, mock_boto3_client):
        """Test successful API key retrieval from SSM."""
        mock_client, mock_ssm, mock_s3 = mock_boto3_client
        mock_ssm.get_parameter.return_value = {
            "Parameter": {"Value": "test-api-key-value"}
        }

        api_key = get_airtable_api_key()

        assert api_key == "test-api-key-value"
        mock_client.assert_called_with("ssm")
        mock_ssm.get_parameter.assert_called_once_with(
            Name="/test/airtable-api-key", WithDecryption=True
        )

    def test_get_airtable_api_key_failure(self, mock_boto3_client):
        """Test API key retrieval failure."""
        mock_client, mock_ssm, mock_s3 = mock_boto3_client
        mock_ssm.get_parameter.side_effect = Exception("SSM error")

        with pytest.raises(Exception) as exc_info:
            get_airtable_api_key()

        assert "Failed to retrieve API key from SSM" in str(exc_info.value)

    def test_handler_success(
        self, mock_boto3_client, mock_requests_get, sample_airtable_response
    ):
        """Test successful handler execution."""
        mock_client, mock_ssm, mock_s3 = mock_boto3_client
        mock_ssm.get_parameter.return_value = {
            "Parameter": {"Value": "test-api-key-value"}
        }

        # Mock requests.get response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_airtable_response
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        # Mock S3 put_object
        mock_s3.put_object.return_value = {}

        result = handler({}, {})

        assert result["statusCode"] == 200
        assert "Saved 2 records" in result["body"]

        # Check that put_object was called twice with correct buckets and keys
        calls = mock_s3.put_object.call_args_list
        assert len(calls) == 2
        # Extract bucket/key for each call
        call_buckets = [call.kwargs.get("Bucket") for call in calls]
        call_keys = [call.kwargs.get("Key") for call in calls]
        # Should have one call for transformed, one for raw
        assert "test-bucket-transformed" in call_buckets
        assert "test-bucket-raw" in call_buckets
        assert "test/prefix/clients.json" in call_keys
        assert any(
            k.startswith("test/prefix/clients_") and k.endswith(".json")
            for k in call_keys
        )

    def test_handler_airtable_failure(self, mock_boto3_client, mock_requests_get):
        """Test handler with Airtable fetch failure."""
        mock_client, mock_ssm, mock_s3 = mock_boto3_client
        mock_ssm.get_parameter.return_value = {
            "Parameter": {"Value": "test-api-key-value"}
        }

        mock_requests_get.side_effect = Exception("Connection error")

        result = handler({}, {})

        assert result["statusCode"] == 500
        assert "Failed to fetch from Airtable" in result["body"]

    def test_handler_s3_failure(
        self, mock_boto3_client, mock_requests_get, sample_airtable_response
    ):
        """Test handler with S3 upload failure."""
        mock_client, mock_ssm, mock_s3 = mock_boto3_client
        mock_ssm.get_parameter.return_value = {
            "Parameter": {"Value": "test-api-key-value"}
        }

        # Mock successful Airtable response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_airtable_response
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        # Mock S3 failure
        mock_s3.put_object.side_effect = Exception("S3 error")

        result = handler({}, {})

        assert result["statusCode"] == 500
        assert "Failed to upload to S3" in result["body"]

    def test_fetch_all_records_single_page(
        self, mock_boto3_client, mock_requests_get, sample_airtable_response
    ):
        """Test fetching records from a single page."""
        mock_client, mock_ssm, mock_s3 = mock_boto3_client
        mock_ssm.get_parameter.return_value = {
            "Parameter": {"Value": "test-api-key-value"}
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_airtable_response
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        records = fetch_all_records()

        assert len(records) == 2
        assert records[0]["id"] == "rec123"
        assert records[1]["id"] == "rec456"

    def test_fetch_all_records_multiple_pages(
        self, mock_boto3_client, mock_requests_get
    ):
        """Test fetching records from multiple pages."""
        mock_client, mock_ssm, mock_s3 = mock_boto3_client
        mock_ssm.get_parameter.return_value = {
            "Parameter": {"Value": "test-api-key-value"}
        }

        # First page response
        page1_response = {
            "records": [{"id": "rec1", "fields": {"name": "Client 1"}}],
            "offset": "next_page_token",
        }

        # Second page response
        page2_response = {"records": [{"id": "rec2", "fields": {"name": "Client 2"}}]}

        # Mock responses
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = page1_response
        mock_response1.raise_for_status = MagicMock()

        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = page2_response
        mock_response2.raise_for_status = MagicMock()

        mock_requests_get.side_effect = [mock_response1, mock_response2]

        records = fetch_all_records()

        assert len(records) == 2
        assert records[0]["id"] == "rec1"
        assert records[1]["id"] == "rec2"

        # Verify both URLs were called
        assert mock_requests_get.call_count == 2
