from app import create_app
from app.utils import db
from flask_migrate import Migrate

app = create_app('development')
migrate = Migrate(app, db)

def create():
    return create_app('development')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)