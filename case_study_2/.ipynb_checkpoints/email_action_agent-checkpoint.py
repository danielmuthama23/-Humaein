import argparse
import logging
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
is_notebook = 'ipykernel' in sys.modules

class EmailAgent:
    def __init__(self, provider):
        self.provider = provider.lower()
        self.config = self.get_provider_config()
        self.driver = self.setup_browser()

    def get_provider_config(self):
        if self.provider == 'gmail':
            return {
                'url': 'https://accounts.google.com/signin',
                'compose_btn': (By.CSS_SELECTOR, 'div[gh="cm"]'),
                'to_field': (By.NAME, 'to'),
                'subject_field': (By.NAME, 'subjectbox'),
                'body_field': (By.CSS_SELECTOR, 'div[aria-label="Message Body"]'),
                'send_btn': (By.CSS_SELECTOR, 'div[aria-label="Send"]'),
            }
        elif self.provider == 'outlook':
            return {
                'url': 'https://login.live.com/',
                'compose_btn': (By.CSS_SELECTOR, 'button[aria-label="New mail"]'),
                'to_field': (By.CSS_SELECTOR, 'input[aria-label="To recipients"]'),
                'subject_field': (By.CSS_SELECTOR, 'input[aria-label="Add a subject"]'),
                'body_field': (By.CSS_SELECTOR, 'div[aria-label="Message body"]'),
                'send_btn': (By.CSS_SELECTOR, 'button[aria-label="Send"]'),
            }
        else:
            raise ValueError("Unsupported provider")

    def setup_browser(self):
        options = Options()
        # options.add_argument("--headless")  # Uncomment for headless
        options.add_argument("--disable-gpu")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def mock_llm_parse_instruction(self, instruction):
        parts = instruction.lower().split('about')
        to_part = parts[0].replace('send an email to', '').strip()
        body_part = parts[1].strip() if len(parts) > 1 else 'No body provided'
        subject = 'Automated Email'
        return {'to': to_part, 'subject': subject, 'body': body_part}

    def authenticate(self):
        wait = WebDriverWait(self.driver, 10)
        self.driver.get(self.config['url'])
        logging.info(f"Logging in to {self.provider}...")

        try:
            if self.provider == 'gmail':
                user = os.getenv('GMAIL_USER')
                pwd = os.getenv('GMAIL_PASS')
                if not user or not pwd:
                    raise ValueError("Set GMAIL_USER and GMAIL_PASS env vars.")

                email_field = wait.until(EC.presence_of_element_located((By.ID, 'identifierId')))
                email_field.send_keys(user)
                next_btn = self.driver.find_element(By.ID, 'identifierNext')
                next_btn.click()

                pass_field = wait.until(EC.presence_of_element_located((By.NAME, 'Passwd')))
                pass_field.send_keys(pwd)
                next_btn = self.driver.find_element(By.ID, 'passwordNext')
                next_btn.click()

                wait.until(EC.url_contains('mail.google.com'))

            elif self.provider == 'outlook':
                user = os.getenv('OUTLOOK_USER')
                pwd = os.getenv('OUTLOOK_PASS')
                if not user or not pwd:
                    raise ValueError("Set OUTLOOK_USER and OUTLOOK_PASS env vars.")

                email_field = wait.until(EC.presence_of_element_located((By.ID, 'i0116')))
                email_field.send_keys(user)
                next_btn = self.driver.find_element(By.ID, 'idSIButton9')
                next_btn.click()

                pass_field = wait.until(EC.presence_of_element_located((By.ID, 'i0118')))
                pass_field.send_keys(pwd)
                signin_btn = self.driver.find_element(By.ID, 'idSIButton9')
                signin_btn.click()

                try:
                    no_btn = wait.until(EC.element_to_be_clickable((By.ID, 'idBtn_Back')))
                    no_btn.click()
                except:
                    pass

                wait.until(EC.url_contains('outlook.live.com/mail'))

            logging.info("Login successful!")
        except Exception as e:
            logging.error(f"Login failed: {e}")
            self.driver.save_screenshot('login_error.png')
            raise

    def send_email(self, instruction):
        params = self.mock_llm_parse_instruction(instruction)
        try:
            self.authenticate()
            wait = WebDriverWait(self.driver, 10)

            logging.info("Clicking compose...")
            compose = wait.until(EC.element_to_be_clickable(self.config['compose_btn']))
            compose.click()

            logging.info("Filling to field...")
            to_field = wait.until(EC.presence_of_element_located(self.config['to_field']))
            to_field.send_keys(params['to'])

            logging.info("Filling subject...")
            subject_field = self.driver.find_element(*self.config['subject_field'])
            subject_field.send_keys(params['subject'])

            logging.info("Filling body...")
            body_field = self.driver.find_element(*self.config['body_field'])
            body_field.send_keys(params['body'])

            logging.info("Sending email...")
            send_btn = self.driver.find_element(*self.config['send_btn'])
            send_btn.click()

            logging.info("Email sent successfully!")
        except Exception as e:
            logging.error(f"Error: {e}. Attempting recovery...")
            self.driver.save_screenshot('error.png')
        finally:
            self.driver.quit()

if not is_notebook:
    parser = argparse.ArgumentParser()
    parser.add_argument("instruction", type=str)
    parser.add_argument("--provider", type=str, default="gmail", choices=["gmail", "outlook"])
    args = parser.parse_args()
    agent = EmailAgent(args.provider)
    agent.send_email(args.instruction)
else:
    instruction = "Send an email to danielmuthama23@gmail.com about the meeting at 2pm"
    provider = "gmail"
    agent = EmailAgent(provider)
    agent.send_email(instruction)

app = FastAPI()
@app.post("/send_email")
async def send_email(instruction: str, provider: str = "gmail"):
    agent = EmailAgent(provider)
    agent.send_email(instruction)
    return {"status": "sent"}