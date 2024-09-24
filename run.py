from app import create_app
from app.extensions import db
from app.models.models import user_datastore
from flask_security.utils import hash_password

app = create_app()

with app.app_context():
    db.create_all()

if __name__ == '__main__':  
    app.run(debug=True)


    #Create roles
    user_datastore.find_or_create_role(name='admin',description='system developer')
    user_datastore.find_or_create_role(name='owner',description='owner of the system')

    #Create admin user
    if not user_datastore.find_user(email='testadmin@gmail.com'):
        hashed_password = hash_password('password')
        user_datastore.create_user(email='testadmin@gmail.com',password=hashed_password,full_name='Test Admin',id_number='123456',roles=[user_datastore.find_role('admin')])
        db.session.commit()
        print('Admin user created successfully.')

if __name__ == "__main__":
    app.run(debug=True,port=5001)
