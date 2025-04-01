from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import sys
import time
import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db

def update_sheet_owner(sheet_id, new_owner):
    # Find the sheet by ID
    sheet = db.sheets.find_one({"id": sheet_id})

    if sheet:
        # Update the owner of the sheet
        db.sheets.update_one({"id": sheet_id}, {"$set": {"owner": new_owner}})
        print(f"Updated owner of sheet {sheet_id} to {new_owner}.")
    else:
        print(f"Sheet with ID {sheet_id} not found.")


def update_all_sheets(new_owner):
    # Find all sheets where the owner is not the desired one
    sheets = db.sheets.find({"owner": {"$ne": new_owner}}, {"id": 1})

    # Update the owner in bulk
    sheet_ids = [sheet["id"] for sheet in sheets if "id" in sheet]

    if sheet_ids:
        db.sheets.update_many({"id": {"$in": sheet_ids}}, {"$set": {"owner": new_owner}})
        print(f"Updated {len(sheet_ids)} sheets to owner {new_owner}.")
    else:
        print("No sheets needed updating.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <email> <password>")
        sys.exit(1)
    email = sys.argv[1]
    password = sys.argv[2]

    update_all_sheets(171118)
    # Initialize the WebDriver
    driver = webdriver.Firefox(executable_path="./geckodriver")  # Or use webdriver.Firefox() for Firefox

    try:
        # Navigate to the Sefaria login page
        driver.get("http://localhost:8000/login")

        # Allow the page to load
        time.sleep(2)

        # Locate the email and password input fields and the login button
        email_input = driver.find_element(By.ID, "id_email")
        password_input = driver.find_element(By.ID, "id_password")
        login_button = driver.find_element(By.ID, "login-submit-button")

        # Enter your credentials
        email_input.send_keys(email)
        password_input.send_keys(password)

        # Submit the login form
        login_button.click()

        # Wait to observe the result
        time.sleep(5)

    finally:
        # Close the browser window
        driver.quit()