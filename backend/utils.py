from datetime import datetime
import random
import string

def convert_date_to_user_format(date_string):
    # Convert date string to datetime object
    datetime_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")

    # Convert datetime object to DD-MM-YYYY format
    formatted_date = datetime_obj.strftime("%d-%m-%Y")

    # Convert datetime object to HH:MM format
    formatted_time = datetime_obj.strftime("%H:%M")

    return formatted_date, formatted_time


def convert_date_to_mongo_format(date_str, time_str):
    # Convert date string to datetime object
    date_obj = datetime.strptime(date_str, "%d-%m-%Y")

    # Convert time string to datetime object
    time_obj = datetime.strptime(time_str, "%H:%M")

    # Combine date and time
    combined_datetime = datetime(date_obj.year, date_obj.month, date_obj.day, time_obj.hour, time_obj.minute)

    # Format to original format
    original_format = combined_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

    return original_format


def generate_random_string(length=5):
    # Define characters to choose from
    characters = string.ascii_uppercase + string.digits
    
    # Generate random string
    random_string = ''.join(random.choice(characters) for _ in range(length))
    
    return random_string

# Example usage:
random_alphanumeric = generate_random_string()
print("Random alphanumeric string:", random_alphanumeric)
