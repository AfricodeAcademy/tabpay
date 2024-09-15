from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
from flask_restful import Resource, marshal_with,abort,fields,reqparse, fields
from app.extensions import db
from app.models.models import UserModel, CommunicationModel, UmbrellaModel, PaymentModel, BlockModel, ZoneModel


umbrella_args = reqparse.RequestParser()
umbrella_args.add_argument('name', type=str, required=True, help='Umbrella Name is required')

block_args = reqparse.RequestParser()
block_args.add_argument('name', type=str, required=True, help='Block Name is required')
block_args.add_argument('parent_umbrella_id', type=int, required=True, help='Parent Umbrella is required')

zone_args = reqparse.RequestParser()
zone_args.add_argument('name', type=str, required=True, help='Zone Name is required')
zone_args.add_argument('parent_block_id', type=int, required=True, help='Parent Block is required')


user_args = reqparse.RequestParser()
user_args.add_argument('full_name', type=str, required=True, help='Name is required')
user_args.add_argument('email', type=str, required=True, help='Email is required')
user_args.add_argument('password', type=str, required=True, help='Password is required')
user_args.add_argument('id_number', type=int, required=True, help='Id Number is required')
user_args.add_argument('age', type=int, required=True, help='Age is required')
user_args.add_argument('phone', type=int, required=True, help='Phone is required')
user_args.add_argument('village', type=str, required=True, help='Village is required')
user_args.add_argument('gender', type=str, required=True, help='Gender is required')
user_args.add_argument('zone_id', type=int, required=True, help='Zone is required')



communication_args = reqparse.RequestParser()
communication_args.add_argument('content', type=str, required=True, help='Content is required')
communication_args.add_argument('user_id', type=int, required=True, help='Author is required')


payment_args = reqparse.RequestParser()
payment_args.add_argument('payer_id', type=int, required=True, help='Payer is required')
payment_args.add_argument('amount', type=float, required=True, help='Amount is required')


user_fields = {"id" : fields.Integer, "full_name" : fields.String,  "email" : fields.String, "password" : fields.String, "id_number" : fields.Integer, "age" : fields.Integer, "phone" : fields.Integer, "village" : fields.String, "zone_id" : fields.Integer,"gender" : fields.String, "registered_at" : fields.DateTime,"updated_at" : fields.DateTime,"message" : fields.String(attribute="author.full_name")}
communication_fields = {"id": fields.Integer,"content": fields.String,"user_id": fields.Integer,"created_at": fields.DateTime,"updated_at": fields.DateTime}
payment_fields = {"id": fields.Integer,"payee_id": fields.Integer,"amount": fields.Float,"payment_date": fields.DateTime,"bank": fields.String,"acc_number": fields.Integer,"payment_method": fields.String,"updated_at": fields.DateTime,"status": fields.Boolean}
block_fields = {"id": fields.Integer,"name": fields.String,"umbrella_id": fields.Integer}
umbrella_fields = {"id": fields.Integer,"name": fields.String}
zone_fields = {"id": fields.Integer,"name": fields.String,"parent_block_id": fields.Integer}


class Users(Resource):
    @marshal_with(user_fields)
    def get(self):
        try:
            users = UserModel.query.all()
            return users, 200
        
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            # Handle HTTP exceptions (e.g., 404 Not Found, 400 Bad Request)
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            # Handle any other exceptions
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()  # Ensure the session is closed

    @marshal_with(user_fields)
    def post(self):
        try:
            args = user_args.parse_args()
            existing_user = UserModel.query.filter_by(email=args['email']).first()
            
            if existing_user:
                abort(409, message='User already exists')
            
            new_user = UserModel(**args)
            db.session.add(new_user)
            db.session.commit()
            return new_user, 201
        
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
           
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
           
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close() 

class User(Resource):
    @marshal_with(user_fields) 
       
    def get(self, id):
        try:
            user = UserModel.query.get_or_404(id)
                
            if user:
                return user, 200
            abort(404, message='User not found')
                   
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()   


    @marshal_with(user_fields)
    def patch(self, id):
          
        try:
            args = user_args.parse_args()
            existing_user = UserModel.query.get_or_404(id)
            
            if existing_user:
                for key, value in args.items():
                    setattr(existing_user, key, value)
                db.session.commit()
                return existing_user, 200
            abort(404, message='User not found')
        
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close() 


    @marshal_with(user_fields)
    def delete(self, id):
        try:
            existing_user = UserModel.query.get_or_404(id)
            
            if existing_user:
                db.session.delete(existing_user)
                db.session.commit()
                users = UserModel.query.all()
                return users, 200
            abort(404, message='User not found')
        
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close() 


class Communications(Resource):
    @marshal_with(communication_fields)
    def get(self):
        try:
            communications = CommunicationModel.query.all()
            return communications, 200
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close() 

   
        
    
    @marshal_with(communication_fields)
    def post(self):
        try:
            args = communication_args.parse_args()
            existing_communication = CommunicationModel.query.filter_by(content=args['content']).first()
            if existing_communication:
                return abort(409, message='Communication already exists')
            new_communication = CommunicationModel(**args)
            db.session.add(new_communication)
            db.session.commit()
            communications = CommunicationModel.query.all()
            return communications, 201
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close() 

        


class Communication(Resource):
    @marshal_with(communication_fields)
    def get(self, id):
        try:
            communications = CommunicationModel.query.all()
            return communications, 200
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close() 
    @marshal_with(communication_fields)
    def patch(self, id):
        try:
            args = communication_args.parse_args()
            exiting_communication = CommunicationModel.query.get_or_404(id)
            if exiting_communication:
                for key, value in args.items():
                    setattr(exiting_communication, key, value)
                db.session.commit()
                return exiting_communication, 200
            abort(404, message='Message not found')        
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    
    @marshal_with(communication_fields)
    def delete(self, id):
        try:
            exiting_communication = CommunicationModel.query.get_or_404(id)
            if exiting_communication:
                db.session.delete(exiting_communication)
                db.session.commit()
                communications = CommunicationModel.query.all()
                return communications, 200
            abort(404, message='Message not found') 
        
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close() 
    


class Payments(Resource):
    @marshal_with(payment_fields)
    def get(self):
        try:
            payments = PaymentModel.query.all()
            return payments, 200
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close() 
    
    @marshal_with(payment_fields)
    def post(self):
        try:
            args = payment_args.parse_args()
            exiting_payment = PaymentModel.query.filter_by(payer_id=args['payer_id']).first()
            if exiting_payment:
                return abort(409, message='Payment already exists')
            new_payment = PaymentModel(**args)
            db.session.add(new_payment)
            db.session.commit()
            payments = PaymentModel.query.all()
            return payments, 201
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close() 
    

class Payment(Resource):
    @marshal_with(payment_fields)
    def get(self, id):
        try:
            payment = PaymentModel.query.get_or_404(id)
            if payment:
                return payment, 200
            abort(404, message='Message not found') 
        
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close() 
    
    @marshal_with(payment_fields)
    def patch(self, id):
        try:
            args = payment_args.parse_args()
            exiting_payment = PaymentModel.query.get_or_404(id)
            if exiting_payment:
                for key, value in args.items():
                    setattr(exiting_payment, key, value)
                db.session.commit()
                return exiting_payment, 200
            abort(404, message='Message not found') 
        
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    
    @marshal_with(payment_fields)
    def delete(self, id):
        try:
            exiting_payment = PaymentModel.query.get_or_404(id)
            if exiting_payment:
                db.session.delete(exiting_payment)
                db.session.commit()
                payments = PaymentModel.query.all()
                return payments, 200
            abort(404, message='Message not found') 
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    


class Blocks(Resource):
    @marshal_with(block_fields)
    def get(self):
        try:
            blocks = BlockModel.query.all()
            return blocks, 200
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    
    @marshal_with(block_fields)
    def post(self):
        try:
            args = block_args.parse_args()
            existing_block = BlockModel.query.filter_by(name=args['name']).first()
            if existing_block:
                return abort(409, message='Block already exists')
            new_block = BlockModel(**args)
            db.session.add(new_block)
            db.session.commit()
            blocks = BlockModel.query.all()
            return blocks, 201
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    

class Block(Resource):
    @marshal_with(block_fields)
    def get(self, id):
        try:
            block = BlockModel.query.get_or_404(id)
            if block:
                return block, 200
            abort(404, message='Message not found') 
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    
    @marshal_with(block_fields)
    def patch(self, id):
        try:
            args = block_args.parse_args()
            existing_block = BlockModel.query.get_or_404(id)
            if existing_block:
                for key, value in args.items():
                    setattr(existing_block, key, value)
                db.session.commit()
                abort(404, message='Message not found') 
            abort(404, message='Message not found') 
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    
    @marshal_with(block_fields)
    def delete(self, id):
        try:
            existing_block = BlockModel.query.get_or_404(id)
            if existing_block:
                db.session.delete(existing_block)
                db.session.commit()
                blocks = BlockModel.query.all()
                return blocks, 200
            abort(404, message='Message not found') 
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    


class Umbrellas(Resource):
    @marshal_with(umbrella_fields)
    def get(self):
        try:
            umbrellas = UmbrellaModel.query.all()
            return umbrellas, 200
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    
    @marshal_with(umbrella_fields)
    def post(self):
        try:
            args = umbrella_args.parse_args()
            existing_umbrella = UmbrellaModel.query.filter_by(name=args['name']).first()
            if existing_umbrella:
                return abort(409, message='Umbrella already exists')
            new_umbrella = UmbrellaModel(**args)
            db.session.add(new_umbrella)
            db.session.commit()
            umbrellas = UmbrellaModel.query.all()
            return umbrellas, 201
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    

class Umbrella(Resource):
    @marshal_with(umbrella_fields)
    def get(self, id):
        try:
            umbrella = UmbrellaModel.query.get_or_404(id)
            if umbrella:
                return umbrella, 200
            abort(404, message='Message not found') 
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    
    @marshal_with(umbrella_fields)
    def patch(self, id):
        try:
            args = umbrella_args.parse_args()
            existing_umbrella = UmbrellaModel.query.get_or_404(id)
            if existing_umbrella:
                for key, value in args.items():
                    setattr(existing_umbrella, key, value)
                db.session.commit()
                return existing_umbrella, 200
            abort(404, message='Message not found') 
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
        
    
    @marshal_with(umbrella_fields)
    def delete(self, id):
        try:
            existing_umbrella = UmbrellaModel.query.get_or_404(id)
            if existing_umbrella:
                db.session.delete(existing_umbrella)
                db.session.commit()
                umbrellas = UmbrellaModel.query.all()
                return umbrellas, 200
            abort(404, message='Message not found') 
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    


class Zones(Resource):
    @marshal_with(zone_fields)
    def get(self):
        try:
            zones = ZoneModel.query.all()
            return zones, 200
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    
    @marshal_with(zone_fields)
    def post(self):
        try:
            args = zone_args.parse_args()
            existing_zone = ZoneModel.query.filter_by(name=args['name']).first()
            if existing_zone:
                return abort(409, message='Zone already exists')
            new_zone = ZoneModel(**args)
            db.session.add(new_zone)
            db.session.commit()
            zones = ZoneModel.query.all()
            return zones, 201
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    

class Zone(Resource):
    @marshal_with(zone_fields)
    def get(self, id):
        try:
            zone = ZoneModel.query.get_or_404(id)
            if zone:
                return zone, 200
            abort(404, message='Message not found') 
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    
    @marshal_with(zone_fields)
    def patch(self, id):
        try:
            args = zone_args.parse_args()
            existing_zone = ZoneModel.query.get_or_404(id)
            if existing_zone:
                for key, value in args.items():
                    setattr(existing_zone, key, value)
                db.session.commit()
                return existing_zone, 200
            abort(404, message='Message not found') 
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    
    @marshal_with(zone_fields)
    def delete(self, id):
        try:
            existing_zone = ZoneModel.query.get_or_404(id)
            if existing_zone:
                db.session.delete(existing_zone)
                db.session.commit()
                zones = ZoneModel.query.all()
                return zones, 200
            abort(404, message='Message not found') 
        except SQLAlchemyError as e:
            print(f"Database error occurred: {e}")
            abort(500, message='Internal server error')
        
        except HTTPException as e:
            print(f"HTTP error occurred: {e}")
            abort(e.code, message=str(e))
        
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            abort(500, message='Internal server error')
        
        finally:
            db.session.close()
    
    








