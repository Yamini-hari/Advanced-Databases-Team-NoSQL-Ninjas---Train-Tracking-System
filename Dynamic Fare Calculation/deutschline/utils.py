from datetime import datetime
import random
import string

def convert_to_iso_format(date_str, time_str):
    # Parse date and time strings
    date_obj = datetime.strptime(date_str, '%d-%m-%Y')
    time_obj = datetime.strptime(time_str, '%H:%M')

    # Combine date and time objects
    datetime_obj = datetime.combine(date_obj.date(), time_obj.time())

    # Format datetime object to ISO 8601 format
    iso_format = datetime_obj.isoformat() + 'Z'

    return iso_format

def convert_from_iso_format(iso_datetime_str):
    # Parse ISO 8601 formatted datetime string
    datetime_obj = datetime.fromisoformat(iso_datetime_str[:-1])  # Remove 'Z' at the end

    # Extract date and time strings
    date_str = datetime_obj.strftime('%d-%m-%Y')
    time_str = datetime_obj.strftime('%H:%M')

    return date_str, time_str

def filter_times(given_time_str, times_to_compare):
    # Convert given time string to datetime object
    given_time = datetime.strptime(given_time_str, "%H:%M")

    # Initialize arrays for filtered indices and times
    filtered_indices = []
    filtered_times = []

    # Filter times and capture indices
    for i, time in enumerate(times_to_compare):
        if datetime.strptime(time, "%H:%M") > given_time:
            filtered_indices.append(i)
            filtered_times.append(time)

    return filtered_indices, filtered_times

def extract_elements(array, indices):
    extracted_elements = [array[i] for i in indices]
    return extracted_elements

def calculatePercentage(actualSeats, totalSeats):
    return (actualSeats / totalSeats ) * 100

def check_substring(main_string, substring):
    # Convert both strings to lowercase
    main_string_lower = main_string.lower()
    substring_lower = substring.lower()

    # Check if substring is present in the main string
    return substring_lower in main_string_lower

def calculateSumPrice(percentage, basePrice, ticketClass):
    totalPrice = ((percentage/100) * basePrice) + basePrice
    if check_substring(ticketClass, "First"):
        totalPrice = totalPrice * 2
    return totalPrice   

def generate_random_string(length):
    alphanumeric_chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(alphanumeric_chars) for _ in range(length))