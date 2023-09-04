import requests
import os
import pandas as pd
from datetime import datetime, timedelta
import json
from retry import retry
from concurrent.futures import ThreadPoolExecutor
import datetime as dt

# Load configuration from config.json
with open("config.json") as config_file:
    config = json.load(config_file)

MAX_RETRIES = config["max_retries"]
MAX_WORKERS = config["max_num_of_threads"]
RETRY_DELAY_SECONDS = config["retry_delay_seconds"]
BASE_HEADER = config["headers"][0]["base_header"]
DETAIL_HEADER = config["headers"][0]["data_header"]

timestamp = 0


@retry(
    requests.exceptions.RequestException, tries=MAX_RETRIES, delay=RETRY_DELAY_SECONDS
)
def get_operators_data():
    # Request data for location and further relevant API calls
    response = requests.request("GET", config["zostel_url"], headers=BASE_HEADER)

    # Define the folder path
    data_folder = "data"
    subfolder_name = "operator_data"

    os.makedirs(os.path.join(data_folder, subfolder_name), exist_ok=True)
    json_file_path = os.path.join(data_folder, subfolder_name, "operators.json")

    data = {
        "operators": [
            {"slug": operator["slug"], "name": operator["destination"]["name"]}
            for operator in response.json()["operators"]
        ]
    }

    # Write the operator data to the json file
    with open(json_file_path, "w") as json_file:
        json.dump(data, json_file, indent=4)


def get_all_room_details(operators):
    # Get the check-in and check-out dates for relevant API calls
    # duration_days is the number of days to fetch data for
    today = datetime.today().date()
    later = today + timedelta(days=config["duration_days"])

    first_date = today.strftime("%Y-%m-%d")
    last_date = later.strftime("%Y-%m-%d")

    # Define the data folder path
    data_folder = "data"

    room_data_folder = "room_data"
    availability_data_folder = "availability_data"

    # Create the subfolder and parent directories if they don't exist
    os.makedirs(os.path.join(data_folder, room_data_folder), exist_ok=True)
    os.makedirs(os.path.join(data_folder, availability_data_folder), exist_ok=True)

    global timestamp
    timestamp = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    room_file_path = os.path.join(data_folder, room_data_folder, "room_data.json")
    availability_file_path = os.path.join(
        data_folder, availability_data_folder, f"{timestamp}.json"
    )

    # Initialize an empty dictionary to accumulate all room data
    all_room_data = {}
    all_availability_data = {}

    # Get data concurrently
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []

        for operator in operators:
            code = operator["slug"].rsplit("-", 1)[-1].upper()

            room_future = executor.submit(get_room_data, operator["slug"])
            availability_future = executor.submit(
                get_availability_data, code, first_date, last_date
            )

            futures.append((operator, room_future, availability_future))

        for operator, room_future, availability_future in futures:
            try:
                room_data = room_future.result()
                all_room_data[operator["name"]] = room_data
            except Exception as room_error:
                print(f"Error getting room data for {operator['name']}: {room_error}")

            try:
                availability_data = availability_future.result()
                all_availability_data[operator["name"]] = availability_data
            except Exception as availability_error:
                print(
                    f"Error getting availability data for {operator['name']} {availability_error}"
                )

    # Write the accumulated data to the JSON files
    with open(room_file_path, "w") as json_file:
        json.dump(all_room_data, json_file, indent=4)

    with open(availability_file_path, "w") as json_file:
        json.dump(all_availability_data, json_file, indent=4)


@retry(
    requests.exceptions.RequestException, tries=MAX_RETRIES, delay=RETRY_DELAY_SECONDS
)
def get_room_data(slug):
    # Request room data such as the room names and room IDs
    response = requests.request(
        "GET", f"{config['zostel_room_url']}{slug}/", headers=BASE_HEADER
    )

    room_data = [
        {"id": room["id"], "room_name": room["name"]}
        for room in response.json()["operator"]["rooms"]
    ]
    return room_data


@retry(
    requests.exceptions.RequestException, tries=MAX_RETRIES, delay=RETRY_DELAY_SECONDS
)
def get_availability_data(code, first_date, last_date):
    # Request availability data such as units and pricing
    response = requests.request(
        "GET",
        f"{config['availability_info_url']}?checkin={first_date}&checkout={last_date}&property_code={code}",
        headers=DETAIL_HEADER,
    )

    availability = response.json()["availability"]
    pricing = response.json()["pricing"]
    availability_data = {}

    for avail_item, price_item in zip(availability, pricing):
        room_id = avail_item["room_id"]

        # Check if the 'room_id' already exists as a key in 'availability_data'
        if room_id in availability_data:
            # Append the data to the existing list associated with 'room_id'
            availability_data[room_id].append(
                {
                    "price": price_item["price"],
                    "units": avail_item["units"],
                    "date": avail_item["date"],
                }
            )
        else:
            # Create a new list with the data for this 'room_id'
            availability_data[room_id] = [
                {
                    "price": price_item["price"],
                    "units": avail_item["units"],
                    "date": avail_item["date"],
                }
            ]

    return availability_data


def compile_data():
    data_list = create_data_list_for_operator()
    df = pd.DataFrame(data_list)
    df.to_csv("output.csv", index=False)


# Get the data from local json files and maintain structure
def create_data_list_for_operator():
    data_list = []

    # Get all places
    with open("data/operator_data/operators.json", "r") as json_file:
        operators = json.load(json_file)["operators"]

    for operator in operators:
        place = operator["name"]

        # Get all rooms of the place
        with open("data/room_data/room_data.json", "r") as json_file:
            rooms = json.load(json_file)[f"{place}"]

        for room in rooms:
            room_name = room["room_name"]
            id = room["id"]

            # Get availability data for the specific room of the specific place
            with open(f"data/availability_data/{timestamp}.json", "r") as json_file:
                availability_data = json.load(json_file)[f"{place}"][f"{id}"]

            for entry in availability_data:
                data_list.append(
                    {
                        "Place": place,
                        "Date": entry["date"],
                        "Room Type": room_name,
                        "Units": entry["units"],
                        "Price": entry["price"],
                    }
                )
    return data_list


def main():
    # Get the destination details and relevant API data
    get_operators_data()

    with open("data/operator_data/operators.json", "r") as json_file:
        operators = json.load(json_file)["operators"]

    get_all_room_details(operators)
    compile_data()


main()
