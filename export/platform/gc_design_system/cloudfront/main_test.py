import pytest
import json
import gzip
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open
from main import load_cloudfront_log, process_cloudfront_log, handler


class TestCloudFrontExport:
    def test_process_cloudfront_log(self):
        # Create test DataFrame
        test_data = {
            'date': ['2024-01-01'],
            'time': ['12:00:00'],
            'x-edge-location': ['IAD89-C1'],
            'sc-bytes': ['1234'],
            'c-ip': ['192.168.1.1']
        }
        df = pd.DataFrame(test_data)
        
        # Process the data
        result = process_cloudfront_log(df)
        
        # Verify results
        assert len(result) == 1
        assert result.iloc[0]['date'] == '2024-01-01'
        assert result.iloc[0]['time'] == '12:00:00'
        assert result.iloc[0]['x-edge-location'] == 'IAD89-C1'
        assert result.iloc[0]['sc-bytes'] == '1234'
        assert result.iloc[0]['c-ip'] == '192.168.1.1'
        assert 'processed_at' in result.columns

    def test_process_cloudfront_log_empty(self):
        # Test with empty DataFrame
        df = pd.DataFrame()
        result = process_cloudfront_log(df)
        assert result.empty

    @patch('main.boto3.client')
    def test_load_cloudfront_log(self, mock_boto3):
        # Mock S3 client
        mock_s3_client = MagicMock()
        mock_boto3.return_value = mock_s3_client
        
        # Create mock CloudFront log content
        log_content = """#Version: 1.0
#Fields: date time x-edge-location sc-bytes c-ip cs-method cs-uri-stem sc-status
2024-01-01	12:00:00	IAD89-C1	1234	192.168.1.1	GET	/test.js	200
2024-01-01	12:01:00	IAD89-C2	5678	192.168.1.2	GET	/style.css	200
"""
        
        # Compress the content
        compressed_content = gzip.compress(log_content.encode('utf-8'))
        
        # Mock S3 response
        mock_response = {
            'Body': MagicMock()
        }
        mock_response['Body'].read = MagicMock(return_value=compressed_content)
        mock_s3_client.get_object.return_value = mock_response
        
        # Test the function
        df = load_cloudfront_log(mock_s3_client, 'test-bucket', 'test-key.gz')
        
        # Verify results
        assert len(df) == 2
        assert df.iloc[0]['date'] == '2024-01-01'
        assert df.iloc[0]['time'] == '12:00:00'
        assert df.iloc[0]['x-edge-location'] == 'IAD89-C1'
        assert df.iloc[1]['c-ip'] == '192.168.1.2'

    @patch('main.boto3.client')
    def test_load_cloudfront_log_no_fields(self, mock_boto3):
        # Mock S3 client
        mock_s3_client = MagicMock()
        mock_boto3.return_value = mock_s3_client
        
        # Create log content without #Fields header
        log_content = """#Version: 1.0
2024-01-01	12:00:00	IAD89-C1	1234	192.168.1.1
"""
        
        compressed_content = gzip.compress(log_content.encode('utf-8'))
        mock_response = {
            'Body': MagicMock()
        }
        mock_response['Body'].read = MagicMock(return_value=compressed_content)
        mock_s3_client.get_object.return_value = mock_response
        
        # Should raise an error
        with pytest.raises(ValueError, match="No #Fields header found"):
            load_cloudfront_log(mock_s3_client, 'test-bucket', 'test-key.gz')

    @patch.dict('os.environ', {
        'S3_BUCKET_NAME_TRANSFORMED': 'transformed-bucket',
        'S3_OBJECT_PREFIX': 'platform/gc-design-system'
    })
    @patch('main.boto3.client')
    @patch('main.load_cloudfront_log')
    @patch('main.process_cloudfront_log')
    @patch('main.pa.Table.from_pandas')
    @patch('main.pq.write_table')
    def test_handler_success(self, mock_write_table, mock_from_pandas, mock_process, mock_load, mock_boto3):
        # Mock S3 client
        mock_s3_client = MagicMock()
        mock_boto3.return_value = mock_s3_client
        
        # Mock the data processing functions
        mock_df = pd.DataFrame({
            'date': ['2024-01-15'],
            'time': ['12:00:00'],
            'processed_at': ['2024-01-01T12:00:00']
        })
        mock_load.return_value = mock_df
        mock_process.return_value = mock_df
        
        # Mock PyArrow table creation
        mock_from_pandas.return_value = MagicMock()
        
        # Mock parquet writing
        mock_write_table.return_value = None
        
        # Create test event
        event = {
            'Records': [{
                's3': {
                    'bucket': {'name': 'source-bucket'},
                    'object': {'key': 'path/to/logfile.gz'}
                }
            }]
        }
        
        # Test the handler
        result = handler(event, {})
        
        # Verify success
        assert result['statusCode'] == 200
        assert 'successfully' in result['body']
        
        # Verify S3 put_object was called
        mock_s3_client.put_object.assert_called_once()
        call_args = mock_s3_client.put_object.call_args[1]
        assert call_args['Bucket'] == 'transformed-bucket'
        assert 'cloudfront-logs' in call_args['Key']
        assert '2024/01/15' in call_args['Key']  # Should use date from data for partitioning
        assert call_args['Key'].endswith('.parquet')
        assert 'ContentType' not in call_args  # Should not have ContentType

    @patch.dict('os.environ', {
        'S3_BUCKET_NAME_TRANSFORMED': 'transformed-bucket',
        'S3_OBJECT_PREFIX': 'platform/gc-design-system'
    })
    @patch('main.boto3.client')
    def test_handler_skip_non_gz(self, mock_boto3):
        # Mock S3 client
        mock_s3_client = MagicMock()
        mock_boto3.return_value = mock_s3_client
        
        # Create event with non-gz file
        event = {
            'Records': [{
                's3': {
                    'bucket': {'name': 'source-bucket'},
                    'object': {'key': 'path/to/textfile.txt'}
                }
            }]
        }
        
        # Test the handler
        result = handler(event, {})
        
        # Should succeed but not process anything
        assert result['statusCode'] == 200
        
        # Should not call put_object
        mock_s3_client.put_object.assert_not_called()
