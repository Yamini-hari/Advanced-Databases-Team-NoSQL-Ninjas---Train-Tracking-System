import httpx
import aioredis
import json
from fastapi import FastAPI,HTTPException,BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()
redis_host = 'localhost'
redis_port = 6379
redis_db = 0


mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
db = mongo_client.Train_tracking  # Change 'mydatabase' to your database name
trips_collection = db.trips


async def get_station_coordinates(station_name: str):
    base_url = "https://v6.db.transport.rest/stations"
    params = {
        'query': station_name,
        'limit': 1,
        'completion': True
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(base_url, params=params)
        data = response.json()
        if data:
            station = next(iter(data.values()), None)
            if station and 'location' in station:
                return station['location']['latitude'], station['location']['longitude']
    return None

async def fetch_radar_data(north, west, south, east):
    base_url = "https://v6.db.transport.rest/radar"
    bbox = f'north={north}&west={west}&south={south}&east={east}'
    params = {
        'results': 10,
        'duration': 100,
        'frames': 10,
        'polylines': True,
        'language': 'en',
        'pretty': True
    }
    full_url = f"{base_url}?{bbox}"
    async with httpx.AsyncClient() as client:
        response = await client.get(full_url, params=params)
        return response.json()

async def update_trip_data(station_name, vehicle_data):
    for vehicle in vehicle_data['movements']:
        trip_id = vehicle['tripId']
        new_location = vehicle['location']
        trips_collection.update_one(
            {'station': station_name, 'tripId': trip_id},
            {'$push': {'trip_path': new_location}},
            upsert=True
        )

@app.get("/radar-data/{station_name}")
async def get_radar_data(station_name: str, background_tasks: BackgroundTasks):
    redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
    async with aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True) as redis:
        cached_data = await redis.get(f'radar_data_{station_name}')
        if cached_data:
            return json.loads(cached_data)

        coordinates = await get_station_coordinates(station_name)
        if not coordinates:
            raise HTTPException(status_code=404, detail="Station not found")

        latitude, longitude = coordinates
        margin = 0.01
        north = latitude + margin
        south = latitude - margin
        west = longitude - margin
        east = longitude + margin

        radar_data = await fetch_radar_data(north, west, south, east)
        if radar_data:
            await redis.setex(f'radar_data_{station_name}', 30, json.dumps(radar_data))
            background_tasks.add_task(update_trip_data, station_name, radar_data)
            return radar_data

        raise HTTPException(status_code=500, detail="Failed to fetch radar data")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)