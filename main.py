import argparse
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.mit-dem-rad-zur-arbeit.de"

def login(session, username, password):
    # Definiere die URL
    url = f"{BASE_URL}/bundesweit/index.php"
    
    # Definiere die Daten für den POST-Request
    data = {
        "username": username,
        "passwort": password,
        "btnLogin": "btnLogin"
    }
    
    # Sende den POST-Request
    response = session.post(url, data=data)
    
    # Überprüfe, ob die Anfrage erfolgreich war
    if response.status_code == 200:
        print("Anmeldung erfolgreich!")
        
        # Gib den HTML-Body zurück
        return response.text
        
    else:
        print("Fehler bei der Anmeldung:", response.status_code)
        return None

def delete_record():
    pass

def insert_record(session, day, kilometers, teilnehmer_id, csrf_token):
    # Definiere die URL für das Einfügen von Datensätzen
    url = f"{BASE_URL}/hamburg/start.php"
    
    # Definiere die Formulardaten
    form_data = {
        "form_data[tn][value]": teilnehmer_id,
        "form_data[distance][req]": "1",
        "form_data[distance][value]": kilometers,
        "form_data[distance][desc]": "Kilometer",
        "form_data[distdate][]": day,
        "csrf": csrf_token,
        "distsub": "1",
        "send": ""
    }
    
    # Sende den POST-Request mit den angegebenen Formulardaten
    response = session.post(url, data=form_data)
    
    # Überprüfe, ob die Anfrage erfolgreich war
    if response.status_code == 200:
        print(f"Teilnehmer {teilnehmer_id}: {kilometers} Kilometer am '{day}' erfolgreich eingefügt!")
    else:
        print("Fehler beim Einfügen des Datensatzes:", response.status_code)

def main():
    # Parameter
    parser = argparse.ArgumentParser(description="Anmelden und Datensatz einfügen")
    parser.add_argument("--username", type=str, help="Benutzername für die Anmeldung")
    parser.add_argument("--password", type=str, help="Passwort für die Anmeldung")
    parser.add_argument("--day", type=str, default="2024-05-07", help="Datum für den Datensatz (Standard: 2024-05-07)")
    parser.add_argument("--kilometers", type=str, default="8", help="Kilometer für den Datensatz (Standard: 8)")
    args = parser.parse_args()

    # Erstelle eine Sitzung
    session = requests.Session()

    # Führe die Anmeldung durch
    html_body = login(session, args.username, args.password)
    
    if html_body:

        soup = BeautifulSoup(html_body, "html.parser")
        csrf_token = soup.find("input", {"name": "csrf"})["value"]
        teilnehmer_id = soup.find("input", {"name": "form_data[tn][value]"})["value"]

        # Datensatz für den Tag einfügen
        insert_record(session, args.day, args.kilometers, teilnehmer_id, csrf_token)
        pass
    else:
        print("Keine gültigen Cookies vorhanden.")

if __name__ == "__main__":
    main()
