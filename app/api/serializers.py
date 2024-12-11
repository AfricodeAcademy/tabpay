from flask_restful import fields, reqparse
from datetime import datetime


# Fields for serialization.
def get_user_fields():
    block_fields = {
        "id": fields.Integer,
        "name": fields.String,
    }
    
    role_fields = {
        "id": fields.Integer,
        "name": fields.String
    }

    zone_fields = {
        "id": fields.Integer,
        "name": fields.String,
    }

    user_fields = {
        "id": fields.Integer,
        "email": fields.String,
        "full_name": fields.String,
        "id_number": fields.Integer,
        "phone_number": fields.String,
        "active": fields.Boolean,
        "bank_id": fields.Integer,
        "umbrella_id": fields.Integer,
         "is_approved": fields.Boolean,
        "approval_date": fields.DateTime,
        "approved_by_id": fields.Integer,
        "acc_number": fields.String,
        "image_file": fields.String,
        "registered_at": fields.DateTime,
        "updated_at": fields.DateTime,
        "confirmed_at": fields.DateTime,
        "roles": fields.List(fields.Nested(role_fields)),
        "block_memberships": fields.List(fields.Nested(block_fields)),
        "zone_memberships": fields.List(fields.Nested(zone_fields)),  
        "bank_name": fields.String(attribute='bank.name'),

        "chaired_blocks": fields.List(fields.Nested(block_fields)),
        "secretary_blocks": fields.List(fields.Nested(block_fields)),
        "treasurer_blocks": fields.List(fields.Nested(block_fields))
    }

    return user_fields


block_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "parent_umbrella_id": fields.Integer,
    "initials": fields.String,
    "created_by": fields.Integer,
}
communication_fields = {
    "id": fields.Integer,
    "content": fields.String,
    "created_at": fields.DateTime,
    "member_id": fields.Integer
}
def format_datetime(value):
    if isinstance(value, str):
        # Convert the string to a datetime object if needed
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return value  # Leave it as is if it can't be parsed
    elif isinstance(value, datetime):
        return value
    return None  # Handle None case

payment_fields = {
    "id": fields.Integer,
    "mpesa_id": fields.String,
    "account_number": fields.String,
    "source_phone_number": fields.String,
    "amount": fields.Integer,
    "payment_date": fields.DateTime(dt_format="rfc822", attribute=lambda x: format_datetime(x.payment_date)),
    "transaction_status": fields.Boolean,
    "bank_id": fields.Integer,
    "block_id": fields.Integer,
    "payer_id": fields.Integer,
    "meeting_id": fields.Integer,
    "payer_full_name": fields.String(attribute=lambda x: getattr(x.payer, 'full_name', 'Unknown')),  
    "block_name": fields.String(attribute=lambda x: getattr(x.block, 'name', 'Unknown')),
    
    # Payment status tracking
    "status": fields.String,
    "status_reason": fields.String,
    "checkout_request_id": fields.String,
    "merchant_request_id": fields.String,
    
    # Timestamps
    "initiated_at": fields.DateTime(dt_format="rfc822"),
    "validated_at": fields.DateTime(dt_format="rfc822"),
    "completed_at": fields.DateTime(dt_format="rfc822"),
    "failed_at": fields.DateTime(dt_format="rfc822"),
    
    # Retry information
    "retry_count": fields.Integer,
    "last_retry_at": fields.DateTime(dt_format="rfc822"),
    
    # Additional M-Pesa fields
    "transaction_type": fields.String,
    "business_short_code": fields.String,
    "invoice_number": fields.String,
    "org_account_balance": fields.Float,
    "third_party_trans_id": fields.String,
    "first_name": fields.String,
    "middle_name": fields.String,
    "last_name": fields.String,
    "customer_name": fields.String(attribute='customer_name')  # Uses the property we defined
}


bank_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "paybill_no": fields.String
}


umbrella_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "location": fields.String,
    "initials": fields.String,
    "created_by": fields.Integer
}

zone_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "parent_block_id": fields.Integer,
    "created_by": fields.Integer
}

role_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "description": fields.String
}

meeting_fields = {
    "id": fields.Integer,
    "unique_id": fields.String,
    "block_id": fields.Integer,
    "zone_id": fields.Integer,
    "host_id": fields.Integer,
    "organizer_id": fields.Integer,
    "date": fields.DateTime
}




user_args = reqparse.RequestParser()
user_args.add_argument('full_name', type=str)
user_args.add_argument('email', type=str)
user_args.add_argument('id_number', type=int)
user_args.add_argument('phone_number', type=str)
user_args.add_argument('bank_id', type=int)
user_args.add_argument('acc_number', type=str)
user_args.add_argument('zone_id', type=int)
user_args.add_argument('image_file', type=str)
user_args.add_argument('role_id', type=int)
user_args.add_argument('action', type=str)
user_args.add_argument('block_id', type=int)  
user_args.add_argument('umbrella_id', type=int)
user_args.add_argument('is_approved', type=bool)
user_args.add_argument('approval_date', type=str) 
user_args.add_argument('approved_by_id', type=int)




communication_args = reqparse.RequestParser()
communication_args.add_argument('content', type=str, required=True, help='Content is required')
communication_args.add_argument('member_id', type=int, required=True, help='Member ID is required')

bank_args = reqparse.RequestParser()
bank_args.add_argument('name', type=str, required=True, help='Bank Name is required')
bank_args.add_argument('paybill_no', type=int, required=True, help='Paybill Number is required')

payment_args = reqparse.RequestParser()
payment_args.add_argument('mpesa_id', type=str, required=True, help='M-Pesa Transaction ID is required')
payment_args.add_argument('account_number', type=str, required=True, help='Account number is required')
payment_args.add_argument('source_phone_number', type=str, required=True, help='Source phone number is required')
payment_args.add_argument('amount', type=int, required=True, help='Amount is required')
payment_args.add_argument('payment_date', type=lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S') if x else None)
payment_args.add_argument('transaction_status', type=bool)
payment_args.add_argument('bank_id', type=int, required=True, help='Bank ID is required')
payment_args.add_argument('block_id', type=int, required=True, help='Block ID is required')
payment_args.add_argument('payer_id', type=int, required=True, help='Payer ID is required')
payment_args.add_argument('meeting_id', type=int)

# STK Push specific fields
payment_args.add_argument('checkout_request_id', type=str)
payment_args.add_argument('merchant_request_id', type=str)
payment_args.add_argument('status', type=str)
payment_args.add_argument('status_reason', type=str)

# M-Pesa specific fields
payment_args.add_argument('transaction_type', type=str)
payment_args.add_argument('business_short_code', type=str)
payment_args.add_argument('invoice_number', type=str)
payment_args.add_argument('org_account_balance', type=float)
payment_args.add_argument('third_party_trans_id', type=str)
payment_args.add_argument('first_name', type=str)
payment_args.add_argument('middle_name', type=str)
payment_args.add_argument('last_name', type=str)

payment_update_args = reqparse.RequestParser()
payment_update_args.add_argument('transaction_status', type=str)
payment_update_args.add_argument('org_account_balance', type=float)
payment_update_args.add_argument('third_party_trans_id', type=str)

block_args = reqparse.RequestParser()
block_args.add_argument('name', type=str, required=True, help='Block Name is required')
block_args.add_argument('parent_umbrella_id', type=int, required=True, help='Parent Umbrella ID is required')
block_args.add_argument('created_by', type=int, required=True, help='Creator ID is required')

umbrella_args = reqparse.RequestParser()
umbrella_args.add_argument('name', type=str, required=True, help='Umbrella Name is required')
umbrella_args.add_argument('location', type=str, required=True, help='Umbrella location is required')
umbrella_args.add_argument('created_by', type=int, required=True, help='Creator ID is required')

zone_args = reqparse.RequestParser()
zone_args.add_argument('name', type=str, required=True, help='Zone Name is required')
zone_args.add_argument('parent_block_id', type=int, required=True, help='Parent Block ID is required')
zone_args.add_argument('created_by', type=int, required=True, help='Creator ID is required')

role_args = reqparse.RequestParser()
role_args.add_argument('name', type=str, required=True, help='Role Name is required')
role_args.add_argument('description', type=int, required=True, help='Description is required')


meeting_args = reqparse.RequestParser()
meeting_args.add_argument('host_id', type=int, required=True, help='Host ID is required')
meeting_args.add_argument('block_id', type=int, required=True, help='Block ID is required')
meeting_args.add_argument('zone_id', type=int, required=True, help='Zone ID is required')
meeting_args.add_argument('organizer_id', type=int, required=True, help='Organizer ID is required')
meeting_args.add_argument('date', type=str, required=True, help='Meeting date is required (format: YYYY-MM-DD HH:MM:SS)')

# M-Pesa validation fields
mpesa_validation_fields = {
    "ResultCode": fields.Integer,
    "ResultDesc": fields.String
}

# M-Pesa confirmation fields
mpesa_confirmation_fields = {
    "ResultCode": fields.String,
    "ResultDesc": fields.String,
    "TransactionType": fields.String,
    "TransID": fields.String,
    "TransAmount": fields.Float,
    "BusinessShortCode": fields.String,
    "BillRefNumber": fields.String,
    "InvoiceNumber": fields.String,
    "OrgAccountBalance": fields.Float,
    "ThirdPartyTransID": fields.String,
    "MSISDN": fields.String,
    "FirstName": fields.String,
    "MiddleName": fields.String,
    "LastName": fields.String,
    "TransTime": fields.String,
    "payment": fields.Nested(payment_fields)
}

# M-Pesa validation request parser
mpesa_validation_args = reqparse.RequestParser()
mpesa_validation_args.add_argument('TransactionType', type=str, required=True, help='Transaction Type is required')
mpesa_validation_args.add_argument('TransAmount', type=float, required=True, help='Transaction Amount is required')
mpesa_validation_args.add_argument('BillRefNumber', type=str, required=True, help='Bill Reference Number is required')
mpesa_validation_args.add_argument('MSISDN', type=str, required=True, help='Phone Number (MSISDN) is required')
mpesa_validation_args.add_argument('TransID', type=str)

# M-Pesa confirmation request parser
mpesa_confirmation_args = reqparse.RequestParser()
mpesa_confirmation_args.add_argument('TransactionType', type=str, required=True, help='Transaction Type is required')
mpesa_confirmation_args.add_argument('TransID', type=str, required=True, help='Transaction ID is required')
mpesa_confirmation_args.add_argument('TransAmount', type=float, required=True, help='Transaction Amount is required')
mpesa_confirmation_args.add_argument('BusinessShortCode', type=str, required=True, help='Business Short Code is required')
mpesa_confirmation_args.add_argument('BillRefNumber', type=str, required=True, help='Bill Reference Number is required')
mpesa_confirmation_args.add_argument('InvoiceNumber', type=str)
mpesa_confirmation_args.add_argument('OrgAccountBalance', type=float)
mpesa_confirmation_args.add_argument('ThirdPartyTransID', type=str)
mpesa_confirmation_args.add_argument('MSISDN', type=str, required=True, help='Phone Number is required')
mpesa_confirmation_args.add_argument('FirstName', type=str)
mpesa_confirmation_args.add_argument('MiddleName', type=str)
mpesa_confirmation_args.add_argument('LastName', type=str)
mpesa_confirmation_args.add_argument('TransTime', type=str)
