import argparse
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import BlowfishEncryption
from datetime import datetime
import time
import sqlite3
import csv

# Load environment variables from .env file
load_dotenv()

BASE_URL = "https://www.mit-dem-rad-zur-arbeit.de"
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

def create_sqlite_db():
    
    print("Ensuring the SQLite database exists...")
    conn = sqlite3.connect('tours.db')
    cursor = conn.cursor()

    #region Staging
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS import_BoardCube_trip (
        InternalUsername TEXT,
        TripDate DATETIME,
        kilometers FLOAT,
        CreatedDatetime DATETIME DEFAULT CURRENT_TIMESTAMP,
        LastModDateTime DATETIME
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS import_BoardCube_MdRzA_Username (
        InternalUsername TEXT,
        UserName_MdRzA TEXT,
        CreatedDatetime DATETIME DEFAULT CURRENT_TIMESTAMP,
        LastModDateTime DATETIME
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS import_BoardCube_MdRzA_Password (
        InternalUsername TEXT,
        Password_MdRzA TEXT,
        CreatedDatetime DATETIME DEFAULT CURRENT_TIMESTAMP,
        LastModDateTime DATETIME
    )
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_import_BoardCube_trip_InternalUsername_TripDate
    ON import_BoardCube_trip (InternalUsername, TripDate)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_import_BoardCube_MdRzA_Username_InternalUsername 
    ON import_BoardCube_MdRzA_Username (InternalUsername)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_import_BoardCube_MdRzA_Password_InternalUsername 
    ON import_BoardCube_MdRzA_Password (InternalUsername)
    ''')
        
    #endregion
    
    # region main
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trips (
        InternalUsername TEXT,
        TripDate DATETIME,
        kilometers FLOAT,
        CreatedDatetime DATETIME DEFAULT CURRENT_TIMESTAMP,
        LastModDateTime DATETIME,
        isNew BOOLEAN DEFAULT TRUE,
        isModified BOOLEAN DEFAULT FALSE,
        UNIQUE(InternalUsername, TripDate)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS userLogin (
        InternalUsername TEXT,
        UserName TEXT,
        EncryptedPassword TEXT,
        CreatedDatetime DATETIME DEFAULT CURRENT_TIMESTAMP,
        LastModDateTime DATETIME,
        UNIQUE(InternalUsername)
    )
    ''')

    # Create indexes to improve performance
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_trips_InternalUsername_TripDate ON trips (InternalUsername, TripDate)
    ''')
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_trips_isModified ON trips (isModified)
    ''')
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_trips_isNew ON trips (isNew)
    ''')
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_userLogin_InternalUsername ON userLogin (InternalUsername)
    ''')
    
    conn.commit()
    conn.close()
    #endregion


    pass

def get_mdrza_logins():
    """
    Fetch UserName and EncryptedPassword for users in the SQLite database.
    
    :param InternalUsername: Internal Username (/)Board)
    :return: List of tuples containing UserName and EncryptedPassword.
    """
    
    print("Retrieving MdRzA Logins from SQLite database...")
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('tours.db')

        # Create a cursor object to interact with the database
        cursor = conn.cursor()

        cursor.execute('''
        SELECT InternalUsername, UserName, EncryptedPassword 
        FROM userLogin
        ''')

        # Fetch all rows from the executed query
        rows = cursor.fetchall()

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        rows = []

    finally:
        # Close the cursor and the connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return rows

def get_mdrza_trips_for_user(InternalUsername):
    """
    Get all Trips to be upserted for MdRzA
    
    :param InternalUsername: Board internal user name
    """
    
    print(f"Retrieving Trips for user {InternalUsername}...")
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('tours.db')

        # Create a cursor object to interact with the database
        cursor = conn.cursor()

        cursor.execute('''
        SELECT TripDate, kilometers, isNew, isModified 
        FROM trips
        WHERE (isNew = 1 OR isModified = 1) AND InternalUsername = ?
        ''', (InternalUsername,))

        # Fetch all rows from the executed query
        rows = cursor.fetchall()

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        rows = []

    finally:
        # Close the cursor and the connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    if len(rows) == 0:
        print("Didn't find new trips.")
    return rows

def import_csv_from_board(data_dir = "data"):
    
    print("Processing Board Cubes...")
    create_sqlite_db()
    conn = sqlite3.connect('tours.db')
    
    # clear staging area
    cursor = conn.cursor()

    cursor.execute('DELETE FROM import_BoardCube_MdRzA_Password')
    cursor.execute('DELETE FROM import_BoardCube_MdRzA_Username')
    cursor.execute('DELETE FROM import_BoardCube_trip')
    conn.commit()

    for entry in os.listdir(data_dir):
        file_path = os.path.join(data_dir, entry)   
     
        # Skip non-.txt files
        if not os.path.isfile(file_path) or os.path.splitext(entry)[1].lower() != '.txt':
            continue
        
        print(f'Processing file: {file_path}')
        
        with open(file_path, 'r') as csvfile:
            csvreader = csv.reader(csvfile, delimiter='\t')
            next(csvreader)  # Skip the header row
            
            for row in csvreader:
                
                if entry.startswith("Cube_AnzahlGefahreneKmJeTag"):
                    
                    try:
                        TripDate, InternalUsername, kilometers = row
                        # Convert date from YYYYMMDD to YYYY-MM-DD
                        TripDate = datetime.strptime(TripDate, '%Y%m%d').strftime('%Y-%m-%d')
                        cursor.execute('''
                        INSERT INTO import_BoardCube_trip (InternalUsername, TripDate, kilometers, LastModDateTime) 
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        ''', (InternalUsername, TripDate, float(kilometers)))
                    except ValueError as e:
                        print(f"Skipping row due to error: {row} - {e}")
                        
                elif entry.startswith("Cube_MdRzA_Kennwort"):
                    try:
                        InternalUsername, Password = row
                        cursor.execute('''
                        INSERT INTO import_BoardCube_MdRzA_Password (InternalUsername, Password_MdRzA, LastModDateTime) 
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                        ''', (InternalUsername, Password))
                    except ValueError as e:
                        print(f"Skipping row due to error: {row} - {e}")
                elif entry.startswith("Cube_MdRzA_Login"):
                    try:
                        InternalUsername, Username = row
                        cursor.execute('''
                        INSERT INTO import_BoardCube_MdRzA_Username (InternalUsername, UserName_MdRzA, LastModDateTime) 
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                        ''', (InternalUsername, Username))
                    except ValueError as e:
                        print(f"Skipping row due to error: {row} - {e}")
       
    # Merge import_BoardCube_trip into trips
    cursor.execute('''
    SELECT InternalUsername, TripDate, kilometers FROM import_BoardCube_trip
    ''')
    rows = cursor.fetchall()

    for row in rows:
        InternalUsername, TripDate, kilometers = row
        cursor.execute('''
        SELECT kilometers FROM trips WHERE InternalUsername = ? AND TripDate = ?
        ''', (InternalUsername, TripDate))
        existing = cursor.fetchone()
        
        if existing is None:
            # Insert new row
            cursor.execute('''
            INSERT INTO trips (TripDate, InternalUsername, kilometers, LastModDateTime) 
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (TripDate, InternalUsername, kilometers))
        elif existing[0] != kilometers:
            # Update existing row
            cursor.execute('''
            UPDATE trips SET kilometers = ?, LastModDateTime = CURRENT_TIMESTAMP, isModified = TRUE 
            WHERE InternalUsername = ? AND TripDate = ?
            ''', (kilometers, InternalUsername, TripDate))
            
    # Merge User Logins
    
    cursor.execute('''
    SELECT import_BoardCube_MdRzA_Username.InternalUsername, UserName_MdRzA AS Login, Password_MdRzA AS Password
    FROM import_BoardCube_MdRzA_Username
    INNER JOIN import_BoardCube_MdRzA_Password 
    ON import_BoardCube_MdRzA_Username.InternalUsername = import_BoardCube_MdRzA_Password.InternalUsername
    ''')
    rows = cursor.fetchall()

    for row in rows:
        InternalUsername, UserName, EncryptedPassword = row
        cursor.execute('''
        SELECT InternalUsername FROM userLogin WHERE InternalUsername = ?
        ''', (InternalUsername,))
        existing = cursor.fetchone()
        
        if existing is None:
            # Insert new row
            cursor.execute('''
            INSERT INTO userLogin (InternalUsername, UserName, EncryptedPassword, LastModDateTime) 
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (InternalUsername, UserName, EncryptedPassword,))
        else:
            # Update existing row
            cursor.execute('''
            UPDATE userLogin SET EncryptedPassword = ?, LastModDateTime = CURRENT_TIMESTAMP
            WHERE InternalUsername = ?
            ''', (EncryptedPassword, InternalUsername))

    conn.commit()
    conn.close()

def delete_record_mdrza(session, day, kilometers, teilnehmer_id, csrf_token):
    print("Deleting existing record on '{day}'...")
 
def insert_record_mdrza(session, day, kilometers, teilnehmer_id, csrf_token):
    
    print("Inserting record on '{day}' in MdRzA portal...")
    
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
        print(f"{teilnehmer_id}: Added {kilometers} kilometers on '{day}'!")
        return response.text
    else:
        print("Error while inserting to MdRzA:", response.status_code)

def login_mdrza(session, username, encrypted_password):
    
    print(f"Logging in as {username}...")
    
    # Definiere die URL
    url = f"{BASE_URL}/bundesweit/index.php"
    
    # Definiere die Daten für den POST-Request
    data = {
        "username": username,
        "passwort": BlowfishEncryption.decrypt_text(encrypted_password, ENCRYPTION_KEY),
        "btnLogin": "btnLogin"
    }
    
    # Sende den POST-Request
    response = session.post(url, data=data)
    
    # Überprüfe, ob die Anfrage erfolgreich war
    if response.status_code == 200:
        print("Login successful!")
        
        # Gib den HTML-Body zurück
        return response.text
        
    else:
        print("Error during login:", response.status_code)
        return None

def mark_trip_as_inserted(InternalUsername, TripDate):
    
    print(f"Marking trip for user {InternalUsername} on {TripDate} as inserted...")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect('tours.db')

        # Create a cursor object to interact with the database
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE trips
        SET isNew = 0, isModified = 0
        WHERE InternalUsername = ? AND TripDate = ?
        ''', (InternalUsername, TripDate))

        conn.commit() 

    except sqlite3.Error as e:
        print(f"An error occurred while updatings trips table: {e}")

    finally:
        # Close the cursor and the connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
def main():
    start_time = time.time()
    
    print(f"Started at {start_time}.")
    import_csv_from_board("E:\BOARD\Dataset\Flomi\MdRzA\data")   
    
    # Erstelle eine Sitzung
    session = requests.Session()

    all_logins = get_mdrza_logins()    
    for InternalUsername, UserName, encrypted_password in all_logins:

        all_trips = get_mdrza_trips_for_user(InternalUsername)        
        
        if len(all_trips) == 0:
        # Proceed to the next user
            continue
    
        html_body = login_mdrza(session, UserName, encrypted_password)
    
        if html_body:

            # extract csrf token and internal user id
            soup = BeautifulSoup(html_body, "html.parser")
            csrf_token = soup.find("input", {"name": "csrf"})["value"]
            teilnehmer_id = soup.find("input", {"name": "form_data[tn][value]"})["value"]

            # upsert records
            for trip in all_trips:
                TripDate, kilometers, isNew, isModified = trip
                
                if isModified:
                    delete_record_mdrza(session=session, day=TripDate, kilometers=kilometers, teilnehmer_id=teilnehmer_id, csrf_token=csrf_token)
                
                # get new csrf token
                insert_response = insert_record_mdrza(session=session, day=TripDate, kilometers=kilometers, teilnehmer_id=teilnehmer_id, csrf_token=csrf_token)           
                mark_trip_as_inserted(InternalUsername=InternalUsername, TripDate=TripDate)     
                
                soup = BeautifulSoup(insert_response, "html.parser")
                csrf_token = soup.find("input", {"name": "csrf"})["value"]
                
                print("Waiting 0.25 seconds between inserts...")
                time.sleep(0.25)
            pass
        else:
            print("No valid cookies.")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time} seconds")
    
if __name__ == "__main__":
    main()
