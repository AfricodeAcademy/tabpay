from flask_restful import fields, reqparse

# Fields for serialization
def get_user_fields():
    block_fields = {
        "id": fields.Integer,
        "name": fields.String       
    }
    role_fields = {
    "id": fields.Integer,
    "name": fields.String
    }
    user_fields = {
        "id": fields.Integer,
        "email": fields.String,
        "full_name": fields.String,
        "id_number": fields.Integer,
        "phone_number": fields.String,
        "active": fields.Boolean,
        "bank_id": fields.Integer,
        "acc_number": fields.String,
        "image_file": fields.String,
        "registered_at": fields.DateTime,
        "updated_at": fields.DateTime,
        "zone_id":  fields.Integer,
        "confirmed_at": fields.DateTime,
        "roles": fields.List(fields.Nested(role_fields)),
        "block_memberships": fields.List(fields.Nested(block_fields)),
        "zone_name": fields.String(attribute='zone.name'),  
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
    "created_by": fields.Integer
}
communication_fields = {
    "id": fields.Integer,
    "content": fields.String,
    "created_at": fields.DateTime,
    "member_id": fields.Integer
}

payment_fields = {
    "id": fields.Integer,
    "mpesa_id": fields.String,
    "account_number": fields.String,
    "source_phone_number": fields.String,
    "amount": fields.Integer,
    "payment_date": fields.DateTime,
    "transaction_status": fields.Boolean,
    "bank_id":fields.Integer,
    "block_id": fields.Integer,
    "payer_id": fields.Integer,
    "payer_full_name": fields.String(attribute=lambda x: getattr(x.payer, 'full_name', 'Unknown')),  
    "block_name": fields.String(attribute=lambda x: getattr(x.block, 'name', 'Unknown'))  
}

bank_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "paybill_no": fields.Integer
}



umbrella_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "location": fields.String,
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



communication_args = reqparse.RequestParser()
communication_args.add_argument('content', type=str, required=True, help='Content is required')
communication_args.add_argument('member_id', type=int, required=True, help='Member ID is required')

bank_args = reqparse.RequestParser()
bank_args.add_argument('name', type=str, required=True, help='Bank Name is required')
bank_args.add_argument('paybill_no', type=int, required=True, help='Paybill Number is required')

payment_args = reqparse.RequestParser()
payment_args.add_argument('mpesa_id', type=str, required=True, help='MPESA ID is required')
payment_args.add_argument('account_number', type=str, required=True, help='Account Number is required')
payment_args.add_argument('source_phone_number', type=str, required=True, help='Source phone number is required')
payment_args.add_argument('amount', type=int, required=True, help='Amount is required')
payment_args.add_argument('bank_id', type=int, required=True, help='Bank ID is required')
payment_args.add_argument('block_id', type=int, required=True, help='Block ID is required')
payment_args.add_argument('payer_id', type=int, required=True, help='Payer ID is required')
payment_args.add_argument('amount', type=int, required=True, help='Meeting ID is required')

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

