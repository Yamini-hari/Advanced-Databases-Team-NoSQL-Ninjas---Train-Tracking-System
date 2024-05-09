from flask import Flask, render_template, request, jsonify
import redis
import json
from collections import defaultdict
import plotly.graph_objs as go

app = Flask(__name__)

# Connect to Redis
redis_host = 'localhost'
redis_port = 6379
redis_db = 0
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)

# Function to fetch and process data
def fetch_data(from_station, to_station):
    # Initialize variables to store calculated features
    average_delay = None
    peak_hours = []
    train_frequencies = {}

    # Retrieve keys matching a pattern
    keys = redis_client.keys('*')

    # Iterate over keys and retrieve corresponding values
    for key in keys:
        entry_json = redis_client.get(key)
        if entry_json:
            entry_data = json.loads(entry_json)

            # Extract journeys from the dataset
            journeys = entry_data["journeys"]

            # Calculate Average Delay, Peak Hours, and Frequency of Trains for relevant journey
            for journey in journeys:
                origin = journey["legs"][0]["origin"]["name"]
                destination = journey["legs"][-1]["destination"]["name"]
                if origin == from_station and destination == to_station:
                    delays = [leg["arrivalDelay"] for leg in journey["legs"] if leg["arrivalDelay"] is not None]
                    if delays:
                        average_delay = sum(delays) / len(delays)
                    else:
                        average_delay = 0

                    departure_times = [journey["legs"][0]["departure"]]
                    for leg in journey["legs"][1:]:
                        if leg["departure"] != departure_times[-1]:
                            departure_times.append(leg["departure"])

                    hour_counts = defaultdict(int)
                    for departure_time in departure_times:
                        hour = int(departure_time.split('T')[1][:2])
                        hour_counts[hour] += 1

                    max_count = max(hour_counts.values())
                    peak_hours = [hour for hour, count in hour_counts.items() if count == max_count]

                    route = f"{origin} to {destination}"
                    train_frequencies[route] = len(departure_times)

                    # Break loop if relevant journey is found
                    break

        # Break loop if relevant journey is found
        if average_delay is not None:
            break

    return average_delay if average_delay is not None else 0, peak_hours, train_frequencies

# Function to fetch peak hours data
def fetch_peak_hours(from_station, to_station):
    _, peak_hours, _ = fetch_data(from_station, to_station)
    return peak_hours

# Function to fetch historical data
def fetch_historical_data(from_station, to_station):
    # Initialize variables to store historical data
    historical_delays = defaultdict(list)
    historical_load_factors = defaultdict(list)

    # Retrieve keys matching a pattern
    keys = redis_client.keys('*')

    # Iterate over keys and retrieve corresponding values
    for key in keys:
        entry_json = redis_client.get(key)
        if entry_json:
            entry_data = json.loads(entry_json)

            # Extract journeys from the dataset
            journeys = entry_data["journeys"]

            # Calculate historical delays and load factors for relevant journey
            for journey in journeys:
                origin = journey["legs"][0]["origin"]["name"]
                destination = journey["legs"][-1]["destination"]["name"]
                if origin == from_station and destination == to_station:
                    delays = [leg["arrivalDelay"] for leg in journey["legs"] if leg["arrivalDelay"] is not None]
                    load_factor = journey.get("loadFactor")
                    departure_time = journey["legs"][0]["departure"].split('T')[0]

                    if delays:
                        historical_delays[departure_time].append(sum(delays) / len(delays))
                    if load_factor:
                        historical_load_factors[departure_time].append(load_factor)

    return historical_delays, historical_load_factors

# Route to handle form submission and return historical data
@app.route('/historical_data')
def historical_data():
    from_station = request.args.get('from')
    to_station = request.args.get('to')
    historical_delays, historical_load_factors = fetch_historical_data(from_station, to_station)
    return jsonify({
        'historical_delays': {date: sum(delays)/len(delays) for date, delays in historical_delays.items()},
        'historical_load_factors': {date: max(set(load_factors), key = load_factors.count) for date, load_factors in historical_load_factors.items()}
    })

# Route to handle form submission and return relevant information
@app.route('/train_info')
def train_info():
    from_station = request.args.get('from')
    to_station = request.args.get('to')
    average_delay, peak_hours, train_frequencies = fetch_data(from_station, to_station)
    return jsonify({
        'average_delay': average_delay,
        'peak_hours': peak_hours,
        'train_frequencies': train_frequencies
    })

# Route to render the webpage with peak hours graph
@app.route('/')
def index():
    from_station = request.args.get('from')
    to_station = request.args.get('to')
    peak_hours = fetch_peak_hours(from_station, to_station)

    # Create Plotly figure
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[str(hour) for hour in peak_hours], y=[1] * len(peak_hours)))

    # Update layout
    fig.update_layout(title='Peak Hours',
                      xaxis_title='Hour',
                      yaxis_title='Frequency',
                      template='plotly_white')

    # Convert Plotly figure to JSON
    graph_json = fig.to_json()

    return render_template('index.html', graph_json=graph_json)

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Change the port number as needed
