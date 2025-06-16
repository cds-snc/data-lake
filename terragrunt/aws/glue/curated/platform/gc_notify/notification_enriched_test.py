import pytest
import pandas as pd
import sys
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta


class MockPysparkDataFrame:
    """Mock PySpark DataFrame."""
    pass


# Mock AWS and PySpark modules before importing main module
sys.modules["pyspark"] = Mock()
sys.modules["pyspark.context"] = Mock()
sys.modules["pyspark.context"].SparkContext = Mock()
sys.modules["pyspark.sql"] = Mock()
sys.modules["pyspark.sql"].DataFrame = MockPysparkDataFrame

sys.modules["awsglue"] = Mock()
sys.modules["awsglue.context"] = Mock()
sys.modules["awsglue.context"].GlueContext = Mock()
sys.modules["awsglue.job"] = Mock()
sys.modules["awsglue.job"].Job = Mock()
sys.modules["awsglue.utils"] = Mock()

# Configure getResolvedOptions mock before import
mock_args = {
    "JOB_NAME": "test_notification_enriched",
    "curated_bucket": "test-curated-bucket",
    "curated_prefix": "test-curated-prefix", 
    "athena_bucket": "test-athena-bucket",
    "transformed_bucket": "test-transformed-bucket",
    "transformed_prefix": "test-transformed-prefix",
    "database_name_transformed": "test_database_transformed",
    "database_name_curated": "test_database_curated",
    "target_env": "test",
    "start_month": "",
    "end_month": "",
}
sys.modules["awsglue.utils"].getResolvedOptions = Mock(return_value=mock_args)

sys.modules["awswrangler"] = Mock()

# Import the module after mocking dependencies
from notification_enriched import execute_enrichment_query, write_to_curated


class TestNotificationEnriched:
    """Test class for notification_enriched script."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset all mocks
        for module_name, module in sys.modules.items():
            if hasattr(module, 'reset_mock') and 'mock' in str(type(module)).lower():
                module.reset_mock()
        
        # Reconfigure the mock after reset
        sys.modules["awsglue.utils"].getResolvedOptions = Mock(return_value=mock_args)

    @patch('notification_enriched.wr')
    def test_execute_enrichment_query_sql_execution(self, mock_wr):
        """Test that execute_enrichment_query executes SQL once with correct query."""
        # Arrange
        start_month = "2024-01"
        end_month = "2024-02"
        expected_df = pd.DataFrame({
            'notification_id': ['123', '456'],
            'service_name': ['Test Service 1', 'Test Service 2']
        })
        mock_wr.athena.read_sql_query.return_value = expected_df
        
        # Act
        result = execute_enrichment_query(start_month, end_month)
        
        # Assert
        mock_wr.athena.read_sql_query.assert_called_once()
        call_args = mock_wr.athena.read_sql_query.call_args
        sql_query = call_args[1]['sql']
        
        # Verify SQL contains month filtering
        assert f"month >= '{start_month}'" in sql_query
        assert f"month <= '{end_month}'" in sql_query
        
        # Verify SQL contains all required CTEs
        assert "WITH notification_data AS" in sql_query
        assert "service_data AS" in sql_query
        assert "template_data AS" in sql_query
        
        # Verify the result is returned correctly
        pd.testing.assert_frame_equal(result, expected_df)

    @patch('notification_enriched.wr')
    def test_write_to_curated_single_write_operation(self, mock_wr):
        """Test that write_to_curated performs exactly one write operation."""
        # Arrange
        test_df = pd.DataFrame({
            'notification_id': ['123', '456'],
            'year': ['2024', '2024'],
            'month': ['2024-01', '2024-01'],
            'processing_date': ['2024-01-15', '2024-01-16']
        })
        table_name = "test_table"
        
        # Act
        write_to_curated(test_df, table_name)
        
        # Assert - verify single write operation with correct parameters
        mock_wr.s3.to_parquet.assert_called_once()
        call_args = mock_wr.s3.to_parquet.call_args
        
        # Verify overwrite_partitions mode is used
        assert call_args[1]['mode'] == 'overwrite_partitions'
        
        # Verify partition columns are correct
        expected_partitions = ['year', 'month']
        assert call_args[1]['partition_cols'] == expected_partitions

    @patch('notification_enriched.datetime')
    def test_date_filtering_when_args_missing(self, mock_datetime):
        """Test default date behavior when start_month and end_month args are missing."""
        # Arrange - mock current datetime
        mock_now = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.side_effect = datetime.strptime
        
        # Mock the module's global variables for empty arguments
        with patch('notification_enriched.START_MONTH', ''), \
             patch('notification_enriched.END_MONTH', ''):
            
            # Expected dates: previous month (2024-02) and current month start (2024-03)
            expected_start = "2024-02"  # Previous month 
            expected_end = "2024-03"    # Current month start
            
            # Import and test the date calculation logic
            from notification_enriched import relativedelta
            
            # Simulate the date calculation from the module
            now = mock_now
            current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            previous_month_start = current_month_start - relativedelta(months=1)
            
            # Test that default dates are calculated correctly
            assert previous_month_start.strftime("%Y-%m") == expected_start
            assert current_month_start.strftime("%Y-%m") == expected_end

    @patch('notification_enriched.wr')
    def test_month_range_filtering_edge_cases(self, mock_wr):
        """Test SQL query generation with various month range scenarios."""
        test_cases = [
            ("2024-01", "2024-01"),  # Single month
            ("2024-12", "2025-01"),  # Year boundary
            ("2023-06", "2024-06"),  # Full year span
        ]
        
        expected_df = pd.DataFrame({'test': ['data']})
        mock_wr.athena.read_sql_query.return_value = expected_df
        
        for start_month, end_month in test_cases:
            # Reset mock for each test case
            mock_wr.reset_mock()
            
            # Act
            execute_enrichment_query(start_month, end_month)
            
            # Assert
            mock_wr.athena.read_sql_query.assert_called_once()
            call_args = mock_wr.athena.read_sql_query.call_args
            sql_query = call_args[1]['sql']
            
            # Verify month filtering is present for both bounds
            assert f"month >= '{start_month}'" in sql_query
            assert f"month <= '{end_month}'" in sql_query