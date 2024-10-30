from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from werkzeug.exceptions import HTTPException
from flask_restful import Api, Resource, marshal_with, marshal, abort
from ..main.models import UserModel, CommunicationModel, \
    PaymentModel, BankModel, BlockModel, UmbrellaModel, ZoneModel, MeetingModel, RoleModel, roles_users
from .serializers import get_user_fields, user_args, communication_fields, \
    communication_args, payment_fields, payment_args, bank_fields, bank_args, \
    block_fields, block_args, umbrella_fields, umbrella_args, zone_fields, zone_args, \
    meeting_fields, meeting_args,role_args,role_fields
from ..utils import db
import logging
from ..main.routes import save_picture
from sqlalchemy.orm import joinedload



api_bp = Blueprint('api', __name__)
api = Api(api_bp)



# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def handle_error(self, e):
    db.session.rollback()
    
    if isinstance(e, SQLAlchemyError):
        logging.error(f"Database error: {str(e)}", exc_info=True)
        error_message = {"success": False, "message": "Database error occurred", "details": str(e)}
        status_code = 500
    elif isinstance(e, HTTPException):
        logging.error(f"HTTP error: {str(e)}", exc_info=True)
        error_message = {"success": False, "message": "HTTP error occurred", "details": str(e)}
        status_code = e.code
    else:
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
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
                logger.info(f"GET request received for user {id}")
                user = self.model.query.get_or_404(id)
                logger.info(f"User zone_id: {user.zone_id}, bank_id: {user.bank_id}")

                if user.zone_id:
                    user.zone_name = ZoneModel.query.filter_by(id=user.zone_id).first().name if user.zone_id else None
                    
                if user.bank_id:
                    user.bank_name = BankModel.query.filter_by(id=user.bank_id).first().name if user.bank_id else None

                if not user:
                    logger.info(f"User with ID {id} not found")
                    return {"message": "User not found"}, 404
                return marshal(user, self.fields), 200

              

            # Check for query parameters: role, id_number, umbrella_id, and zone_id
            role_name = request.args.get('role')
            id_number = request.args.get('id_number')
            umbrella_id = request.args.get('umbrella_id')
            zone_id = request.args.get('zone_id') 

            # Fetch user by id_number if provided
            if id_number:
                logger.info(f"GET request received for user with id_number {id_number}")
                user = self.model.query.filter_by(id_number=id_number).first()
                if not user:
                    return {"message": "User not found"}, 404
                return marshal(user, self.fields), 200

            # Fetch users by role, umbrella, and zone if all are provided
            if role_name and umbrella_id:
                logger.info(f"GET request received for users with role {role_name}, umbrella {umbrella_id}, and zone {zone_id}")
                users = (
                    self.model.query
                    .join(UserModel.roles)
                    .join(UserModel.block_memberships)
                    .filter(RoleModel.name == role_name)
                    .filter(BlockModel.parent_umbrella_id == umbrella_id)
                    .all()
                )
                if zone_id:
                    query = query.filter(UserModel.zone_id == zone_id)
            
                return marshal(users, self.fields), 200

            # Fetch users by role and umbrella if both are provided
            if role_name and umbrella_id:
                logger.info(f"GET request received for users with role {role_name} and umbrella {umbrella_id}")
                users = (
                    self.model.query
                    .join(UserModel.roles)
                    .join(UserModel.block_memberships)
                    .filter(RoleModel.name == role_name)
                    .filter(BlockModel.parent_umbrella_id == umbrella_id)
                    .all()
                )
                return marshal(users, self.fields), 200
            


            # Fetch users by role if role_name is provided (without umbrella)
            if role_name:
                logger.info(f"GET request received for users with role {role_name}")
                users = self.model.query.join(UserModel.roles).filter(RoleModel.name == role_name).all()
                return marshal(users, self.fields), 200

            # Fetch all users if no filters are provided
            logger.info("GET request received for all users")
            users = self.model.query.all()
            for user in users:
                if user.zone_id:
                    user.zone_name = ZoneModel.query.filter_by(id=user.zone_id).first().name if user.zone_id else None

                if user.bank_id:
                    bank = BankModel.query.get(user.bank_id)
                    logger.info(f"Bank fetched: {bank}")
                    if bank:
                        user.bank_name = bank.name
            return marshal(users, self.fields), 200

        except Exception as e:
            logger.error(f"Error retrieving users: {str(e)}")
            return self.handle_error(e)


    def post(self):
        try:
            args = self.args.parse_args()
            logger.info(f"POST request received to create new user. Payload: {args}")
    
            # Check for umbrella and generate initials for unique member identifier
            umbrella = UmbrellaModel.query.get(args['umbrella_id'])
            if not umbrella:
                return {"message": "Umbrella does not exist."}, 400

            # Generate unique member identifier based on umbrella initials
            unique_id = UserModel.generate_member_identifier(umbrella)
            

            # Create the new user
            new_user = UserModel(
                full_name=args['full_name'],
                id_number=args['id_number'],
                phone_number=args['phone_number'],
                zone_id=args['zone_id'],
                bank_id=args['bank_id'],
                acc_number=args['acc_number'],
                unique_id=unique_id,
                umbrella_id=args['umbrella_id']
            )
                    
            db.session.add(new_user)
                   # Assign the role if role_id is provided
            if 'role_id' in args and args['role_id'] is not None:
                role = RoleModel.query.get(args['role_id'])
                if role:
                    new_user.roles.append(role)

            zone_id = args.get('zone_id')
            if zone_id is not None:
                zone = ZoneModel.query.get(zone_id)
                if zone:
                    new_user.zone_memberships.append(zone)
                          

            # Fetch the block associated with the selected zone
            zone = ZoneModel.query.get(args['zone_id'])
            if zone and zone.parent_block_id:
                block = BlockModel.query.get(zone.parent_block_id)  
                if block:
                    new_user.block_memberships.append(block)  

            db.session.commit()
            logger.info(f"Successfully created user {new_user.id} with roles {[r.name for r in new_user.roles]},block memberships {[b.name for b in new_user.block_memberships]} and zone memberships {[z.name for z in new_user.zone_memberships]}")

            return marshal(new_user, self.fields), 201
        
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Duplicate entry detected: {str(e)}")
            return {"message": "A member with this ID number, phone number, or account number already exists in this zone."}, 400


        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating new user: {str(e)}. Rolling back changes.")
            return self.handle_error(e)
 
        
    def patch(self, id):
        try:
            args = self.args.parse_args() if 'multipart/form-data' not in request.content_type else {}
            
            user = UserModel.query.get_or_404(id)
            updated = False

            if 'multipart/form-data' in request.content_type:
                logger.info("Handling multipart form data for profile update")
                if 'picture' in request.files:
                    image_file = request.files['picture']
                    if image_file:
                        saved_filename = save_picture(image_file)
                        user.image_file = saved_filename
                        updated = True
                    else:
                        logger.error("No image file provided in multipart request")
                        return {"message": "No image file provided."}, 400
            else:
                logger.info(f"PATCH request received to update user {id}. Payload: {args}")
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
                        logger.warning("Cannot assign Chairman role when the user already has the Secretary or Umbrella Treasurer role.")
                        return {"message": "Cannot assign Chairman when the user is already a Secretary or Treasurer."}, 400

                    elif role_id == 4 and any(r.id in [3, 6] for r in user.roles):
                        logger.warning("Cannot assign Secretary role when the user already has the Chairman or Treasurer role.")
                        return {"message": "Cannot assign Secretary when the user is already a Chairman or Treasurer."}, 400

                    elif role_id == 6 and any(r.id in [3, 4] for r in user.roles):
                        logger.warning("Cannot assign Treasurer role when the user already has the Chairman or Secretary role.")
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
                                logger.info(f"Removed role {role.name} from user {user.id}")
                                updated = True

                                # Remove the block from the corresponding block list
                                if block_id:
                                    if role_id == 3:  # Chairman
                                        user.chaired_blocks = [b for b in user.chaired_blocks if b.id != block_id]
                                        logger.info(f"Removed block {block_id} from user's chaired_blocks.")
                                    elif role_id == 4:  # Secretary
                                        user.secretary_blocks = [b for b in user.secretary_blocks if b.id != block_id]
                                        logger.info(f"Removed block {block_id} from user's secretary_blocks.")
                                    elif role_id == 6:  # Treasurer
                                        user.treasurer_blocks = [b for b in user.treasurer_blocks if b.id != block_id]
                                        logger.info(f"Removed block {block_id} from user's treasurer_blocks.")

                        else:
                            return {"message": "User does not have this role"}, 400


                    # Handle Role Addition
                    elif action == 'add':
                        if role in user.roles:
                            logger.info(f"User {user.id} already has the role {role.name}.")
                            return {"message": f"User already has the role '{role.name}'."}, 400
                        else:
                            user.roles.append(role)  # Add the role if it's not already assigned
                            logger.info(f"Assigned additional role {role.name} to user {user.id}")
                            updated = True

                    # Update Blocks Based on Role
                    block_id = args.get('block_id')
                    if block_id is not None:
                        block = BlockModel.query.get(block_id)
                        if block:
                            if role_id == 3:  # Chairman
                                if block not in user.chaired_blocks:
                                    user.chaired_blocks.append(block)
                                    logger.info(f"Added block {block.id} to user's chaired_blocks.")

                            elif role_id == 4:  # Secretary
                                if block not in user.secretary_blocks:
                                    user.secretary_blocks.append(block)
                                    logger.info(f"Added block {block.id} to user's secretary_blocks.")

                            elif role_id == 5:  # Treasurer
                                if block not in user.treasurer_blocks:
                                    user.treasurer_blocks.append(block)
                                    logger.info(f"Added block {block.id} to user's treasurer_blocks.")
                        else:
                            logger.warning(f"Block {block_id} not found.")

            if updated:
                db.session.commit()
                logger.info(f"Successfully updated user {user.id} with roles {[r.name for r in user.roles]}")
                return marshal(user, self.fields), 200

            return {"message": "No updates made to user."}, 400

        except Exception as e:
            logger.error(f"Error updating user {id}: {str(e)}")
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
        if id:
            # Fetch a specific payment by ID
            return super().get(id)
        
        # Check if a meeting_id query parameter is provided
        meeting_id = request.args.get('meeting_id', None)
        
        if meeting_id:
            try:
                logger.info(f"Fetching payments for meeting ID: {meeting_id}")

                # Query payments by meeting_id and join payer (user) and block tables
                payments = PaymentModel.query \
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

        
    def post(self):
        args = self.args.parse_args()
        
        # Check if the meeting exists
        meeting = MeetingModel.query.get(args['meeting_id'])
        if not meeting:
            return {'message': 'Meeting not found.'}, 404
        
        # Check if the block exists
        block = BlockModel.query.get(args['block_id'])
        if not block:
            return {'message': 'Block not found.'}, 404
        
        # Create a new payment
        new_payment = PaymentModel(
            mpesa_id=args['mpesa_id'],
            account_number=args['account_number'],
            source_phone_number=args['source_phone_number'],
            amount=args['amount'],
            bank_id=args['bank_id'],
            block_id=args['block_id'],
            payer_id=args['payer_id'],
            meeting_id=args['meeting_id']
        )
        if new_payment.amount > 200:
            new_payment.transaction_status = True

        db.session.add(new_payment)
        db.session.commit()
        
        
        return marshal(new_payment,self.fields), 201


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
            logger.info(f"POST request received to create new umbrella. Payload: {args}")

            # Generate unique initials based on the umbrella name
            initials = UmbrellaModel.generate_unique_initials(args['name'])

            # Create the new umbrella
            new_umbrella = UmbrellaModel(
                name=args['name'],
                location=args['location'],
                created_by=args['created_by'],
                initials=initials  # Set the generated initials here
            )

            db.session.add(new_umbrella)
            db.session.commit()

            logger.info(f"Successfully created umbrella {new_umbrella.id} with initials {initials}")
            return marshal(new_umbrella, self.fields), 201
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating new umbrella: {str(e)}. Rolling back changes.")
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
            logging.info(f"Incoming request received: {request.url}")

            # Fetch meeting by ID if 'id' is provided
            if id:
                logging.info(f"Fetching meeting with ID: {id}")

                meeting = self.model.query.get_or_404(id)
                return marshal(meeting, self.fields), 200

            # Get 'organizer_id', 'start', and 'end' query parameters
            organizer_id = request.args.get('organizer_id')
            start_date = request.args.get('start')
            end_date = request.args.get('end')

            logging.info(f"Query parameters: organizer_id={organizer_id}, start={start_date}, end={end_date}")

            # Check if both 'organizer_id' and date range are provided
            if organizer_id and start_date and end_date:
                # Convert string query params to datetime objects
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
                    end_date = datetime.strptime(end_date, '%Y-%m-%d')
                    logging.info(f"Parsed start date: {start_date}, end date: {end_date}")

                except ValueError:
                    logging.error(f"Invalid date format received: start={start_date}, end={end_date}")

                    return {'error': 'Invalid date format. Use YYYY-MM-DD.'}, 400

                # Fetch meetings by organizer_id within the provided date range
                meetings = MeetingModel.query.filter(MeetingModel.organizer_id == organizer_id,
                                                     MeetingModel.date >= start_date,
                                                     MeetingModel.date <= end_date).all()
                logging.info(f"Meetings found: {len(meetings)}")

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
                            'when': meeting.date.strftime('%a, %d %b %Y %H:%M:%S'),
                            'meeting_id':meeting.id
                        }
                        meeting_details.append(details)
                    logging.info(f"Meeting details: {meeting_details}")

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
                            'meeting_id':meeting.id,
                            'paybill_no': paybill_no,
                            'acc_number': acc_number,
                            'when': meeting.date.strftime('%a, %d %b %Y %H:%M:%S')
                        }
                        meeting_details.append(details)

                    return meeting_details, 200
                else:
                    logging.warning(f"No meetings found for organizer_id={organizer_id} within date range.")

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
            logging.error(f"Exception in MeetingsResource: {e}", exc_info=True)

            return self.handle_error(e)


    def post(self):
        try:
            # Parse the request arguments
            args = self.args.parse_args()

            # Convert the 'date' argument from string to a datetime object
            try:
                meeting_date = datetime.strptime(args['date'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return {'error': 'Invalid date format, expected YYYY-MM-DD HH:MM:SS'}, 400

            # Get the current week range (start and end of the week)
            week_start = meeting_date - timedelta(days=meeting_date.weekday())
            week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

             # Check if there's already a meeting scheduled in any block for this week
            existing_meeting = self.model.query.filter(
                self.model.date >= week_start,
                self.model.date <= week_end
            ).first()

            if existing_meeting:
                return {'error': f'A meeting is already scheduled this week.', 'block': existing_meeting.block_id}, 400

            # Create the new meeting object with parsed date
            new_meeting = self.model(
                host_id=args['host_id'],
                block_id=args['block_id'],
                zone_id=args['zone_id'],
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

class ZonesResource(BaseResource):
    model = ZoneModel
    fields = zone_fields
    args = zone_args

    def get(self, id=None):
        logging.debug(f"Received GET request for zones. ID: {id}, Args: {request.args}")
        try:
            if id:
                return super().get(id)
            
            parent_block_id = request.args.get('parent_block_id')
            logging.debug(f"Parent block ID from query params: {parent_block_id}")

            query = self.model.query
            if parent_block_id:
                query = query.filter_by(parent_block_id=parent_block_id)

            zones = query.all()
            logging.debug(f"Found {len(zones)} zones")
            result = marshal(zones, self.fields)
            return result, 200
        except Exception as e:
            logging.error(f"Error in ZonesResource.get: {str(e)}", exc_info=True)
            return self.handle_error(e)




# API routes
api.add_resource(UsersResource, '/users/', '/users/<int:id>', '/users/<int:id>/roles/')
api.add_resource(CommunicationsResource, '/communications/', '/communications/<int:id>')
api.add_resource(BanksResource, '/banks/', '/banks/<int:id>')
api.add_resource(PaymentsResource, '/payments/', '/payments/<int:id>')
api.add_resource(BlocksResource, '/blocks/', '/blocks/<int:id>')
api.add_resource(UmbrellasResource, '/umbrellas/', '/umbrellas/<int:id>')
api.add_resource(ZonesResource, '/zones/', '/zones/<int:id>')
api.add_resource(MeetingsResource, '/meetings/', '/meetings/<int:id>')
api.add_resource(RolesResource, '/roles/','/roles/<int:id>')


