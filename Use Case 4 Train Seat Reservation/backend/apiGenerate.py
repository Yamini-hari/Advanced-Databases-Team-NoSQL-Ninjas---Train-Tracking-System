from flask import Flask, request, jsonify
from pymongo import MongoClient
from utils import generate_random_string
from db_connection import mongo_connection

app = Flask(__name__)
    
@app.route('/add_booking', methods=['POST'])
def add_booking():
    # Get request data
    booking_data = request.json

    # Check if all required fields are present
    required_fields = ['user_id', 'first_name', 'last_name', 'train_number', 'from_station', 'to_station', 'date_time']
    if not all(field in booking_data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    booking_data['booking_id'] = generate_random_string()
    booking_data['is_seat_reserved'] = False

    try:
        collection_name = "bookings"
        mongo_connection.insert(collection_name, booking_data)
        return jsonify({"message": "Booking added successfully"})
    finally:
        mongo_connection.close()

if __name__ == '__main__':
    app.run(debug=True)
