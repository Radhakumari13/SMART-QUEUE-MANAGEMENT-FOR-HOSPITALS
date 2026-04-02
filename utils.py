import json
import os

DATA_FILE = "data.json"

def load_data():
    """Read queue data from data.json. Returns empty list if file doesn't exist or is empty."""
    if not os.path.exists(DATA_FILE):
        return []
    
    try:
        with open(DATA_FILE, 'r') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        return []

def save_data(data):
    """Save the updated queue back to data.json."""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error saving data: {e}")

def add_patient(name):
    """
    Add a new patient to the queue.
    Auto-increments token number based on existing queue.
    Returns the assigned token number.
    """
    queue = load_data()
    
    # Calculate next token number
    # If queue is empty, start from 1; otherwise increment from last token
    if queue:
        last_token = max(patient['token'] for patient in queue)
        token = last_token + 1
    else:
        token = 1
    
    # Create new patient entry
    patient = {
        'name': name,
        'token': token
    }
    
    queue.append(patient)
    save_data(queue)
    
    return token

def get_queue():
    """Return the full queue list."""
    return load_data()

def next_patient():
    """
    Remove and return the first patient in the queue (FIFO).
    Returns None if queue is empty.
    """
    queue = load_data()
    
    if not queue:
        return None
    
    # Get the first patient
    patient = queue.pop(0)
    
    # Save updated queue
    save_data(queue)
    
    return patient

def calculate_wait_time(position, avg_time=5):
    """
    Calculate estimated waiting time based on position in queue.
    
    Args:
        position: Position in queue (1-based index)
        avg_time: Average time per patient in minutes (default: 5)
    
    Returns:
        Estimated wait time in minutes
    """
    # Position 1 means next in line, so wait time is 0 or minimal
    if position <= 0:
        return 0
    
    # Wait time = (position - 1) * avg_time
    # Position 1 = 0 minutes wait, Position 2 = 5 minutes, etc.
    return (position - 1) * avg_time