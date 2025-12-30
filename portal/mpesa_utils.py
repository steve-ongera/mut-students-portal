"""
M-Pesa STK Push Integration Utility
Create this file as: portal/utils/mpesa_utils.py

Before using:
1. Register for M-Pesa API at https://developer.safaricom.co.ke/
2. Get your Consumer Key, Consumer Secret, and Passkey
3. Set up your callback URL
4. Add credentials to settings.py or environment variables
"""

import requests
import base64
from datetime import datetime
from django.conf import settings
import json


class MpesaClient:
    """M-Pesa Daraja API Client"""
    
    def __init__(self):
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.business_short_code = getattr(settings, 'MPESA_SHORTCODE', '')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', '')
        self.callback_url = getattr(settings, 'MPESA_CALLBACK_URL', '')
        
        # API URLs
        self.environment = getattr(settings, 'MPESA_ENVIRONMENT', 'sandbox')
        
        if self.environment == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'
        
        self.access_token_url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
        self.stk_push_url = f'{self.base_url}/mpesa/stkpush/v1/processrequest'
        self.stk_query_url = f'{self.base_url}/mpesa/stkpushquery/v1/query'
    
    def get_access_token(self):
        """
        Generate access token for API authentication
        Returns: access_token string or None if failed
        """
        try:
            response = requests.get(
                self.access_token_url,
                auth=(self.consumer_key, self.consumer_secret)
            )
            
            if response.status_code == 200:
                json_response = response.json()
                return json_response.get('access_token')
            else:
                print(f"Access token error: {response.text}")
                return None
                
        except Exception as e:
            print(f"Exception getting access token: {str(e)}")
            return None
    
    def generate_password(self):
        """
        Generate password for STK Push request
        Returns: (password, timestamp) tuple
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = f"{self.business_short_code}{self.passkey}{timestamp}"
        encoded = base64.b64encode(data_to_encode.encode()).decode('utf-8')
        return encoded, timestamp
    
    def format_phone_number(self, phone_number):
        """
        Format phone number to required format (254XXXXXXXXX)
        Args:
            phone_number: Phone number in any format
        Returns: Formatted phone number
        """
        # Remove any spaces, dashes, or plus signs
        phone = phone_number.replace(' ', '').replace('-', '').replace('+', '')
        
        # Remove leading zero if present
        if phone.startswith('0'):
            phone = phone[1:]
        
        # Add country code if not present
        if not phone.startswith('254'):
            phone = '254' + phone
        
        return phone
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Initiate STK Push payment request
        
        Args:
            phone_number: Customer's phone number
            amount: Amount to charge
            account_reference: Reference for the transaction (max 12 chars)
            transaction_desc: Description of the transaction
        
        Returns:
            dict: Response containing success status and details
        """
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {
                    'success': False,
                    'message': 'Failed to get access token'
                }
            
            # Format phone number
            formatted_phone = self.format_phone_number(phone_number)
            
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            # Prepare request payload
            payload = {
                "BusinessShortCode": self.business_short_code,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": formatted_phone,
                "PartyB": self.business_short_code,
                "PhoneNumber": formatted_phone,
                "CallBackURL": self.callback_url,
                "AccountReference": account_reference[:12],  # Max 12 characters
                "TransactionDesc": transaction_desc[:13]  # Max 13 characters
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Make API request
            response = requests.post(
                self.stk_push_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                json_response = response.json()
                
                if json_response.get('ResponseCode') == '0':
                    return {
                        'success': True,
                        'message': 'STK Push sent successfully',
                        'merchant_request_id': json_response.get('MerchantRequestID'),
                        'checkout_request_id': json_response.get('CheckoutRequestID'),
                        'response_code': json_response.get('ResponseCode'),
                        'response_description': json_response.get('ResponseDescription'),
                        'customer_message': json_response.get('CustomerMessage')
                    }
                else:
                    return {
                        'success': False,
                        'message': json_response.get('ResponseDescription', 'STK Push failed'),
                        'response_code': json_response.get('ResponseCode')
                    }
            else:
                return {
                    'success': False,
                    'message': f'API request failed: {response.text}',
                    'status_code': response.status_code
                }
                
        except requests.Timeout:
            return {
                'success': False,
                'message': 'Request timed out. Please try again.'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Exception occurred: {str(e)}'
            }
    
    def query_stk_status(self, checkout_request_id):
        """
        Query the status of an STK Push transaction
        
        Args:
            checkout_request_id: CheckoutRequestID from STK Push response
        
        Returns:
            dict: Response containing transaction status
        """
        try:
            access_token = self.get_access_token()
            if not access_token:
                return {
                    'success': False,
                    'message': 'Failed to get access token'
                }
            
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            payload = {
                "BusinessShortCode": self.business_short_code,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                self.stk_query_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                json_response = response.json()
                return {
                    'success': True,
                    'result_code': json_response.get('ResultCode'),
                    'result_desc': json_response.get('ResultDesc'),
                    'response': json_response
                }
            else:
                return {
                    'success': False,
                    'message': f'Query failed: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Exception occurred: {str(e)}'
            }


# Convenience function to use in views
def initiate_hostel_payment(student, phone_number, amount, bed_reservation, application):
    """
    Initiate M-Pesa payment for hostel booking
    
    Args:
        student: Student instance
        phone_number: Phone number for payment
        amount: Amount to charge
        bed_reservation: BedReservation instance
        application: HostelApplication instance
    
    Returns:
        dict: Payment initiation response
    """
    from portal.models import MpesaPayment
    
    mpesa_client = MpesaClient()
    
    # Generate account reference
    account_reference = f"H{application.id}"
    transaction_desc = f"Hostel {bed_reservation.bed.room.hostel.code}"
    
    # Initiate STK Push
    response = mpesa_client.stk_push(
        phone_number=phone_number,
        amount=amount,
        account_reference=account_reference,
        transaction_desc=transaction_desc
    )
    
    if response['success']:
        # Create payment record
        mpesa_payment = MpesaPayment.objects.create(
            merchant_request_id=response['merchant_request_id'],
            checkout_request_id=response['checkout_request_id'],
            student=student,
            phone_number=mpesa_client.format_phone_number(phone_number),
            amount=amount,
            account_reference=account_reference,
            transaction_desc=transaction_desc,
            status='pending',
            bed_reservation=bed_reservation,
            hostel_application=application
        )
        
        return {
            'success': True,
            'message': 'Payment request sent successfully',
            'checkout_request_id': response['checkout_request_id'],
            'mpesa_payment': mpesa_payment
        }
    else:
        return response


def query_payment_status(checkout_request_id):
    """
    Query payment status
    
    Args:
        checkout_request_id: CheckoutRequestID to query
    
    Returns:
        dict: Payment status response
    """
    mpesa_client = MpesaClient()
    return mpesa_client.query_stk_status(checkout_request_id)


# ============= SMS UTILITIES =============

def send_sms(phone_number, message):
    """
    Send SMS notification
    You can use Africa's Talking, Twilio, or any other SMS provider
    
    Args:
        phone_number: Recipient phone number
        message: SMS message
    
    Returns:
        dict: SMS sending response
    """
    # Example using Africa's Talking
    # Uncomment and configure when ready to use
    
    """
    import africastalking
    
    # Initialize SDK
    username = settings.AFRICASTALKING_USERNAME
    api_key = settings.AFRICASTALKING_API_KEY
    africastalking.initialize(username, api_key)
    
    # Get SMS service
    sms = africastalking.SMS
    
    try:
        response = sms.send(message, [phone_number])
        return {
            'success': True,
            'response': response
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }
    """
    
    # For now, just log the SMS
    print(f"SMS to {phone_number}: {message}")
    return {
        'success': True,
        'message': 'SMS sent (simulated)'
    }


def send_booking_confirmation_sms(student, hostel, room, bed, allocation, mpesa_receipt):
    """
    Send booking confirmation SMS to student
    
    Args:
        student: Student instance
        hostel: Hostel instance
        room: HostelRoom instance
        bed: HostelBed instance
        allocation: HostelAllocation instance
        mpesa_receipt: M-Pesa receipt number
    
    Returns:
        bool: Success status
    """
    from portal.models import SMSNotification
    
    phone_number = student.user.phone_number
    
    message = (
        f"Dear {student.user.first_name}, your hostel booking is CONFIRMED! "
        f"Hostel: {hostel.name}, Room: {room.room_number}, Bed: {bed.bed_number}. "
        f"Receipt: {mpesa_receipt}. Check-in details will be sent soon. "
        f"Welcome home!"
    )
    
    # Send SMS
    sms_response = send_sms(phone_number, message)
    
    # Log SMS
    sms_notification = SMSNotification.objects.create(
        student=student,
        phone_number=phone_number,
        sms_type='booking_confirmation',
        message=message,
        hostel_allocation=allocation,
        status='sent' if sms_response['success'] else 'failed',
        response=str(sms_response)
    )
    
    if sms_response['success']:
        from django.utils import timezone
        sms_notification.sent_at = timezone.now()
        sms_notification.save()
    
    return sms_response['success']