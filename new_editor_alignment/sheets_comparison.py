import os
import sys
import time
from tqdm import tqdm
import django

django.setup()
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from sefaria.system.database import db
from selenium.webdriver.firefox.options import Options



def save_sheet_content(driver, sheet_id, css_selector, output_folder, max_retries=3):
    """Saves the HTML content of a sheet, ensuring all elements are fully loaded."""
    url = f"http://localhost:8000/sheets/{sheet_id}"
    os.makedirs(output_folder, exist_ok=True)

    filename = f"{sheet_id}.html"
    error_filename = f"{sheet_id}_error.html"
    filepath = os.path.join(output_folder, filename)
    error_filepath = os.path.join(output_folder, error_filename)

    # Skip if either success or error file exists
    if os.path.exists(filepath) or os.path.exists(error_filepath):
        print(f"Skipping sheet {sheet_id}, file already exists.")
        return

    for attempt in range(max_retries):
        try:
            driver.get(url)

            # Wait until the page is fully loaded
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # Wait for the target element to be visible (not just present)
            content_element = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector))
            )

            # Optional: Wait for additional elements if needed
            time.sleep(2)  # Small delay to ensure dynamic content is loaded

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content_element.get_attribute("outerHTML"))

            print(f"Saved sheet {sheet_id} as {filepath}")
            return  # Successfully saved, exit function

        except (TimeoutException, WebDriverException) as e:
            print(f"Attempt {attempt + 1} failed for sheet {sheet_id}: {e}. Retrying...")

    # If all retries fail, save an error file
    with open(error_filepath, "w", encoding="utf-8") as f:
        f.write(f"<html><body><h1>Failed to load sheet {sheet_id}</h1></body></html>")
    print(f"Failed to load sheet {sheet_id} after {max_retries} attempts. Error log saved.")


def sign_in_to_account(driver, email, password):
    """Signs in to the Sefaria account using Selenium."""
    driver.get("http://localhost:8000/login")
    time.sleep(2)

    try:
        email_input = driver.find_element(By.ID, "id_email")
        password_input = driver.find_element(By.ID, "id_password")
        login_button = driver.find_element(By.ID, "login-submit-button")

        email_input.send_keys(email)
        password_input.send_keys(password)
        login_button.click()

        time.sleep(5)  # Wait to ensure login succeeds
        print("Successfully logged in.")
    except Exception as e:
        print(f"Login failed: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <email> <password>")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]
    sheets_owner = 171118

    options = Options()
    options.headless = True  # Enable headless mode

    # Retrieve all sheets owned by `sheets_owner`
    sheet_ids = [sheet["id"] for sheet in db.sheets.find({"owner": sheets_owner}, {"id": 1})]

    # Simulate sheets viewer
    driver = webdriver.Firefox(executable_path="./geckodriver", options=options)
    driver.get("http://localhost:8000")

    for sheet_id in tqdm(sheet_ids, desc="Simulating sheets viewer"):
        save_sheet_content(driver, sheet_id, ".text", "sheets_content_viewer")

    driver.quit()

    # Simulate sheets new editor
    driver = webdriver.Firefox(executable_path="./geckodriver", options=options)
    sign_in_to_account(driver, email, password)

    for sheet_id in tqdm(sheet_ids, desc="Simulating sheets new editor"):
        save_sheet_content(driver, sheet_id, ".text.editorContent", "sheets_content_new_editor")

    driver.quit()
