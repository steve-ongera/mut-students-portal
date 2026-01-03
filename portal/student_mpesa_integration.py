# student_mpesa_integration.py
"""
M-Pesa Integration for Student ID Card Payments
Separate from other M-Pesa integrations in the project
"""

import requests
import base64
from datetime import datetime
from django.conf import settings
from django.utils import timezone
import json


class StudentIDMpesaIntegration:
    """Handle M-Pesa STK Push for Student ID payments"""
    
    def __init__(self):
        # M-Pesa credentials - Add these to your settings.py
        self.consumer_key = getattr(settings, 'STUDENT_ID_MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'STUDENT_ID_MPESA_CONSUMER_SECRET', '')
        self.business_shortcode = getattr(settings, 'STUDENT_ID_MPESA_SHORTCODE', '')
        self.passkey = getattr(settings, 'STUDENT_ID_MPESA_PASSKEY', '')
        self.callback_url = getattr(settings, 'STUDENT_ID_MPESA_CALLBACK_URL', '')
        
        # API URLs
        self.auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        self.stk_push_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
        self.query_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query'
        
        # For production, use these URLs:
        # self.auth_url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        # self.stk_push_url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    
    def get_access_token(self):
        """Get OAuth access token from M-Pesa"""
        try:
            # Create base64 encoded string of consumer_key:consumer_secret
            credentials = f"{self.consumer_key}:{self.consumer_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}'
            }
            
            response = requests.get(self.auth_url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return result.get('access_token')
            
        except Exception as e:
            print(f"Error getting access token: {str(e)}")
            return None
    
    def generate_password(self, timestamp):
        """Generate password for M-Pesa request"""
        data_to_encode = f"{self.business_shortcode}{self.passkey}{timestamp}"
        encoded_string = base64.b64encode(data_to_encode.encode()).decode()
        return encoded_string
    
    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Initiate STK Push to customer's phone
        
        Args:
            phone_number: Customer phone number (format: 254XXXXXXXXX)
            amount: Amount to charge
            account_reference: Unique reference for the transaction
            transaction_desc: Description of the transaction
            
        Returns:
            dict: Response from M-Pesa API or None if failed
        """
        try:
            # Get access token
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'error': 'Failed to get access token'}
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Generate password
            password = self.generate_password(timestamp)
            
            # Format phone number
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+'):
                phone_number = phone_number[1:]
            elif phone_number.startswith('7') or phone_number.startswith('1'):
                phone_number = '254' + phone_number
            
            # Prepare request headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Prepare request payload
            payload = {
                'BusinessShortCode': self.business_shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(float(amount)),  # Convert to integer
                'PartyA': phone_number,
                'PartyB': self.business_shortcode,
                'PhoneNumber': phone_number,
                'CallBackURL': self.callback_url,
                'AccountReference': account_reference,
                'TransactionDesc': transaction_desc
            }
            
            # Make request
            response = requests.post(
                self.stk_push_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Check if request was successful
            if result.get('ResponseCode') == '0':
                return {
                    'success': True,
                    'merchant_request_id': result.get('MerchantRequestID'),
                    'checkout_request_id': result.get('CheckoutRequestID'),
                    'response_code': result.get('ResponseCode'),
                    'response_description': result.get('ResponseDescription'),
                    'customer_message': result.get('CustomerMessage')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('ResponseDescription', 'Unknown error'),
                    'response_code': result.get('ResponseCode')
                }
                
        except requests.exceptions.RequestException as e:
            print(f"M-Pesa API request error: {str(e)}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            print(f"M-Pesa STK Push error: {str(e)}")
            return {
                'success': False,
                'error': f'Error: {str(e)}'
            }
    
    def query_transaction(self, checkout_request_id):
        """
        Query the status of an STK Push transaction
        
        Args:
            checkout_request_id: CheckoutRequestID from initial STK push
            
        Returns:
            dict: Transaction status
        """
        try:
            # Get access token
            access_token = self.get_access_token()
            if not access_token:
                return {'success': False, 'error': 'Failed to get access token'}
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # Generate password
            password = self.generate_password(timestamp)
            
            # Prepare request headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Prepare request payload
            payload = {
                'BusinessShortCode': self.business_shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }
            
            # Make request
            response = requests.post(
                self.query_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                'success': True,
                'result_code': result.get('ResultCode'),
                'result_desc': result.get('ResultDesc'),
                'response_code': result.get('ResponseCode')
            }
            
        except Exception as e:
            print(f"M-Pesa query error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


def process_student_id_mpesa_callback(callback_data):
    """
    Process M-Pesa callback for student ID payments
    
    Args:
        callback_data: Dictionary containing callback data from M-Pesa
        
    Returns:
        dict: Processing result
    """
    from .models import StudentIDPayment, StudentIDApplication, IDCardNotification
    
    try:
        # Extract data from callback
        body = callback_data.get('Body', {}).get('stkCallback', {})
        
        merchant_request_id = body.get('MerchantRequestID')
        checkout_request_id = body.get('CheckoutRequestID')
        result_code = body.get('ResultCode')
        result_desc = body.get('ResultDesc')
        
        # Find payment record
        try:
            payment = StudentIDPayment.objects.get(
                checkout_request_id=checkout_request_id
            )
        except StudentIDPayment.DoesNotExist:
            return {
                'success': False,
                'error': 'Payment record not found'
            }
        
        # Process based on result code
        if result_code == 0:  # Success
            # Extract callback metadata
            callback_metadata = body.get('CallbackMetadata', {}).get('Item', [])
            mpesa_receipt = None
            transaction_date = None
            
            for item in callback_metadata:
                if item.get('Name') == 'MpesaReceiptNumber':
                    mpesa_receipt = item.get('Value')
                elif item.get('Name') == 'TransactionDate':
                    transaction_date = item.get('Value')
            
            # Update payment
            payment.status = 'completed'
            payment.mpesa_receipt_number = mpesa_receipt or f"MPX{payment.id:08d}"
            payment.result_code = str(result_code)
            payment.result_description = result_desc
            payment.confirmed_date = timezone.now()
            payment.save()
            
            # Update application
            application = payment.application
            application.amount_paid += payment.amount
            application.payment_reference = payment.payment_reference
            application.payment_date = timezone.now()
            
            if application.amount_paid >= application.amount_due:
                application.status = 'payment_confirmed'
            
            application.save()
            
            # Send notification
            IDCardNotification.objects.create(
                student=application.student,
                application=application,
                notification_type='payment_confirmed',
                title='Payment Confirmed',
                message=f'Your payment of KES {payment.amount:,.2f} for Student ID application #{application.application_number} has been confirmed. Receipt: {mpesa_receipt}',
                sent_via_portal=True,
                sent_via_email=True,
                sent_via_sms=True
            )
            
            return {
                'success': True,
                'message': 'Payment processed successfully'
            }
            
        else:  # Failed or cancelled
            payment.status = 'failed'
            payment.result_code = str(result_code)
            payment.result_description = result_desc
            payment.save()
            
            # Send notification
            IDCardNotification.objects.create(
                student=payment.application.student,
                application=payment.application,
                notification_type='payment_failed',
                title='Payment Failed',
                message=f'Your M-Pesa payment for application #{payment.application.application_number} failed. Reason: {result_desc}',
                sent_via_portal=True,
                sent_via_email=True
            )
            
            return {
                'success': True,
                'message': 'Payment failure processed'
            }
            
    except Exception as e:
        print(f"Callback processing error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


