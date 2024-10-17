from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from datetime import datetime
from flask import Blueprint, jsonify, request
from werkzeug.exceptions import HTTPException
from flask_restful import Api, Resource, marshal_with, marshal, abort,reqparse
from ..main.models import UserModel, CommunicationModel, \
    PaymentModel, BankModel, BlockModel, UmbrellaModel, ZoneModel, MeetingModel, RoleModel, roles_users
from .serializers import get_user_fields, user_args, communication_fields, \
    communication_args, payment_fields, payment_args, bank_fields, bank_args, \
    block_fields, block_args, umbrella_fields, umbrella_args, zone_fields, zone_args, \
    meeting_fields, meeting_args, block_report_args, block_report_fields,role_args,role_fields
from ..utils import db
import logging
from ..main.routes import save_picture


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
                return marshal(user, self.fields), 200

            # Check for query parameters: role and id_number
            role_name = request.args.get('role')
            id_number = request.args.get('id_number')

            # Fetch user by id_number if provided
            if id_number:
                logger.info(f"GET request received for user with id_number {id_number}")
                user = self.model.query.filter_by(id_number=id_number).first()
                if not user:
                    return {"message": "User not found"}, 404
                return marshal(user, self.fields), 200

            # Fetch users by role if role_name is provided
            if role_name:
                logger.info(f"GET request received for users with role {role_name}")
                users = self.model.query.join(UserModel.roles).filter(RoleModel.name == role_name).all()
                return marshal(users, self.fields), 200

            # Otherwise, return all users
            logger.info("GET request received for all users")
            users = self.model.query.all()

            return marshal(users, self.fields), 200

        except Exception as e:
            logger.error(f"Error retrieving users: {str(e)}")
            return self.handle_error(e)


    def post(self):
        try:
            args = self.args.parse_args()
            logger.info(f"POST request received to create new user. Payload: {args}")

            # Create the new user
            new_user = UserModel(
                full_name=args['full_name'],
                id_number=args['id_number'],
                phone_number=args['phone_number'],
                zone_id=args['zone_id'],
                bank_id=args['bank_id'],
                acc_number=args['acc_number']
            )

           # Assign the role if role_id is provided
            if 'role_id' in args and args['role_id'] is not None:
                role = RoleModel.query.get(args['role_id'])
                if role:
                    new_user.roles.append(role)

            # Fetch the block associated with the selected zone
            zone = ZoneModel.query.get(args['zone_id'])
            if zone and zone.parent_block_id:
                block = BlockModel.query.get(zone.parent_block_id)  
                if block:
                    new_user.block_memberships.append(block)  

                    
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"Successfully created user {new_user.id} with roles {[r.name for r in new_user.roles]} and block memberships {[b.name for b in new_user.block_memberships]}")

            return marshal(new_user, self.fields), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating new user: {str(e)}. Rolling back changes.")
            return self.handle_error(e)
 
        
    def patch(self, id):
        try:
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
                args = self.args.parse_args()
                logger.info(f"PATCH request received to update user {id}. Payload: {args}")
                unchanged_fields = []

                for field in ['full_name', 'id_number', 'phone_number', 'zone_id', 'bank_id', 'acc_number', 'email', 'image_file']:
                    if args[field] is not None and getattr(user, field) != args[field]:
                        setattr(user, field, args[field])
                        updated = True
                    else:
                        unchanged_fields.append(field)

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

class BlocksResource(BaseResource):
    model = BlockModel
    fields = block_fields
    args = block_args

class UmbrellasResource(BaseResource):
    model = UmbrellaModel
    fields = umbrella_fields
    args = umbrella_args

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
            if id:
                # Fetch a specific meeting by ID
                meeting = self.model.query.get_or_404(id)               
                return marshal(meeting,self.fields), 200

            # Check for query parameters for filtering
            organizer_id = request.args.get('organizer_id')
            if organizer_id:
                meeting = db.session.query(MeetingModel)\
                                    .filter(MeetingModel.organizer_id == organizer_id)\
                                    .first()
                if meeting:
                    # Fetch related block, zone, and host details
                    meeting_details = {
                        'meeting_block': meeting.block.name if meeting.block else 'Unknown Block',
                        'meeting_zone': meeting.zone.name if meeting.zone else 'Unknown Zone',
                        'host': meeting.host.full_name if meeting.host else 'Unknown Host',
                        'when': meeting.date.strftime('%a, %d %b %Y %H:%M:%S')
                    }
                    return meeting_details, 200
                return {'error': 'Meeting not found'}, 404

            # If no filters are applied, fetch all meetings
            meetings = MeetingModel.query.all()
            if meetings:
                return marshal(meetings, self.fields), 200
            
            return {'message': 'No meetings found'}, 404

        except Exception as e:
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


class BlockReportsResource(Resource):
    @marshal_with(block_report_fields)
    def get(self):
        args = block_report_args.parse_args()

        try:
            # Build the base query
            query = db.session.query(
                ZoneModel.name.label('zone'),
                UserModel.full_name.label('host'),
                func.sum(PaymentModel.amount).label('contributed_amount')
            ).join(UserModel, PaymentModel.payer_id == UserModel.id
                   ).join(ZoneModel, UserModel.zone_id == ZoneModel.name
                          ).group_by(ZoneModel.name, UserModel.full_name)

            # Apply filters
            query = self._apply_filters(query, args)

            # Pagination
            page = args['page']
            per_page = args['per_page']
            paginated_results = query.paginate(page=page, per_page=per_page, error_out=False)

            total_contributed = db.session.query(func.sum(PaymentModel.amount)).scalar() or 0

            return {
                'total_contributed': total_contributed,
                'detailed_contributions': [
                    {
                        'zone': item.zone,
                        'host': item.host,
                        'contributed_amount': item.contributed_amount
                    } for item in paginated_results.items
                ],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_pages': paginated_results.pages,
                    'total_items': paginated_results.total
                }
            }

        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

    def _apply_filters(self, query, args):
        if args['blocks']:
            block = BlockModel.query.filter_by(name=args['blocks']).first()
            if not block:
                raise ValueError(f"Block '{args['blocks']}' not found")
            members_in_block = [member.id for member in block.members]
            query = query.filter(PaymentModel.payer_id.in_(members_in_block))

        if args['member']:
            member = UserModel.query.filter_by(full_name=args['member']).first()
            if not member:
                raise ValueError(f"Member '{args['member']}' not found")
            query = query.filter(PaymentModel.payer_id == member.id)

        start_date = self._parse_date(args['start_date'])
        end_date = self._parse_date(args['end_date'])

        if start_date:
            query = query.filter(PaymentModel.payment_date >= start_date)
        if end_date:
            query = query.filter(PaymentModel.payment_date <= end_date)

        return query

    def _parse_date(self, date_str):
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD.")


# API routes
api.add_resource(UsersResource, '/users/', '/users/<int:id>', '/users/<int:id>/roles/')
api.add_resource(CommunicationsResource, '/communications/', '/communications/<int:id>')
api.add_resource(BanksResource, '/banks/', '/banks/<int:id>')
api.add_resource(PaymentsResource, '/payments/', '/payments/<int:id>')
api.add_resource(BlocksResource, '/blocks/', '/blocks/<int:id>')
api.add_resource(UmbrellasResource, '/umbrellas/', '/umbrellas/<int:id>')
api.add_resource(ZonesResource, '/zones/', '/zones/<int:id>')
api.add_resource(MeetingsResource, '/meetings/', '/meetings/<int:id>')
api.add_resource(BlockReportsResource, '/block_reports/')
api.add_resource(RolesResource, '/roles/','/roles/<int:id>')


