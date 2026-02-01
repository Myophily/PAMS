"""
Quick test to verify the recurring transfer scheduler fix.

This test verifies that _scheduled_check creates its own database session
instead of using a closed session from startup.
"""

import pytest
from unittest.mock import Mock
from app.services.recurring_transfer_service import RecurringTransferService
from app.models.recurring_transfer import RecurringTransfer
from decimal import Decimal
from datetime import date


class TestRecurringTransferSchedulerFix:
    """Test that the scheduler fix works correctly."""

    def test_scheduled_check_creates_own_session(self, db_session, checking_account):
        """
        Verify _scheduled_check creates its own session and doesn't depend on
        the startup session that gets closed.
        """
        service = RecurringTransferService()
        
        # Create a recurring transfer for the 1st of the month
        recurring = RecurringTransfer(
            from_account_id=checking_account.id,
            to_account_id=None,  # External transfer
            amount=Decimal("100000"),
            day_of_month=1,
            description="Test external payment",
            is_active=True,
            last_executed_date=None
        )
        db_session.add(recurring)
        db_session.commit()
        
        # Add initial balance using date object (not datetime)
        from app.services.transaction_service import TransactionService
        tx_service = TransactionService()
        tx_service.create_deposit(
            account_id=checking_account.id,
            amount=Decimal("500000"),
            transaction_date=date(2026, 2, 1),  # Use date, not datetime
            description="Initial balance",
            db=db_session
        )
        
        # Verify the recurring transfer is ready to execute
        assert recurring.last_executed_date is None
        
        # The key test: _scheduled_check should work even if we close this session
        # In the old code, it would fail because it captured this session in a lambda
        db_session.close()
        
        # Now call _scheduled_check - it should create its own session
        # This would fail with the old code because it tried to use the closed session
        try:
            service._scheduled_check()
            success = True
        except Exception as e:
            print(f"Error during scheduled check: {e}")
            success = False
        
        assert success, "_scheduled_check should work even when startup session is closed"

    def test_load_and_schedule_does_not_capture_session(self, db_session, checking_account):
        """
        Verify that load_and_schedule_all doesn't capture the db session in the lambda.
        
        The bug was that `lambda: self._scheduled_check(db)` captured the session,
        which then got closed after startup.
        """
        service = RecurringTransferService()
        
        # Create a mock scheduler
        mock_scheduler = Mock()
        mock_scheduler.add_job = Mock()
        
        # Call load_and_schedule_all
        service.load_and_schedule_all(db_session, mock_scheduler)
        
        # Verify add_job was called
        assert mock_scheduler.add_job.called, "add_job should have been called"
        
        # Get the call arguments
        call_args = mock_scheduler.add_job.call_args
        func = call_args[1]['func']  # Get the func argument
        
        # The fix: func should be the method directly, not a lambda
        assert func == service._scheduled_check, \
            "func should be the method directly, not a lambda capturing db session"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
