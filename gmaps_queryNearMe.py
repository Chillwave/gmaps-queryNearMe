import csv
import googlemaps
import requests
from bs4 import BeautifulSoup
import re

print("Google Maps nearby search query exporter")
print("github.com/chillwave // 2023")

searchQuery = input("Input requested search query. Verify address.txt & api_key.txt exists.")
requestedRadius = int(input("Input radius in meters. (16093.44 Meters = 10 Miles)"))


def sanitize_hours(opening_hours):
    if isinstance(opening_hours, list):
        return ', '.join(opening_hours)
    return opening_hours


def scrape_website_for_email(website):
    try:
        response = requests.get(website)
        soup = BeautifulSoup(response.content, 'html.parser')
        email = extract_email_from_html(soup)
        return email if email else "Not found on site"
    except requests.exceptions.RequestException:
        return "Not found on site"


def extract_email_from_html(soup):
    email_regex = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}")
    for element in soup.find_all(string=email_regex):
        email = email_regex.search(element)
        if email:
            return email.group()
    return None


def get_keyword_information(address, api_key):
    gmaps = googlemaps.Client(key=api_key)

    # Geocode the address to get its latitude and longitude
    geocode_result = gmaps.geocode(address)
    if not geocode_result:
        print("Invalid address. Please check the address and try again.")
        return []

    location = geocode_result[0]['geometry']['location']
    lat = location['lat']
    lng = location['lng']

    # Perform a nearby search for the provided keyword
    places = gmaps.places_nearby(location=(lat, lng), radius=requestedRadius, keyword=searchQuery)

    if 'results' in places:
        obtainedLocationInfo = []

        for place in places['results']:
            place_details = gmaps.place(
                place['place_id'],
                fields=['name', 'formatted_address', 'formatted_phone_number', 'website', 'opening_hours']
            )

            if 'result' in place_details:
                name = place_details['result'].get('name', '')
                address = place_details['result'].get('formatted_address', '')
                phone = place_details['result'].get('formatted_phone_number', '')
                website = place_details['result'].get('website', '')
                opening_hours = place_details['result'].get('opening_hours', {}).get('weekday_text', [])

                if isinstance(opening_hours, str):
                    opening_hours = [opening_hours]  # Convert string to list of one item

                formatted_opening_hours = sanitize_hours(opening_hours)

                email = scrape_website_for_email(website)

                print(f"Place: {name}")
                print(f"Address: {address}")
                print(f"Website: {website}")
                print(f"Phone: {phone}")
                print(f"Opening Hours: {formatted_opening_hours}")
                print(f"Email: {email}")
                print()

                obtainedLocationInfo.append({
                    'Name': name,
                    'Address': address,
                    'Phone': phone,
                    'Website': website,
                    'Opening Hours': formatted_opening_hours,
                    'Email': email
                })

        return obtainedLocationInfo
    else:
        print("No entries found.")
        return []


def save_to_csv(obtainedLocationInfo, filename):
    fieldnames = ['Name', 'Address', 'Phone', 'Website', 'Opening Hours', 'Email']

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(obtainedLocationInfo)


# Load address from address.txt
try:
    with open('address.txt', 'r') as address_file:
        your_address = address_file.read().strip()
except FileNotFoundError:
    print("Error: address.txt file not found.")
    exit(1)

# Load API key from api_key.txt
try:
    with open('api_key.txt', 'r') as api_key_file:
        api_key = api_key_file.read().strip()
except FileNotFoundError:
    print("Error: api_key.txt file not found.")
    exit(1)

# Call the functions
locationInformation = get_keyword_information(your_address, api_key)

if locationInformation:
    save_to_csv(
        locationInformation,
        searchQuery + '_radius_' + str(requestedRadius) + '_meters_' + 'searchQuery.csv'
    )
    print("Obtained locations saved to CSV format.")
