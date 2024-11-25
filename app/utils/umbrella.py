import requests
from flask import current_app, g
from flask_security import current_user
from functools import wraps
import time

def cache_for_request(f):
    """Cache the result of a function for the duration of the request."""
    @wraps(f)
    def decorated(*args, **kwargs):
        cache_key = f"{f.__name__}:{':'.join(str(arg) for arg in args)}"
        if not hasattr(g, 'cache'):
            g.cache = {}
        if cache_key not in g.cache:
            g.cache[cache_key] = f(*args, **kwargs)
        return g.cache[cache_key]
    return decorated

@cache_for_request
def get_umbrella_by_user(user_id):
    """Get umbrella details for a user from the API."""
    try:
        response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/umbrellas/",
            params={"created_by": user_id},
            headers={"Authorization": f"Bearer {current_user.get_auth_token()}"}
        )
        if response.status_code == 200:
            umbrellas = response.json()
            return umbrellas[0] if umbrellas else None
        return None
    except Exception as e:
        current_app.logger.error(f"Error fetching umbrella: {str(e)}")
        return None

@cache_for_request
def get_blocks_by_umbrella():
    """Get blocks for the current user's umbrella."""
    umbrella = get_umbrella_by_user(current_user.id)
    if not umbrella:
        return []
    
    try:
        response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/blocks/",
            params={"parent_umbrella_id": umbrella['id']},
            headers={"Authorization": f"Bearer {current_user.get_auth_token()}"}
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        current_app.logger.error(f"Error fetching blocks: {str(e)}")
        return []

@cache_for_request
def get_zones_by_block(block_id):
    """Get zones for a specific block."""
    try:
        response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/zones/",
            params={"parent_block_id": block_id},
            headers={"Authorization": f"Bearer {current_user.get_auth_token()}"}
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        current_app.logger.error(f"Error fetching zones: {str(e)}")
        return []

def update_user_memberships(user_id, block_id=None, zone_id=None):
    """Update a user's block and zone memberships with proper umbrella association."""
    umbrella = get_umbrella_by_user(current_user.id)
    if not umbrella:
        current_app.logger.error("No umbrella found for the current user")
        return False, "No umbrella found"

    try:
        # Prepare the update payload
        payload = {
            'umbrella_id': umbrella['id']
        }
        
        if block_id:
            payload['block_id'] = block_id
        if zone_id:
            payload['zone_id'] = zone_id

        # Update user memberships
        response = requests.patch(
            f"{current_app.config['API_BASE_URL']}/api/v1/users/{user_id}",
            params={"umbrella_id": umbrella['id']},  # Ensure umbrella_id is in query params
            json=payload,
            headers={"Authorization": f"Bearer {current_user.get_auth_token()}"}
        )

        if response.status_code == 200:
            return True, "Memberships updated successfully"
        else:
            current_app.logger.error(f"Failed to update memberships: {response.text}")
            return False, f"Failed to update memberships: {response.text}"

    except Exception as e:
        current_app.logger.error(f"Error updating memberships: {str(e)}")
        return False, f"Error updating memberships: {str(e)}"
