from flask_restful import fields, reqparse

# Fields for serialization
user_fields = {
    "id": fields.Integer,
    "email": fields.String,
    "full_name": fields.String,
    "id_number": fields.Integer,
    "phone_number": fields.String,
    "active": fields.Boolean,
    "bank": fields.Integer,
    "acc_number": fields.String,
    "image_file": fields.String,
    "registered_at": fields.DateTime,
    "updated_at": fields.DateTime,
    "zone_id": fields.Integer,
    "confirmed_at": fields.DateTime,
    "roles": fields.List(fields.Nested({"id": fields.Integer, "name": fields.String})),
    "block_memberships": fields.List(fields.Nested({"id": fields.Integer, "name": fields.String}))
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
    "bank_id": fields.Integer,
    "block_id": fields.Integer,
    "payer_id": fields.Integer
}

bank_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "paybill_no": fields.Integer
}

block_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "parent_umbrella_id": fields.Integer,
    "created_by": fields.Integer
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

meeting_fields = {
    "id": fields.Integer,
    "block_id": fields.Integer,
    "zone_id": fields.Integer,
    "organizer_id": fields.Integer,
    "date": fields.DateTime
}

# Argument parsers for different resources
# user_args = reqparse.RequestParser()
# user_args.add_argument('full_name', type=str, required=True, help='Full Name is required.')
# user_args.add_argument('id_number', type=int, required=True, help='ID Number must be an integer and is required.')
# user_args.add_argument('phone_number', type=str, required=True, help='Phone Number is required.')
# user_args.add_argument('bank', type=int, required=True, help='Bank ID must be an integer and is required.')
# user_args.add_argument('acc_number', type=str, required=True, help='Account Number is required.')
# user_args.add_argument('zone_id', type=int, required=True, help='Zone is required.')


user_args = reqparse.RequestParser()
user_args.add_argument('full_name', type=str)
user_args.add_argument('email', type=str)
user_args.add_argument('id_number', type=int)
user_args.add_argument('phone_number', type=str)
user_args.add_argument('bank', type=int)
user_args.add_argument('acc_number', type=str)
user_args.add_argument('zone_id', type=int)
user_args.add_argument('image_file', type=str)




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

meeting_args = reqparse.RequestParser()
meeting_args.add_argument('block_id', type=int, required=True, help='Block ID is required')
meeting_args.add_argument('zone_id', type=int, required=True, help='Zone ID is required')
meeting_args.add_argument('organizer_id', type=int, required=True, help='Organizer ID is required')
meeting_args.add_argument('date', type=str, required=True, help='Meeting date is required (format: YYYY-MM-DD HH:MM:SS)')

# Keep the block_report_args and block_report_fields as they were
block_report_args = reqparse.RequestParser()
block_report_args.add_argument('blocks', type=str, help='Block name for filtering')
block_report_args.add_argument('member', type=str, help='Member name for filtering')
block_report_args.add_argument('start_date', type=str, help='Start date for filtering (format: YYYY-MM-DD)')
block_report_args.add_argument('end_date', type=str, help='End date for filtering (format: YYYY-MM-DD)')
block_report_args.add_argument('page', type=int, default=1, help='Page number for pagination')
block_report_args.add_argument('per_page', type=int, default=20, help='Items per page for pagination')

block_report_fields = {
    "total_contributed": fields.Float,
    "detailed_contributions": fields.List(fields.Nested({
        "zone": fields.String,
        "host": fields.String,
        "contributed_amount": fields.Float,
    })),
    "pagination": fields.Nested({
        "page": fields.Integer,
        "per_page": fields.Integer,
        "total_pages": fields.Integer,
        "total_items": fields.Integer
    })
}