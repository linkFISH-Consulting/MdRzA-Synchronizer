import BlowfishEncryption
from dotenv import load_dotenv
import os
import csv
import argparse

load_dotenv()
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

def encrypt_password_for_user(file_path):
    updated_rows = []
    with open(file_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        header = next(reader)  # Skip the header row
        updated_rows.append(header)
        
        # Modify only the first row after the header
        try:
            first_row = next(reader)
            if len(first_row) >= 2:
                new_value = BlowfishEncryption.encrypt_text(text=first_row[1], key=ENCRYPTION_KEY)
                first_row[1] = new_value
            updated_rows.append(first_row)
        except StopIteration:
            pass
        
        # Append the remaining rows without changes
        for row in reader:
            updated_rows.append(row)

    # Write updated rows back to the file
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter='\t')
        writer.writerows(updated_rows)
        
if __name__ == "__main__":

    encrypt_password_for_user(file_path="E:\BOARD\Dataset\Flomi\MdRzA\data\Cube_MdRzA_Kennwort.txt")
