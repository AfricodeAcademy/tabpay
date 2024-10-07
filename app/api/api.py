from sqlalchemy.exc import SQLAlchemyError
import logging
from sqlalchemy import func
from datetime import datetime
from flask import Blueprint, jsonify
from werkzeug.exceptions import HTTPException
from flask_restful import Api, Resource, marshal_with, marshal, abort
from ..main.models import UserModel, CommunicationModel, \
    PaymentModel, BankModel, BlockModel, UmbrellaModel, ZoneModel, MeetingModel
from .serializers import user_fields, user_args, communication_fields, \
    communication_args, payment_fields, payment_args, bank_fields, bank_args, \
    block_fields, block_args, umbrella_fields, umbrella_args, zone_fields, zone_args, \
    meeting_fields, meeting_args, block_report_args, block_report_fields
from ..utils import db


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)


api_bp = Blueprint('api', __name__)
api = Api(api_bp)



@api_bp.errorhandler(HTTPException)
def handle_http_exception(e):
    response = e.get_response()
    response.data = jsonify({
        "success": False,
        "message": e.description
    }).data
    response.content_type = "application/json"
    return response

@api_bp.errorhandler(400)
def handle_validation_error(error):
    response = jsonify({
        "success": False,
        "message": "Invalid input data",
        "details": error.description
    })
    response.status_code = 400
    return response

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
            logging.error("Fields attribute not set for the resource.")
            return {"success": False, "message": "Internal server error. Please contact support."}, 500

        try:
            if id:
                logging.info(f"Fetching {self.model.__name__} with ID {id}")
                item = self.model.query.get_or_404(id)
                return marshal(item, self.fields), 200
            logging.info(f"Fetching all {self.model.__name__} records")
            items = self.model.query.all()
            return marshal(items, self.fields), 200
        except HTTPException as http_exc:
            logging.error(f"Validation error: {str(http_exc)}")
            return {"success": False, "message": "Invalid request."}, 400
        except SQLAlchemyError as db_exc:
            return self.handle_error(db_exc)
        except Exception as e:
            return self.handle_error(e)


    def post(self):
        logging.info(f"Attempting to create a new {self.model.__name__}")
        try:
            args = self.args.parse_args()
            new_item = self.model(**args)
            db.session.add(new_item)
            db.session.commit()
            logging.info(f"{self.model.__name__} created successfully")
            return marshal(new_item, self.fields), 201
        except HTTPException as http_exc:
            logging.error(f"Validation error: {str(http_exc)}")
            return {
                "success": False,
                "message": "Invalid data provided.",
                "details": str(http_exc)
            }, 400
        except SQLAlchemyError as db_exc:
            return self.handle_error(db_exc)
        except Exception as e:
            return self.handle_error(e)


    def patch(self, id):
        logging.info(f"Attempting to update {self.model.__name__} with ID {id}")
        try:
            args = self.args.parse_args()
            item = self.model.query.get_or_404(id)
            for key, value in args.items():
                setattr(item, key, value)
            db.session.commit()
            logging.info(f"{self.model.__name__} with ID {id} updated successfully")
            return marshal(item, self.fields), 200
        except Exception as e:
            return self.handle_error(e)

    def delete(self, id):
        logging.info(f"Attempting to delete {self.model.__name__} with ID {id}")
        try:
            item = self.model.query.get_or_404(id)
            db.session.delete(item)
            db.session.commit()
            logging.info(f"{self.model.__name__} with ID {id} deleted successfully")
            items = self.model.query.all()
            return marshal(items, self.fields), 200
        except Exception as e:
            return self.handle_error(e)

    def handle_error(self, e):
        db.session.rollback()
        logging.error(f"Error occurred: {str(e)}")

        if isinstance(e, SQLAlchemyError):
            error_message = {
                "success": False,
                "message": "A database error occurred. Please contact support.",
                "details": "Something went wrong while interacting with the database."
            }
            return jsonify(error_message), 500

        elif isinstance(e, HTTPException):
            error_message = {
                "success": False,
                "message": "An error occurred.",
                "details": e.description
            }
            return jsonify(error_message), e.code

        else:
            error_message = {
                "success": False,
                "message": "An unexpected error occurred. Please try again later."
            }
            return jsonify(error_message), 500



class UsersResource(BaseResource):
    model = UserModel
    fields = user_fields
    args = user_args

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

class MeetingsResource(BaseResource):
    model = MeetingModel
    fields = meeting_fields
    args = meeting_args

class ZonesResource(BaseResource):
    model = ZoneModel
    fields = zone_fields
    args = zone_args


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
                   ).join(ZoneModel, UserModel.zone == ZoneModel.name
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
api.add_resource(UsersResource, '/users/', '/users/<int:id>')
api.add_resource(CommunicationsResource, '/communications/', '/communications/<int:id>')
api.add_resource(BanksResource, '/banks/', '/banks/<int:id>')
api.add_resource(PaymentsResource, '/payments/', '/payments/<int:id>')
api.add_resource(BlocksResource, '/blocks/', '/blocks/<int:id>')
api.add_resource(UmbrellasResource, '/umbrellas/', '/umbrellas/<int:id>')
api.add_resource(ZonesResource, '/zones/', '/zones/<int:id>')
api.add_resource(MeetingsResource, '/meetings/', '/meetings/<int:id>')
api.add_resource(BlockReportsResource, '/block_reports/')
