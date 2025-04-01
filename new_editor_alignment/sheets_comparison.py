from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
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


def save_sheet_content_new_editor(driver, sheet_id, output_folder="sheets_content_old_new_editor"):
    url = f"http://localhost:8000/sheets/{sheet_id}"
    driver.get(url)

    try:
        # Wait for the sheet content to load
        content_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".text"))
        )

        # Create output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Save only the content element's HTML
        filename = f"{sheet_id}.html"
        filepath = os.path.join(output_folder, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content_element.get_attribute('outerHTML'))

        print(f"Saved sheet {sheet_id} as {filepath}")

    except TimeoutException:
        print(f"Timeout while waiting for sheet {sheet_id} to load")
    except Exception as e:
        print(f"Error processing sheet {sheet_id}: {str(e)}")

def save_sheet_content_viewer(driver, sheet_id, output_folder="sheets_content_viewer"):
    url = f"http://localhost:8000/sheets/{sheet_id}"
    driver.get(url)

    try:
        # Wait for the sheet content to load
        content_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".text"))
        )

        # Create output folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Save only the content element's HTML
        filename = f"{sheet_id}.html"
        filepath = os.path.join(output_folder, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content_element.get_attribute('outerHTML'))

        print(f"Saved sheet {sheet_id} as {filepath}")

    except TimeoutException:
        print(f"Timeout while waiting for sheet {sheet_id} to load")
    except Exception as e:
        print(f"Error processing sheet {sheet_id}: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <email> <password>")
        sys.exit(1)
    email = sys.argv[1]
    password = sys.argv[2]
    sheets_owner = 171118
    update_all_sheets(sheets_owner)
    sheet_ids = [sheet["id"] for sheet in db.sheets.find({"owner": sheets_owner}, {"id": 1})]
    # Initialize the WebDriver
    driver = webdriver.Firefox(executable_path="./geckodriver")  # Or use webdriver.Firefox() for Firefox

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

    for sheet_id in sheet_ids:
        break
        try:
            save_sheet_content_new_editor(driver, sheet_id)
            # Small delay between requests to avoid overloading the server
            time.sleep(1)
        except Exception as e:
            print(f"Failed to process sheet {sheet_id}: {str(e)}")
            continue
    driver.quit()
    driver = webdriver.Firefox(executable_path="./geckodriver")
    driver.get("http://localhost:8000/login")
    for sheet_id in sheet_ids:
        for sheet_id in sheet_ids:
            try:
                save_sheet_content_viewer(driver, sheet_id)
                # Small delay between requests to avoid overloading the server
                time.sleep(1)
            except Exception as e:
                print(f"Failed to process sheet {sheet_id}: {str(e)}")
                continue

    driver.quit()