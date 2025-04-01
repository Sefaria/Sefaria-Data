from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import sys
import time

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <email> <password>")
        sys.exit(1)
    email = sys.argv[1]
    password = sys.argv[2]
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