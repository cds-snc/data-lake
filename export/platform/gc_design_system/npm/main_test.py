import pytest
import json
from unittest.mock import patch, MagicMock
from main import fetch_npm_downloads_for_year, fetch_all_npm_data, handler


class TestNPMExport:
    @patch("main.requests.get")
    def test_fetch_npm_downloads_for_year(self, mock_get):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "package": "@cdssnc/gcds-components-vue",
            "downloads": [
                {"day": "2024-01-01", "downloads": 100},
                {"day": "2024-01-02", "downloads": 150},
            ],
        }
        mock_get.return_value = mock_response

        result = fetch_npm_downloads_for_year(2024)

        assert result["package"] == "@cdssnc/gcds-components-vue"
        assert len(result["downloads"]) == 2
        mock_get.assert_called_once()

    @patch("main.fetch_npm_downloads_for_year")
    def test_fetch_all_npm_data(self, mock_fetch_year):
        # Mock year data
        mock_fetch_year.return_value = {
            "package": "@cdssnc/gcds-components-vue",
            "downloads": [{"day": "2024-01-01", "downloads": 100}],
        }

        result = fetch_all_npm_data()

        assert len(result) > 0
        assert "package" in result[0]
        assert "year" in result[0]
        assert "fetched_at" in result[0]

    @patch("main.boto3.client")
    @patch("main.fetch_all_npm_data")
    def test_handler_success(self, mock_fetch_data, mock_boto3):
        # Mock NPM data
        mock_fetch_data.return_value = [
            {
                "day": "2024-01-01",
                "downloads": 100,
                "package": "@cdssnc/gcds-components-vue",
            }
        ]

        # Mock S3 and Glue clients
        mock_s3 = MagicMock()
        mock_glue = MagicMock()
        mock_boto3.side_effect = lambda service: (
            mock_s3 if service == "s3" else mock_glue
        )

        result = handler({}, {})

        assert result["statusCode"] == 200
        assert "Saved 1 NPM download records" in result["body"]
        mock_s3.put_object.assert_called()
        mock_glue.start_crawler.assert_called()

    @patch("main.fetch_all_npm_data")
    def test_handler_fetch_error(self, mock_fetch_data):
        # Mock fetch error
        mock_fetch_data.side_effect = Exception("API Error")

        result = handler({}, {})

        assert result["statusCode"] == 500
        assert "Failed to fetch from NPM API" in result["body"]
