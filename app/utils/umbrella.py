from flask import current_app, flash, g
from flask_security import current_user
from functools import wraps
import time
import requests

def cache_for_request(f):
    """Cache the result of a function for the duration of the request."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'cache'):
            g.cache = {}
        cache_key = f"{f.__name__}:{':'.join(str(arg) for arg in args)}:{':'.join(f'{k}={v}' for k,v in kwargs.items())}"
        if cache_key not in g.cache:
            g.cache[cache_key] = f(*args, **kwargs)
        return g.cache[cache_key]
    return decorated

@cache_for_request
def get_umbrella_by_user(user_id):
    """Get umbrella for a specific user."""
    try:
        response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/umbrellas/",
            params={"user_id": user_id},
            headers={"Authorization": f"Bearer {current_user.get_auth_token()}"}
        )
        if response.status_code == 200:
            data = response.json()
            return data[0] if isinstance(data, list) and data else data
        return None
    except Exception as e:
        current_app.logger.error(f"Error fetching umbrella: {str(e)}")
        return None

@cache_for_request
def get_blocks_by_umbrella(show_flash_messages=True, max_retries=3):
    """Fetches blocks associated with the current user's umbrella via API.
    
    Args:
        show_flash_messages: Whether to show flash messages on errors (default: True)
        max_retries: Maximum number of retry attempts (default: 3)
    
    Returns:
        list: List of blocks associated with the user's umbrella
    """
    retry_count = 0
    while retry_count < max_retries:
        try:
            # Get the user's umbrella first
            umbrella = get_umbrella_by_user(current_user.id)
            if not umbrella:
                if show_flash_messages:
                    flash('No umbrella association found.', 'warning')
                return []

            response = requests.get(
                f"{current_app.config['API_BASE_URL']}/api/v1/blocks/",
                params={'parent_umbrella_id': umbrella['id']},
                headers={"Authorization": f"Bearer {current_user.get_auth_token()}"},
                timeout=20
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else []
            
        except requests.exceptions.Timeout:
            retry_count += 1
            if retry_count == max_retries:
                current_app.logger.error(f"Timeout error after {max_retries} retries when fetching blocks")
                if show_flash_messages:
                    flash('Server is taking too long to respond. Please try again later.', 'danger')
                return []
            current_app.logger.warning(f"Timeout occurred, retrying ({retry_count}/{max_retries})...")
            continue
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Error fetching blocks: {str(e)}")
            if show_flash_messages:
                flash('Error retrieving blocks from the server. Please try again later.', 'danger')
            return []
        except ValueError as e:
            current_app.logger.error(f"Error processing block data: {str(e)}")
            if show_flash_messages:
                flash('Error processing server response. Please contact support.', 'danger')
            return []

@cache_for_request
def get_zones_by_block(block_id, show_flash_messages=True, max_retries=3):
    """Get zones for a specific block.
    
    Args:
        block_id: ID of the block to get zones for
        show_flash_messages: Whether to show flash messages on errors (default: True)
        max_retries: Maximum number of retry attempts (default: 3)
    
    Returns:
        list: List of zones associated with the block
    """
    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.get(
                f"{current_app.config['API_BASE_URL']}/api/v1/zones/",
                params={"parent_block_id": block_id},
                headers={"Authorization": f"Bearer {current_user.get_auth_token()}"},
                timeout=20  # Increased timeout
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else []
        except requests.exceptions.Timeout:
            retry_count += 1
            if retry_count == max_retries:
                current_app.logger.error(f"Timeout error after {max_retries} retries when fetching zones")
                if show_flash_messages:
                    flash('Server is taking too long to respond. Please try again later.', 'danger')
                return []
            current_app.logger.warning(f"Timeout occurred, retrying ({retry_count}/{max_retries})...")
            continue
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Error fetching zones: {str(e)}")
            if show_flash_messages:
                flash('Error retrieving zones from the server. Please try again later.', 'danger')
            return []
        except ValueError as e:
            current_app.logger.error(f"Error processing zone data: {str(e)}")
            if show_flash_messages:
                flash('Error processing server response. Please contact support.', 'danger')
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
