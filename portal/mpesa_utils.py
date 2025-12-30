"""
M-Pesa STK Push Integration
For Safaricom M-Pesa Daraja API
"""
import requests
import base64
from datetime import datetime
from django.conf import settings
from django.utils import timezone
import logging

from portal.models import MpesaPayment

logger = logging.getLogger(__name__)


def get_mpesa_access_token():
    """Get M-Pesa OAuth access token"""
    try:
        consumer_key = settings.MPESA_CONSUMER_KEY
        consumer_secret = settings.MPESA_CONSUMER_SECRET
        api_url = settings.MPESA_API_URL
        
        # Create credentials
        credentials = f"{consumer_key}:{consumer_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}'
        }
        
        response = requests.get(
            f'{api_url}/oauth/v1/generate?grant_type=client_credentials',
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            logger.error(f'M-Pesa token error: {response.text}')
            return None
            
    except Exception as e:
        logger.error(f'M-Pesa token exception: {str(e)}')
        return None


def initiate_stk_push(phone_number, amount, account_reference, transaction_desc, 
                     student, reservation, application):
    """
    Initiate M-Pesa STK Push
    
    Args:
        phone_number: Customer phone (254XXXXXXXXX)
        amount: Amount to charge
        account_reference: Transaction reference
        transaction_desc: Transaction description
        student: Student instance
        reservation: BedReservation instance
        application: HostelApplication instance
    
    Returns:
        dict: Response with success status and details
    """
    try:
        access_token = get_mpesa_access_token()
        if not access_token:
            return {
                'success': False,
                'message': 'Failed to get M-Pesa access token'
            }
        
        # Configuration
        business_short_code = settings.MPESA_SHORTCODE
        passkey = settings.MPESA_PASSKEY
        api_url = settings.MPESA_API_URL
        callback_url = settings.MPESA_CALLBACK_URL
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Generate password
        password_string = f'{business_short_code}{passkey}{timestamp}'
        password = base64.b64encode(password_string.encode()).decode()
        
        # Prepare request payload
        payload = {
            'BusinessShortCode': business_short_code,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),
            'PartyA': phone_number,
            'PartyB': business_short_code,
            'PhoneNumber': phone_number,
            'CallBackURL': callback_url,
            'AccountReference': account_reference,
            'TransactionDesc': transaction_desc
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Make API request
        response = requests.post(
            f'{api_url}/mpesa/stkpush/v1/processrequest',
            json=payload,
            headers=headers,
            timeout=30
        )
        
        response_data = response.json()
        logger.info(f'STK Push response: {response_data}')
        
        if response.status_code == 200 and response_data.get('ResponseCode') == '0':
            # Create payment record
            payment = MpesaPayment.objects.create(
                merchant_request_id=response_data.get('MerchantRequestID'),
                checkout_request_id=response_data.get('CheckoutRequestID'),
                student=student,
                phone_number=phone_number,
                amount=amount,
                account_reference=account_reference,
                transaction_desc=transaction_desc,
                status='pending',
                bed_reservation=reservation,
                hostel_application=application
            )
            
            return {
                'success': True,
                'checkout_request_id': response_data.get('CheckoutRequestID'),
                'merchant_request_id': response_data.get('MerchantRequestID'),
                'customer_message': response_data.get('CustomerMessage'),
                'payment_id': payment.id
            }
        else:
            error_message = response_data.get('errorMessage', 
                                             response_data.get('CustomerMessage', 
                                                              'Payment initiation failed'))
            return {
                'success': False,
                'message': error_message
            }
            
    except requests.Timeout:
        logger.error('M-Pesa API timeout')
        return {
            'success': False,
            'message': 'Request timeout. Please try again.'
        }
    except Exception as e:
        logger.error(f'STK Push error: {str(e)}', exc_info=True)
        return {
            'success': False,
            'message': f'Error initiating payment: {str(e)}'
        }


def query_stk_status(checkout_request_id):
    """
    Query STK Push transaction status
    
    Args:
        checkout_request_id: Checkout request ID from STK push
    
    Returns:
        dict: Transaction status
    """
    try:
        access_token = get_mpesa_access_token()
        if not access_token:
            return {
                'success': False,
                'message': 'Failed to get access token'
            }
        
        business_short_code = settings.MPESA_SHORTCODE
        passkey = settings.MPESA_PASSKEY
        api_url = settings.MPESA_API_URL
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f'{business_short_code}{passkey}{timestamp}'
        password = base64.b64encode(password_string.encode()).decode()
        
        payload = {
            'BusinessShortCode': business_short_code,
            'Password': password,
            'Timestamp': timestamp,
            'CheckoutRequestID': checkout_request_id
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f'{api_url}/mpesa/stkpushquery/v1/query',
            json=payload,
            headers=headers,
            timeout=30
        )
        
        response_data = response.json()
        logger.info(f'STK Query response: {response_data}')
        
        if response.status_code == 200:
            return {
                'success': True,
                'result_code': response_data.get('ResultCode'),
                'result_desc': response_data.get('ResultDesc'),
                'response': response_data
            }
        else:
            return {
                'success': False,
                'message': 'Query failed'
            }
            
    except Exception as e:
        logger.error(f'STK Query error: {str(e)}')
        return {
            'success': False,
            'message': str(e)
        }