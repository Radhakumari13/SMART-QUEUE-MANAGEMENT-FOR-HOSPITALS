# model.py
# Smart Queue Management System - Waiting Time Prediction Model
# Designed for small hospitals using basic Python logic (no ML libraries required)


def predict_wait_time(position, avg_time=5):
    """
    Calculate estimated waiting time based on the patient's position in the queue.

    How it works:
        Multiplies the patient's position by the average service time per patient.
        Example: position 3 with avg_time 5 → 3 × 5 = 15 minutes

    Args:
        position  (int): Patient's current position in the queue (1 = next in line)
        avg_time  (int): Average time (in minutes) to serve one patient. Default is 5.

    Returns:
        int: Estimated waiting time in minutes
    """
    estimated_time = position * avg_time
    return estimated_time


def adjust_time_based_on_load(total_patients):
    """
    Determine the adjusted average service time per patient based on current queue load.

    How it works:
        Hospitals get busier as more patients arrive, so doctors and staff tend to
        spend slightly less focused time per patient. This function simulates that
        effect by returning a higher avg_time when the queue is larger.

        - Small queue  (1–5 patients)  → avg_time = 5 minutes (calm, thorough)
        - Medium queue (6–10 patients) → avg_time = 6 minutes (moderate load)
        - Large queue  (11+ patients)  → avg_time = 7 minutes (high load, rushed)

    Args:
        total_patients (int): Total number of patients currently in the queue

    Returns:
        int: Adjusted average time (in minutes) per patient
    """
    if total_patients <= 5:
        # Small queue — staff can take more time per patient
        avg_time = 5
    elif total_patients <= 10:
        # Medium queue — moderate load, slight time pressure
        avg_time = 6
    else:
        # Large queue — high load, less time available per patient
        avg_time = 7

    return avg_time


def predict_dynamic_wait_time(position, total_patients):
    """
    Predict a smarter, more realistic waiting time by combining position
    and current queue load.

    How it works:
        First calls adjust_time_based_on_load() to get the right avg_time
        for the current situation, then multiplies it by the patient's position.
        This gives a more accurate estimate than a fixed avg_time alone.

        Example: position 4, total_patients 8
            → adjust_time_based_on_load(8) returns 6
            → 4 × 6 = 24 minutes estimated wait

    Args:
        position       (int): Patient's current position in the queue
        total_patients (int): Total number of patients currently in the queue

    Returns:
        int: Dynamically estimated waiting time in minutes
    """
    # Get the load-adjusted average time per patient
    avg_time = adjust_time_based_on_load(total_patients)

    # Calculate total estimated wait using the adjusted time
    dynamic_wait = position * avg_time

    return dynamic_wait


def get_patient_message(position, wait_time):
    """
    Generate a clear, friendly message for the patient based on their
    position and estimated waiting time.

    How it works:
        Uses simple thresholds to decide which message best fits the patient's
        situation. The goal is to keep patients informed and calm.

        - Position 1 or wait ≤ 5 min  → "Your turn is coming soon"
        - Wait between 6–15 minutes   → "Please wait approximately X minutes"
        - Wait between 16–30 minutes  → "Please be patient, estimated wait: X minutes"
        - Wait over 30 minutes        → "High waiting time due to crowd"

    Args:
        position  (int): Patient's current position in the queue
        wait_time (int): Estimated waiting time in minutes

    Returns:
        str: A user-friendly status message
    """
    if position == 1 or wait_time <= 5:
        # Patient is next or almost next
        message = "Your turn is coming soon. Please be ready!"

    elif wait_time <= 15:
        # Short wait — give a specific time estimate
        message = f"Please wait approximately {wait_time} minutes. We will call your token shortly."

    elif wait_time <= 30:
        # Moderate wait — reassure the patient
        message = f"Please be patient. Your estimated wait time is {wait_time} minutes."

    else:
        # Long wait — acknowledge the crowd situation honestly
        message = (
            f"High waiting time due to crowd. "
            f"Estimated wait: {wait_time} minutes. Thank you for your patience."
        )

    return message