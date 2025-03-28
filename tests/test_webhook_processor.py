import sys
import os
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Add the parent directory to sys.path to allow for importing the API modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from api.webhook_processor import (
    process_webhook_request,
    process_modified_reservation,
    process_deleted_reservation,
    is_checkin_date_older_than_one_month,
    process_new_transactions
)
from .mocks.reservations import (
    get_sample_reservation_data,
    get_sample_reservation_report,
    get_sample_reservation_dto
)

# Fixtures
@pytest.fixture
def sample_webhook_data():
    return get_sample_reservation_data()

@pytest.fixture
def sample_reservation_report():
    return get_sample_reservation_report()

@pytest.fixture
def sample_reservation_dto():
    return get_sample_reservation_dto()

class TestWebhookProcessor:

    @patch('api.webhook_processor.process_modified_reservation')
    async def test_process_webhook_request_modified(self, mock_process_modified, sample_webhook_data, async_db_session_factory):
        """Test processing a modified reservation webhook"""
        mock_process_modified.return_value = {"status": "processed"}
        
        result = await process_webhook_request(sample_webhook_data, async_db_session_factory)
        
        assert result == {"status": "processed"}
        mock_process_modified.assert_called_once()

    @patch('api.webhook_processor.process_deleted_reservation')
    async def test_process_webhook_request_deleted(self, mock_process_deleted, sample_webhook_data, async_db_session_factory):
        """Test processing a deleted reservation webhook"""
        sample_webhook_data["action"] = "reservation.deleted"
        mock_process_deleted.return_value = {"status": "processed"}
        
        result = await process_webhook_request(sample_webhook_data, async_db_session_factory)
        
        assert result == {"status": "processed"}
        mock_process_deleted.assert_called_once()

    @patch('api.webhook_processor.create_log')
    async def test_process_webhook_request_created(self, mock_create_log, sample_webhook_data, async_db_session_factory):
        """Test processing a created reservation webhook"""
        sample_webhook_data["action"] = "reservation.created"
        
        result = await process_webhook_request(sample_webhook_data, async_db_session_factory)
        
        assert result == {"status": "logged"}
        mock_create_log.assert_called_once()

    async def test_process_webhook_request_unsupported_action(self, sample_webhook_data, async_db_session_factory):
        """Test processing an unsupported action webhook"""
        sample_webhook_data["action"] = "reservation.unsupported"
        
        result = await process_webhook_request(sample_webhook_data, async_db_session_factory)
        
        assert result["status"] == "ignored"
        assert "Unsupported action" in result["reason"]

    async def test_process_webhook_request_error(self, sample_webhook_data, mock_db_session, async_db_session_factory):
        """Test processing a webhook that raises an exception"""
        mock_db_session.close.side_effect = Exception("Test exception")
        
        result = await process_webhook_request(sample_webhook_data, async_db_session_factory)
        
        assert result["status"] == "error"
        assert "Test exception" in result["error"]

    @patch('api.webhook_processor.get_reservation_report')
    @patch('api.webhook_processor.create_reservation_dto')
    @patch('api.webhook_processor.calculate_expedia')
    @patch('api.webhook_processor.check_transaction_created')
    @patch('api.webhook_processor.process_new_transactions')
    @patch('api.webhook_processor.update_transaction')
    @patch('api.webhook_processor.create_log')
    async def test_process_modified_reservation_new_transaction(
        self, mock_create_log, mock_update_transaction, mock_process_new, 
        mock_check_created, mock_calculate_expedia, mock_create_dto, mock_get_report,
        sample_webhook_data, mock_db_session, sample_reservation_report, sample_reservation_dto
    ):
        """Test processing a modified reservation that requires new transactions"""
        mock_get_report.return_value = sample_reservation_report
        mock_create_dto.return_value = sample_reservation_dto
        mock_calculate_expedia.return_value = sample_reservation_dto
        mock_check_created.return_value = False
        
        result = await process_modified_reservation(sample_webhook_data, mock_db_session, [])
        
        assert result == {"status": "processed"}
        mock_process_new.assert_called_once_with(sample_reservation_dto, [])
        mock_update_transaction.assert_not_called()
        mock_create_log.assert_called_once()

    @patch('api.webhook_processor.get_reservation_report')
    @patch('api.webhook_processor.create_reservation_dto')
    @patch('api.webhook_processor.calculate_expedia')
    @patch('api.webhook_processor.check_transaction_created')
    @patch('api.webhook_processor.process_new_transactions')
    @patch('api.webhook_processor.update_transaction')
    @patch('api.webhook_processor.create_log')
    async def test_process_modified_reservation_update_transaction(
        self, mock_create_log, mock_update_transaction, mock_process_new, 
        mock_check_created, mock_calculate_expedia, mock_create_dto, mock_get_report,
        sample_webhook_data, mock_db_session, sample_reservation_report, sample_reservation_dto
    ):
        """Test processing a modified reservation that requires updating transactions"""
        mock_get_report.return_value = sample_reservation_report
        mock_create_dto.return_value = sample_reservation_dto
        mock_calculate_expedia.return_value = sample_reservation_dto
        mock_check_created.return_value = True
        mock_update_transaction.return_value = (True, [])
        
        result = await process_modified_reservation(sample_webhook_data, mock_db_session, [])
        
        assert result == {"status": "processed"}
        mock_process_new.assert_not_called()
        mock_update_transaction.assert_called_once_with(sample_reservation_report, sample_reservation_dto)
        mock_create_log.assert_called_once()

    @patch('api.webhook_processor.get_reservation_report')
    @patch('api.webhook_processor.create_log')
    async def test_process_modified_reservation_old_checkin(
        self, mock_create_log, mock_get_report,
        sample_webhook_data, mock_db_session
    ):
        """Test processing a modified reservation with an old check-in date"""
        old_date = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d")
        mock_get_report.return_value = {"checkInDate": old_date, "partnerName": "website"}
        
        result = await process_modified_reservation(sample_webhook_data, mock_db_session, [])
        
        assert result["status"] == "ignored"
        assert "check-in date older than 1 month" in result["reason"]
        mock_create_log.assert_called_once()

    @patch('api.webhook_processor.get_reservation_report')
    @patch('api.webhook_processor.delete_transaction')
    @patch('api.webhook_processor.create_log')
    async def test_process_deleted_reservation(
        self, mock_create_log, mock_delete_transaction, mock_get_report,
        sample_webhook_data, mock_db_session, sample_reservation_report
    ):
        """Test processing a deleted reservation"""
        sample_webhook_data["action"] = "reservation.deleted"
        mock_get_report.return_value = sample_reservation_report
        mock_delete_transaction.return_value = True
        
        result = await process_deleted_reservation(sample_webhook_data, mock_db_session, [])
        
        assert result == {"status": "processed"}
        mock_delete_transaction.assert_called_once_with(sample_webhook_data["payload"]["id"])
        mock_create_log.assert_called_once()

    @patch('api.webhook_processor.get_reservation_report')
    @patch('api.webhook_processor.create_log')
    async def test_process_deleted_reservation_old_checkin(
        self, mock_create_log, mock_get_report,
        sample_webhook_data, mock_db_session
    ):
        """Test processing a deleted reservation with an old check-in date"""
        sample_webhook_data["action"] = "reservation.deleted"
        old_date = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d")
        mock_get_report.return_value = {"checkInDate": old_date}
        
        result = await process_deleted_reservation(sample_webhook_data, mock_db_session, [])
        
        assert result["status"] == "ignored"
        assert "check-in date older than 1 month" in result["reason"]
        mock_create_log.assert_called_once()

    @patch('api.webhook_processor.send_transaction')
    def test_process_new_transactions_standard(self, mock_send_transaction, sample_reservation_dto):
        """Test processing new transactions for a standard reservation"""
        track_log = []
        mock_send_transaction.return_value = {"transaction": "data"}
        
        process_new_transactions(sample_reservation_dto, track_log)
        
        # Should call send_transaction twice for standard reservations
        assert mock_send_transaction.call_count == 2
        assert len(track_log) == 2
        mock_send_transaction.assert_any_call(sample_reservation_dto, "receivable")
        mock_send_transaction.assert_any_call(sample_reservation_dto, "operational")

    @patch('api.webhook_processor.send_transaction')
    def test_process_new_transactions_booking_unpaid(self, mock_send_transaction, sample_reservation_dto):
        """Test processing new transactions for an unpaid Booking.com reservation"""
        sample_reservation_dto["partner_name"] = "API booking.com"
        sample_reservation_dto["total_paid"] = 0
        track_log = []
        mock_send_transaction.return_value = {"transaction": "data"}
        
        process_new_transactions(sample_reservation_dto, track_log)
        
        # Should call send_transaction three times for unpaid Booking.com reservations
        assert mock_send_transaction.call_count == 3
        assert len(track_log) == 3
        mock_send_transaction.assert_any_call(sample_reservation_dto, "receivable")
        mock_send_transaction.assert_any_call(sample_reservation_dto, "operational")
        mock_send_transaction.assert_any_call(sample_reservation_dto, "comission")

    def test_is_checkin_date_older_than_one_month(self):
        """Test the function that checks if check-in date is older than one month"""
        # Test with a future date
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        assert not is_checkin_date_older_than_one_month(future_date)
        
        # Test with a past date (older than one month)
        past_date = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d")
        assert is_checkin_date_older_than_one_month(past_date)
        
        # Test with None
        assert not is_checkin_date_older_than_one_month(None) 