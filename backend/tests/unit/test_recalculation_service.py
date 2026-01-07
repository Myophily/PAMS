
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date
from decimal import Decimal
from app.services.recalculation_service import RecalculationService
from app.models.transaction import Transaction

class TestRecalculationService:
    """Test RecalculationService logic."""

    def test_recalculate_from_date_handles_datetime(self):
        """
        Test that passing a datetime object to recalculate_from_date
        correctly converts it to a date object for internal calls.
        This verifies the fix for: '>' not supported between instances of 'datetime.datetime' and 'datetime.date'
        """
        service = RecalculationService()
        mock_db = Mock()

        # Setup mock transactions to ensure logic proceeds to internal calls
        mock_tx = Mock(spec=Transaction)
        mock_tx.account_id = 1
        mock_tx.date = datetime(2024, 1, 1, 10, 0, 0)
        
        # Mock the query chain
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = [mock_tx]

        # Patch internal methods to verify arguments
        with patch.object(service, '_rebuild_holdings_for_account') as mock_rebuild, \
             patch.object(service, '_regenerate_snapshots_from_date') as mock_regenerate:
            
            # Input: datetime object
            input_datetime = datetime(2024, 1, 1, 14, 30, 0)
            
            # Call method
            service.recalculate_from_date(input_datetime, mock_db)

            # Verification 1: _rebuild_holdings_for_account called with date (not datetime)
            args, _ = mock_rebuild.call_args
            assert args[0] == 1  # account_id
            assert isinstance(args[1], date)
            assert not isinstance(args[1], datetime)
            assert args[1] == date(2024, 1, 1)

            # Verification 2: _regenerate_snapshots_from_date called with date (not datetime)
            args_gen, _ = mock_regenerate.call_args
            assert isinstance(args_gen[0], date)
            assert not isinstance(args_gen[0], datetime)
            assert args_gen[0] == date(2024, 1, 1)

    def test_recalculate_from_date_handles_date(self):
        """
        Test that passing a date object to recalculate_from_date works as expected.
        """
        service = RecalculationService()
        mock_db = Mock()

        # Setup mock transactions
        mock_tx = Mock(spec=Transaction)
        mock_tx.account_id = 1
        mock_tx.date = datetime(2024, 1, 1, 10, 0, 0)
        
        # Mock the query chain
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order_by = mock_filter.order_by.return_value
        mock_order_by.all.return_value = [mock_tx]

        with patch.object(service, '_rebuild_holdings_for_account') as mock_rebuild, \
             patch.object(service, '_regenerate_snapshots_from_date') as mock_regenerate:
            
            # Input: date object
            input_date = date(2024, 1, 1)
            
            # Call method
            service.recalculate_from_date(input_date, mock_db)

            # Verify it's passed through as date
            args, _ = mock_rebuild.call_args
            assert isinstance(args[1], date)
            assert args[1] == input_date

            args_gen, _ = mock_regenerate.call_args
            assert args_gen[0] == input_date

