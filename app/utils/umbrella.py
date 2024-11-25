import requests
from flask import current_app
from flask_security import current_user

def get_umbrella_by_user(user_id):
    """Get umbrella details for a user from the API."""
    try:
        response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/umbrella/user/{user_id}",
            headers={"Authorization": f"Bearer {current_user.get_auth_token()}"}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        current_app.logger.error(f"Error fetching umbrella: {str(e)}")
        return None

def get_blocks_by_umbrella():
    """Get blocks for the current user's umbrella."""
    umbrella = get_umbrella_by_user(current_user.id)
    if not umbrella:
        return []
    
    try:
        response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/blocks/umbrella/{umbrella['id']}",
            headers={"Authorization": f"Bearer {current_user.get_auth_token()}"}
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        current_app.logger.error(f"Error fetching blocks: {str(e)}")
        return []
