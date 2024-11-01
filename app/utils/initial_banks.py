import json
from flask import current_app
from app.main.models import BankModel
from app.utils import db

def import_banks(json_file_path):
    """
    Import banks from a JSON file into the database.
    
    Args:
        json_file_path (str): Path to the JSON file containing bank information
        
    Returns:
        tuple: (success: bool, message: str, count: int)
    """
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as file:
            data = json.load(file)
            
        if not isinstance(data, dict) or 'banks' not in data:
            return False, "Invalid JSON format. Expected {'banks': [...]}.", 0
            
        banks_created = 0
        banks_updated = 0
        
        for bank_data in data['banks']:
            # Check if bank already exists (by paybill number)
            existing_bank = BankModel.query.filter_by(
                paybill_no=bank_data['paybill_no']
            ).first()
            
            if existing_bank:
                # Update existing bank
                existing_bank.name = bank_data['name']
                banks_updated += 1
            else:
                # Create new bank
                new_bank = BankModel(
                    name=bank_data['name'],
                    paybill_no=bank_data['paybill_no']
                )
                db.session.add(new_bank)
                banks_created += 1
        
        db.session.commit()
        message = f"Successfully processed {banks_created + banks_updated} banks "
        message += f"({banks_created} created, {banks_updated} updated)"
        return True, message, banks_created + banks_updated
        
    except FileNotFoundError:
        return False, f"File not found: {json_file_path}", 0
    except json.JSONDecodeError:
        return False, "Invalid JSON format in file.", 0
    except Exception as e:
        db.session.rollback()
        return False, f"Error importing banks: {str(e)}", 0

# Add this to your create_app function after creating roles and users
def import_initial_banks(app):
    """Import initial banks during app initialization."""
    with app.app_context():
        # Check if we already have banks in the database
        if BankModel.query.first() is None:
            # Adjust this path according to your project structure
            json_file_path = 'banks.json'
            success, message, count = import_banks(json_file_path)
            if success:
                print(f"Initial banks import: {message}")
            else:
                print(f"Failed to import initial banks: {message}")