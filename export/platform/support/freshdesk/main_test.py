import pytest
from unittest.mock import Mock, patch

from main import (
    FreshdeskClient,
    upload_to_s3,
    get_ssm_parameter,
    handler,
    STATUS_LOOKUP,
    PRIORITY_LOOKUP,
    SOURCE_LOOKUP,
)

# Test data
MOCK_PRODUCTS = [{"id": 1, "name": "Product 1"}, {"id": 2, "name": "Product 2"}]

MOCK_TICKET = {
    "id": 1,
    "status": 2,
    "priority": 1,
    "source": 1,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z",
    "due_by": "2024-01-02T00:00:00Z",
    "fr_due_by": "2024-01-02T00:00:00Z",
    "is_escalated": False,
    "tags": ["tag1", "tag2"],
    "spam": False,
    "requester_id": 123,
    "type": "Incident",
    "product_id": 1,
    "custom_fields": {
        "cf_language": "en",
        "cf_provinceterritory": "ON",
        "cf_organization": "Test Org",
    },
}

MOCK_CONVERSATIONS = [
    {"source": 0},  # Reply
    {"source": 0},  # Reply
    {"source": 2},  # Note
]


@pytest.fixture
def mock_freshdesk_client():
    with patch("requests.get") as mock_get:
        client = FreshdeskClient("test.freshdesk.com", "dummy_key")
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = MOCK_PRODUCTS
        client.products_cache = {str(p["id"]): p["name"] for p in MOCK_PRODUCTS}
        yield client


@pytest.fixture
def mock_s3_client():
    with patch("boto3.client") as mock_client:
        yield mock_client


@pytest.fixture
def mock_ssm_client():
    with patch("boto3.client") as mock_client:
        mock_ssm = Mock()
        mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "test_api_key"}}
        mock_client.return_value = mock_ssm
        yield mock_client


class TestFreshdeskClient:
    def test_init(self):
        client = FreshdeskClient("test.freshdesk.com", "test_key")
        assert client.base_url == "https://test.freshdesk.com"
        assert "Basic" in client.headers["Authorization"]
        assert client.headers["Content-Type"] == "application/json"

    def test_get_products(self, mock_freshdesk_client):
        products = mock_freshdesk_client.get_products()
        assert isinstance(products, dict)
        assert products["1"] == "Product 1"
        assert products["2"] == "Product 2"

    def test_get_ticket_conversations(self, mock_freshdesk_client):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = MOCK_CONVERSATIONS

            conversations = mock_freshdesk_client.get_ticket_conversations(1)
            assert conversations["total_count"] == 3
            assert conversations["reply_count"] == 2
            assert conversations["note_count"] == 1

    def test_get_requester_email_suffix_internal(self, mock_freshdesk_client):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"email": "test@cds-snc.ca"}

            suffix = mock_freshdesk_client.get_requester_email_suffix(123)
            assert suffix == "cds-snc.ca"

    def test_get_requester_email_suffix_external(self, mock_freshdesk_client):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"email": "test@example.com"}

            suffix = mock_freshdesk_client.get_requester_email_suffix(123)
            assert suffix == "external"

    def test_get_tickets(self, mock_freshdesk_client):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"results": [MOCK_TICKET]}

            # Mock the conversation call
            mock_freshdesk_client.get_ticket_conversations = Mock(
                return_value={"total_count": 3, "reply_count": 2, "note_count": 1}
            )

            # Mock the requester email suffix
            mock_freshdesk_client.get_requester_email_suffix = Mock(
                return_value="external"
            )

            tickets = mock_freshdesk_client.get_tickets()
            assert len(tickets) == 1
            ticket = tickets[0]

            assert ticket["id"] == 1
            assert ticket["status_label"] == STATUS_LOOKUP[2]
            assert ticket["priority_label"] == PRIORITY_LOOKUP[1]
            assert ticket["source_label"] == SOURCE_LOOKUP[1]
            assert ticket["product_name"] == "Product 1"
            assert ticket["conversations_total_count"] == 3


def test_upload_to_s3(mock_s3_client):
    test_data = {"test": "data"}
    result = upload_to_s3("test-bucket", "prefix", test_data)

    assert result.startswith("s3://test-bucket/prefix/")
    assert result.endswith(".json")
    mock_s3_client.return_value.put_object.assert_called_once()


def test_get_ssm_parameter(mock_ssm_client):
    result = get_ssm_parameter("test_param")
    assert result == "test_api_key"
    mock_ssm_client.return_value.get_parameter.assert_called_once_with(
        Name="test_param", WithDecryption=True
    )


def test_handler_tickets(mock_ssm_client):
    with patch("main.FreshdeskClient") as MockClient:
        mock_client = Mock()
        mock_client.get_tickets.return_value = [MOCK_TICKET]
        MockClient.return_value = mock_client

        with patch("main.upload_to_s3") as mock_upload:
            handler({}, {})
            mock_client.get_tickets.assert_called_once()
            mock_upload.assert_called_once()


def test_handler_no_tickets(mock_ssm_client):
    with patch("main.FreshdeskClient") as MockClient:
        mock_client = Mock()
        mock_client.get_tickets.return_value = []
        MockClient.return_value = mock_client

        with patch("main.upload_to_s3") as mock_upload:
            handler({}, {})
            mock_client.get_tickets.assert_called_once()
            mock_upload.assert_not_called()
