import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup

chrome_driver_path = '/usr/local/bin/chromedriver-linux64/chromedriver'

url = 'https://www.zostel.com/zostel/'

data = {}

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')  # Run Chrome in headless mode (no GUI)
chrome_options.add_argument('--disable-gpu')  # Disable GPU acceleration in headless mode
chrome_options.add_argument('--remote-debugging-port=9222')

service = ChromeService(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

driver.get(url)
driver.implicitly_wait(5)
time.sleep(3)

destinationData = driver.find_elements(By.CSS_SELECTOR, ".text-xl.font-bold.block.text-white.truncate")
destinations = ["banikhet"]

# Loop through the extracted destination texts and navigate to the URLs
for destination in destinations:
    driver.get(f"{url}{destination}")
    driver.implicitly_wait(5)
    time.sleep(3)

    stays = driver.find_element(By.CSS_SELECTOR, 'div.flex.items-center.flex-col.sm\\:flex-wrap.h-content')
    view_buttons = stays.find_elements(By.CSS_SELECTOR, 'button.text-base')

    for index in range(len(view_buttons)):
        try:
            
            stays = driver.find_element(By.CSS_SELECTOR, 'div.flex.items-center.flex-col.sm\\:flex-wrap.h-content')
            view_buttons = stays.find_elements(By.CSS_SELECTOR, 'button.text-base')

            button = view_buttons[index]
            time.sleep(2)

            # Scroll to the button using JavaScript
            driver.execute_script("arguments[0].scrollIntoView();", button)

            wait = WebDriverWait(driver, 5)
            button = wait.until(EC.element_to_be_clickable(button))
            time.sleep(2)
            button.click()

            wait = WebDriverWait(driver, 5)
            wait.until(EC.url_changes(url))
            driver.implicitly_wait(5)

            current_url = driver.current_url
            print(f"Current URL {index + 1}: {current_url}")

            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Adjust the waiting time as needed
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            time.sleep(2)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            sections = soup.find_all("section", class_ = ["mt-4 overflow-hidden w-full shadow-xs hover:shadow-md rounded-t-lg", "mt-4 overflow-hidden w-full shadow-xs hover:shadow-md rounded-lg"])
            details = soup.find_all("div", class_ = "flex w-full bg-white rounded-b-lg border-t relative px-4")

            availButtons = driver.find_elements(By.CSS_SELECTOR, ".text-xs.flex.items-center.font-semibold.text-orange.cursor-pointer")

            print (len(sections), len(details), len(availButtons))

            if len(sections) != len(details):
                for i in range(len(sections)):
                    nextElement = sections[i].find_next_sibling()
                    print(nextElement.name)
                    if nextElement.name != 'div':
                        driver.execute_script("arguments[0].scrollIntoView();", availButtons[i])
                        driver.implicitly_wait(2)
                        driver.execute_script("arguments[0].click();", availButtons[i])
                        time.sleep(2)
                
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')

                sections = soup.find_all("section", class_ = "mt-4 overflow-hidden w-full shadow-xs hover:shadow-md rounded-t-lg")
                details = soup.find_all("div", class_ = "flex w-full bg-white rounded-b-lg border-t relative px-4")

            table_data = []

            for j in range(len(details)):

                name = sections[j].find("span", class_="sm:text-xl font-semibold leading-snug block")
                data_divs = details[j].find_all(class_=["flex flex-col items-center px-2 py-4 flex-1", "flex flex-col items-center px-2 py-4 flex-1 hover:bg-gray-200 cursor-pointer"])

                print(name.text)

                for div in data_divs:
                    day_elem = div.find("span", class_="uppercase tracking-wide text-xs text-gray-600")
                    date_elem = div.find("span", class_="font-semibold text-sm text-gray-600")
                    price_elem = div.find("span", class_="mt-2 text-green-500 font-semibold")
                    units_elem = div.find("span", class_="text-sm font-medium text-gray-800")

                    if not price_elem:
                        price_elem = div.find("span", class_="text-sm font-medium text-gray-700 mt-1")

                    if not units_elem:
                        units_elem = div.find("span", class_="text-sm font-medium text-gray-700 mt-1")

                    day = day_elem.text if day_elem else "N/A"
                    date = date_elem.text if date_elem else "N/A"
                    price = price_elem.text if price_elem else "N/A"
                    units = units_elem.text if units_elem else "N/A"

                    table_data.append([day, date, price, units])



            for row in table_data:
                print("\t".join(row))

            time.sleep(3)
            driver.execute_script("window.history.go(-1);")

        except Exception as e:
            print("An error occurred:", e)
            continue

driver.quit()