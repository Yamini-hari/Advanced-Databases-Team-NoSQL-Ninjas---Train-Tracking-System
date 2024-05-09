from flask import Flask, render_template, request, jsonify
from neo4j import GraphDatabase, exceptions
import requests
import json
import random
import time
from haversine import haversine

app = Flask(__name__)

# Define the Neo4j connection
neo_uri = "bolt://localhost:7687"
neo_username = "adithi"
neo_password = "Praveen@1999"

# Connect to the Neo4j database
neo_driver = GraphDatabase.driver(neo_uri, auth=(neo_username, neo_password))

# Redis
import redis
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Define the base URL for the API
base_url = 'https://v6.vbb.transport.rest/stations'

# Function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

# Function to calculate distance between two points using Haversine formula
def haversine_distance(station1, station2):
    return haversine((station1['latitude'], station1['longitude']),
                     (station2['latitude'], station2['longitude']))

# Function to fetch station data from the API or Redis cache
def fetch_station_data(station_name):
    # Check if the station data is in the Redis cache
    cached_station = redis_client.get(f"station:{station_name}")
    if cached_station:
        return json.loads(cached_station)

    # If not in the cache, fetch the data from the API
    url = f"{base_url}?query={station_name}&limit=1&fuzzy=true&completion=true"
    res_data = make_api_request(url)
    if not res_data:
        return None  # Return None if no data found

    # Extract relevant data
    station = res_data.get(next(iter(res_data.keys())), {})
    station_id = station.get('id', 'Unknown')[9:]  # Change string to json representation
    station_location = station.get('location', {})
    
    # Simulate delay (for demonstration purposes)
    delay = random.randint(0, 10)  # Simulate delay in minutes
    time.sleep(delay)  # Simulate delay with sleep
    station_data = {
        'name': station_name,
        'latitude': station_location.get('latitude', 0),
        'longitude': station_location.get('longitude', 0),
        'delay': delay
    }
    # Store the station data in the Redis cache
    redis_client.set(f"station:{station_name}", json.dumps(station_data))
    return station_data

# Function to create relationships between stations
def create_relationships(session, start_station, end_station):
    distance = haversine_distance(start_station, end_station)
    if distance <= 120:
        delay = max(start_station['delay'], end_station['delay'])  # Use the maximum delay between the two stations
        session.run("""
            MATCH (start:Station {name: $start_name})
            MATCH (end:Station {name: $end_name})
            MERGE (start)-[r:CONNECTED_TO]->(end)
            ON CREATE SET r.distance = $distance, r.delay = $delay
            ON MATCH SET r.distance = $distance, r.delay = $delay
        """, start_name=start_station['name'], end_name=end_station['name'], distance=distance, delay=delay)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/find_route', methods=['POST'])
def find_route():
    user_station_name1 = request.form['start_station']
    user_station_name2 = request.form['end_station']

    # Fetch latitude and longitude of user-specified stations
    user_station1 = fetch_station_data(user_station_name1)
    user_station2 = fetch_station_data(user_station_name2)

    print("Received start station:", user_station_name1)
    print("Received end station:", user_station_name2)


    # Check if user_station1 or user_station2 is None
    if user_station1 is None or user_station2 is None:
        return "One or both of the specified stations could not be found.", 400

    # Create nodes and relationships in Neo4j
    with neo_driver.session() as neo_session:
        # Create station nodes for user-specified stations if they don't already exist
        if user_station1:
            neo_session.run("""
                MERGE (s:Station {name: $name})
                ON CREATE SET s.latitude = $latitude, s.longitude = $longitude
            """, name=user_station1['name'], latitude=user_station1['latitude'], longitude=user_station1['longitude'])

        if user_station2:
            neo_session.run("""
                MERGE (s:Station {name: $name})
                ON CREATE SET s.latitude = $latitude, s.longitude = $longitude
            """, name=user_station2['name'], latitude=user_station2['latitude'], longitude=user_station2['longitude'])

        # Create relationships between user-specified stations
        if user_station1 and user_station2:
            create_relationships(neo_session, user_station1, user_station2)

    # Fetch all routes and optimal route
    all_routes_data = calculate_all_routes(neo_driver, user_station1, user_station2)
    optimal_route_data = calculate_optimal_route(neo_driver, user_station1, user_station2)

    # Limit the number of routes displayed to 5
    all_routes = []
    for i, route_data in enumerate(all_routes_data):
        if i >= 5:
            break
        stations = [node['name'] for node in route_data[0]]
        total_delay = route_data[2]
        # Convert delay to hours if it's more than 59 minutes
        if total_delay > 59:
            total_delay = f"{total_delay // 60} hours"
        else:
            total_delay = f"{total_delay} minutes"
        route = {
            'start_station': stations[0],
            'end_station': stations[-1],
            'total_delay': total_delay,
            'total_distance': int(route_data[3]),
            'stations_visited': stations
        }
        all_routes.append(route)

    if optimal_route_data:
        optimal_stations = [node['name'] for node in optimal_route_data[0][0]]
        total_delay = optimal_route_data[0][2]
        # Convert delay to hours if it's more than 59 minutes
        if total_delay > 59:
            total_delay = f"{total_delay // 60} hours"
        else:
            total_delay = f"{total_delay} minutes"
        optimal_route = {
            'start_station': optimal_stations[0],
            'end_station': optimal_stations[-1],
            'total_delay': total_delay,
            'total_distance': int(optimal_route_data[0][3]),
            'stations_visited': optimal_stations
        }
    else:
        optimal_route = None
       # Find the route between the user-specified stations
    user_route = None
    for route in all_routes:
        if user_station_name1 in route['stations_visited'] and user_station_name2 in route['stations_visited']:
          user_route = route
          break
    return render_template('result.html', all_routes=all_routes, optimal_route=optimal_route,user_route=user_route)

def calculate_all_routes(neo_driver, start_station, end_station):
    """Calculate all routes between two stations considering delay and distance"""
    with neo_driver.session() as session:
        result = session.run("""
        MATCH (start:Station {name: $start_name}), (end:Station {name: $end_name})
        CALL apoc.algo.allSimplePaths(start, end, '>', 10) YIELD path
        UNWIND relationships(path) AS rel 
        WITH nodes(path) AS nodes, collect(rel) AS relationships 
        RETURN nodes, relationships, 
               reduce(total_delay = 0, r IN relationships | total_delay + r.delay) AS total_delay,
               reduce(total_distance = 0, r IN relationships | total_distance + r.distance) AS total_distance
        """, start_name=start_station['name'], end_name=end_station['name'])
        routes = [(record['nodes'], record['relationships'], record['total_delay'], record['total_distance']) for record in result]
        return routes

def calculate_optimal_route(neo_driver, start_station, end_station):
    """Calculate the optimal route between two stations considering delay and distance"""
    with neo_driver.session() as session:
        result = session.run("""
        MATCH (start:Station {name: $start_name}), (end:Station {name: $end_name})
        CALL apoc.algo.dijkstra(start, end, 'CONNECTED_TO', 'delay') YIELD path, weight as delay
        WITH nodes(path) AS nodes, relationships(path) AS relationships, delay
        UNWIND relationships AS rel
        WITH nodes, collect(rel) AS all_rels, delay
        RETURN nodes, all_rels, delay, reduce(total_distance = 0, r IN all_rels | total_distance + r.distance) AS total_distance
        ORDER BY total_distance
        LIMIT 1
        """, start_name=start_station['name'], end_name=end_station['name'])
        
        routes = []
        for record in result:
            nodes = [dict(node) for node in record['nodes']]
            relationships = [(rel.start_node, rel.end_node) for rel in record['all_rels']]
            total_delay = record['delay']
            total_distance = record['total_distance']
            routes.append((nodes, relationships, total_delay, total_distance))
        
        return routes

if __name__ == "__main__":
    app.run(debug=True)
