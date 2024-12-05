from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request
from flask_security import current_user
from werkzeug.exceptions import HTTPException
from flask_restful import Api, Resource, marshal_with, marshal, abort
from ..main.models import UserModel, CommunicationModel, \
    PaymentModel, BankModel, BlockModel, UmbrellaModel, ZoneModel, MeetingModel, RoleModel, roles_users, member_blocks,member_zones
from .serializers import get_user_fields, user_args, communication_fields, \
    communication_args, payment_fields, payment_args, payment_update_args, \
    bank_fields, bank_args, block_fields, block_args, \
    umbrella_fields, umbrella_args, zone_fields, zone_args, \
    meeting_fields, meeting_args,role_args,role_fields, mpesa_validation_args, mpesa_validation_fields, mpesa_confirmation_args, mpesa_confirmation_fields
from ..utils import db
import logging
from ..main.routes import save_picture
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)
api = Api(api_bp)




def handle_error(self, e):
    db.session.rollback()

    if isinstance(e, SQLAlchemyError):
        # logging.error(f"Database error: {str(e)}", exc_info=True)
        error_message = {"success": False, "message": "Database error occurred", "details": str(e)}
        status_code = 500
    elif isinstance(e, HTTPException):
        # logging.error(f"HTTP error: {str(e)}", exc_info=True)
        error_message = {"success": False, "message": "HTTP error occurred", "details": str(e)}
        status_code = e.code
    else:
        # logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        error_message = {"success": False, "message": "Unexpected error occurred", "details": str(e)}
        status_code = 500

    return jsonify(error_message), status_code


def marshal_with_fields(fields):
    def decorator(func):
        return marshal_with(fields)(func)
    return decorator


class BaseResource(Resource):
    model = None
    fields = None
    args = None

    def get(self, id=None):
        if self.fields is None:
            return {"success": False, "message": "Internal server error. Please contact support."}, 500

        try:
            if id:
                item = self.model.query.get_or_404(id)
                return marshal(item, self.fields), 200
            items = self.model.query.all()
            return marshal(items, self.fields), 200
        except Exception as e:
            return self.handle_error(e)


    def post(self):
        try:
            args = self.args.parse_args()
            new_item = self.model(**args)
            db.session.add(new_item)
            db.session.commit()
            return marshal(new_item, self.fields), 201
        except Exception as e:
            return self.handle_error(e)


    def patch(self, id):
        try:
            args = self.args.parse_args()
            item = self.model.query.get_or_404(id)
           # Only update fields that are provided (not None)
            for key, value in args.items():
                if value is not None:
                    setattr(item, key, value)
            db.session.commit()
            return marshal(item, self.fields), 200
        except Exception as e:
            return self.handle_error(e)

    def delete(self, id):
        try:
            item = self.model.query.get_or_404(id)
            db.session.delete(item)
            db.session.commit()
            items = self.model.query.all()
            return marshal(items, self.fields), 200
        except Exception as e:
            return self.handle_error(e)

    def handle_error(self, e):
        db.session.rollback()

        if isinstance(e, SQLAlchemyError):
            error_message = {"success": False, "message": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)

        elif isinstance(e, HTTPException):
            error_message = {"success": False, "message": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)

        else:
            error_message = {"success": False, "message": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        return error_message

class UsersResource(BaseResource):
    model = UserModel
    fields = get_user_fields()
    args = user_args

    def get(self, id=None):
        try:
            if id:
                user = self.model.query.get_or_404(id)

                if user.zone_id:
                    user.zone_name = ZoneModel.query.filter_by(id=user.zone_id).first().name if user.zone_id else None

                if user.bank_id:
                    user.bank_name = BankModel.query.filter_by(id=user.bank_id).first().name if user.bank_id else None

                if not user:
                    return {"message": "User not found"}, 404
                return marshal(user, self.fields), 200

            # Check for query parameters: role, id_number, umbrella_id, and zone_id
            role_name = request.args.get('role')
            id_number = request.args.get('id_number')
            umbrella_id = request.args.get('umbrella_id')
            zone_id = request.args.get('zone_id')

            # Fetch user by id_number if provided
            if id_number:
                user = self.model.query.filter_by(id_number=id_number).first()
                if not user:
                    return {"message": "User not found"}, 404
                return marshal(user, self.fields), 200

            # Fetch users by role and zone_id
            if role_name and zone_id:
                users = (
                    self.model.query
                    .join(UserModel.roles)
                    .filter(RoleModel.name == role_name, UserModel.zone_id == zone_id)
                    .all()
                )
                return marshal(users, self.fields), 200

            # Fetch users by role and umbrella_id if both are provided
            if role_name and umbrella_id:
                users = (
                    self.model.query
                    .join(UserModel.roles)
                    .join(UserModel.block_memberships)
                    .filter(RoleModel.name == role_name)
                    .filter(BlockModel.parent_umbrella_id == umbrella_id)
                    .all()
                )
                return marshal(users, self.fields), 200
            # Fetch users by role, zone_id, and umbrella_id
            if role_name and zone_id and umbrella_id:
                users = (
                    self.model.query
                    .join(UserModel.roles)
                    .join(UserModel.block_memberships)
                    .filter(RoleModel.name == role_name)
                    .filter(UserModel.zone_id == zone_id)
                    .filter(BlockModel.parent_umbrella_id == umbrella_id)
                    .all()
                )
                return marshal(users, self.fields), 200

            # Fetch users by role if role_name is provided (without umbrella or zone)
            if role_name:
                users = self.model.query.join(UserModel.roles).filter(RoleModel.name == role_name).all()
                return marshal(users, self.fields), 200

            # Fetch all users if no filters are provided
            users = self.model.query.all()
            for user in users:
                if user.zone_id:
                    user.zone_name = ZoneModel.query.filter_by(id=user.zone_id).first().name if user.zone_id else None

                if user.bank_id:
                    bank = BankModel.query.get(user.bank_id)
                    if bank:
                        user.bank_name = bank.name
            return marshal(users, self.fields), 200

        except Exception as e:
            return self.handle_error(e)


    def post(self):
        try:
            # Parse arguments
            args = self.args.parse_args()

            # Validate umbrella
            umbrella = UmbrellaModel.query.get(args['umbrella_id'])
            if not umbrella:
                return {"message": "Umbrella does not exist."}, 400

            # Validate zone
            zone = ZoneModel.query.get(args['zone_id'])
            if not zone:
                return {"message": "Zone does not exist."}, 400

            # Validate block (parent of the zone)
            block = BlockModel.query.get(zone.parent_block_id)
            if not block:
                return {"message": "Block associated with the zone does not exist."}, 400

            # Check for duplicate user
            existing_user = UserModel.query.filter(
                (UserModel.id_number == args['id_number']) |
                (UserModel.phone_number == args['phone_number']) |
                (UserModel.acc_number == args['acc_number']),
                UserModel.zone_id == args['zone_id'],
                UserModel.umbrella_id == args['umbrella_id']
            ).first()

            if existing_user:
                return {
                    "message": "A member with this ID number, phone number, or account number already exists in this zone."
                }, 400

            # Create the new user
            new_user = UserModel(
                full_name=args['full_name'],
                id_number=args['id_number'],
                phone_number=args['phone_number'],
                zone_id=args['zone_id'],
                bank_id=args['bank_id'],
                acc_number=args['acc_number'],
                umbrella_id=args['umbrella_id']
            )

            # Add user to the session
            db.session.add(new_user)
            db.session.flush()  # Flush to assign an ID to the user

            # Assign role if provided
            if 'role_id' in args and args['role_id'] is not None:
                role = RoleModel.query.get(args['role_id'])
                if role:
                    new_user.roles.append(role)

        
            # Insert user into the `member_blocks` table
            stmt = member_blocks.insert().values(
                user_id=new_user.id,
                block_id=block.id,
            )
            db.session.execute(stmt)

            # Add zone membership
            stmt = member_zones.insert().values(
                user_id=new_user.id,
                zone_id=zone.id,
            )
            db.session.execute(stmt)

            # Commit the session
            db.session.commit()
   
            # Return the newly created user
            return marshal(new_user, self.fields), 201

        except IntegrityError as e:
            # Handle duplicate entries
            db.session.rollback()
            return {
                "message": "A member with this ID number, phone number, or account number already exists in this zone."
            }, 400

        except Exception as e:
            # General exception handling
            db.session.rollback()
            return self.handle_error(e)


 

    def patch(self, id):
        try:
            args = self.args.parse_args() if 'multipart/form-data' not in request.content_type else {}

            user = UserModel.query.get_or_404(id)
            updated = False

                        # Handle approval
            if 'is_approved' in args and args['is_approved'] is not None:
                if args['is_approved'] and not user.is_approved:
                    user.approve(current_user)  # Assuming current_user is the approver
                    updated = True
                elif not args['is_approved'] and user.is_approved:
                    user.unapprove()
                    updated = True

            # Update fields except 'is_approved', 'approval_date', and 'approved_by_id'
            for key, value in args.items():
                if value is not None and key not in ['is_approved', 'approval_date', 'approved_by_id', 'block_id']:
                    setattr(user, key, value)
                    updated = True

            if 'multipart/form-data' in request.content_type:
                if 'picture' in request.files:
                    image_file = request.files['picture']
                    if image_file:
                        saved_filename = save_picture(image_file)
                        user.image_file = saved_filename
                        updated = True
                    else:
                        return {"message": "No image file provided."}, 400
            else:
                unchanged_fields = []

                for field in ['full_name', 'id_number', 'phone_number', 'zone_id', 'bank_id', 'acc_number', 'email','image_file']:
                    if args[field] is not None and getattr(user, field) != args[field]:
                        setattr(user, field, args[field])
                        updated = True
                    else:
                        unchanged_fields.append(field)

            # Check if block_id is provided to update block memberships
                block_id = args.get('block_id')
                if block_id is not None:
                    block = BlockModel.query.get(block_id)
                    if block:
                        if block not in user.block_memberships:
                            user.block_memberships.append(block)
                            logger.info(f"Added block {block.id} to user's block memberships.")
                            updated = True
                        else:
                            logger.info(f"User {user.id} is already a member of block {block.id}.")
                    else:
                        logger.warning(f"Block {block_id} not found.")
                # Check if zone_id is provided to update zone memberships
                zone_id = args.get('zone_id')
                if zone_id is not None:
                    zone = ZoneModel.query.get(zone_id)
                    if zone:
                        if zone not in user.zone_memberships:
                            user.zone_memberships.append(zone)
                            logger.info(f"Added zone {zone.id} to user's zone memberships.")
                            updated = True
                        else:
                            logger.info(f"User {user.id} is already a member of zone {zone.id}.")
                    else:
                        logger.warning(f"Zone {zone_id} not found.")


            role_id = args.get('role_id')
            action = args.get('action')

            if role_id is not None:
                role = RoleModel.query.get(role_id)

                if role:
                    # Ensure Chairman, Secretary, and Treasurer are mutually exclusive
                    if role_id == 3 and any(r.id in [4, 6] for r in user.roles):
                        return {"message": "Cannot assign Chairman when the user is already a Secretary or Treasurer."}, 400

                    elif role_id == 4 and any(r.id in [3, 6] for r in user.roles):
                        return {"message": "Cannot assign Secretary when the user is already a Chairman or Treasurer."}, 400

                    elif role_id == 6 and any(r.id in [3, 4] for r in user.roles):
                        return {"message": "Cannot assign Treasurer when the user is already a Chairman or Secretary."}, 400

                    # Handle Role Removal
                    if action == 'remove':
                        if role in user.roles:
                            # Retrieve the block_id associated with the user's role
                            role_assignment = db.session.query(roles_users).filter_by(user_id=user.id, role_id=role_id).first()
                            if role_assignment:
                                block_id = role_assignment.block_id  # Get the block_id

                                # Remove the role from the user
                                user.roles.remove(role)
                                updated = True

                                # Remove the block from the corresponding block list
                                if block_id:
                                    if role_id == 3:  # Chairman
                                        user.chaired_blocks = [b for b in user.chaired_blocks if b.id != block_id]
                                    elif role_id == 4:  # Secretary
                                        user.secretary_blocks = [b for b in user.secretary_blocks if b.id != block_id]
                                    elif role_id == 6:  # Treasurer
                                        user.treasurer_blocks = [b for b in user.treasurer_blocks if b.id != block_id]

                        else:
                            return {"message": "User does not have this role"}, 400


                    # Handle Role Addition
                    elif action == 'add':
                        if role in user.roles:
                            return {"message": f"User already has the role '{role.name}'."}, 400
                        else:
                            user.roles.append(role)  # Add the role if it's not already assigned
                            updated = True

                    # Update Blocks Based on Role
                    block_id = args.get('block_id')
                    if block_id is not None:
                        block = BlockModel.query.get(block_id)
                        if block:
                            if role_id == 3:  # Chairman
                                if block not in user.chaired_blocks:
                                    user.chaired_blocks.append(block)

                            elif role_id == 4:  # Secretary
                                if block not in user.secretary_blocks:
                                    user.secretary_blocks.append(block)

                            elif role_id == 5:  # Treasurer
                                if block not in user.treasurer_blocks:
                                    user.treasurer_blocks.append(block)
             

            if updated:
                db.session.commit()
                return marshal(user, self.fields), 200

            return {"message": "No updates made to user."}, 400

        except Exception as e:
            return {"message": "An error occurred while updating the user."}, 500



class CommunicationsResource(BaseResource):
    model = CommunicationModel
    fields = communication_fields
    args = communication_args

class BanksResource(BaseResource):
    model = BankModel
    fields = bank_fields
    args = bank_args

class PaymentsResource(BaseResource):
    model = PaymentModel
    fields = payment_fields
    args = payment_args

    def get(self, id=None):
        """Get a single payment or list all payments"""
        try:
            if id:
                return super().get(id)
            
            # Check for query parameters
            meeting_id = request.args.get('meeting_id', None)
            mpesa_id = request.args.get('mpesa_id', None)
            
            query = PaymentModel.query
            
            if mpesa_id:
                # Filter by mpesa_id if provided
                query = query.filter_by(mpesa_id=mpesa_id)
                payments = query.all()
                return marshal(payments, self.fields), 200
            
            if meeting_id:
                try:
                    logger.info(f"Fetching payments for meeting ID: {meeting_id}")
                    # Query payments by meeting_id and join payer (user) and block tables
                    payments = query \
                        .filter_by(meeting_id=meeting_id) \
                        .join(UserModel, PaymentModel.payer_id == UserModel.id) \
                        .join(BlockModel, PaymentModel.block_id == BlockModel.id) \
                        .options(joinedload(PaymentModel.payer), joinedload(PaymentModel.block)) \
                        .all()
                    logger.info(f"Payments fetched for meeting ID {meeting_id}: {payments}")
                    payment_data = []
                    for payment in payments:
                        logger.debug(f"Processing payment: ID {payment.id}, Payer {payment.payer.full_name}, Block {payment.block.name}")
                        payment_data.append({
                        "mpesa_id": payment.mpesa_id,
                        "amount": payment.amount,
                        "transaction_status": payment.transaction_status,
                        "payer_id": payment.payer.id,  # Payer ID
                        "payer_full_name": payment.payer.full_name,  # Payer Full Name
                        "block_id": payment.block.id,  # Block ID
                        "block_name": payment.block.name,  # Block Name
                        "payment_date": payment.payment_date,
                        "status": "Contributed" if payment.transaction_status else "Pending"
                    })
                    logger.info(f"Payments query result: {payment_data}")
                    return marshal(payments, self.fields), 200
                except Exception as e:
                    logger.error(f'Payments error: {e}')
                    return self.handle_error(e)
            else:
                # Handle other queries for fetching all payments or specific payment by ID
                return super().get()
            
        except Exception as e:
            logger.error(f"Error retrieving payment(s): {str(e)}", exc_info=True)
            return handle_error(self, e)

    def post(self):
        try:
            args = self.args.parse_args()
            
            # Create new payment with all fields
            new_payment = self.model(
                mpesa_id=args['mpesa_id'],
                account_number=args['account_number'],
                source_phone_number=args['source_phone_number'],
                amount=args['amount'],
                payment_date=args.get('payment_date', datetime.now(timezone.utc)),
                transaction_status=args.get('transaction_status', False),
                bank_id=args['bank_id'],
                block_id=args['block_id'],
                payer_id=args['payer_id'],
                meeting_id=args.get('meeting_id'),
                
                # M-Pesa specific fields
                transaction_type=args.get('transaction_type'),
                business_short_code=args.get('business_short_code'),
                invoice_number=args.get('invoice_number'),
                org_account_balance=args.get('org_account_balance'),
                third_party_trans_id=args.get('third_party_trans_id'),
                first_name=args.get('first_name'),
                middle_name=args.get('middle_name'),
                last_name=args.get('last_name')
            )
            
            db.session.add(new_payment)
            db.session.commit()
            
            logger.info(f"Successfully created payment with ID: {new_payment.id}")
            return marshal(new_payment, self.fields), 201
            
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}", exc_info=True)
            db.session.rollback()
            return {"success": False, "message": "Error creating payment", "details": str(e)}, 500

    def patch(self, id):
        """Update a payment"""
        try:
            payment = db.session.get(PaymentModel, id)
            if not payment:
                abort(404, message=f"Payment with id {id} not found")
                
            args = payment_update_args.parse_args()
            
            for key, value in args.items():
                if value is not None:
                    setattr(payment, key, value)
            
            db.session.commit()
            logger.info(f"Successfully updated payment with ID: {id}")
            return marshal(payment, payment_fields), 200
            
        except Exception as e:
            logger.error(f"Error updating payment with ID {id}: {str(e)}", exc_info=True)
            return handle_error(self, e)

    def delete(self, id):
        """Delete a payment"""
        try:
            payment = db.session.get(PaymentModel, id)
            if not payment:
                abort(404, message=f"Payment with id {id} not found")
                
            db.session.delete(payment)
            db.session.commit()
            return {"message": f"Payment with id {id} deleted successfully"}, 200
            
        except Exception as e:
            logger.error(f"Error deleting payment with ID {id}: {str(e)}", exc_info=True)
            return handle_error(self, e)

    def handle_error(self, e):
        db.session.rollback()

        if isinstance(e, SQLAlchemyError):
            error_message = {"success": False, "message": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)

        elif isinstance(e, HTTPException):
            error_message = {"success": False, "message": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)

        else:
            error_message = {"success": False, "message": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        return error_message

class BlocksResource(BaseResource):
    model = BlockModel
    fields = block_fields
    args = block_args

    def get(self, id=None):
        if self.fields is None:
            return {"success": False, "message": "Internal server error. Please contact support."}, 500

        try:
            if id:
                # Fetch block by ID
                block = self.model.query.get_or_404(id)
                return marshal(block, self.fields), 200

            # Check for 'parent_umbrella_id' parameter to filter blocks
            parent_umbrella_id = request.args.get('parent_umbrella_id')
            query = self.model.query

            if parent_umbrella_id:
                # Filter blocks by parent umbrella ID
                query = query.filter_by(parent_umbrella_id=parent_umbrella_id)

            # Get all matching blocks
            blocks = query.all()
            return marshal(blocks, self.fields), 200

        except Exception as e:
            return self.handle_error(e)
    
    def post(self):
        try:
            args = self.args.parse_args()

            # Generate unique initials for the block name
            initials = BlockModel.block_initials(args['name'])

            # Check for duplicates within the same umbrella
            existing_block = self.model.query.filter_by(
                name=args['name'],
                parent_umbrella_id=args['parent_umbrella_id']
            ).first()

            if existing_block:
                return {"success": False, "message": "Block with this name already exists under the specified umbrella."}, 400

            # Create the new block
            new_block = self.model(
                name=args['name'],
                parent_umbrella_id=args['parent_umbrella_id'],
                created_by=args['created_by'],
                initials=initials
            )

            db.session.add(new_block)
            db.session.commit()

            return marshal(new_block, self.fields), 201

        except Exception as e:
            db.session.rollback()
            return self.handle_error(e)
        
        
class UmbrellasResource(BaseResource):
    model = UmbrellaModel
    fields = umbrella_fields
    args = umbrella_args

    def get(self, id=None):
        if self.fields is None:
            return {"success": False, "message": "Internal server error. Please contact support."}, 500

        try:
            if id:
                # If an umbrella ID is provided, return that specific umbrella
                item = self.model.query.get_or_404(id)
                return marshal(item, self.fields), 200

            # Check for 'created_by' parameter in the request
            created_by = request.args.get('created_by')
            query = self.model.query

            if created_by:
                # Filter umbrellas based on the 'created_by' field
                query = query.filter_by(created_by=created_by)

            # Get all matching umbrellas
            items = query.all()
            return marshal(items, self.fields), 200

        except Exception as e:
            return self.handle_error(e)

    def post(self):
        try:
            args = self.args.parse_args()

            # Generate unique initials based on the umbrella name
            initials = UmbrellaModel.generate_unique_initials(args['name'])

            # Create the new umbrella
            new_umbrella = UmbrellaModel(
                name=args['name'],
                location=args['location'],
                created_by=args['created_by'],
                initials=initials 
            )

            db.session.add(new_umbrella)
            db.session.commit()

            return marshal(new_umbrella, self.fields), 201

        except Exception as e:
            db.session.rollback()
            return self.handle_error(e)

class RolesResource(BaseResource):
    model = RoleModel
    fields = role_fields
    args = role_args


class MeetingsResource(BaseResource):
    model = MeetingModel
    fields = meeting_fields
    args = meeting_args

    def get(self, id=None):
        try:
            # logging.info(f"Incoming request received: {request.url}")

            if id:
                # logging.info(f"Fetching meeting with ID: {id}")
                meeting = self.model.query.get_or_404(id)
                if meeting.date < datetime.now():
                    # logging.info("The meeting date has passed; setting meeting to None.")
                    return {'message': 'No upcoming meeting available'}, 404
                return marshal(meeting, self.fields), 200


            # Get 'organizer_id', 'start', and 'end' query parameters
            organizer_id = request.args.get('organizer_id')
            start_date = request.args.get('start')
            end_date = request.args.get('end')

            # logging.info(f"Query parameters: organizer_id={organizer_id}, start={start_date}, end={end_date}")

            # Check if both 'organizer_id' and date range are provided
            if organizer_id and start_date and end_date:
                # Convert string query params to datetime objects
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
                    end_date = datetime.strptime(end_date, '%Y-%m-%d')
                    # logging.info(f"Parsed start date: {start_date}, end date: {end_date}")

                except ValueError:
                    # logging.error(f"Invalid date format received: start={start_date}, end={end_date}")

                    return {'error': 'Invalid date format. Use YYYY-MM-DD.'}, 400

                # Fetch meetings by organizer_id within the provided date range
                meetings = MeetingModel.query.filter(MeetingModel.organizer_id == organizer_id,
                                                     MeetingModel.date >= start_date,
                                                     MeetingModel.date <= end_date).all()
                # logging.info(f"Meetings found: {len(meetings)}")

                if meetings:
                    # Prepare details for all meetings within the date range
                    meeting_details = []
                    for meeting in meetings:
                        host = meeting.host
                        paybill_no = host.bank.paybill_no if host and host.bank else 'Unknown Paybill'
                        acc_number = host.acc_number if host else 'Unknown Account'

                        details = {
                            'meeting_block': meeting.block.name if meeting.block else 'Unknown Block',
                            'meeting_zone': meeting.zone.name if meeting.zone else 'Unknown Zone',
                            'host': meeting.host.full_name if meeting.host else 'Unknown Host',
                            'paybill_no': paybill_no,
                            'acc_number': acc_number,
                            'meeting_id':meeting.id,
                            'when': meeting.date.strftime('%a, %d %b %Y %H:%M:%S'),
                            'event_id': meeting.unique_id
                        }
                        meeting_details.append(details)
                    # logging.info(f"Meeting details: {meeting_details}")

                    return meeting_details, 200
                else:
                    return {'message': 'No meetings found for the organizer within the specified date range'}, 404

            # If only 'organizer_id' is provided (no date range)
            if organizer_id:
                # Fetch all meetings by this organizer
                meetings = MeetingModel.query.filter_by(organizer_id=organizer_id).all()

                if meetings:
                    meeting_details = []
                    for meeting in meetings:
                        host = meeting.host
                        paybill_no = host.bank.paybill_no if host and host.bank else 'Unknown Paybill'
                        acc_number = host.acc_number if host else 'Unknown Account'

                        details = {
                            'meeting_block': meeting.block.name if meeting.block else 'Unknown Block',
                            'meeting_zone': meeting.zone.name if meeting.zone else 'Unknown Zone',
                            'host': meeting.host.full_name if meeting.host else 'Unknown Host',
                            'event_id': meeting.unique_id,
                            'paybill_no': paybill_no,
                            'acc_number': acc_number,
                            'meeting_id':meeting.id,
                            'when': meeting.date.strftime('%a, %d %b %Y %H:%M:%S')
                        }
                        meeting_details.append(details)

                    return meeting_details, 200
                else:
                    # logging.warning(f"No meetings found for organizer_id={organizer_id} within date range.")

                    return {'message': 'No meetings found for this organizer'}, 404

            # Check for 'start' and 'end' date filtering without 'organizer_id'
            if start_date and end_date:
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
                    end_date = datetime.strptime(end_date, '%Y-%m-%d')
                except ValueError:
                    return {'error': 'Invalid date format. Use YYYY-MM-DD.'}, 400

                # Fetch meetings within the provided date range
                meetings = MeetingModel.query.filter(MeetingModel.date >= start_date,
                                                     MeetingModel.date <= end_date).all()

                if meetings:

                    meeting_details = []
                    for meeting in meetings:
                        host = meeting.host
                        paybill_no = host.bank.paybill_no if host and host.bank else 'Unknown Paybill'
                        acc_number = host.acc_number if host else 'Unknown Account'

                        details = {
                            'meeting_block': meeting.block.name if meeting.block else 'Unknown Block',
                            'meeting_zone': meeting.zone.name if meeting.zone else 'Unknown Zone',
                            'host': meeting.host.full_name if meeting.host else 'Unknown Host',
                            'paybill_no': paybill_no,
                            'acc_number': acc_number,
                            'meeting_id':meeting.id,
                            'event_id': meeting.unique_id,
                            'when': meeting.date.strftime('%a, %d %b %Y %H:%M:%S')
                        }
                        meeting_details.append(details)

                    return meeting_details, 200
                else:
                    return {'message': 'No meetings found within the specified date range'}, 404

            # If no parameters are provided, fetch all meetings
            meetings = MeetingModel.query.all()
            if meetings:
                return marshal(meetings, self.fields), 200
            else:
                return {'message': 'No meetings found'}, 404

        except Exception as e:
            # logging.error(f"Exception in MeetingsResource: {e}", exc_info=True)

            return self.handle_error(e)


    def post(self):
        try:
            # Parse the request arguments
            args = self.args.parse_args()

            block_id = args.get('block_id')
            zone_id = args.get('zone_id')
            date = args.get('date')
            
            if not block_id or not zone_id or not date:
                return {'error': 'Block ID, Zone ID, and date are required'}, 400

            # Convert the 'date' argument from string to a datetime object
            try:
                meeting_date = datetime.strptime(args['date'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return {'error': 'Invalid date format, expected YYYY-MM-DD HH:MM:SS'}, 400
            
            block = BlockModel.query.get(block_id)
            if not block:
                return {'error': 'Block not found'}, 404
            zone = ZoneModel.query.filter_by(id=zone_id, parent_block_id=block_id).first()
            if not zone:
                return {'error': 'Zone does not belong to the specified block'}, 400

            umbrella_id = block.parent_umbrella_id
            # Get the current week range (start and end of the week)
            week_start = meeting_date - timedelta(days=meeting_date.weekday())
            week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

             # Check if there's already a meeting scheduled in any block for this week
            existing_meeting = self.model.query.join(
                BlockModel, self.model.block_id == BlockModel.id
            ).filter(
                MeetingModel.block_id == block_id,
                MeetingModel.zone_id == zone_id,
                BlockModel.parent_umbrella_id == block.parent_umbrella_id,
                self.model.date >= week_start,
                self.model.date <= week_end
            ).first()

            if existing_meeting:
                return {
                                'error': 'A meeting is already scheduled this week.',
                                'block': block_id,
                                'zone': zone_id,
                                'umbrella': block.parent_umbrella_id
                            }, 409
            # Create the new meeting object with parsed date
            new_meeting = self.model(
                host_id=args['host_id'],
                block_id=block_id,
                zone_id=zone_id,
                organizer_id=args['organizer_id'],
                date=meeting_date
            )

            # Add and commit the new meeting to the database
            db.session.add(new_meeting)
            db.session.commit()

            # Return the newly created meeting
            return marshal(new_meeting, self.fields), 201

        except Exception as e:
            return self.handle_error(e)

    def patch(self, id):
        try:
            args = self.args.parse_args()
            meeting = self.model.query.get_or_404(id)

            # Validate date if provided
            if args.get('date'):
                try:
                    updated_date = datetime.strptime(args['date'], '%Y-%m-%d %H:%M:%S')
                    if updated_date < datetime.now():
                        return {'error': 'Meeting date must be in the future'}, 400
                    args['date'] = updated_date
                except ValueError:
                    return {'error': 'Invalid date format, expected YYYY-MM-DD HH:MM:SS'}, 400

            # Validate block and zone relationship if provided
            if args.get('block_id') and args.get('zone_id'):
                block = BlockModel.query.get(args['block_id'])
                zone = ZoneModel.query.filter_by(id=args['zone_id'], parent_block_id=args['block_id']).first()
                if not block or not zone:
                    return {'error': 'Zone does not belong to the specified block'}, 400

            # Update fields dynamically
            for key, value in args.items():
                if value is not None:
                    setattr(meeting, key, value)

            db.session.commit()
            return marshal(meeting, self.fields), 200

        except Exception as e:
            return self.handle_error(e)


class ZonesResource(BaseResource):
    model = ZoneModel
    fields = zone_fields
    args = zone_args

    def get(self, id=None):
        # logging.debug(f"Received GET request for zones. ID: {id}, Args: {request.args}")
        try:
            if id:
                return super().get(id)

            parent_block_id = request.args.get('parent_block_id')
            # logging.debug(f"Parent block ID from query params: {parent_block_id}")

            query = self.model.query
            if parent_block_id:
                query = query.filter_by(parent_block_id=parent_block_id)

            zones = query.all()
            # logging.debug(f"Found {len(zones)} zones")
            result = marshal(zones, self.fields)
            return result, 200
        except Exception as e:
            # logging.error(f"Error in ZonesResource.get: {str(e)}", exc_info=True)
            return self.handle_error(e)

class MpesaValidationResource(BaseResource):
    model = PaymentModel
    fields = mpesa_validation_fields
    args = mpesa_validation_args

    def get(self, id=None):
        return super().get(id)

    def post(self):
        """Handle M-Pesa validation requests for both STK push and direct payments"""
        try:
            # Parse and validate incoming data
            args = self.args.parse_args()
            logger.info(f"Received M-Pesa validation: {args}")
            
            # Validate amount is positive
            if args['TransAmount'] <= 0:
                logger.error("Invalid amount: must be positive")
                return {
                    "ResultCode": "C2B00012",
                    "ResultDesc": "Invalid amount: must be positive"
                }
            
            # Get bill reference number (meeting unique_id)
            bill_ref = args['BillRefNumber']
            
            # Find the meeting using the bill reference
            meeting = MeetingModel.query.filter_by(unique_id=bill_ref).first()
            if not meeting:
                logger.error(f"Meeting not found for bill reference: {bill_ref}")
                return {
                    "ResultCode": "C2B00012",
                    "ResultDesc": "Invalid bill reference number"
                }
                
            # For direct payments, we need to find the member by phone number
            msisdn = args['MSISDN']  # Phone number making payment
            if msisdn.startswith('+254'):
                msisdn = msisdn[4:]
            elif msisdn.startswith('0'):
                msisdn = msisdn[1:]
            msisdn = '254' + msisdn
            
            # Find member by phone number
            member = UserModel.query.filter_by(phone_number=msisdn).first()
            if not member:
                logger.error(f"Member not found for phone number: {msisdn}")
                return {
                    "ResultCode": "C2B00012",
                    "ResultDesc": "Member not found for this phone number"
                }
            
            # Check if member belongs to the meeting's block
            if not member.blocks.filter_by(id=meeting.block_id).first():
                logger.error(f"Member {member.id} does not belong to block {meeting.block_id}")
                return {
                    "ResultCode": "C2B00012",
                    "ResultDesc": "Member does not belong to this block"
                }
                
            # Validation successful
            return {
                "ResultCode": "0",
                "ResultDesc": "Success"
            }
            
        except Exception as e:
            logger.error(f"Error in validation endpoint: {str(e)}", exc_info=True)
            return {
                "ResultCode": "1",
                "ResultDesc": "Internal server error"
            }

    def patch(self, id):
        return super().patch(id)

    def delete(self, id):
        return super().delete(id)

class MpesaConfirmationResource(BaseResource):
    model = PaymentModel
    fields = mpesa_confirmation_fields
    args = mpesa_confirmation_args

    def get(self, id=None):
        return super().get(id)

    def post(self):
        """Handle M-Pesa confirmation callback"""
        try:
            # Parse and validate incoming data
            args = self.args.parse_args()
            logger.info(f"Received M-Pesa confirmation: {args}")
            
            # Validate amount is positive
            if args['TransAmount'] <= 0:
                logger.error("Invalid amount: must be positive")
                return {
                    "ResultCode": "C2B00012",
                    "ResultDesc": "Invalid amount: must be positive"
                }
            
            # Validate TransTime format if provided
            if args.get('TransTime'):
                try:
                    datetime.strptime(args['TransTime'], '%Y%m%d%H%M%S')
                except ValueError:
                    logger.error(f"Invalid transaction time format: {args['TransTime']}")
                    return {
                        "ResultCode": "C2B00012",
                        "ResultDesc": "Invalid transaction time format"
                    }
            
            # Find the umbrella meeting using bill reference (meeting unique_id)
            meeting = MeetingModel.query.filter_by(unique_id=args['BillRefNumber']).first()
            if not meeting:
                logger.error(f"Meeting not found for bill reference: {args['BillRefNumber']}")
                return {
                    "ResultCode": "C2B00012",
                    "ResultDesc": "Invalid bill reference number"
                }

            # Format phone number consistently
            msisdn = args['MSISDN']
            if msisdn.startswith('+254'):
                msisdn = msisdn[4:]
            elif msisdn.startswith('0'):
                msisdn = msisdn[1:]
            msisdn = '254' + msisdn

            # Find member by phone number
            member = UserModel.query.filter_by(phone_number=msisdn).first()
            if not member:
                logger.error(f"Member not found for phone number: {msisdn}")
                return {
                    "ResultCode": "C2B00012",
                    "ResultDesc": "Member not found for this phone number"
                }

            # Get the block from the meeting
            block = meeting.block
            if not block:
                logger.error(f"Block not found for meeting: {meeting.id}")
                return {
                    "ResultCode": "C2B00012",
                    "ResultDesc": "Meeting block not found"
                }

            # Verify member belongs to the umbrella
            if not member.blocks.filter_by(parent_umbrella_id=block.parent_umbrella_id).first():
                logger.error(f"Member {member.id} does not belong to umbrella of block {block.id}")
                return {
                    "ResultCode": "C2B00012",
                    "ResultDesc": "Member does not belong to this umbrella"
                }
                
            # Check for duplicate transaction
            existing_payment = self.model.query.filter_by(mpesa_id=args['TransID']).first()
            if existing_payment:
                logger.warning(f"Duplicate M-Pesa transaction: {args['TransID']}")
                return {
                    "ResultCode": "0",
                    "ResultDesc": "Success",
                    "payment": existing_payment
                }
                
            # Create new payment record
            try:
                payment = self.model(
                    mpesa_id=args['TransID'],
                    account_number=args['BillRefNumber'],
                    source_phone_number=msisdn,
                    amount=int(float(args['TransAmount'])),
                    payment_date=datetime.strptime(args['TransTime'], '%Y%m%d%H%M%S') if args.get('TransTime') else datetime.now(timezone.utc),
                    transaction_status=True,
                    transaction_type=args['TransactionType'],
                    business_short_code=args['BusinessShortCode'],
                    invoice_number=args.get('InvoiceNumber'),
                    first_name=args.get('FirstName'),
                    middle_name=args.get('MiddleName'),
                    last_name=args.get('LastName'),
                    bank_id=1,  # Set default bank_id
                    block_id=block.id,
                    payer_id=member.id,
                    meeting_id=meeting.id  # Associate payment with the meeting
                )
                
                db.session.add(payment)
                db.session.commit()
                logger.info(f"Successfully saved payment: {args['TransID']} for meeting {meeting.unique_id}")
                
                return {
                    "ResultCode": "0",
                    "ResultDesc": "Success",
                    "payment": payment
                }
                
            except Exception as e:
                logger.error(f"Error saving payment: {str(e)}")
                db.session.rollback()
                return {
                    "ResultCode": "1",
                    "ResultDesc": "Internal server error"
                }
                
        except Exception as e:
            logger.error(f"Error processing M-Pesa confirmation: {str(e)}", exc_info=True)
            return {
                "ResultCode": "1",
                "ResultDesc": f"Error: {str(e)}"
            }

    def patch(self, id):
        return super().patch(id)

    def delete(self, id):
        return super().delete(id)

class MpesaStkCallback(BaseResource):
    """Handle callbacks from STK Push requests"""
    
    def post(self):
        try:
            # Parse the callback data
            data = request.get_json()
            logger.info(f"Received STK callback: {data}")
            
            # Extract the relevant data
            body = data.get('Body', {}).get('stkCallback', {})
            merchant_request_id = body.get('MerchantRequestID')
            checkout_request_id = body.get('CheckoutRequestID')
            result_code = body.get('ResultCode')
            result_desc = body.get('ResultDesc')
            
            # Find the payment by checkout_request_id
            payment = PaymentModel.query.filter_by(checkout_request_id=checkout_request_id).first()
            if not payment:
                logger.error(f"Payment not found for checkout_request_id: {checkout_request_id}")
                return {"ResultCode": "1", "ResultDesc": "Payment not found"}
            
            # Update payment status based on result
            if result_code == 0:  # Success
                payment.status = 'completed'
                payment.completed_at = datetime.now()
                payment.transaction_status = True
                
                # Extract payment details
                callback_metadata = body.get('CallbackMetadata', {}).get('Item', [])
                for item in callback_metadata:
                    if item['Name'] == 'MpesaReceiptNumber':
                        payment.mpesa_id = item['Value']
                    elif item['Name'] == 'Amount':
                        payment.amount = item['Value']
                    elif item['Name'] == 'TransactionDate':
                        payment.payment_date = datetime.strptime(str(item['Value']), '%Y%m%d%H%M%S')
                    elif item['Name'] == 'PhoneNumber':
                        payment.source_phone_number = str(item['Value'])
                
            else:  # Failed
                payment.status = 'failed'
                payment.failed_at = datetime.now()
                payment.status_reason = result_desc
                payment.transaction_status = False
                
                # If payment failed due to a retryable reason, increment retry count
                retryable_codes = [1001, 1002, 1003]  # Add relevant M-Pesa error codes
                if result_code in retryable_codes and payment.retry_count < 3:
                    payment.retry_count += 1
                    payment.last_retry_at = datetime.now()
                    
                    # Schedule a retry
                    try:
                        mpesa = get_mpesa_client()
                        response = mpesa.initiate_stk_push(
                            phone_number=payment.source_phone_number,
                            amount=payment.amount,
                            account_reference=payment.account_number
                        )
                        
                        # Update payment with new request IDs
                        payment.checkout_request_id = response.get('CheckoutRequestID')
                        payment.merchant_request_id = response.get('MerchantRequestID')
                        payment.status = 'pending'
                        logger.info(f"Retrying payment {payment.id}, attempt {payment.retry_count}")
                        
                    except Exception as e:
                        logger.error(f"Failed to retry payment {payment.id}: {str(e)}")
            
            # Save changes
            db.session.commit()
            logger.info(f"Updated payment {payment.id} status to {payment.status}")
            
            return {"ResultCode": "0", "ResultDesc": "Success"}
            
        except Exception as e:
            logger.error(f"Error processing STK callback: {str(e)}", exc_info=True)
            return {"ResultCode": "1", "ResultDesc": f"Error: {str(e)}"}

# API routes
api.add_resource(UsersResource, '/users/', '/users/<int:id>')
api.add_resource(CommunicationsResource, '/communications/', '/communications/<int:id>')
api.add_resource(BanksResource, '/banks/', '/banks/<int:id>')
api.add_resource(PaymentsResource, '/payments/', '/payments/<int:id>')
api.add_resource(BlocksResource, '/blocks/', '/blocks/<int:id>')
api.add_resource(UmbrellasResource, '/umbrellas/', '/umbrellas/<int:id>')
api.add_resource(RolesResource, '/roles/', '/roles/<int:id>')
api.add_resource(MeetingsResource, '/meetings/', '/meetings/<int:id>')
api.add_resource(ZonesResource, '/zones/', '/zones/<int:id>')
api.add_resource(MpesaValidationResource, '/v1/payments/c2b/validation')
api.add_resource(MpesaConfirmationResource, '/v1/payments/c2b/confirmation')
api.add_resource(MpesaStkCallback, '/v1/payments/stk/callback')
