from playwright.sync_api import sync_playwright
import re
import json
from html import unescape
import logging
from datetime import datetime, timezone
import requests

###############################
# Configuration Section Begin
###############################

# Change these values as needed

## Signal api values ##
# The ip:port of the signal api docker container
# UPDATE THIS TO YOUR SIGNAL API IP:PORT
WEBHOOK_URL = "http://192.168.x.x:8080/v2/send"
# The list of numbers to send the message to. 
# They must be in the format of a full international number
RECIPIENT_NUMBERS = ["+491231231234", "+491231231235"]
# The number that will be used to send the message
# This number must be registered in the signal api
# and must be in the format of a full international number
SENDING_NUMBER = "+491231231236"

# The number of hours before the appointment to send the message
# This is used to filter out appointments that are too far in the future
# The default is to only consider appointments withing the next 24 hours
THRESHOLD_HOURS = 24

# Simply select your appointment type here (1-45)
# You can see the available appointment types below
SELECTED_APPOINTMENT_TYPE = 44
# Appointment Types
### Ausweise / Reisepässe - Wohnsitz im Inland ###
# 1: Erstellung Biometrisches Foto
# 2: Ausweis: Erstbeantragung nach Einbürgerung (Personen unter 16 Jahren)
# 3: Ausweis: Erstbeantragung nach Einbürgerung (Personen ab 16 Jahren)
# 4: Verlust alter Ausweis mit Neubeantragung Ausweis
# 5: Ausweis: Beantragung (Personen unter 16 Jahren)
# 6: Ausweis: Beantragung (Personen ab 16 Jahren)
# 7: Ausweis: vorläufig
# 8: Antrag auf Befreiung von der Ausweispflicht
# 9: Ausweis: Aushändigung
# 10: Reisepass: Erstbeantragung nach Einbürgerung (Personen unter 18 Jahren)
# 11: Reisepass: Erstbeantragung nach Einbürgerung (Personen ab 18 Jahren)
# 12: Reisepass: Beantragung (Personen unter 18 Jahren)
# 13: Reisepass: Beantragung (Personen ab 18 Jahren)
# 14: Reisepass: vorläufig
# 15: Reisepass: Aushändigung
# 16: eID einschalten
# 17: Pin ändern
### weitere Dienstleistungen ###
# 18: Bewohnerparken
# 19: Bescheinigungen (z.B. Melde- / Familien- / Lebensbescheinigung)
# 20: Untersuchungsberechtigungsschein
# 21: Mitteilung SteuerID
# 22: Führungszeugnis
# 23: Beglaubigungen
# 24: Aachen-Pass
# 25: Familienkarte
# 26: Beantragung eiD-Karte (für EU-Staatsangehörige)
# 27: Aushändigung eID-Karte (für EU-Staatsangehörige)
# 28: Mitteilung von Personenstandsveränderungen im Melderegister
# 29: Führerschein: Beantragung/Umtausch
# 30: Führerschein: Aushändigung
# 31: Schwerbehindertenausweis (Antragsausgabe und Verlängerung)
# 32: Verkauf amtlicher Abfallsäcke
# 33: Sperrmüll-Abholung beauftragen
# 34: Mülltonnen: Abmeldung, Anmeldung, Ummeldung, defekt
### Ausweise / Reisepässe - Wohnsitz im Ausland ###
# 35: Erstellung Biometrisches Foto (Wohnsitz Ausland)
# 36: Ausweis: Beantragung (Personen unter 16 Jahren, Wohnsitz Ausland)
# 37: Ausweis: Beantragung (Personen ab 16 Jahren, Wohnsitz Ausland)
# 38: Reisepass: Beantragung (Personen unter 18 Jahren, Wohnsitz Ausland)
# 39: Reisepass: Beantragung (Personen ab 18 Jahren, Wohnsitz Ausland)
# 40: Ausweis: Aushändigung (Wohnsitz Ausland)
# 41: Reisepass: Aushändigung (Wohnsitz Ausland)
# 42: Pin ändern (Wohnsitz Ausland)
### Meldeangelegenheiten ###
# 43: Zuzug aus dem Ausland
# 44: Wohnsitz an-/ab-/ummelden
# 45: KFZ-Schein-Adressänderungen

# The amount of appointments to check for
APPOINTMENT_AMOUNT = 1


###############################
# Configuration Section End
###############################

# Don't change anything below this line (unless you know what you're doing)

# Appointment Type Configuration
APPOINTMENT_TYPES = {
    1: {
        "name": "Erstellung Biometrisches Foto",
        "service_id": "116df7ba-ea4e-4cf0-b6b9-0723d37ef78d"
    },
    2: {
        "name": "Ausweis: Erstbeantragung nach Einbürgerung (Personen unter 16 Jahren)",
        "service_id": "e2da5155-fe39-4a21-bc07-46cd16a824b9"
    },
    3: {
        "name": "Ausweis: Erstbeantragung nach Einbürgerung (Personen ab 16 Jahren)",
        "service_id": "167f484a-f65d-49cf-8925-dca7be061b36"
    },
    4: {
        "name": "Verlust alter Ausweis mit Neubeantragung Ausweis",
        "service_id": "c4e3989a-e5c0-418f-9198-80493c707ec2"
    },
    5: {
        "name": "Ausweis: Beantragung (Personen unter 16 Jahren)",
        "service_id": "fae35b04-9e00-4f73-b1f2-e1ad0a17a87e"
    },
    6: {
        "name": "Ausweis: Beantragung (Personen ab 16 Jahren)",
        "service_id": "10b657a5-0e90-44bc-b72a-2cfec873f6d2"
    },
    7: {
        "name": "Ausweis: vorläufig",
        "service_id": "00dc099a-f550-4481-b1da-48321aea5224"
    },
    8: {
        "name": "Antrag auf Befreiung von der Ausweispflicht",
        "service_id": "c4893630-52bf-4f77-b728-f09407c728e3"
    },
    9: {
        "name": "Ausweis: Aushändigung",
        "service_id": "0886bc62-fa3e-405a-af63-8054959e85b3"
    },
    10: {
        "name": "Reisepass: Erstbeantragung nach Einbürgerung (Personen unter 18 Jahren)",
        "service_id": "716e4507-b635-4dca-8b86-00c10da3d3f9"
    },
    11: {
        "name": "Reisepass: Erstbeantragung nach Einbürgerung (Personen ab 18 Jahren)",
        "service_id": "74575ac4-9906-4ad5-a8af-aa556e526704"
    },
    12: {
        "name": "Reisepass: Beantragung (Personen unter 18 Jahren)",
        "service_id": "0f3887e6-be79-46fc-a5b1-af02110d91be"
    },
    13: {
        "name": "Reisepass: Beantragung (Personen ab 18 Jahren)",
        "service_id": "d9c6e7d3-d24d-4ccf-8fd4-62ba9c05caf7"
    },
    14: {
        "name": "Reisepass: vorläufig",
        "service_id": "51d53890-e2e0-4f76-a05d-537341860a51"
    },
    15: {
        "name": "Reisepass: Aushändigung",
        "service_id": "a38ae120-a5a8-4fe7-a5b1-7a7a938a07db"
    },
    16: {
        "name": "eID einschalten",
        "service_id": "d60dc34b-8586-48bd-9feb-23bc6fa91794"
    },
    17: {
        "name": "Pin ändern",
        "service_id": "07103639-8025-4df0-9772-220e84eb0af2"
    },
    18: {
        "name": "Bewohnerparken",
        "service_id": "5e0d7cd5-8784-43f0-a3ac-b10da3d2af96"
    },
    19: {
        "name": "Bescheinigungen (z.B. Melde- / Familien- / Lebensbescheinigung)",
        "service_id": "7d4c84e7-fb13-45c1-97a6-185af8235b6e"
    },
    20: {
        "name": "Untersuchungsberechtigungsschein",
        "service_id": "2fc984c8-70b3-439c-9dca-b77db3ad76d8"
    },
    21: {
        "name": "Mitteilung SteuerID",
        "service_id": "05bdef1d-1b12-45ba-bd29-fae0d1a58ed7"
    },
    22: {
        "name": "Führungszeugnis",
        "service_id": "7caa3811-0ba7-4e31-841e-aa69831d7782"
    },
    23: {
        "name": "Beglaubigungen",
        "service_id": "5e57c467-63cb-4fbc-bed9-6fd30cf515ec"
    },
    24: {
        "name": "Aachen-Pass",
        "service_id": "7028a6df-7a61-40f8-a920-3ec5c9d1f969"
    },
    25: {
        "name": "Familienkarte",
        "service_id": "146c80d6-bb02-42b8-aafa-bd3e855414c9"
    },
    26: {
        "name": "Beantragung eiD-Karte (für EU-Staatsangehörige)",
        "service_id": "64a30e77-8224-41e8-bee9-624464dcd860"
    },
    27: {
        "name": "Aushändigung eID-Karte (für EU-Staatsangehörige)",
        "service_id": "cc8b1d05-8cd9-4555-a666-39ed185292ba"
    },
    28: {
        "name": "Mitteilung von Personenstandsveränderungen im Melderegister",
        "service_id": "38c66af1-44e8-4781-804d-1693e703a346"
    },
    29: {
        "name": "Führerschein: Beantragung/Umtausch",
        "service_id": "b0a3bbe1-4747-44cb-a8d3-b56a3be9fe15"
    },
    30: {
        "name": "Führerschein: Aushändigung",
        "service_id": "b755ee1f-9df1-4a66-acfd-76b9e46b1211"
    },
    31: {
        "name": "Schwerbehindertenausweis (Antragsausgabe und Verlängerung)",
        "service_id": "216bbe43-d673-472b-be08-fe122ee1bc2b"
    },
    32: {
        "name": "Verkauf amtlicher Abfallsäcke",
        "service_id": "b829df33-9df6-4bd9-b740-301df3efb643"
    },
    33: {
        "name": "Sperrmüll-Abholung beauftragen",
        "service_id": "2db0b2e2-8f00-4aa6-a08c-44dff95cc043"
    },
    34: {
        "name": "Mülltonnen: Abmeldung, Anmeldung, Ummeldung, defekt",
        "service_id": "7bee4872-ba56-4070-9f6d-f45afdf491cb"
    },
    35: {
        "name": "Erstellung Biometrisches Foto (Wohnsitz Ausland)",
        "service_id": "d1a00eaf-f73b-4e98-ac2f-568b2d9c16c1"
    },
    36: {
        "name": "Ausweis: Beantragung (Personen unter 16 Jahren, Wohnsitz Ausland)",
        "service_id": "4a561c29-1721-4e27-b470-1a3265bf93ab"
    },
    37: {
        "name": "Ausweis: Beantragung (Personen ab 16 Jahren, Wohnsitz Ausland)",
        "service_id": "1d2f6113-811d-4643-87d0-ebd3a7780959"
    },
    38: {
        "name": "Reisepass: Beantragung (Personen unter 18 Jahren, Wohnsitz Ausland)",
        "service_id": "4c62d7e6-1c14-44a2-a8ea-3dac4b680023"
    },
    39: {
        "name": "Reisepass: Beantragung (Personen ab 18 Jahren, Wohnsitz Ausland)",
        "service_id": "98025ae5-88a5-4e8e-ac53-6ddd11231543"
    },
    40: {
        "name": "Ausweis: Aushändigung (Wohnsitz Ausland)",
        "service_id": "b98b99d3-aa3b-4af8-99c6-ed9580de78aa"
    },
    41: {
        "name": "Reisepass: Aushändigung (Wohnsitz Ausland)",
        "service_id": "bab4aab0-4572-4ae6-9b81-5db9f7ea75df"
    },
    42: {
        "name": "Pin ändern (Wohnsitz Ausland)",
        "service_id": "3f6be2ff-0acf-477f-afd7-1bc3400dfa0e"
    },
    43: {
        "name": "Zuzug aus dem Ausland",
        "service_id": "f8a495fc-90bf-4e96-a776-802483d2b542"
    },
    44: {
        "name": "Wohnsitz an-/ab-/ummelden",
        "service_id": "602452fb-fdcf-49ad-a3f6-48dba4af97db"
    },
    45: {
        "name": "KFZ-Schein-Adressänderungen",
        "service_id": "9968f6be-36d5-494e-846d-cdcb0388b221"
    }
}

WEBHOOK_HEADERS = {"Content-Type": "application/json"}


# Create handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('/app/config/bot.log')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO,
    handlers=[
        file_handler,
        console_handler
    ]
)

# Assuming Appointment is a defined class
class Appointment:
    @staticmethod
    def from_json(data):
        # Placeholder implementation; adjust based on your actual class
        return data

def get_appointments() -> list[Appointment]:
    with sync_playwright() as p:
        # Launch browser in headless mode (required for GitHub Actions)
        browser = p.chromium.launch(headless=True)

        # Create a browser context with stealth settings
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",  # Do Not Track
            }
        )
        page = context.new_page()

        # Mask automation indicators
        page.evaluate("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3].map(() => ({})) });
        """)

        # Visit homepage to establish session and set referer
        homepage = "https://stadt-aachen.saas.smartcjm.com/"
        page.goto(homepage)
        page.wait_for_load_state("networkidle")

        # Navigate to the target URL
        initial_url = "https://stadt-aachen.saas.smartcjm.com/m/buergerservice/extern/calendar/?uid=15940648-b483-46d9-819e-285707f1fc34"
        page.goto(initial_url)
        page.wait_for_load_state("networkidle")

        # Get page content and check for Cloudflare block
        content = page.content()
        if "Sorry, you have been blocked" in content:
            logging.error("Blocked by Cloudflare")
            browser.close()
            raise Exception("Failed to bypass Cloudflare protection")

        # Extract the request verification token
        pattern = r"<input\b[^>]*\bname=['\"]__RequestVerificationToken['\"][^>]*\bvalue=['\"](.*?)['\"][^>]*>"
        match = re.search(pattern, content)
        if not match:
            logging.error("Could not find request verification token")
            browser.close()
            raise Exception("Token extraction failed")
        form_token = match.group(1)

        # Extract wsid
        pattern2 = r"uid=15940648-b483-46d9-819e-285707f1fc34&wsid=([^&]+)"
        match2 = re.search(pattern2, content)
        if not match2:
            logging.error("Could not find wsid token")
            browser.close()
            raise Exception("Token extraction failed")
        wsid_token = match2.group(1)

        # Construct and submit form data (adjust based on your actual needs)
        appointment_config = APPOINTMENT_TYPES[SELECTED_APPOINTMENT_TYPE]
        form_data = {
            "__RequestVerificationToken": form_token,
            "action_type": "",
            "steps": "serviceslocationssearch_resultsbookingfinish",
            "step_current": "services",
            "step_current_index": "0",
            "step_goto": "+1",
            "services": appointment_config["service_id"],
        }
        if SELECTED_APPOINTMENT_TYPE != 23:
            amount_key = f"service_{appointment_config['service_id']}_amount"
            form_data.update({amount_key: APPOINTMENT_AMOUNT})
        response = page.request.post(initial_url + "&wsid=" + wsid_token, form=form_data)

        # Navigate to search results (adjust URL construction as needed)
        base_url = initial_url.split("?")[0]
        search_result_url = f"{base_url}search_result?search_mode=all&uid=15940648-b483-46d9-819e-285707f1fc34&wsid={wsid_token}"
        page.goto(search_result_url)
        page.wait_for_load_state("networkidle")
        content = page.content()

        # Extract JSON data (adjust pattern based on actual page structure)
        json_pattern = r"(?<=<div id=\"json_appointment_list\">).*?(?=</div>)"
        json_match = re.search(json_pattern, content, flags=re.DOTALL)
        if not json_match:
            logging.error("JSON data not found in page content")
            browser.close()
            raise Exception("Failed to extract appointment data")

        appointments_json = json.loads(unescape(json_match.group(0)))
        if "nothing_Found" in appointments_json.get("appointments", ""):
            logging.info("No appointments found")
            browser.close()
            return []

        # Parse appointments
        appointments = [Appointment.from_json(appointment) for appointment in appointments_json["appointments"]]
        
        browser.close()
        return appointments


def send_webhook_notification(count, earliest_appointment):
    # Change message format as needed
    message = (
        f"There are {count} appointments available within the next {THRESHOLD_HOURS} hours!\n"
        f"Appointment Type: {APPOINTMENT_TYPES[SELECTED_APPOINTMENT_TYPE]['name']}\n"
        f"Next available:\n"
        f"Date: {earliest_appointment['date_time']}\n"
        f"Location: {earliest_appointment['unit']}\n"
        f"Link: https://stadt-aachen.saas.smartcjm.com{earliest_appointment['link']}"
    )
    
    payload = {
        "message": message,
        "number": SENDING_NUMBER,
        "recipients": RECIPIENT_NUMBERS
    }
    
    try:
        logging.debug(f"Sending webhook with payload: {json.dumps(payload, indent=2)}")
        response = requests.post(WEBHOOK_URL, json=payload, headers=WEBHOOK_HEADERS)
        logging.debug(f"Response status: {response.status_code}")
        logging.debug(f"Response content: {response.text}")
        response.raise_for_status()
        logging.info("Webhook notification sent")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send webhook notification: {e}")


if __name__ == "__main__":
    try:
        appointments = get_appointments()
        logging.info(f"Found {len(appointments)} appointments")
        if len(appointments) > 0:
            current_time = datetime.now(timezone.utc)
            
            # Sort all appointments first
            sorted_appointments = sorted(appointments, 
                key=lambda x: datetime.fromisoformat(x['datetime_iso86001'].replace('.0000000', '')))
            
            # Filter appointments within threshold
            available_appointments = []
            for appointment in sorted_appointments:
                appointment_date = datetime.fromisoformat(appointment['datetime_iso86001'].replace('.0000000', '')).replace(tzinfo=timezone.utc)
                hours_difference = (appointment_date - current_time).total_seconds() / 3600
                if hours_difference <= THRESHOLD_HOURS:
                    available_appointments.append(appointment)
                else:
                    # Since appointments are sorted, if this one is too far, all remaining ones will be too
                    break
            
            if available_appointments:
                earliest_appointment = available_appointments[0]  # Already sorted
                logging.info(f"Found {len(available_appointments)} appointments within {THRESHOLD_HOURS} hours")
                send_webhook_notification(len(available_appointments), earliest_appointment)
            else:
                logging.info(f"No appointments found within {THRESHOLD_HOURS} hours")

    except Exception as e:
        print(f"Error: {str(e)}")