from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from datetime import datetime
from flask import Blueprint, jsonify, request
from werkzeug.exceptions import HTTPException
from flask_restful import Api, Resource, marshal_with, marshal, abort,reqparse
from ..main.models import UserModel, CommunicationModel, \
    PaymentModel, BankModel, BlockModel, UmbrellaModel, ZoneModel, MeetingModel, RoleModel
from .serializers import user_fields, user_args, communication_fields, \
    communication_args, payment_fields, payment_args, bank_fields, bank_args, \
    block_fields, block_args, umbrella_fields, umbrella_args, zone_fields, zone_args, \
    meeting_fields, meeting_args, block_report_args, block_report_fields,role_args,role_fields
from ..utils import db
import logging


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
    fields = user_fields
    args = user_args

    def get(self, id=None):
        try:
            if id:
                logger.info(f"GET request received for user {id}")
                user = self.model.query.get_or_404(id)
                return marshal(user, self.fields), 200

            role_name = request.args.get('role')
            if role_name:
                logger.info(f"GET request received for users with role {role_name}")
                users = UserModel.query.join(UserModel.roles).filter(RoleModel.name == role_name).all()
            else:
                logger.info("GET request received for all users")
                users = UserModel.query.all()

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

            # Assign the default "Member" role
            member_role = RoleModel.query.filter_by(name='Member').first()
            if member_role:
                new_user.roles.append(member_role)
                logger.info(f"Assigned default Member role to user {new_user.id}")

            db.session.add(new_user)
            db.session.commit()
            logger.info(f"Successfully created user {new_user.id} with roles {[r.name for r in new_user.roles]}")

            return marshal(new_user, self.fields), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating new user: {str(e)}. Rolling back changes.")
            return self.handle_error(e)
 

    def patch(self, id):
        try:
            args = self.args.parse_args()
            logger.info(f"PATCH request received to update user {id}. Payload: {args}")

            # Find the user by ID
            user = UserModel.query.get_or_404(id)

            # Check which fields are provided and update accordingly
            updated = False
            if args['full_name'] is not None:
                user.full_name = args['full_name']
                updated = True
            if args['id_number'] is not None:
                user.id_number = args['id_number']
                updated = True
            if args['phone_number'] is not None:
                user.phone_number = args['phone_number']
                updated = True
            if args['zone_id'] is not None:
                user.zone_id = args['zone_id']
                updated = True
            if args['bank_id'] is not None:
                user.bank_id = args['bank_id']
                updated = True
            if args['acc_number'] is not None:
                user.acc_number = args['acc_number']
                updated = True

            # If role_id is provided, update the user's roles
            if args['role_id'] is not None:
                role = RoleModel.query.get(args['role_id'])
                if role:
                    if role not in user.roles:
                        user.roles.append(role)  # Add the role if it's not already assigned
                        logger.info(f"Assigned additional role {role.name} to user {user.id}")
                        updated = True
            
            # Commit only if there are updates
            if updated:
                db.session.commit()
                logger.info(f"Successfully updated user {user.id} with roles {[r.name for r in user.roles]}")
                return marshal(user, self.fields), 200
            else:
                logger.info(f"No updates made for user {user.id}.")
                return {"message": "No updates made."}, 400

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user {id}: {str(e)}. Rolling back changes.")
            return self.handle_error(e)

    def delete(self, id=None):
        try:
            if not id:
                return {"message": "User ID is required for deletion or role removal"}, 400

            user = self.model.query.get_or_404(id)
            args = self.args.parse_args()
            role_id = args.get('role_id')

            # If role_id is provided, remove the role
            if role_id:
                role = RoleModel.query.get(role_id)
                if not role:
                    return {"message": f"Role with ID {role_id} not found"}, 404

                # Check if the role is assigned to the user
                if role in user.roles:
                    user.roles.remove(role)
                    db.session.commit()  # Commit changes to the database
                    logger.info(f"Removed role {role.name} from user {user.id}")
                    return {"message": f"Role {role.name} removed from user {user.id}"}, 200
                else:
                    return {"message": "User does not have this role"}, 400

            # If no role_id is provided, delete the user
            else:
                db.session.delete(user)
                db.session.commit()
                logger.info(f"Deleted user {user.id}")
                return {"message": f"User {user.full_name} with ID {user.id} has been deleted"}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during deletion: {str(e)}")
            return self.handle_error(e)


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

    def get(self):
        try:
            # Assuming we are fetching meetings based on organizer_id
            organizer_id = request.args.get('organizer_id')
            if organizer_id:
                meeting = db.session.query(MeetingModel)\
                                    .filter(MeetingModel.organizer_id == organizer_id)\
                                    .first()
                if meeting:
                    # Fetch related block, zone, and host details
                    meeting_details = {
                        'block': meeting.block.name if meeting.block else 'Unknown Block',
                        'zone': meeting.zone.name if meeting.zone else 'Unknown Zone',
                        'host': meeting.host.full_name if meeting.host else 'Unknown Host',
                        'when': meeting.date.strftime('%a, %d %b %Y %H:%M:%S')
                    }
                    return meeting_details, 200
            return {'error': 'Meeting not found'}, 404

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


