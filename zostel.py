import requests
import pandas as pd
from datetime import datetime, timedelta

today = datetime.today().date()
later = today + timedelta(days=10)

first_date = today.strftime("%Y-%m-%d")
last_date = later.strftime("%Y-%m-%d")

url = "https://api.zostel.com/api/v1/stay/operators/?operating_model=F&fields=name,slug,destination"

headers = {
    "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Brave";v="116"',
    "sec-ch-ua-mobile": "?0",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.zostel.com/",
    "Client-App-Id": "FrcIH2m03QxVgFD037u8oaQczaAImvAN506cUQb4",
    "Client-User-Id": "d4fe781f74",
    "sec-ch-ua-platform": '"Linux"',
}

codeResponse = requests.request("GET", url, headers=headers)

data = codeResponse.json()
operators = data["operators"]

data_list = []

for operator in operators:
    slug = operator["slug"]
    place = operator["destination"]["name"]
    code = slug.rsplit("-", 1)[-1].upper()

    nameURL = f"https://api.zostel.com/api/v1/stay/operators/{slug}/"
    response = requests.request("GET", nameURL, headers=headers)
    rooms = response.json()["operator"]["rooms"]

    detailURL = f"https://api.zostel.com/api/v1/stay/availability/?checkin={first_date}&checkout={last_date}&property_code={code}"

    detailHeader = {
        "authority": "api.zostel.com",
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-GB,en;q=0.5",
        "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6IkFOLTY2NzgxOTQiLCJhcHBfaWQiOiJGcmNJSDJtMDNReFZnRkQwMzd1OG9hUWN6YUFJbXZBTjUwNmNVUWI0IiwidXNlcl9pZCI6IjQ1NjkyNDFmMWEiLCJhdXRoZW50aWNhdGVkIjpmYWxzZSwiaWF0IjoxNjkzMDQ2OTI2fQ.J0F7cmM6ECps0Q_b3laALr_8wXFrcz64CEpoEjm7rKQ",
        "client-app-id": "FrcIH2m03QxVgFD037u8oaQczaAImvAN506cUQb4",
        "client-user-id": "4569241f1a",
        "origin": "https://www.zostel.com",
        "referer": "https://www.zostel.com/",
        "sec-ch-ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Brave";v="116"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    }

    details = requests.request("GET", detailURL, headers=detailHeader)
    detailResponse = details.json()

    general_info = detailResponse["availability"]
    pricing_info = detailResponse["pricing"]

    for room in rooms:
        room_name = room["name"]

        for i in range(len(general_info)):
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

df = pd.DataFrame(data_list)
df.to_csv("output.csv", index=False)
