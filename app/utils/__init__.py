from flask_sqlalchemy import SQLAlchemy
from flask_security import Security
from flask_mailman import Mail
import secrets
from PIL import Image
from flask import current_app
import logging
import os


db = SQLAlchemy()
security = Security()
mail = Mail()


# Function to save the profile picture
def save_picture(form_picture):
    try:
        # Generate a random hex for the filename and get the file extension
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext

        # Ensure the directory exists and log the action
        image_dir = os.path.join(current_app.root_path, 'static/images')
        if not os.path.exists(image_dir):
            logging.info(f"Directory {image_dir} does not exist. Creating directory...")
            os.makedirs(image_dir)
        else:
            logging.info(f"Directory {image_dir} already exists.")

        # Create the path to save the image
        picture_path = os.path.join(image_dir, picture_fn)

        # Resize the image and save it
        output_size = (125, 125)
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)

        logging.info(f"Profile picture saved at {picture_path}")
        return picture_fn

    except Exception as e:
        logging.error(f"Error saving picture: {e}")
        raise e
