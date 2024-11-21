from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os
import time
import random
from utils import BrowserUtils, QuestionHandlers, AIUtils

class SurveyBot:
    def __init__(self, email, password, headless=False, chrome_profile_path=None):
        self.email = email
        self.password = password
        self.base_url = "https://app.surveyjunkie.com"
        self.chrome_profile_path = chrome_profile_path
        
        # Initialize utils
        self.driver = self._setup_browser(headless)
        self.browser = BrowserUtils(self.driver)
        self.ai = AIUtils()
        self.handlers = QuestionHandlers(self.driver, self.browser, self.ai)

    def _setup_browser(self, headless):
        """Set up the browser with improved error handling."""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument('--headless')
            
            if self.chrome_profile_path:
                chrome_options.add_argument(f'user-data-dir={self.chrome_profile_path}')
            
            # Add stealth settings
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'
            })
            
            # Set window size
            driver.set_window_size(1920, 1080)
            
            return driver
            
        except Exception as e:
            print(f"Error setting up browser: {str(e)}")
            return None

    def login(self):
        """Enhanced login with better element interaction."""
        try:
            self.driver.get(self.base_url + "/login")
            time.sleep(random.uniform(2, 4))
            
            # Enter email
            email_input = self.browser.wait_for_element(By.CSS_SELECTOR, 'input[type="email"]')
            if email_input:
                self.browser.simulate_human_typing(email_input, self.email)
            
            # Enter password
            password_input = self.browser.wait_for_element(By.CSS_SELECTOR, 'input[type="password"]')
            if password_input:
                self.browser.simulate_human_typing(password_input, self.password)
            
            # Click login button
            login_button = self.browser.wait_for_element(By.CSS_SELECTOR, 'button[type="submit"]')
            if login_button:
                self.browser.safe_click(login_button)
            
            # Wait for login to complete
            time.sleep(random.uniform(3, 5))
            
            return self.check_logged_in()
            
        except Exception as e:
            print(f"Error during login: {str(e)}")
            return False

    def check_logged_in(self):
        """Check if we're already logged into Survey Junkie."""
        try:
            dashboard_elements = self.driver.find_elements(By.CSS_SELECTOR, '.dashboard, .user-profile, .account-info')
            return len(dashboard_elements) > 0
        except:
            return False

    def find_available_surveys(self):
        """Find available surveys with improved detection."""
        try:
            self.driver.get(self.base_url + "/dashboard")
            time.sleep(random.uniform(2, 4))
            
            # Scroll page to load all surveys
            self.browser.scroll_page()
            
            # Find survey elements
            survey_selectors = [
                '.survey-card',
                '.survey-item',
                '[class*="survey"]',
                '[class*="offer"]'
            ]
            
            surveys = []
            for selector in survey_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    surveys.extend(elements)
                    break
            
            return surveys
            
        except Exception as e:
            print(f"Error finding surveys: {str(e)}")
            return []

    def start_survey(self, survey):
        """Start a selected survey with improved clicking."""
        try:
            # Move mouse naturally to survey element
            self.browser.move_mouse_naturally(survey)
            time.sleep(random.uniform(0.5, 1))
            
            # Click survey
            if not self.browser.safe_click(survey):
                return False
            
            # Wait for survey to load
            time.sleep(random.uniform(3, 5))
            
            # Switch to survey frame if needed
            self.switch_to_survey_frame()
            
            return True
            
        except Exception as e:
            print(f"Error starting survey: {str(e)}")
            return False

    def switch_to_survey_frame(self):
        """Enhanced method to switch to the correct survey frame."""
        try:
            # First try to find iframe
            frame_selectors = [
                'iframe[src*="survey"]',
                'iframe[title*="survey"]',
                'iframe[class*="survey"]',
                'iframe'
            ]
            
            for selector in frame_selectors:
                try:
                    frames = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if frames:
                        self.driver.switch_to.frame(frames[0])
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Error switching to frame: {str(e)}")
            return False

    def complete_survey(self):
        """Complete a survey with enhanced handling."""
        try:
            # Initialize success tracking
            questions_handled = False
            
            # Find and handle all question types
            question_containers = self.driver.find_elements(
                By.CSS_SELECTOR,
                '.question, [class*="question"], form, .survey-page'
            )
            
            for container in question_containers:
                # Matrix/Grid questions
                if self.handlers.handle_matrix_question(container):
                    questions_handled = True
                    continue
                
                # Slider questions
                if self.handlers.handle_slider_question(container):
                    questions_handled = True
                    continue
                
                # Dropdown questions
                if self.handlers.handle_dropdown_question(container):
                    questions_handled = True
                    continue
                
                # Ranking questions
                if self.handlers.handle_ranking_question(container):
                    questions_handled = True
                    continue
                
                # Grid questions
                if self.handlers.handle_grid_question():
                    questions_handled = True
                    continue
            
            return questions_handled
            
        except Exception as e:
            print(f"Error completing survey: {str(e)}")
            return False

    def run(self):
        """Main execution loop with improved error handling."""
        try:
            if not self.check_logged_in():
                if not self.login():
                    print("Failed to log in")
                    return
            
            while True:
                surveys = self.find_available_surveys()
                if not surveys:
                    print("No surveys available")
                    time.sleep(300)  # Wait 5 minutes
                    continue
                
                for survey in surveys:
                    if self.start_survey(survey):
                        if self.complete_survey():
                            print("Survey completed successfully")
                        else:
                            print("Failed to complete survey")
                        
                        # Return to dashboard
                        self.driver.get(self.base_url + "/dashboard")
                        time.sleep(random.uniform(2, 4))
                
                # Wait between survey attempts
                time.sleep(random.uniform(60, 120))
                
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
        finally:
            self.driver.quit()

if __name__ == "__main__":
    bot = SurveyBot(
        email=os.getenv("SURVEY_JUNKIE_EMAIL"),
        password=os.getenv("SURVEY_JUNKIE_PASSWORD"),
        headless=False
    )
    bot.run()
