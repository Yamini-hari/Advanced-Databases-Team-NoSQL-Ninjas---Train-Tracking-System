from flask import Flask, jsonify
from flask import request
from utils import filter_times, extract_elements, calculatePercentage, check_substring, convert_from_iso_format, calculateSumPrice, convert_to_iso_format, generate_random_string
from db import neo4j_connection, mongo_connection
from datetime import datetime, date
from mongo import get_num_tickets, get_train_fare_increases
from flask_cors import CORS, cross_origin

app = Flask(__name__, template_folder='frontend')
cors = CORS(app)
app.config["CORS_HEADERS"] = 'COntent-Type'
     
# @app.route('/search', methods=['GET', 'POST'])
# def search():
#     # Extract the journey details from the POST request
#     request_data = request.get_json()
#     current_location = request_data.get('current_location')
#     destination = request_data.get('destination')
#     date = request_data.get('date')
#     time = request_data.get('time')
#     train_class = request_data.get('class')

#     # Perform any necessary processing or validation

#     print(request_data)
#     print(convert_to_iso_format(date,time))
#     # Return a response indicating success
#     return jsonify({'message': 'POST request received successfully'})


@app.route('/deutschline', methods=['GET'])
@cross_origin()
def index():
    current_location = request.args.get('current_location')
    destination = request.args.get('destination')

    
    sourceKeys = neo4j_connection.query("MATCH (n) WHERE n.name = '"+ current_location +"' RETURN n.short_name AS stationKey")
    destinationKeys = neo4j_connection.query("MATCH (n) WHERE n.name = '"+ destination +"' RETURN n.short_name AS stationKey")
    

    for sourceKey in sourceKeys:
        start = sourceKey["stationKey"]

    for destinationKey in destinationKeys:
        end = destinationKey["stationKey"]

    user_date = request.args.get('date')
    user_time = request.args.get('time')
    ticket_class = request.args.get('class')
    user_date_oject = datetime.strptime(user_date, "%d-%m-%Y").date()
    cypher_query = """
            MATCH path = shortestPath((dor:Station {short_name: '"""+start+"""'})-[:CONNECTED_TO*]->(bon:Station {short_name: '"""+end+"""'}))
            RETURN path, reduce(total = 0, rel in relationships(path) | total + rel.base_price) AS total_base_price,
                [rel in relationships(path) | { 
                    train_type: rel.train_type, 
                    train_num: rel.train_num, 
                    departures: rel.departures, 
                    arrivals: rel.arrivals, 
                    base_price: rel.base_price,
                    secondclass_seats: rel.secondclass_seats,
                    firstclass_seats: rel.firstclass_seats
                }] AS segments
    """

    try:
        result = neo4j_connection.query(cypher_query)
        query_result = jsonify(result)
        
        print("RESPONSE<< >>" , query_result.json)

       # data = json.loads(result)

        for data in result:
            total_base_price = data['total_base_price']    
            firstclass_seats = [segment['firstclass_seats'] for segment in data['segments']]
            train_number = [segment['train_num'] for segment in data['segments']]
            departures = [segment['departures'] for segment in data['segments']]
            arrivals = [segment['arrivals'] for segment in data['segments']]
            secondclass_seats = [segment['secondclass_seats'] for segment in data['segments']]
            
        print("TOTAL BASE PRICE : ", total_base_price)
        print(firstclass_seats[0])
        print(secondclass_seats[0])
        print(departures[0])
        print(train_number[0])
        print(arrivals[len(arrivals) - 1])
    
        today_date = date.today()
        if user_date_oject > today_date:
            actual_departures = departures[0]
            actual_arrivals = arrivals[len(arrivals) - 1]
        elif user_date_oject == today_date:
            # Filter times and capture indices
            indices, actual_departures = filter_times(user_time, departures[0])
            actual_arrivals = extract_elements(arrivals[len(arrivals) - 1], indices)
        else:
            actual_departures = None
            actual_arrivals = None

        print("DEPARTURE :: ", actual_departures)

        print("ARRIVAL :: ", actual_arrivals)

        num_of_tickets = get_num_tickets(user_date, train_number, ticket_class, actual_departures, actual_arrivals)

        print(num_of_tickets)

        if check_substring(ticket_class, "First"):
            seat_limit = firstclass_seats[0]
        if check_substring(ticket_class, "Second"):
            seat_limit = secondclass_seats[0]
        demandRequests = []
        for data in num_of_tickets:
            for another_data in data:
                capacity = calculatePercentage(another_data["total_tickets"], seat_limit)
                print(capacity)
                demandRequests.append({"capacity": capacity, "train_date_time": another_data["train_date_time"]})

        print("DEMANDING :: ", demandRequests)

        fare_increases = get_train_fare_increases(demandRequests)
        print("LAST TIME FARE :: ", fare_increases)

        createResponses = []
        count = 0
        for fare_increase in fare_increases:
           for another_fare in fare_increase:
             response = {}
             response["current_location"] = current_location
             response["destination"] = destination
             response["train_number"] = train_number[0]
             response["class"] = ticket_class

             train_date, train_time = convert_from_iso_format(another_fare["train_date_time"])
             fare_percentage_increase = another_fare["total_fare_increase"]
             total_price = calculateSumPrice(fare_percentage_increase, total_base_price, ticket_class)

             response["train_time"] = train_time
             response["train_demand"] = fare_percentage_increase
             response["ticket_fare"] = total_price
             response["train_arrival"] = actual_arrivals[count]
             createResponses.append(response)
             count = count + 1


        #numberOfTickets=get_num_tickets(date, time, str.upper(train_number[0]), ticket_class)

        return jsonify(createResponses)  # Return the result as JSON response
    finally:
        neo4j_connection.close()

@app.route('/create_booking', methods=['POST'])
def create_booking():
    # Extract data from request
    data = request.json
    print(data)
    updatedData ={}
    sourceKeys = neo4j_connection.query("MATCH (n) WHERE n.name = '"+ data['source'] +"' RETURN n.short_name AS stationKey")
    destinationKeys = neo4j_connection.query("MATCH (n) WHERE n.name = '"+ data['destination'] +"' RETURN n.short_name AS stationKey")
    print(sourceKeys,destinationKeys)
    for sourceKey in sourceKeys:
        start = sourceKey["stationKey"]

    for destinationKey in destinationKeys:
        end = destinationKey["stationKey"]

    # Insert the data into MongoDB
    
    date_time = convert_to_iso_format(data['train_date'],data['departureTime'])
    updatedData['date_time']=date_time
    updatedData['from_station']=str.upper(start)
    updatedData['to_station']=str.upper(end)
    updatedData['fare']=data['price']
    updatedData['email']=data['email']
    updatedData['number_of_tickets']=data['number_of_tickets']
    updatedData['seat_demand']=data['train_demand']
    updatedData['train_num']=str.upper(data['train_number'])
    updatedData['train_type']="ICE"
    updatedData['booking_id']=generate_random_string(7)
    if check_substring(data['class'], "First"):
        updatedData['ticket_class']='First Class'
    if check_substring(data['class'], "Second"):
        updatedData['ticket_class']='Second Class'
    result = mongo_connection.insert('data2',updatedData)

    # Response
    if result.inserted_id:
        return jsonify({'message': 'Booking created successfully', 'booking_id': str(updatedData['booking_id'])}), 201
    else:
        return jsonify({'message': 'Failed to create booking'}), 500


if __name__ == '__main__':
    app.run(debug=True)

