from flask import Flask, request, jsonify
from db_connection import neo_connection
from apiAggregate import get_reserved_seats
from flask_cors import CORS, cross_origin
from bson import ObjectId
from db_connection import mongo_connection
from utils import generate_random_string

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/get_available_seats', methods=['GET'])
@cross_origin()
def get_available_seats():
    # Extract parameters from the request URL
    train_number = request.args.get('train_number')
    coach_number = request.args.get('coach_number')
    from_station = request.args.get('from_station')
    to_station = request.args.get('to_station')
    date_time = request.args.get('date_time')

    # Check if parameters are provided
    if not train_number or not date_time or not coach_number or not from_station or not to_station:
        return jsonify({"error": "Missing parameters"}), 400

    # Define your Neo4j Cypher query
    cypher_query = "MATCH (train1:Train {train_number: " + train_number + "})-[:COMPRISES]->(coach:Coach {coach_number: " + coach_number + "})-[:HAS_SEAT]->(seat:Seat) WHERE NOT seat.seat_number IN $reserved_seats_array RETURN seat.seat_number AS availableSeats"
    reserverd_seats = get_reserved_seats(train_number, date_time, coach_number, from_station, to_station) 
    if reserverd_seats is None:
        reserverd_seats = []
    print("RESERVED", reserverd_seats)

    result = neo_connection().run(cypher_query, reserved_seats_array=reserverd_seats)
    available_seats = []
    for data in result:
        node = data.get("availableSeats")
        available_seats.append(node)
    print("AVAILABLE :: ",sorted(available_seats))

    coach_length_query = "MATCH p=(:Train {train_number: "+ train_number +"})-[r:COMPRISES]->(c:Coach) RETURN p AS length ORDER BY c.coach_number"
    coachlengths = neo_connection().run(coach_length_query)
    c_length = len(coachlengths.data())
    print(c_length)
    seat_length_query = "MATCH p=(:Train {train_number: "+ train_number +"})-[r:COMPRISES]->(c:Coach {coach_number: 1}) -[h:HAS_SEAT]->(s:Seat) RETURN s AS length ORDER BY s.seat_number"
    seatlengths = neo_connection().run(seat_length_query)
    s_length = len(seatlengths.data())
    print(s_length)

    response = {}
    response["availableSeats"] = sorted(available_seats)
    response["reserverdSeats"] = sorted(reserverd_seats)
    response["coachLength"] = c_length
    response["seatLength"] = s_length
    return response


@app.route('/get_booking', methods=['GET'])
@cross_origin()
def get_booking():
    # Extract parameters from the request URL
    booking_id = request.args.get('booking_id')
    last_name = request.args.get('last_name')

    # Check if parameters are provided
    if not booking_id or not last_name:
        return jsonify({"error": "Missing parameters"}), 400

    # Define your MongoDB query
    query = {"booking_id": booking_id, "last_name": last_name}

    result = mongo_connection.query(collection_name="bookings", query=query)
    result = [{key: str(value) if isinstance(value, ObjectId) else value for key, value in record.items()} for record in result]
    for data in result:
        from_station_fullname = getFullName(data["from_station"])
        to_station_fullname = getFullName(data["to_station"])
        
        data["from_station"] = from_station_fullname
        data["to_station"]   = to_station_fullname

    print(jsonify(result))

    return jsonify(result)

@app.route('/update_booking', methods=['PUT'])
@cross_origin()
def update_booking():
    data = request.json
    if not data.get('is_seat_reserved'):
        return jsonify({"error": "No 'is_seat_reserved' data provided."}), 400
    if not data.get('booking_id'):
        return jsonify({"error": "No 'booking_id' data provided."}), 400
    if not data.get('last_name'):
        return jsonify({"error": "No 'last_name' data provided."}), 400
    if not data.get('coach_number'):
        return jsonify({"error": "No 'coach_number' data provided."}), 400
    if not data.get('seat_numbers'):
        return jsonify({"error": "No 'seat_numbers' data provided."}), 400
    if not data.get('ticket_class'):
        return jsonify({"error": "No 'ticket_class' data provided."}), 400
    
    
    booking_id = data.get('booking_id')
    last_name = data.get('last_name')

    query = {"booking_id": booking_id, "last_name": last_name}

    # Retrieve existing document to get existing seat numbers
    existing_documents = mongo_connection.query(collection_name="bookings", query=query)
    if existing_documents:
        existing_document = existing_documents[0]  # Assuming we are interested in the first document
        existing_seat_numbers = existing_document.get('seat_numbers', [])
    else:
        existing_seat_numbers = []

    update = {}
    is_seat_reserved = data.get('is_seat_reserved')
    update["is_seat_reserved"] = bool(is_seat_reserved)

    coach_number = data.get('coach_number')
    update["coach_number"] = int(coach_number)

    new_seat_numbers = data.get('seat_numbers', [])
    # Combine existing and new seat numbers, remove duplicates
    updated_seat_numbers = list(set(existing_seat_numbers + new_seat_numbers))

    update["seat_numbers"] = [int(num) for num in updated_seat_numbers]

    ticket_class = data.get('ticket_class')
    update["ticket_class"] = ticket_class

    mongo_connection.update_booking(collection_name="bookings", query=query, update=update)

    return jsonify({"message": "Booking updated successfully."}), 200

@app.route('/add_booking', methods=['POST'])
@cross_origin()
def add_booking():
    # Get request data
    booking_data = request.json

    # Check if all required fields are present
    required_fields = ['user_id', 'first_name', 'last_name', 'train_number', 'from_station', 'to_station', 'date_time']
    if not all(field in booking_data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    booking_data['booking_id'] = generate_random_string()
    booking_data['is_seat_reserved'] = False

    collection_name = "bookings"
    mongo_connection.insert(collection_name, booking_data)
    return jsonify({"message": "Booking added successfully with Booking Id: " + booking_data['booking_id']})

def getFullName(shortName):
    query = "MATCH (station:Station) WHERE station.shortname = '"+ shortName +"' RETURN station.name AS name"
    resp = neo_connection().run(query)
    for data in resp:
        node = data.get("name")
        return node
    

def get_train_coaches_config(train_number):
    query = "MATCH p=(:Train {train_number: "+ train_number +"})-[r:COMPRISES]->(c:Coach) RETURN p ORDER BY c.coach_number"
    result = neo_connection().run(query)
    print(result.data())


if __name__ == '__main__':
    app.run(debug=True)
