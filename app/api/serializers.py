from flask_restful import fields, reqparse


# Fields for serialization
user_fields = {
    "id": fields.Integer,
    "full_name": fields.String,
    "email": fields.String,
    "password": fields.String,
    "id_number": fields.Integer,
    "phone_number": fields.String,  # Changed to String
    "active": fields.Boolean,
    "zone_id": fields.Integer,
    "bank": fields.String,
    "acc_number": fields.String,  # Changed to String
    "registered_at": fields.DateTime,
    "updated_at": fields.DateTime,
    "message": fields.String(attribute="author.full_name")
}

communication_fields = {
    "id": fields.Integer,
    "content": fields.String,
    "user_id": fields.Integer,
    "created_at": fields.DateTime,
    "updated_at": fields.DateTime
}

payment_fields = {
    "id": fields.Integer,
    "payer_id": fields.Integer,
    "amount": fields.Float,
    "payment_date": fields.DateTime,
    "mpesa_id": fields.String,
    "account_number": fields.String,  # Changed to String
    "source_phone_number": fields.String,  # Changed to String
    "transaction_status": fields.Boolean
}

bank_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "paybill_no": fields.Integer,
    "total_transactions": fields.List(fields.Nested(payment_fields))
}

block_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "umbrella_id": fields.Integer
}

umbrella_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "location": fields.String
}

zone_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "parent_block_id": fields.Integer
}

# block_report_fields = {
#     "total_contributed": fields.Float,
#     "contributions": fields.List(fields.Nested({
#         "id": fields.Integer,
#         "amount": fields.Float,
#         "payment_date": fields.DateTime,
#     })),
#     "detailed_contributions": fields.List(fields.Nested({
#         "zone": fields.String,
#         "host": fields.String,
#         "contributed_amount": fields.Float,
#     })),
# }
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

meeting_fields = {
    "id": fields.Integer,
    "block_id": fields.Integer,
    "zone_id": fields.Integer,
    "host_id": fields.Integer,
    "date": fields.DateTime,
    "status": fields.String,
    "created_at": fields.DateTime,
    "updated_at": fields.DateTime,
}

# Argument parsers for different resources
umbrella_args = reqparse.RequestParser()
umbrella_args.add_argument('name', type=str, required=True, help='Umbrella Name is required')
umbrella_args.add_argument('location', type=str, required=True, help='Umbrella location is required')

block_args = reqparse.RequestParser()
block_args.add_argument('name', type=str, required=True, help='Block Name is required')
block_args.add_argument('parent_umbrella_id', type=int, required=True, help='Parent Umbrella is required')

zone_args = reqparse.RequestParser()
zone_args.add_argument('name', type=str, required=True, help='Zone Name is required')
zone_args.add_argument('parent_block_id', type=int, required=True, help='Parent Block is required')

user_args = reqparse.RequestParser()
user_args.add_argument('email', type=str, required=True, help='Email is required')
user_args.add_argument('password', type=str, required=True, help='Password is required')

communication_args = reqparse.RequestParser()
communication_args.add_argument('content', type=str, required=True, help='Content is required')
communication_args.add_argument('user_id', type=int, required=True, help='Author is required')

bank_args = reqparse.RequestParser()
bank_args.add_argument('name', type=str, required=True, help='Bank Name is required')
bank_args.add_argument('paybill_no', type=int, required=True, help='Paybill Number is required')

payment_args = reqparse.RequestParser()
payment_args.add_argument('payer_id', type=int, required=True, help='Payer is required')
payment_args.add_argument('source_phone_number', type=str, required=True, help='Source phone number is required')  
payment_args.add_argument('amount', type=float, required=True, help='Amount is required')

# Arguments parser for BlockReportsResource
block_report_args = reqparse.RequestParser()
block_report_args.add_argument('blocks', type=str, help='Block name for filtering')
block_report_args.add_argument('member', type=str, help='Member name for filtering')
# block_report_args.add_argument('date', type=str, help='Date for filtering (format: YYYY-MM-DD)')
block_report_args.add_argument('start_date', type=str, help='Start date for filtering (format: YYYY-MM-DD)')
block_report_args.add_argument('end_date', type=str, help='End date for filtering (format: YYYY-MM-DD)')
block_report_args.add_argument('page', type=int, default=1, help='Page number for pagination')
block_report_args.add_argument('per_page', type=int, default=20, help='Items per page for pagination')

# Arguments parser for MeetingsResource
meeting_args = reqparse.RequestParser()
meeting_args.add_argument('block_id', type=int, required=True, help='Block ID is required')
meeting_args.add_argument('zone_id', type=int, required=True, help='Zone ID is required')
meeting_args.add_argument('host_id', type=int, required=True, help='Host ID is required')
meeting_args.add_argument('date', type=str, required=True, help='Meeting date is required (format: YYYY-MM-DD HH:MM:SS)')
meeting_args.add_argument('status', type=str, help='Meeting status')