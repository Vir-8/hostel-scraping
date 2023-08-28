import requests
import pandas as pd
from datetime import datetime, timedelta
import json
from retry import retry

# Load configuration from config.json
with open("config.json") as config_file:
    config = json.load(config_file)

MAX_RETRIES = config["max_retries"]
RETRY_DELAY_SECONDS = config["retry_delay_seconds"]
BASE_HEADER = config["headers"][0]["base_header"]
DETAIL_HEADER = config["headers"][0]["data_header"]


@retry(
    requests.exceptions.RequestException, tries=MAX_RETRIES, delay=RETRY_DELAY_SECONDS
)
def get_operators_data():
    # Request data for location and further relevant API calls
    response = requests.request("GET", config["zostel_url"], headers=BASE_HEADER)
    return response.json()["operators"]


@retry(
    requests.exceptions.RequestException, tries=MAX_RETRIES, delay=RETRY_DELAY_SECONDS
)
def get_room_data(slug):
    # Request room data such as the room names
    response = requests.request(
        "GET", f"{config['zostel_room_url']}{slug}/", headers=BASE_HEADER
    )
    rooms = response.json()["operator"]["rooms"]
    return rooms


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
    return response.json()


def create_data_list(operators, first_date, last_date):
    data_list = []
    for operator in operators:
        # Get the specific keyword for getting zostel room data
        slug = operator["slug"]
        place = operator["destination"]["name"]

        # Get the destination code for accessing availability data
        code = slug.rsplit("-", 1)[-1].upper()

        rooms = get_room_data(slug)
        room_details = get_availability_data(code, first_date, last_date)

        general_info = room_details["availability"]  # Extract availability data
        pricing_info = room_details["pricing"]  # Extract prices

        for index in range(len(rooms)):
            # Get the zostel room name
            room_name = rooms[index]["name"]

            # Set loop start and end such that the appropriate room data is extracted
            start_index = index * config["duration_days"]
            end_index = start_index + config["duration_days"]

            for i in range(start_index, end_index):
                date = general_info[i]["date"]
                unit_value = general_info[i]["units"]
                price = pricing_info[i]["price"]
                data_list.append(
                    {
                        "Place": place,
                        "Date": date,
                        "Room Type": room_name,
                        "Units": unit_value,
                        "Price": price,
                    }
                )
    return data_list


def main():
    # Get the check-in and check-out dates for relevant API calls
    # duration_days is the number of days to fetch data for
    today = datetime.today().date()
    later = today + timedelta(days=config["duration_days"])

    first_date = today.strftime("%Y-%m-%d")
    last_date = later.strftime("%Y-%m-%d")

    # Get the destination details and relevant API data
    operators = get_operators_data()
    data_list = create_data_list(operators, first_date, last_date)

    df = pd.DataFrame(data_list)
    df.to_csv("output.csv", index=False)


main()
