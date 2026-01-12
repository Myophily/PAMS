from sqlalchemy.orm import Session
from app.models.recurring_transfer import RecurringTransfer
from app.models.account import Account
from app.services.transaction_service import TransactionService
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from typing import List, Optional
import calendar
from app.utils.timezone import now_kst


class RecurringTransferService:
    """
    Service for managing recurring transfers.

    Handles creation, execution, and management of recurring monthly transfers.
    Integrates with APScheduler to execute transfers automatically.
    """

    def __init__(self):
        self.transaction_service = TransactionService()

    def create_recurring_transfer(
        self,
        from_account_id: int,
        to_account_id: Optional[int],  # None = external transfer
        amount: Decimal,
        day_of_month: int,
        description: Optional[str],
        db: Session
    ) -> RecurringTransfer:
        """
        Create a new recurring transfer rule.

        Args:
            from_account_id: Source account ID
            to_account_id: Target account ID (None = external transfer)
            amount: Transfer amount (must be positive)
            day_of_month: Day of month to execute (1-31)
            description: Optional user notes (required for external transfers)
            db: Database session

        Returns:
            Created RecurringTransfer object

        Raises:
            ValueError: If validation fails
        """
        # Validate from account exists
        from_account = db.query(Account).get(from_account_id)
        if not from_account:
            raise ValueError(f"From account {from_account_id} not found")

        # Branch validation based on transfer type
        if to_account_id is None:
            # External transfer - validate Withdrawal is allowed
            from app.services.transaction_validation import validate_transaction_type
            validate_transaction_type(from_account.type, "Withdrawal")

            # Description is REQUIRED for external transfers
            if not description or description.strip() == "":
                raise ValueError("Description is required for external transfers")

            destination_name = "External"
        else:
            # Internal transfer - validate both accounts
            to_account = db.query(Account).get(to_account_id)
            if not to_account:
                raise ValueError(f"To account {to_account_id} not found")

            if from_account_id == to_account_id:
                raise ValueError("Cannot transfer to the same account")

            # Validate account types
            from app.services.transaction_validation import validate_transaction_type
            validate_transaction_type(from_account.type, "Transfer_Out")
            validate_transaction_type(to_account.type, "Transfer_In")

            destination_name = to_account.name

        # Create recurring transfer
        recurring = RecurringTransfer(
            from_account_id=from_account_id,
            to_account_id=to_account_id,  # May be None
            amount=amount,
            day_of_month=day_of_month,
            description=description,
            is_active=True,
            last_executed_date=None
        )
        db.add(recurring)
        db.commit()
        db.refresh(recurring)

        print(f"[RecurringTransfer] Created: {recurring.id} ({from_account.name} → {destination_name}, {amount} KRW, day {day_of_month})")
        return recurring

    def execute_recurring_transfer(
        self,
        recurring_id: int,
        execution_date: datetime,
        db: Session
    ) -> bool:
        """
        Execute a single recurring transfer.

        Args:
            recurring_id: RecurringTransfer ID
            execution_date: Date to execute the transfer
            db: Database session

        Returns:
            True if executed successfully, False otherwise
        """
        recurring = db.query(RecurringTransfer).filter(
            RecurringTransfer.id == recurring_id,
            RecurringTransfer.is_active == True,
            RecurringTransfer.deleted_at.is_(None)
        ).first()

        if not recurring:
            print(f"[RecurringTransfer] Recurring transfer {recurring_id} not found or inactive")
            return False

        # Check if already executed this month
        if recurring.last_executed_date:
            last_exec = recurring.last_executed_date
            if (last_exec.year == execution_date.year and
                last_exec.month == execution_date.month):
                print(f"[RecurringTransfer] Already executed this month: {recurring_id}")
                return False

        # Branch: External vs Internal transfer
        try:
            if recurring.to_account_id is None:
                # PATTERN ① - External withdrawal
                tx = self.transaction_service.create_withdrawal(
                    account_id=recurring.from_account_id,
                    amount=recurring.amount,
                    transaction_date=execution_date,
                    description=f"[Recurring] {recurring.description or 'External payment'}",
                    db=db
                )
                print(f"[RecurringTransfer] Executed external withdrawal: {recurring.id} → Tx {tx.id}")
            else:
                # PATTERN ② - Internal transfer
                tx_out, tx_in = self.transaction_service.create_transfer(
                    from_account_id=recurring.from_account_id,
                    to_account_id=recurring.to_account_id,
                    amount=recurring.amount,
                    transaction_date=execution_date,
                    description=f"[Recurring] {recurring.description or 'Monthly transfer'}",
                    db=db
                )
                print(f"[RecurringTransfer] Executed internal transfer: {recurring.id} → Tx {tx_out.id}, {tx_in.id}")

            # Update last_executed_date
            recurring.last_executed_date = execution_date
            db.commit()

            return True

        except Exception as e:
            db.rollback()
            print(f"[RecurringTransfer] Failed to execute {recurring_id}: {str(e)}")
            return False

    def check_and_execute_due_transfers(self, db: Session):
        """
        Check all active recurring transfers and execute if due.

        This method is called daily by the scheduler.

        Args:
            db: Database session
        """
        now = now_kst()
        today = now.date()

        # Get all active recurring transfers
        recurring_transfers = db.query(RecurringTransfer).filter(
            RecurringTransfer.is_active == True,
            RecurringTransfer.deleted_at.is_(None)
        ).all()

        print(f"[RecurringTransfer] Checking {len(recurring_transfers)} active transfers")

        for recurring in recurring_transfers:
            # Determine execution date for this month
            execution_day = self._get_execution_day(recurring.day_of_month, today.year, today.month)
            execution_date = datetime(today.year, today.month, execution_day, 0, 0, 0)

            # Check if execution date has passed and not yet executed this month
            should_execute = False

            if today.day >= execution_day:
                # We're past the execution day this month
                if recurring.last_executed_date is None:
                    should_execute = True
                else:
                    last_exec = recurring.last_executed_date
                    if not (last_exec.year == today.year and last_exec.month == today.month):
                        should_execute = True

            if should_execute:
                self.execute_recurring_transfer(recurring.id, execution_date, db)

    def catch_up_missed_transfers(self, db: Session):
        """
        Execute missed transfers since last app run.

        This method is called on application startup to catch up any transfers
        that should have been executed while the app was not running.

        Args:
            db: Database session
        """
        now = now_kst()
        today = now.date()

        recurring_transfers = db.query(RecurringTransfer).filter(
            RecurringTransfer.is_active == True,
            RecurringTransfer.deleted_at.is_(None)
        ).all()

        print(f"[RecurringTransfer] Running catch-up for {len(recurring_transfers)} active transfers")

        for recurring in recurring_transfers:
            if recurring.last_executed_date is None:
                # Never executed - check if should have executed in current month
                execution_day = self._get_execution_day(recurring.day_of_month, today.year, today.month)
                if today.day >= execution_day:
                    execution_date = datetime(today.year, today.month, execution_day, 0, 0, 0)
                    self.execute_recurring_transfer(recurring.id, execution_date, db)
            else:
                # Check for missed months
                last_exec = recurring.last_executed_date.date()
                current_check = last_exec + relativedelta(months=1)

                while current_check <= today:
                    execution_day = self._get_execution_day(
                        recurring.day_of_month,
                        current_check.year,
                        current_check.month
                    )
                    execution_date = datetime(current_check.year, current_check.month, execution_day, 0, 0, 0)

                    # Only execute if the execution day has passed
                    if execution_date.date() <= today:
                        self.execute_recurring_transfer(recurring.id, execution_date, db)

                    current_check += relativedelta(months=1)

    def load_and_schedule_all(self, db: Session, scheduler):
        """
        Load all active recurring transfers and schedule them.

        This method is called on application startup to initialize the scheduler.

        Args:
            db: Database session
            scheduler: APScheduler instance
        """
        # Run catch-up first
        self.catch_up_missed_transfers(db)

        # Schedule daily check job (runs at 00:01 AM every day)
        scheduler.add_job(
            func=lambda: self._scheduled_check(db),
            trigger='cron',
            hour=0,
            minute=1,
            id='recurring_transfer_daily_check',
            replace_existing=True
        )

        print("[RecurringTransfer] Scheduler initialized - daily check at 00:01 AM")

    def _scheduled_check(self, db: Session):
        """Scheduled job that checks and executes due transfers."""
        print(f"[RecurringTransfer] Running scheduled check at {now_kst()}")
        self.check_and_execute_due_transfers(db)

    def _get_execution_day(self, day_of_month: int, year: int, month: int) -> int:
        """
        Get the actual execution day, handling months with fewer days.

        For example, if day_of_month is 31 but the month only has 30 days,
        returns 30. For February with 28/29 days, returns the last day.

        Args:
            day_of_month: Desired day of month (1-31)
            year: Year
            month: Month (1-12)

        Returns:
            Actual execution day for the month
        """
        max_day = calendar.monthrange(year, month)[1]
        return min(day_of_month, max_day)

    def _calculate_next_execution(self, recurring: RecurringTransfer) -> Optional[datetime]:
        """
        Calculate the next execution date for a recurring transfer.

        Args:
            recurring: RecurringTransfer object

        Returns:
            Next execution date or None if inactive
        """
        if not recurring.is_active or recurring.deleted_at:
            return None

        today = date.today()

        # Determine if this month's execution is still pending
        execution_day_this_month = self._get_execution_day(recurring.day_of_month, today.year, today.month)

        if today.day < execution_day_this_month:
            # This month's execution hasn't happened yet
            return datetime(today.year, today.month, execution_day_this_month, 0, 0, 0)
        else:
            # Check if already executed this month
            if recurring.last_executed_date:
                last_exec = recurring.last_executed_date
                if last_exec.year == today.year and last_exec.month == today.month:
                    # Already executed this month, next is next month
                    next_month = today + relativedelta(months=1)
                    execution_day = self._get_execution_day(recurring.day_of_month, next_month.year, next_month.month)
                    return datetime(next_month.year, next_month.month, execution_day, 0, 0, 0)

            # Not executed this month yet
            return datetime(today.year, today.month, execution_day_this_month, 0, 0, 0)

    def list_recurring_transfers(
        self,
        db: Session,
        account_id: Optional[int] = None,
        include_inactive: bool = False
    ) -> List[RecurringTransfer]:
        """
        List recurring transfers with filtering.

        Args:
            db: Database session
            account_id: Optional account ID to filter by (from or to)
            include_inactive: Whether to include inactive transfers

        Returns:
            List of RecurringTransfer objects
        """
        query = db.query(RecurringTransfer).filter(
            RecurringTransfer.deleted_at.is_(None)
        )

        if account_id:
            query = query.filter(
                (RecurringTransfer.from_account_id == account_id) |
                (RecurringTransfer.to_account_id == account_id)
            )

        if not include_inactive:
            query = query.filter(RecurringTransfer.is_active == True)

        return query.order_by(RecurringTransfer.created_at.desc()).all()

    def update_recurring_transfer(
        self,
        recurring_id: int,
        amount: Optional[Decimal],
        day_of_month: Optional[int],
        description: Optional[str],
        is_active: Optional[bool],
        db: Session
    ) -> RecurringTransfer:
        """
        Update an existing recurring transfer.

        Args:
            recurring_id: RecurringTransfer ID
            amount: New amount (optional)
            day_of_month: New day of month (optional)
            description: New description (optional)
            is_active: New active status (optional)
            db: Database session

        Returns:
            Updated RecurringTransfer object

        Raises:
            ValueError: If recurring transfer not found
        """
        recurring = db.query(RecurringTransfer).get(recurring_id)
        if not recurring or recurring.deleted_at:
            raise ValueError(f"Recurring transfer {recurring_id} not found")

        if amount is not None:
            recurring.amount = amount
        if day_of_month is not None:
            recurring.day_of_month = day_of_month
        if description is not None:
            recurring.description = description
        if is_active is not None:
            recurring.is_active = is_active

        db.commit()
        db.refresh(recurring)

        print(f"[RecurringTransfer] Updated: {recurring.id}")
        return recurring

    def delete_recurring_transfer(self, recurring_id: int, db: Session):
        """
        Soft delete a recurring transfer.

        Args:
            recurring_id: RecurringTransfer ID
            db: Database session

        Raises:
            ValueError: If recurring transfer not found
        """
        recurring = db.query(RecurringTransfer).get(recurring_id)
        if not recurring or recurring.deleted_at:
            raise ValueError(f"Recurring transfer {recurring_id} not found")

        recurring.deleted_at = now_kst()
        db.commit()

        print(f"[RecurringTransfer] Deleted: {recurring.id}")
