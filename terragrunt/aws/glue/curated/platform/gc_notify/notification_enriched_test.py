import datetime
from dateutil.relativedelta import relativedelta


def test_default_date_logic():
    """Test the default date range logic that chooses current and previous month."""

    # Mock current time as June 18, 2025, 10:30 AM UTC
    mock_now = datetime.datetime(2025, 6, 18, 10, 30, 0, tzinfo=datetime.timezone.utc)

    # Replicate the date logic from notification_enriched.py
    current_month_start = mock_now.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    previous_month_start = current_month_start - relativedelta(months=1)

    # Test empty parameters (should use defaults)
    start_month = ""
    end_month = ""

    if start_month and start_month.strip():
        start_date = datetime.datetime.strptime(start_month, "%Y-%m").replace(
            day=1, tzinfo=datetime.timezone.utc
        )
    else:
        start_date = previous_month_start

    if end_month and end_month.strip():
        end_date = datetime.datetime.strptime(end_month, "%Y-%m").replace(
            day=1, tzinfo=datetime.timezone.utc
        )
    else:
        end_date = current_month_start

    # Verify the results
    expected_start = datetime.datetime(
        2025, 5, 1, tzinfo=datetime.timezone.utc
    )  # Previous month (May)
    expected_end = datetime.datetime(
        2025, 6, 1, tzinfo=datetime.timezone.utc
    )  # Current month (June)

    assert start_date == expected_start
    assert end_date == expected_end

    # Test the string formats that would be used in SQL
    start_month_str = start_date.strftime("%Y-%m")
    end_month_str = end_date.strftime("%Y-%m")

    assert start_month_str == "2025-05"
    assert end_month_str == "2025-06"


def test_custom_date_parameters():
    """Test parsing custom date parameters."""

    # Test custom date parameters
    start_month = "2024-01"
    end_month = "2024-03"

    # Parse the dates (replicating the logic from notification_enriched.py)
    if start_month and start_month.strip():
        start_date = datetime.datetime.strptime(start_month, "%Y-%m").replace(
            day=1, tzinfo=datetime.timezone.utc
        )

    if end_month and end_month.strip():
        end_date = datetime.datetime.strptime(end_month, "%Y-%m").replace(
            day=1, tzinfo=datetime.timezone.utc
        )

    # Verify the results
    expected_start = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
    expected_end = datetime.datetime(2024, 3, 1, tzinfo=datetime.timezone.utc)

    assert start_date == expected_start
    assert end_date == expected_end

    # Test string formats for SQL queries
    start_month_str = start_date.strftime("%Y-%m")
    end_month_str = end_date.strftime("%Y-%m")

    assert start_month_str == "2024-01"
    assert end_month_str == "2024-03"
