#!/usr/bin/env python
"""
Standalone tests for webhook processor functions
"""
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


def is_checkin_date_older_than_one_month(check_in_date_str):
    """Check if the check-in date is older than 1 month from now"""
    if not check_in_date_str:
        return False
        
    check_in_date = datetime.strptime(check_in_date_str, "%Y-%m-%d")
    one_month_ago = datetime.now() - timedelta(days=30)
    return check_in_date < one_month_ago


def process_new_transactions(reservation_dto, track_log, send_transaction_func):
    """Process new transactions for a reservation"""
    # Send receivable transaction
    receivable_transaction = send_transaction_func(reservation_dto, "receivable")
    track_log.append({"send_transaction_receivable": receivable_transaction})
    
    # Send operational transaction
    operational_transaction = send_transaction_func(reservation_dto, "operational")
    track_log.append({"send_transaction_operational": operational_transaction})
    
    # Send commission transaction if needed
    if reservation_dto["partner_name"] == "API booking.com" and reservation_dto["total_paid"] == 0:
        comission_transaction = send_transaction_func(reservation_dto, "comission")
        track_log.append({"send_transaction_comission": comission_transaction})


class TestWebhookProcessorFunctions(unittest.TestCase):
    """Unit tests for webhook processor functions"""

    def test_is_checkin_date_older_than_one_month(self):
        """Test the function that checks if check-in date is older than one month"""
        # Test with a future date
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        self.assertFalse(is_checkin_date_older_than_one_month(future_date))
        
        # Test with a past date (older than one month)
        past_date = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d")
        self.assertTrue(is_checkin_date_older_than_one_month(past_date))
        
        # Test with None
        self.assertFalse(is_checkin_date_older_than_one_month(None))
    
    def test_process_new_transactions_standard(self):
        """Test processing new transactions for a standard reservation"""
        # Set up mock
        mock_send_transaction = MagicMock(return_value={"transaction": "data"})
        
        # Test with a standard reservation
        reservation_dto_standard = {
            "partner_name": "website",
            "total_paid": 1000
        }
        track_log = []
        
        process_new_transactions(reservation_dto_standard, track_log, mock_send_transaction)
        
        # Should call send_transaction twice for standard reservations
        self.assertEqual(mock_send_transaction.call_count, 2)
        self.assertEqual(len(track_log), 2)
        mock_send_transaction.assert_any_call(reservation_dto_standard, "receivable")
        mock_send_transaction.assert_any_call(reservation_dto_standard, "operational")
    
    def test_process_new_transactions_booking_unpaid(self):
        """Test processing new transactions for an unpaid Booking.com reservation"""
        # Set up mock
        mock_send_transaction = MagicMock(return_value={"transaction": "data"})
        
        # Test with an unpaid Booking.com reservation
        reservation_dto_booking = {
            "partner_name": "API booking.com",
            "total_paid": 0
        }
        track_log = []
        
        process_new_transactions(reservation_dto_booking, track_log, mock_send_transaction)
        
        # Should call send_transaction three times for unpaid Booking.com reservations
        self.assertEqual(mock_send_transaction.call_count, 3)
        self.assertEqual(len(track_log), 3)
        mock_send_transaction.assert_any_call(reservation_dto_booking, "receivable")
        mock_send_transaction.assert_any_call(reservation_dto_booking, "operational")
        mock_send_transaction.assert_any_call(reservation_dto_booking, "comission")


if __name__ == "__main__":
    unittest.main() 