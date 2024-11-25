import requests
from flask import current_app, g
from flask_security import current_user
from functools import wraps

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
        # Use the correct endpoint that returns umbrella by created_by
        response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/umbrellas/",
            params={"created_by": user_id},
            headers={"Authorization": f"Bearer {current_user.get_auth_token()}"}
        )
        if response.status_code == 200:
            umbrellas = response.json()
            # Return the first umbrella if any exist
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
            f"{current_app.config['API_BASE_URL']}/api/v1/blocks/umbrella/{umbrella['id']}",
            headers={"Authorization": f"Bearer {current_user.get_auth_token()}"}
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        current_app.logger.error(f"Error fetching blocks: {str(e)}")
        return []
