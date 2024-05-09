import requests
import redis
import json
from neo4j import GraphDatabase
import time

# Connect to Redis
r = redis.Redis(host='127.0.0.1', port=6379, db=0)

# Connect to Neo4j
neo4j_uri = "bolt://localhost:7687"
neo4j_user = "neo4j"
neo4j_password = "password"
neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

# Function to save journey data to Neo4j
def save_journey_to_neo4j(from_station, to_station, journey_data, from_latitude, from_longitude, to_latitude, to_longitude):
    with neo4j_driver.session() as session:
        session.run(
            """
            MERGE (from:Station {id: $from_id, latitude: $from_lat, longitude: $from_lon})
            MERGE (to:Station {id: $to_id, latitude: $to_lat, longitude: $to_lon})
            MERGE (from)-[j:JOURNEY]->(to)
            SET j.data = $journey_data
            """,
            from_id=from_station,
            to_id=to_station,
            journey_data=json.dumps(journey_data),
            from_lat=from_latitude,
            from_lon=from_longitude,
            to_lat=to_latitude,
            to_lon=to_longitude
        )

# Function to fetch journeys
def fetch_journeys(from_param, to_param, options=None):
    try:
        # Base URL for journeys endpoint
        journeys_url = 'https://v6.db.transport.rest/journeys'

        # Construct the parameters for the request
        params = {'from': from_param, 'to': to_param}
        if options:
            params.update(options)

        # Make a GET request to fetch journey information
        response = requests.get(journeys_url, params=params)
        response.raise_for_status()  # Raise an exception for non-200 status codes

        # Parse the JSON response
        journey_data = response.json()
        return journey_data
    except Exception as e:
        #print(f"Error fetching journeys: {e}")
        return None

urls = [
    "https://v6.db.transport.rest/locations?query=munchen&results=1",
    "https://v6.db.transport.rest/locations?query=berlin&results=1",
    "https://v6.db.transport.rest/locations?query=mannheim&results=1",
    "https://v6.db.transport.rest/locations?query=frankfurt&results=1",
    "https://v6.db.transport.rest/locations?query=hamburg&results=1"
]

station_ids = []
station_latitude = []
station_longitude = []

for url in urls:
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for entry in data:
            station_ids.append(entry['id'])
            # Accessing latitude and longitude
            location = entry.get('location', {})
            latitude = location.get('latitude')
            longitude = location.get('longitude')
            station_latitude.append(latitude)
            station_longitude.append(longitude)

    else:
        print("Failed to retrieve data from", url, ". Status code:", response.status_code)

print(station_latitude)
print(station_longitude)

# Define options for the request
options = {
    'results': 1,  # Number of journeys
    'stopovers': True,  # Include stopovers
    'language': 'en',  # Language of the results
    'tickets': False,  # Do not include ticket information
    'polylines': False,  # Do not include polylines
    'subStops': True,  # Parse & expose sub-stops of stations
    'entrances': True,  # Parse & expose entrances of stops/stations
    'remarks': True  # Parse & expose hints & warnings
}

# Iterate over all combinations of station IDs
for i, from_station in enumerate(station_ids, 1):
    for to_station in station_ids:
        # Skip same station combinations
        if from_station == to_station:
            continue

        # Fetch journeys
        journey_data = fetch_journeys(from_station, to_station, options)

        if journey_data:
            # Store journey data in Neo4j
            from_lat = station_latitude[station_ids.index(from_station)]
            from_lon = station_longitude[station_ids.index(from_station)]
            to_lat = station_latitude[station_ids.index(to_station)]
            to_lon = station_longitude[station_ids.index(to_station)]
            save_journey_to_neo4j(from_station, to_station, journey_data, from_lat, from_lon, to_lat, to_lon)
            # Store journey data in Redis
            key = f"{from_station}_{to_station}"  # Use combination as the key
            r.set(key, json.dumps(journey_data))  # Convert data to JSON string before storing
        else:
            print(f"No journey data found for {from_station} to {to_station}. Skipping...")

        # Introduce a delay of 1 second
        time.sleep(1)

    # Display progress
    print(f"Progress: {i}/{len(station_ids)}")

print("All combinations processed.")
