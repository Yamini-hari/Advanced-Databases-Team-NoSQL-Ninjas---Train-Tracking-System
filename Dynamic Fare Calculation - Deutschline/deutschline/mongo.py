from db import MongoDBConnection, mongo_connection
from utils import convert_to_iso_format, convert_from_iso_format

# Define your MongoDB query
query = {"train_type": "ICE"}

def get_num_tickets(date, train_number, ticket_class, departures, arrivals):
    train_number = str.upper(train_number[0])
    if not departures or not arrivals:
        return "Train Not Found"
    count = 0
    trains = []
    for data in departures:
        date_time_departure = convert_to_iso_format(date, data)
        date_time_arrival = convert_to_iso_format(date, arrivals[count])
        print(date_time_departure)
        print(date_time_arrival)
        pipeline = [
            {
                "$match": {
                    "train_num": train_number,
                    "date_time": {
                        "$gte": date_time_departure,
                        "$lt": date_time_arrival
                    },
                    "ticket_class": ticket_class
                }
            },
            {
                "$group": {
                "_id": {
                    "train_num": "$train_num",
                    "date_time": "$date_time",
                    "ticket_class": "$ticket_class"
                },
                "tickets": { "$sum": "$number_of_tickets" }
                }
            },
            {
                "$group": {
                "_id": "null",
                "total_tickets": {
                    "$sum": "$tickets"
                }
                }
            }
        ]

        print(pipeline)

        result = mongo_connection.aggregate(collection_name="data2", pipeline=pipeline)

        if not result:
            result.append({'total_tickets': 0, 'train_date_time': date_time_departure})
        
        for data in result:
            data["train_date_time"] = date_time_departure
        count=count+1
        trains.append(result)
        print("AGGREGATE ::: ", result)
    return trains


def get_train_fare_increases(demandRequest):
    finalRes = []
    for data in demandRequest:
        print("HERE :: " , data)
        percentage = data["capacity"]
        train_date, train_time = convert_from_iso_format(data["train_date_time"])
        print("HERE :: " , train_date, train_time)

        pipeline = [
            {
                "$project": {
                    "_id": 0,
                    "timing_fare_increase": {
                        "$reduce": {
                            "input": "$fare_rules.timing",
                            "initialValue": 0,
                            "in": {
                                "$cond": [
                                    {
                                        "$and": [
                                            {"$lte": ["$$this.time_range.start", train_time]},
                                            {"$gt": ["$$this.time_range.end", train_time]}
                                        ]
                                    },
                                    "$$this.fare_increase",
                                    "$$value"
                                ]
                            }
                        }
                    },
                    "demand_fare_increase": {
                        "$reduce": {
                            "input": "$fare_rules.demand",
                            "initialValue": 0,
                            "in": {
                                "$cond": [
                                    {
                                        "$and": [
                                            {"$lte": ["$$this.booking_percentage_range.start", percentage]},
                                            {"$gte": ["$$this.booking_percentage_range.end", percentage]}
                                        ]
                                    },
                                    "$$this.fare_increase",
                                    "$$value"
                                ]
                            }
                        }
                    },
                    "vacation_fare_increase": {
                        "$reduce": {
                            "input": "$fare_rules.vacation",
                            "initialValue": 0,
                            "in": {
                                "$cond": [
                                    {
                                        "$and": [
                                            {"$eq": ["$$this.period", "vacation"]},
                                            {"$in": [train_date, "$$this.dates"]}
                                        ]
                                    },
                                    "$$this.fare_increase",
                                    "$$value"
                                ]
                            }
                        }
                    }
                }
            },
            {
                "$addFields": {
                    "total_fare_increase": {
                        "$add": [
                            "$timing_fare_increase",
                            "$demand_fare_increase",
                            "$vacation_fare_increase"
                        ]
                    }
                }
            }
        ]
        mongo_connection = MongoDBConnection(uri="mongodb://localhost:27017", database="test")        
        mongo_connection.connect()
        results = mongo_connection.aggregate(collection_name="fare_rules", pipeline=pipeline)
        for result in results:
            result["train_date_time"] = data["train_date_time"]
        print("FARE_INCREASE ::: ", results)
        finalRes.append(results)
    return finalRes



