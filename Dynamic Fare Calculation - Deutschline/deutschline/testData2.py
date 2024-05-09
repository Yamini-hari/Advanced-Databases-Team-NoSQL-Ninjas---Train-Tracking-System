import pymongo
import random
from datetime import datetime, timedelta

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["test"]
collection = db["data3"]

# Function to generate random alphanumeric string for booking_id
def generate_booking_id(length=7):
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(random.choices(chars, k=length))

# Function to generate random email
def generate_email():
    domains = ["gmail.com", "yahoo.com", "outlook.com", "example.com"]
    return f"user{random.randint(1, 100)}@{random.choice(domains)}"

# Function to generate random ticket class and number of tickets
def generate_ticket_info(ticket_class):
    if ticket_class == "First Class":
        number_of_tickets = random.randint(1, 50)
    else:
        number_of_tickets = random.randint(1, 100)
    return number_of_tickets

# ICE2 train route stations and timings
ice2_stations = ["MUN", "AUG", "ULM", "STR", "HD", "MAN", "FRA"]
ice2_departures = {
    "MUN": ["08:00", "15:00", "21:00"],
    "AUG": ["08:25", "15:25", "21:25"],
    "ULM": ["08:55", "15:55", "21:55"],
    "STR": ["09:25", "16:25", "22:25"],
    "HD": ["09:55", "16:55", "22:55"],
    "MAN": ["10:10", "17:10", "23:10"],
    "FRA": ["10:50", "17:50", "23:50"]
}

# Function to get next station for ICE2
def get_next_station_ice2(station):
    index = ice2_stations.index(station)
    if index < len(ice2_stations) - 1:
        next_station = ice2_stations[index + 1]
    else:
        next_station = ice2_stations[0]  # Loop back to the first station
    return next_station

# Loop to insert booking data for ICE2
for _ in range(20):  # Insert 20 booking data for ICE2 for testing
    from_station = random.choice(ice2_stations[:-1])  # Exclude the last station
    to_station = random.choice(ice2_stations[ice2_stations.index(from_station) + 1:])

    # Get the departure times for the from_station
    departure_times = ice2_departures[from_station]

    # Choose a random departure time for the from_station
    departure_time = datetime.strptime(f"2024-12-20 {random.choice(departure_times)}", "%Y-%m-%d %H:%M")

    # Calculate date_time based on departure time
    date_time = departure_time + timedelta(minutes=random.randint(0, 5))  # Add random delay
    
    # Format date_time as "2024-12-20T07:00:00Z"
    formatted_date_time = date_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Generate other random data
    fare = random.randint(1, 999)
    seat_demand = random.randint(0, 100)
    ticket_class = random.choice(["First Class", "Second Class"])
    number_of_tickets = generate_ticket_info(ticket_class)
    booking_id = generate_booking_id()
    user_email = generate_email()

    # Insert booking data into MongoDB
    booking_info = {
        "user_email": user_email,
        "from_station": from_station,
        "to_station": to_station,
        "train_type": "ICE",
        "train_num": "ICE2",
        "date_time": formatted_date_time,
        "fare": fare,
        "seat_demand": seat_demand,
        "number_of_tickets": number_of_tickets,
        "ticket_class": ticket_class,
        "booking_id": booking_id
    }
    collection.insert_one(booking_info)

print("Booking data for ICE2 inserted successfully.")
