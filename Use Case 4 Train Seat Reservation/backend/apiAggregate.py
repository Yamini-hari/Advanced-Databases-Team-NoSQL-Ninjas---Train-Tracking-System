from flask import Flask, request, jsonify
from db_connection import mongo_connection
from db_connection import neo_connection

app = Flask(__name__)

def get_reserved_seats(train_number, date_time, coach_number, from_station, to_station):
    shortname_routes = []
    ordered_stations = get_forward_train_route(train_number)
    
    if is_from_station_before(from_station, to_station, ordered_stations):
        for data in ordered_stations:
            shortname_routes.append(data['station']['shortname'])
    else:
        ordered_stations = get_reverse_train_route(train_number)
        for data in ordered_stations:
            shortname_routes.append(data['station']['shortname'])

    pre_stations, post_stations = extract_pre_and_post_stations(from_station, to_station, ordered_stations)
    print(shortname_routes)
    print("PRE", pre_stations)
    print("POST", post_stations)
    

    # Check if parameters are provided
    if not train_number or not date_time or not coach_number or not from_station or not to_station:
        return jsonify({"error": "Missing parameters"}), 400

    # Define your MongoDB pipeline
    pipeline = [
        {
            "$match": {
                "train_number": int(train_number),
                "date_time": date_time,
                "coach_number": int(coach_number),
                "$or": [
                    { 
                    "from_station": { "$lte": from_station },
                    "to_station": { "$gte": to_station }
                    },
                    { 
                    "from_station": { "$in": shortname_routes },
                    "to_station": { "$in": shortname_routes }
                    }
                ],
                "to_station": { "$nin": pre_stations },
                "from_station": { "$nin": post_stations }
            }
        },
        {
            "$unwind": "$seat_numbers"
        },
        {
            "$group": {
                "_id": "null",
                "reserved_seats": { "$push": "$seat_numbers" }
            }
        },
        {
            "$project": {
                "_id": 0,
                "reserved_seats": 1
            }
        }
    ]


    result = mongo_connection.aggregate(collection_name="bookings", pipeline=pipeline)
    for data in result:
        return data["reserved_seats"] 

def get_forward_train_route(train_number):
    query = "MATCH (train:Train)-[rel:STOPS_AT]->(station) WHERE train.train_number = " + train_number + " AND rel.direction = 'Forward' RETURN station ORDER BY rel.order"
    try:
        result = neo_connection().run(query)
    finally:
        neo_connection().close()
    return result.data()

def get_reverse_train_route(train_number):
    query = "MATCH (train:Train)-[rel:STOPS_AT]->(station) WHERE train.train_number = " + train_number + " AND rel.direction = 'Reverse' RETURN station ORDER BY rel.order"
    try:
        result = neo_connection().run(query)
    finally:
        neo_connection().close()
    return result.data()

def is_from_station_before(from_station, to_station, route_array):
    for i, item in enumerate(route_array):
        if item['station']['name'] == from_station:
            from_index = i
        elif item['station']['name'] == to_station:
            to_index = i
    
    return from_index < to_index

def extract_pre_and_post_stations(from_station, to_station, route_array):
    from_station_index = None
    to_station_index = None

    # Find the indices of from_stop and to_stop
    for i, item in enumerate(route_array):
        if item['station']['name'] == from_station:
            from_station_index = i
        elif item['station']['name'] == to_station:
            to_station_index = i
    
    # Slice the array based on from_index and to_index
    if from_station_index is not None and to_station_index is not None:
        pre_from_stations = [item['station']['shortname'] for item in route_array[:from_station_index+1]]
        post_to_stations = [item['station']['shortname'] for item in route_array[to_station_index:]]
        return pre_from_stations, post_to_stations
    else:
        return None, None

if __name__ == '__main__':
    app.run(debug=True)