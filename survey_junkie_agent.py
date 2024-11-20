from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
import random
import json
import os
import math
from dotenv import load_dotenv
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
import platform
from selenium.webdriver.support.ui import Select
import re
from selenium.common.exceptions import TimeoutException

# Load environment variables from .env file
load_dotenv()

class SurveyJunkieAgent:
    def __init__(self, email, password, headless=False, chrome_profile_path=None):
        self.email = email
        self.password = password
        self.base_url = "https://app.surveyjunkie.com"
        self.chrome_profile_path = chrome_profile_path
        
        if not self.setup_browser():
            print("Failed to set up browser, exiting...")
            exit(1)
        
        # Modify navigator properties
        self.inject_stealth_js()
    
    def setup_browser(self):
        """Set up the browser with improved error handling."""
        try:
            print("Setting up browser...")
            
            # Set up Chrome options
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-notifications')
            
            # Handle Chrome profile
            profile_path = os.getenv('CHROME_PROFILE_PATH')
            if profile_path:
                if not os.path.exists(profile_path):
                    print(f"Warning: Profile path {profile_path} not found. Creating new profile.")
                    os.makedirs(profile_path, exist_ok=True)
                
                options.add_argument(f'--user-data-dir={os.path.dirname(profile_path)}')
                options.add_argument(f'--profile-directory={os.path.basename(profile_path)}')
                print(f"Using Chrome profile at: {profile_path}")
            
            # Set up driver with retry logic
            max_retries = 3
            retry_count = 0
            last_error = None
            
            while retry_count < max_retries:
                try:
                    print(f"Attempting to start browser (attempt {retry_count + 1}/{max_retries})...")
                    
                    # Kill any existing Chrome processes
                    os.system('pkill chrome')
                    os.system('pkill chromium')
                    time.sleep(2)
                    
                    # Create browser instance
                    self.driver = uc.Chrome(
                        options=options,
                        version_main=130,  # Match installed Chrome version
                        headless=False
                    )
                    
                    self.driver.set_page_load_timeout(30)
                    self.driver.implicitly_wait(10)
                    
                    # Test browser connection
                    self.driver.get('https://www.google.com')
                    print("Browser setup successful!")
                    return True
                    
                except Exception as e:
                    last_error = str(e)
                    print(f"Browser setup attempt {retry_count + 1} failed: {last_error}")
                    retry_count += 1
                    
                    try:
                        if 'driver' in locals():
                            driver.quit()
                    except:
                        pass
                    
                    time.sleep(2)
            
            raise Exception(f"Failed to set up browser after {max_retries} attempts. Last error: {last_error}")
            
        except Exception as e:
            print(f"Error setting up browser: {str(e)}")
            return False
    
    def inject_stealth_js(self):
        """Inject JavaScript to help avoid detection."""
        try:
            # Overwrite navigator properties
            js_script = """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            """
            self.driver.execute_script(js_script)
            
            # Add random mouse movements
            js_mouse = """
            (() => {
                let lastMove = Date.now();
                document.addEventListener('mousemove', () => {
                    lastMove = Date.now();
                });
                setInterval(() => {
                    if (Date.now() - lastMove > 10000) {
                        const event = new MouseEvent('mousemove', {
                            'view': window,
                            'bubbles': true,
                            'cancelable': true,
                            'clientX': Math.random() * window.innerWidth,
                            'clientY': Math.random() * window.innerHeight
                        });
                        document.dispatchEvent(event);
                    }
                }, 10000);
            })();
            """
            self.driver.execute_script(js_mouse)
            
        except Exception as e:
            print(f"Error injecting stealth JS: {str(e)}")
    
    def wait_for_element(self, by, selector, timeout=10, condition="presence"):
        """Wait for an element with better error handling."""
        try:
            if condition == "clickable":
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by, selector))
                )
            elif condition == "visible":
                element = WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located((by, selector))
                )
            else:  # presence
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, selector))
                )
            return element
        except Exception as e:
            print(f"Error waiting for element {selector}: {str(e)}")
            return None

    def wait_for_element_stable(self, element, timeout=5):
        """Wait for an element to become stable (not stale) and return a fresh reference."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Try to check if element is still valid
                _ = element.is_enabled()
                return element
            except:
                try:
                    # Try to find element again using various attributes
                    attributes = {
                        'id': element.get_attribute('id'),
                        'name': element.get_attribute('name'),
                        'class': element.get_attribute('class'),
                        'type': element.get_attribute('type'),
                        'value': element.get_attribute('value'),
                        'role': element.get_attribute('role')
                    }
                    
                    # Build CSS selector from available attributes
                    selectors = []
                    for attr, value in attributes.items():
                        if value:
                            if attr == 'class':
                                classes = value.split()
                                for class_name in classes:
                                    selectors.append(f"[class*='{class_name}']")
                            else:
                                selectors.append(f"[{attr}='{value}']")
                    
                    if selectors:
                        # Try each selector
                        for selector in selectors:
                            try:
                                new_element = WebDriverWait(self.driver, 1).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                )
                                return new_element
                            except:
                                continue
                                
                    # If no attributes found or no success with selectors,
                    # try to find by XPath position
                    try:
                        xpath = self.driver.execute_script("""
                            function getXPath(element) {
                                if (element.id !== '')
                                    return `//*[@id="${element.id}"]`;
                                if (element === document.body)
                                    return '/html/body';
                                var ix = 0;
                                var siblings = element.parentNode.childNodes;
                                for (var i = 0; i < siblings.length; i++) {
                                    var sibling = siblings[i];
                                    if (sibling === element)
                                        return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                                        ix++;
                                }
                            }
                            return getXPath(arguments[0]);
                        """, element)
                        
                        if xpath:
                            try:
                                new_element = WebDriverWait(self.driver, 1).until(
                                    EC.presence_of_element_located((By.XPATH, xpath))
                                )
                                return new_element
                            except:
                                pass
                    except:
                        pass
                        
                except:
                    pass
                    
            time.sleep(0.1)
        
        return None

    def safe_interact_with_element(self, element, action='click', value=None):
        """Safely interact with an element, handling stale references."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Get fresh reference to element
                fresh_element = self.wait_for_element_stable(element)
                if not fresh_element:
                    print(f"Could not get fresh reference to element after {attempt + 1} attempts")
                    return False
                
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", fresh_element)
                time.sleep(0.5)  # Let scroll complete
                
                # Perform requested action
                if action == 'click':
                    # Try multiple click methods
                    try:
                        fresh_element.click()
                    except:
                        try:
                            self.driver.execute_script("arguments[0].click();", fresh_element)
                        except:
                            ActionChains(self.driver).move_to_element(fresh_element).click().perform()
                elif action == 'type':
                    fresh_element.clear()
                    self.simulate_human_typing(fresh_element, value)
                elif action == 'select':
                    Select(fresh_element).select_by_visible_text(value)
                
                return True
                
            except Exception as e:
                print(f"Interaction attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_attempts - 1:
                    return False
                time.sleep(0.5)
        
        return False

    def safe_click(self, element):
        """Attempt to click an element using multiple methods."""
        try:
            # Try regular click
            element.click()
            return True
        except:
            try:
                # Try JavaScript click
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except:
                try:
                    # Try ActionChains click
                    ActionChains(self.driver).move_to_element(element).click().perform()
                    return True
                except Exception as e:
                    print(f"All click attempts failed: {str(e)}")
                    return False

    def simulate_human_typing(self, element, text):
        """Simulate human-like typing with natural delays."""
        try:
            # Clear existing text if any
            try:
                element.clear()
            except:
                pass

            # Type each character with random delay
            for char in text:
                try:
                    element.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))  # Random delay between keystrokes
                except:
                    # If send_keys fails, try JavaScript
                    try:
                        current_value = element.get_attribute('value') or ''
                        new_value = current_value + char
                        self.driver.execute_script(
                            "arguments[0].value = arguments[1];", 
                            element, 
                            new_value
                        )
                        time.sleep(random.uniform(0.05, 0.15))
                    except:
                        continue

        except Exception as e:
            print(f"Error simulating typing: {str(e)}")

    def move_mouse_naturally(self, element):
        """Move mouse in a natural curved path to element."""
        try:
            # Scroll element into view first
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Get element location after scrolling
            location = element.location_once_scrolled_into_view
            size = element.size
            
            # Calculate target coordinates relative to viewport
            target_x = location['x'] + size['width'] // 2
            target_y = location['y'] + size['height'] // 2
            
            # Get current viewport size
            viewport_width = self.driver.execute_script('return window.innerWidth;')
            viewport_height = self.driver.execute_script('return window.innerHeight;')
            
            # Ensure target coordinates are within viewport
            target_x = min(max(0, target_x), viewport_width)
            target_y = min(max(0, target_y), viewport_height)
            
            # Start from center of viewport
            current_x = viewport_width // 2
            current_y = viewport_height // 2
            
            # Calculate relative movement
            move_x = target_x - current_x
            move_y = target_y - current_y
            
            # Break movement into smaller steps
            steps = random.randint(10, 20)
            for i in range(steps + 1):
                progress = i / steps
                # Add slight curve to movement
                curve = math.sin(progress * math.pi)
                offset_x = move_x * progress + curve * random.randint(-10, 10)
                offset_y = move_y * progress + curve * random.randint(-10, 10)
                
                self.actions.move_by_offset(offset_x / steps, offset_y / steps)
                self.actions.pause(random.uniform(0.001, 0.003))
            
            self.actions.perform()
            self.actions.reset_actions()
            
            # Small pause after movement
            time.sleep(random.uniform(0.1, 0.3))
            
        except Exception as e:
            print(f"Mouse movement failed: {str(e)}")
            # Fallback to direct click
            try:
                element.click()
            except:
                self.driver.execute_script("arguments[0].click();", element)
    
    def login(self):
        """Enhanced login with better element interaction."""
        try:
            print("Logging into Survey Junkie...")
            self.driver.get(f"{self.base_url}/login")
            
            # Wait for page load with random delay
            time.sleep(random.uniform(2, 4))
            
            print("Looking for login form...")
            
            # Try multiple common selectors for email/username field
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[id*="email"]',
                'input[id*="username"]',
                'input[name*="username"]'
            ]
            
            email_field = None
            for selector in email_selectors:
                print(f"Trying email selector: {selector}")
                email_field = self.wait_for_element(By.CSS_SELECTOR, selector, timeout=3, condition="visible")
                if email_field:
                    print(f"Found email field with selector: {selector}")
                    break
            
            if not email_field:
                print("Could not find email field with any known selector")
                return False
            
            # Try multiple common selectors for password field
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id*="password"]'
            ]
            
            password_field = None
            for selector in password_selectors:
                print(f"Trying password selector: {selector}")
                password_field = self.wait_for_element(By.CSS_SELECTOR, selector, timeout=3, condition="visible")
                if password_field:
                    print(f"Found password field with selector: {selector}")
                    break
            
            if not password_field:
                print("Could not find password field with any known selector")
                return False
            
            # Try to focus and clear fields first
            print("Interacting with email field...")
            self.driver.execute_script("arguments[0].focus();", email_field)
            email_field.clear()
            time.sleep(random.uniform(0.3, 0.7))
            
            # Type email
            self.simulate_human_typing(email_field, self.email)
            time.sleep(random.uniform(0.5, 1.5))
            
            # Focus and clear password field
            print("Interacting with password field...")
            self.driver.execute_script("arguments[0].focus();", password_field)
            password_field.clear()
            time.sleep(random.uniform(0.3, 0.7))
            
            # Type password
            self.simulate_human_typing(password_field, self.password)
            time.sleep(random.uniform(0.5, 1.0))
            
            # Try multiple common selectors for login button
            print("Looking for login button...")
            button_selectors = [
                'button[type="submit"]',
                '.login-button',
                '#login-button'
            ]
            
            login_button = None
            for selector in button_selectors:
                print(f"Trying button selector: {selector}")
                login_button = self.wait_for_element(By.CSS_SELECTOR, selector, timeout=3, condition="clickable")
                if login_button:
                    print(f"Found login button with selector: {selector}")
                    break
            
            if not login_button:
                print("Could not find login button with any known selector")
                return False
            
            # Try to click the login button
            print("Attempting to click login button...")
            if not self.safe_click(login_button):
                print("Failed to click login button")
                return False
            
            # Wait for successful login
            print("Waiting for dashboard...")
            dashboard_selectors = [
                '.dashboard-content',
                '#dashboard',
                '.user-dashboard',
                '.account-dashboard'
            ]
            
            dashboard = None
            for selector in dashboard_selectors:
                dashboard = self.wait_for_element(
                    By.CSS_SELECTOR,
                    selector,
                    timeout=5,
                    condition="presence"
                )
                if dashboard:
                    print(f"Found dashboard with selector: {selector}")
                    break
            
            if not dashboard:
                print("Login might have failed - could not find dashboard")
                return False
            
            print("Successfully logged in!")
            return True
            
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False
    
    def check_logged_in(self):
        """Check if we're already logged into Survey Junkie."""
        try:
            print("Checking login status...")
            self.driver.get(f"{self.base_url}/dashboard")
            time.sleep(random.uniform(2, 4))
            
            # Try multiple dashboard selectors
            dashboard_selectors = [
                '.dashboard-content',
                '#dashboard',
                '.user-dashboard',
                '.account-dashboard',
                '.survey-list'  # Add more specific selectors that indicate logged-in state
            ]
            
            for selector in dashboard_selectors:
                try:
                    element = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if element:
                        print("Already logged in!")
                        return True
                except:
                    continue
            
            print("Not logged in.")
            return False
            
        except Exception as e:
            print(f"Error checking login status: {str(e)}")
            return False

    def find_available_surveys(self):
        """Find available surveys."""
        try:
            print("\nSearching for available surveys...")
            
            # Wait for page to load and scroll
            time.sleep(5)
            self.scroll_page()
            
            # Find survey cards using the discovered structure
            survey_cards = self.driver.execute_script("""
                function findSurveyCards() {
                    // Find all survey cards that contain points info
                    const cards = [];
                    const startButtons = document.querySelectorAll('button.sc-1saobic-0.ilZXlC');
                    
                    for (const button of startButtons) {
                        // Look up to find the survey card container
                        let parent = button;
                        for (let i = 0; i < 6; i++) {
                            if (!parent) break;
                            // Look for the specific survey card class
                            if (parent.classList.contains('sc-55mkux-1')) {
                                cards.push({
                                    container: parent,
                                    button: button,
                                    text: parent.textContent,
                                    // Try to get points and time directly from their containers
                                    pointsElem: parent.querySelector('.sc-55mkux-6'),
                                    timeElem: parent.querySelector('.sc-55mkux-9')
                                });
                                break;
                            }
                            parent = parent.parentElement;
                        }
                    }
                    return cards;
                }
                return findSurveyCards();
            """)
            
            if not survey_cards:
                print("No survey cards found")
                return []
            
            print(f"\nFound {len(survey_cards)} potential survey cards")
            
            # Process each survey card
            surveys = []
            for card in survey_cards:
                try:
                    # Get the card text
                    card_text = card['text'].lower()
                    print(f"\nProcessing card with text: {card_text}")
                    
                    # Extract points and time
                    points = 0
                    time_estimate = 0
                    
                    # First try to find points - look for "X pts" at the start of a segment
                    points_matches = re.finditer(r'(\d+)\s*pts?(?:\s|$|/)', card_text)
                    for match in points_matches:
                        potential_points = int(match.group(1))
                        # Take the first reasonable points value (usually the actual points, not pts/min)
                        if potential_points <= 1000:  # Sanity check
                            points = potential_points
                            break
                    
                    if points == 0:
                        print("No valid points found in text:", card_text)
                        continue
                    print(f"Found points: {points}")
                    
                    # Try to find time - look for "X min" at the end of a segment
                    time_matches = re.finditer(r'(\d+)\s*min(?:utes?)?(?:\s|$)', card_text)
                    for match in time_matches:
                        potential_time = int(match.group(1))
                        # Take the last time value (usually the total time, not pts/min)
                        time_estimate = potential_time
                    
                    if time_estimate == 0:
                        print("No time estimate found, using default")
                        time_estimate = 10
                    else:
                        print(f"Found time: {time_estimate}")
                    
                    # Calculate points per minute
                    points_per_min = points / time_estimate if time_estimate > 0 else 0
                    
                    survey_data = {
                        'element': card['button'],  # Store the actual button to click
                        'points': points,
                        'time': time_estimate,
                        'points_per_min': points_per_min,
                        'text': card_text
                    }
                    surveys.append(survey_data)
                    print(f"Added survey: {points} points, {time_estimate} minutes ({points_per_min:.1f} pts/min)")
                    
                except Exception as e:
                    print(f"Error processing survey card: {str(e)}")
                    continue
            
            # Sort surveys by points per minute
            surveys.sort(key=lambda x: x['points_per_min'], reverse=True)
            
            if surveys:
                best_survey = surveys[0]
                print(f"\nFound {len(surveys)} valid surveys.")
                print(f"Best survey: {best_survey['points']} points, {best_survey['time']} minutes ({best_survey['points_per_min']:.1f} pts/min)")
                print(f"Survey text: {best_survey['text']}")
            else:
                print("No valid surveys found")
            
            return surveys
            
        except Exception as e:
            print(f"Error finding surveys: {str(e)}")
            return []
    
    def start_survey(self, survey):
        """Start a selected survey with improved clicking."""
        try:
            print("\nAttempting to start survey...")
            
            element = survey['element']
            print(f"Starting survey worth {survey['points']} points")
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(random.uniform(1, 2))
            
            # Try multiple click methods
            try:
                # Try regular click
                element.click()
            except:
                try:
                    # Try JavaScript click
                    self.driver.execute_script("arguments[0].click();", element)
                except:
                    try:
                        # Try Actions click
                        ActionChains(self.driver).move_to_element(element).click().perform()
                    except Exception as e:
                        print(f"Failed to click survey: {str(e)}")
                        return False
            
            # Wait for new window/tab
            time.sleep(random.uniform(2, 3))
            
            # Switch to new window if opened
            handles = self.driver.window_handles
            if len(handles) > 1:
                self.driver.switch_to.window(handles[-1])
                print("Switched to survey window")
                return True
            
            print("Survey started in same window")
            return True
            
        except Exception as e:
            print(f"Error starting survey: {str(e)}")
            return False

    def answer_question(self, question_text):
        """Answer a survey question based on its content."""
        try:
            # Check for math questions
            math_match = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)\s*=\s*\?', question_text)
            if math_match:
                num1 = int(math_match.group(1))
                operator = math_match.group(2)
                num2 = int(math_match.group(3))
                
                # Calculate result
                if operator == '+':
                    answer = str(num1 + num2)
                elif operator == '-':
                    answer = str(num1 - num2)
                elif operator == '*':
                    answer = str(num1 * num2)
                elif operator == '/':
                    answer = str(round(num1 / num2))
                
                print(f"Found math question: {num1}{operator}{num2}={answer}")
                return answer
            
            # Check for open-ended questions about activities/hobbies
            if "activity" in question_text.lower() or "hobby" in question_text.lower():
                activities = [
                    "I enjoy reading books in my spare time. It helps me relax and learn new things.",
                    "Going for walks in nature is my favorite activity. It makes me feel peaceful and energized.",
                    "I love cooking new recipes. It's creative and satisfying to make delicious meals.",
                    "Playing video games helps me unwind and have fun while solving challenges.",
                    "Gardening is my passion. It's rewarding to grow plants and connect with nature."
                ]
                return random.choice(activities)
            
            # Generic positive response for other questions
            return "I enjoy it very much and find it interesting."
            
        except Exception as e:
            print(f"Error answering question: {str(e)}")
            return "Yes"

    def navigate_survey(self):
        """Navigate through survey with improved validation and progress tracking."""
        try:
            print("Navigating through survey...")
            start_time = time.time()
            last_page_source = ""
            stuck_count = 0
            progress = 0
            
            # Navigation selectors
            navigation_selectors = {
                'next': [
                    'button[type="submit"]',
                    '.next-button',
                    '.continue-button',
                    '[aria-label*="Next"]',
                    '[aria-label*="Continue"]',
                    'button:contains("Next")',
                    'button:contains("Continue")'
                ],
                'progress': [
                    '.progress-bar',
                    '.progress-indicator',
                    '.survey-progress',
                    '[role="progressbar"]'
                ]
            }
            
            # Completion indicators
            completion_indicators = [
                'thank you for your time',
                'survey completed',
                'thank you for participating',
                'successfully completed',
                'survey finished',
                'points earned',
                'points awarded'
            ]
            
            # Disqualification indicators
            disqualification_indicators = [
                'disqualified',
                'not qualified',
                'does not qualify',
                'survey closed',
                'quota full',
                'sorry',
                'unfortunately'
            ]

            while True:
                current_time = time.time()
                if current_time - start_time > 1800:  # 30 minute timeout
                    print("Survey timeout reached")
                    return False
                
                # Get current page state
                current_page = self.driver.page_source
                
                # Check if we're stuck on the same page
                if current_page == last_page_source:
                    stuck_count += 1
                    if stuck_count > 3:
                        print("Seems stuck, trying to find any clickable elements...")
                        # Try clicking next button first
                        if self.find_and_click_next_button():
                            print("Successfully clicked next button")
                            stuck_count = 0
                        # If that fails, try any visible button
                        elif not self.click_any_visible_button():
                            print("Unable to proceed after multiple attempts")
                            return False
                else:
                    stuck_count = 0
                    last_page_source = current_page

                # Check for completion or disqualification
                try:
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                except:
                    self.driver.switch_to.default_content()
                    continue
                
                # Check for completion
                if any(text in page_text for text in completion_indicators):
                    print("Survey completed successfully!")
                    return True
                
                # Check for disqualification
                if any(text in page_text for text in disqualification_indicators):
                    print("Disqualified from survey")
                    return False

                # Try to find question text
                question_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "h1, h2, h3, h4, p, label, .question-text, [class*='question'], [class*='prompt']")
                
                question_text = ""
                for elem in question_elements:
                    try:
                        text = elem.text.strip()
                        if text and len(text) > 10:  # Only consider substantial text
                            question_text = text
                            break
                    except:
                        continue

                # Handle different question types
                handled = False
                
                # Try different question types in order of most common to least common
                if self.handle_radio_checkbox_inputs(question_text):
                    print("Handled radio/checkbox inputs")
                    handled = True
                elif self.handle_matrix_question():
                    print("Handled matrix question")
                    handled = True
                elif self.handle_text_inputs(question_text):
                    print("Handled text input")
                    handled = True
                elif self.handle_slider_question():
                    print("Handled slider question")
                    handled = True
                elif self.handle_dropdown_question():
                    print("Handled dropdown question")
                    handled = True
                elif self.handle_rating_question():
                    print("Handled rating question")
                    handled = True
                elif self.handle_ranking_question():
                    print("Handled ranking question")
                    handled = True
                elif self.handle_image_selection():
                    print("Handled image selection")
                    handled = True
                elif self.handle_grid_question():
                    print("Handled grid question")
                    handled = True

                # If we handled a question, try to click next
                if handled:
                    if not self.find_and_click_next_button():
                        print("Could not find next button after handling question")
                        if not self.click_any_visible_button():
                            print("Could not find any clickable buttons")
                            # Don't return False here, give it another chance
                else:
                    print("No recognizable question type found")
                    if not self.click_any_visible_button():
                        print("Could not find any clickable buttons")
                        # Don't return False here, give it another chance

                # Natural delay between questions
                time.sleep(random.uniform(1.5, 3))
                
        except Exception as e:
            print(f"Error navigating survey: {str(e)}")
            return False
            
    def switch_to_survey_frame(self):
        """Enhanced method to switch to the correct survey frame."""
        try:
            # First switch back to default content
            self.driver.switch_to.default_content()
            time.sleep(1)

            # Print all iframes for debugging
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            print(f"Found {len(iframes)} iframes")
            for idx, iframe in enumerate(iframes):
                try:
                    src = iframe.get_attribute('src') or ''
                    id_attr = iframe.get_attribute('id') or ''
                    name_attr = iframe.get_attribute('name') or ''
                    print(f"Frame {idx}: src={src}, id={id_attr}, name={name_attr}")
                except:
                    print(f"Frame {idx}: Unable to get attributes")

            # Try each frame until we find survey content
            for frame in iframes:
                try:
                    print(f"Attempting to switch to frame...")
                    self.driver.switch_to.frame(frame)
                    
                    # Wait for and verify content
                    try:
                        WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        
                        # Get page source and check for survey-related content
                        page_source = self.driver.page_source.lower()
                        survey_indicators = [
                            'question',
                            'survey',
                            'answer',
                            'option',
                            'next',
                            'continue',
                            'submit',
                            'radio',
                            'checkbox',
                            'input'
                        ]
                        
                        if any(indicator in page_source for indicator in survey_indicators):
                            print("Found survey content in frame")
                            return True
                            
                    except:
                        pass
                    
                    # If no survey content found, switch back to default
                    self.driver.switch_to.default_content()
                    
                except Exception as e:
                    print(f"Error switching to frame: {str(e)}")
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass
                    continue

            # If no frame found with direct approach, try waiting for specific frame
            try:
                frame = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='survey'], iframe[id*='survey'], iframe[name*='survey'], iframe[title*='survey']"))
                )
                self.driver.switch_to.frame(frame)
                return True
            except:
                print("No survey frame found with wait")
                pass

            return False

        except Exception as e:
            print(f"Error in switch_to_survey_frame: {str(e)}")
            return False

    def verify_frame_content(self):
        """Verify we're in the correct frame with survey content."""
        try:
            # Try to find common survey elements
            selectors = [
                'input[type="radio"]',
                'input[type="checkbox"]',
                'input[type="text"]',
                'textarea',
                'select',
                '.question',
                '.answer',
                '.option',
                '[role="radio"]',
                '[role="checkbox"]'
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"Found {len(elements)} elements with selector: {selector}")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Error verifying frame content: {str(e)}")
            return False

    def wait_for_survey_elements(self):
        """Wait for survey elements to be present and interactive."""
        try:
            # Wait for common survey elements with multiple strategies
            selectors = [
                # Questions and content
                ".question",
                "[class*='question']",
                "[class*='survey']",
                "form",
                # Input elements
                "input",
                "select",
                "textarea",
                # Custom elements
                "[role='radio']",
                "[role='checkbox']",
                "[role='textbox']",
                # Buttons
                "button",
                "input[type='submit']",
                "[class*='next']",
                "[class*='continue']"
            ]
            
            for selector in selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"Found element with selector: {selector}")
                    return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Error waiting for survey elements: {str(e)}")
            return False

    def find_and_click_next_button(self):
        """Enhanced method to find and click the next button with comprehensive detection."""
        try:
            # Common button text variations
            button_texts = [
                'next', 'continue', 'submit', 'forward', 'weiter', 'siguiente',
                'suivant', '下一个', '次へ', 'далее', '다음', 'proceed', 'ok', 'done',
                'start', 'begin', 'advance', 'go', 'send', 'save', 'complete'
            ]

            # Special handling for submit buttons
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                '[role="button"][type="submit"]',
                'button.submit',
                '.submit-button',
                'button:contains("Submit")',
                'input.submit',
                '[class*="submit"]'
            ]
            
            # Print page source for debugging
            print("\nLooking for next/submit button...")
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                print(f"Page text contains: {body_text[:200]}...")  # Print first 200 chars
                
                # Check if this looks like a submit page
                submit_indicators = ['submit', 'finish', 'complete', 'done', 'end']
                is_submit_page = any(indicator in body_text for indicator in submit_indicators)
                if is_submit_page:
                    print("This appears to be a submit/completion page")
            except:
                print("Could not get body text")

            # First try: Submit-specific selectors if this looks like a submit page
            if is_submit_page:
                print("Trying submit-specific selectors...")
                for selector in submit_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            try:
                                if element.is_displayed() and element.is_enabled():
                                    print(f"Found submit button with selector: {selector}")
                                    # Try multiple click methods for submit buttons
                                    try:
                                        element.submit()  # Try form submit first
                                        time.sleep(1)
                                        return True
                                    except:
                                        try:
                                            element.click()  # Try direct click
                                            time.sleep(1)
                                            return True
                                        except:
                                            try:
                                                self.driver.execute_script("arguments[0].click();", element)
                                                time.sleep(1)
                                                return True
                                            except:
                                                continue
                            except:
                                continue
                    except Exception as e:
                        print(f"Error with submit selector {selector}: {str(e)}")
                        continue

            # Rest of the button finding logic...
            # Common button selectors
            button_selectors = [
                # Standard buttons
                'button[type="submit"]',
                'input[type="submit"]',
                'button:not([disabled])',
                'input[type="button"]:not([disabled])',
                
                # Class-based selectors
                '[class*="next"]:not([disabled])',
                '[class*="continue"]:not([disabled])',
                '[class*="submit"]:not([disabled])',
                '[class*="forward"]:not([disabled])',
                '[class*="button"]:not([disabled])',
                '[class*="btn"]:not([disabled])',
                
                # Role-based selectors
                '[role="button"]',
                
                # Aria-based selectors
                '[aria-label*="next"]',
                '[aria-label*="continue"]',
                '[aria-label*="submit"]',
                
                # Data attribute selectors
                '[data-role="button"]',
                '[data-type="button"]',
                '[data-action="next"]',
                '[data-action="continue"]'
            ]
            
            print("Trying standard button selectors...")
            for selector in button_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                text = element.text.lower().strip()
                                if any(btn_text in text for btn_text in button_texts):
                                    print(f"Found button with selector {selector} and text: {text}")
                                    if self.safe_interact_with_element(element, 'click'):
                                        return True
                        except:
                            continue
                except Exception as e:
                    print(f"Error with selector {selector}: {str(e)}")
                    continue

            # Second try: Text-based XPath search
            print("Trying text-based button search...")
            for text in button_texts:
                try:
                    # Complex XPath to find elements containing text
                    xpath = f"""
                        //*[
                            (self::button or self::input or self::a or 
                             contains(@class, 'button') or contains(@class, 'btn') or
                             @role='button' or contains(@type, 'button') or contains(@type, 'submit'))
                            and 
                            (
                                contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')
                                or 
                                contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')
                                or
                                contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')
                            )
                        ]
                    """
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                print(f"Found button with text: {text}")
                                if self.safe_interact_with_element(element, 'click'):
                                    return True
                        except:
                            continue
                except Exception as e:
                    print(f"Error with text search {text}: {str(e)}")
                    continue

            # Third try: Find any clickable element that might be a button
            print("Trying to find any clickable elements...")
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, '*')
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            tag_name = element.tag_name.lower()
                            if tag_name in ['button', 'input', 'a'] or 'button' in element.get_attribute('class').lower():
                                text = element.text.lower().strip()
                                if any(btn_text in text for btn_text in button_texts):
                                    print(f"Found clickable element with text: {text}")
                                    if self.safe_interact_with_element(element, 'click'):
                                        return True
                    except:
                        continue
            except Exception as e:
                print(f"Error in general element search: {str(e)}")

            # Fourth try: JavaScript click on elements that look like buttons
            print("Trying JavaScript click on button-like elements...")
            js_script = """
                function findButtonLikeElement() {
                    const buttonTexts = ['next', 'continue', 'submit', 'forward', 'proceed'];
                    const elements = document.querySelectorAll('*');
                    for (const element of elements) {
                        const text = (element.textContent || element.value || '').toLowerCase();
                        const isVisible = element.offsetWidth > 0 && element.offsetHeight > 0;
                        const isClickable = element.tagName === 'BUTTON' || 
                                         element.tagName === 'INPUT' || 
                                         element.tagName === 'A' ||
                                         element.className.includes('button') ||
                                         element.className.includes('btn');
                        
                        if (isVisible && isClickable && buttonTexts.some(btn => text.includes(btn))) {
                            return element;
                        }
                    }
                    return null;
                }
                const buttonElement = findButtonLikeElement();
                if (buttonElement) {
                    buttonElement.click();
                    return true;
                }
                return false;
            """
            try:
                if self.driver.execute_script(js_script):
                    print("Successfully clicked button using JavaScript")
                    time.sleep(1)  # Wait for any navigation
                    return True
            except Exception as e:
                print(f"Error in JavaScript click: {str(e)}")

            # If still not found, try to find and submit the form directly
            print("Trying to find and submit form directly...")
            try:
                forms = self.driver.find_elements(By.TAG_NAME, "form")
                for form in forms:
                    try:
                        if form.is_displayed():
                            print("Found visible form, attempting to submit...")
                            try:
                                form.submit()
                                time.sleep(1)
                                return True
                            except:
                                try:
                                    submit_btn = form.find_element(By.CSS_SELECTOR, 
                                        'button[type="submit"], input[type="submit"]')
                                    submit_btn.click()
                                    time.sleep(1)
                                    return True
                                except:
                                    continue
                    except:
                        continue
            except Exception as e:
                print(f"Error submitting form: {str(e)}")

            # If everything else failed, try to trigger form submission via JavaScript
            print("Trying JavaScript form submission...")
            js_submit = """
                var forms = document.getElementsByTagName('form');
                for(var i = 0; i < forms.length; i++) {
                    try {
                        forms[i].submit();
                        return true;
                    } catch(e) {
                        continue;
                    }
                }
                return false;
            """
            try:
                if self.driver.execute_script(js_submit):
                    print("Successfully submitted form via JavaScript")
                    time.sleep(1)
                    return True
            except Exception as e:
                print(f"Error in JavaScript form submission: {str(e)}")

            print("No next/submit button found")
            return False

        except Exception as e:
            print(f"Error finding next/submit button: {str(e)}")
            return False

    def handle_popup_windows(self):
        """Handle any popup windows or alerts that might appear."""
        try:
            # Switch to alert if present
            try:
                alert = self.driver.switch_to.alert
                alert.accept()
                return True
            except:
                pass

            # Get current window handle
            main_window = self.driver.current_window_handle
            
            # Check for new windows
            all_windows = self.driver.window_handles
            if len(all_windows) > 1:
                for window in all_windows:
                    if window != main_window:
                        try:
                            # Switch to new window
                            self.driver.switch_to.window(window)
                            # Close it
                            self.driver.close()
                        except:
                            continue
                # Switch back to main window
                self.driver.switch_to.window(main_window)
                return True

            return False

        except Exception as e:
            print(f"Error handling popups: {str(e)}")
            return False

    def complete_survey(self):
        """Complete a survey with enhanced frame and element handling."""
        try:
            print("Starting survey completion...")
            
            # Switch to survey frame with enhanced debugging
            if not self.switch_to_survey_frame():
                print("Failed to switch to survey frame")
                return False
                
            # Verify we're in the correct frame
            if not self.verify_frame_content():
                print("Failed to verify survey content")
                self.driver.switch_to.default_content()
                return False
                
            # Wait for survey elements to be present
            if not self.wait_for_survey_elements():
                print("Failed to find survey elements")
                self.driver.switch_to.default_content()
                return False

            # Main survey completion loop
            max_attempts = 30  # Prevent infinite loops
            attempt = 0
            
            while attempt < max_attempts:
                print(f"\nSurvey completion attempt {attempt + 1}")
                
                # Handle any popups that might interfere
                self.handle_popup_windows()
                
                # Re-verify frame and content on each iteration
                if not self.verify_frame_content():
                    print("Lost survey frame context, attempting to recover...")
                    if not self.switch_to_survey_frame():
                        print("Could not recover survey frame")
                        return False
                
                # Get all interactive elements
                elements = self.get_all_interactive_elements()
                if not elements:
                    print("No interactive elements found")
                    # Check if we're at the end
                    if self.check_survey_completion():
                        print("Survey appears to be complete")
                        return True
                    break
                
                # Handle each type of element
                handled_any = False
                for element in elements:
                    try:
                        if self.is_radio_or_checkbox(element):
                            if self.handle_radio_checkbox_inputs([element]):
                                handled_any = True
                        elif self.is_text_input(element):
                            if self.handle_text_inputs([element]):
                                handled_any = True
                        elif self.is_select(element):
                            if self.handle_select_inputs([element]):
                                handled_any = True
                    except Exception as e:
                        print(f"Error handling element: {str(e)}")
                        continue
                
                if not handled_any:
                    print("No elements were successfully handled")
                    # Try to find and click next button even if no elements were handled
                    # as some questions might be optional
                
                # Try to proceed to next question
                if not self.find_and_click_next_button():
                    print("Could not find next button")
                    # Check if we're at the end
                    if self.check_survey_completion():
                        print("Survey appears to be complete")
                        return True
                    break
                
                # Small delay between questions
                time.sleep(random.uniform(1.5, 3.0))
                attempt += 1
            
            print("Survey completion loop ended")
            return False
            
        except Exception as e:
            print(f"Error in complete_survey: {str(e)}")
            return False
        finally:
            try:
                self.driver.switch_to.default_content()
            except:
                pass

    def handle_matrix_question(self):
        """Handle matrix-style questions with multiple rows and columns."""
        try:
            # Find matrix rows (usually table rows or div containers)
            rows = self.driver.find_elements(By.CSS_SELECTOR, 
                "tr, div[role='row'], .matrix-row, div[class*='row']")
            
            if not rows:
                return False
                
            for row in rows:
                try:
                    # Find radio buttons or checkboxes in this row
                    options = row.find_elements(By.CSS_SELECTOR, 
                        "input[type='radio'], input[type='checkbox'], [role='radio'], [role='checkbox']")
                    
                    if options:
                        # Choose a somewhat positive option (70% chance of positive)
                        choice = random.randint(1, 10)
                        index = len(options) - 1 if choice <= 7 else random.randint(0, len(options) - 1)
                        
                        try:
                            options[index].click()
                        except:
                            self.driver.execute_script("arguments[0].click();", options[index])
                            
                        time.sleep(random.uniform(0.5, 1.5))
                        
                except Exception as e:
                    print(f"Error handling matrix row: {str(e)}")
                    continue
                    
            return True
            
        except Exception as e:
            print(f"Error handling matrix question: {str(e)}")
            return False

    def handle_slider_question(self):
        """Handle slider-based questions."""
        try:
            sliders = self.driver.find_elements(By.CSS_SELECTOR, 
                "input[type='range'], [role='slider'], .slider-input")
                
            if not sliders:
                return False
                
            for slider in sliders:
                try:
                    # Get slider range
                    min_val = float(slider.get_attribute('min') or '0')
                    max_val = float(slider.get_attribute('max') or '100')
                    
                    # Choose a somewhat positive value (60-90% of range)
                    value = min_val + (max_val - min_val) * random.uniform(0.6, 0.9)
                    
                    # Set slider value
                    self.driver.execute_script(
                        f"arguments[0].value = '{value}'; " +
                        "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", 
                        slider)
                        
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    print(f"Error handling slider: {str(e)}")
                    continue
                    
            return True
            
        except Exception as e:
            print(f"Error handling slider question: {str(e)}")
            return False

    def handle_dropdown_question(self):
        """Handle dropdown/select questions."""
        try:
            dropdowns = self.driver.find_elements(By.CSS_SELECTOR, 
                "select, [role='combobox'], .select-input")
                
            if not dropdowns:
                return False
                
            for dropdown in dropdowns:
                try:
                    # Try standard select element first
                    try:
                        select = Select(dropdown)
                        options = select.options
                        if len(options) > 1:
                            # Skip first option if it looks like a placeholder
                            start_index = 1 if options[0].text.lower() in ['select', 'choose', 'please select'] else 0
                            select.select_by_index(random.randint(start_index, len(options) - 1))
                    except:
                        # If not a standard select, try clicking to open and select option
                        dropdown.click()
                        time.sleep(0.5)
                        
                        options = self.driver.find_elements(By.CSS_SELECTOR, 
                            "option, [role='option'], .select-option")
                        if options:
                            option = random.choice(options)
                            option.click()
                            
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    print(f"Error handling dropdown: {str(e)}")
                    continue
                    
            return True
            
        except Exception as e:
            print(f"Error handling dropdown question: {str(e)}")
            return False

    def handle_rating_question(self):
        """Handle star rating or numeric rating questions."""
        try:
            # Look for rating elements
            rating_elements = self.driver.find_elements(By.CSS_SELECTOR,
                "[role='radio'][aria-label*='rating'], .rating-input, .star-rating input")
                
            if not rating_elements:
                return False
                
            # Group related ratings together
            current_group = []
            for elem in rating_elements:
                try:
                    # Check if this is a new group
                    if current_group and not self.are_related_elements(current_group[0], elem):
                        # Handle previous group
                        self.select_rating(current_group)
                        current_group = []
                    
                    current_group.append(elem)
                    
                except Exception as e:
                    print(f"Error processing rating element: {str(e)}")
                    continue
                    
            # Handle last group
            if current_group:
                self.select_rating(current_group)
                
            return True
            
        except Exception as e:
            print(f"Error handling rating question: {str(e)}")
            return False

    def are_related_elements(self, elem1, elem2):
        """Check if two elements are part of the same question group."""
        try:
            # Get common parent within reasonable depth
            parent1 = elem1
            parent2 = elem2
            for _ in range(3):  # Check up to 3 levels up
                if parent1 == parent2:
                    return True
                parent1 = parent1.find_element(By.XPATH, "..")
                parent2 = parent2.find_element(By.XPATH, "..")
            return False
        except:
            return False

    def select_rating(self, rating_group):
        """Select a rating from a group of rating options."""
        try:
            # Choose a somewhat positive rating (70% chance)
            if random.random() < 0.7:
                # Select from top 30% of options
                start_idx = int(len(rating_group) * 0.7)
                choice = rating_group[random.randint(start_idx, len(rating_group) - 1)]
            else:
                choice = random.choice(rating_group)
                
            try:
                choice.click()
            except:
                self.driver.execute_script("arguments[0].click();", choice)
                
            time.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            print(f"Error selecting rating: {str(e)}")

    def handle_grid_question(self):
        """Handle grid-style questions with multiple rows and columns."""
        try:
            # Expanded list of grid selectors
            grid_selectors = [
                '.grid-question',
                'table',
                '[role="grid"]',
                '.matrix-question',
                '.matrix-table',
                '.survey-grid',
                '[class*="grid"]',
                '[class*="matrix"]',
                '.question-grid',
                '.response-grid',
                'table[class*="question"]',
                '.survey-table',
                '[class*="table"]'
            ]
            
            grid_element = None
            for selector in grid_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        grid_element = elements[0]
                        break
                except:
                    continue
            
            if not grid_element:
                print("No grid element found with CSS selectors, trying XPath...")
                # Try XPath as fallback
                xpath_patterns = [
                    "//table",
                    "//div[contains(@class, 'grid') or contains(@class, 'matrix')]",
                    "//div[contains(@class, 'question')]//table",
                    "//div[contains(@class, 'survey')]//table"
                ]
                for xpath in xpath_patterns:
                    try:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        if elements:
                            grid_element = elements[0]
                            break
                    except:
                        continue

            if not grid_element:
                return False
                
            # Find all rows
            row_selectors = [
                'tr',
                '[role="row"]',
                '.grid-row',
                '.matrix-row',
                '[class*="row"]'
            ]
            
            rows = []
            for selector in row_selectors:
                try:
                    elements = grid_element.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        rows = elements
                        break
                except:
                    continue
            
            if not rows:
                return False
                
            # Process each row
            for row in rows:
                try:
                    # Find inputs in this row
                    inputs = row.find_elements(By.CSS_SELECTOR, 
                        'input[type="radio"], input[type="checkbox"], [role="radio"], [role="checkbox"]')
                    
                    if inputs:
                        # Choose a somewhat positive option (70% chance of positive)
                        choice = random.randint(1, 10)
                        index = len(inputs) - 1 if choice <= 7 else random.randint(0, len(inputs) - 1)
                        
                        try:
                            self.safe_interact_with_element(inputs[index], 'click')
                        except:
                            continue
                            
                        time.sleep(random.uniform(0.5, 1.5))
                        
                except Exception as e:
                    print(f"Error handling grid row: {str(e)}")
                    continue
                    
            return True
            
        except Exception as e:
            print(f"Error handling grid question: {str(e)}")
            return False

    def handle_ranking_question(self):
        """Handle ranking/ordering questions."""
        try:
            # Common ranking selectors
            ranking_selectors = [
                '[class*="rank"]',
                '[class*="order"]',
                '[class*="sort"]',
                '.ranking-question',
                '.ordering-question',
                '[role="listbox"]',
                '.drag-drop',
                '.sortable'
            ]
            
            ranking_elements = []
            for selector in ranking_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        ranking_elements = elements
                        break
                except:
                    continue

            if not ranking_elements:
                return False

            # Try different ranking mechanisms
            for element in ranking_elements:
                try:
                    # Check if it's a drag-drop ranking
                    draggable = element.find_elements(By.CSS_SELECTOR, '[draggable="true"], [class*="draggable"]')
                    if draggable:
                        # Perform random drag-drop operations
                        action_chains = ActionChains(self.driver)
                        positions = list(range(len(draggable)))
                        random.shuffle(positions)
                        
                        for i, item in enumerate(draggable):
                            target = draggable[positions[i]]
                            action_chains.drag_and_drop(item, target).perform()
                            time.sleep(random.uniform(0.5, 1.0))
                        continue

                    # Check if it's a number input ranking
                    number_inputs = element.find_elements(By.CSS_SELECTOR, 'input[type="number"]')
                    if number_inputs:
                        numbers = list(range(1, len(number_inputs) + 1))
                        random.shuffle(numbers)
                        for i, input_field in enumerate(number_inputs):
                            self.safe_interact_with_element(input_field, 'type', str(numbers[i]))
                            time.sleep(random.uniform(0.3, 0.8))
                        continue

                    # Check if it's a dropdown ranking
                    dropdowns = element.find_elements(By.CSS_SELECTOR, 'select')
                    if dropdowns:
                        numbers = list(range(1, len(dropdowns) + 1))
                        random.shuffle(numbers)
                        for i, dropdown in enumerate(dropdowns):
                            Select(dropdown).select_by_value(str(numbers[i]))
                            time.sleep(random.uniform(0.3, 0.8))
                        continue

                except Exception as e:
                    print(f"Error handling ranking element: {str(e)}")
                    continue

            return True

        except Exception as e:
            print(f"Error handling ranking question: {str(e)}")
            return False

    def handle_image_selection(self):
        """Handle image selection questions."""
        try:
            # Common image selection selectors
            image_selectors = [
                'img[onclick], img[role="button"]',
                '[class*="image-select"]',
                '[class*="image-choice"]',
                '[class*="picture-select"]',
                '.image-option',
                '.picture-option',
                '[role="img"][aria-label]',
                'label:has(img)',
                'div[class*="image"]:has(input)'
            ]
            
            image_elements = []
            for selector in image_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        image_elements.extend(elements)
                except:
                    continue

            if not image_elements:
                return False

            # Select one or more images based on input type
            try:
                # Check if multiple selection is required
                multiple_select = any('checkbox' in elem.get_attribute('class').lower() 
                                   for elem in image_elements if elem.get_attribute('class'))
                
                if multiple_select:
                    # Select 1-3 images
                    num_to_select = min(random.randint(1, 3), len(image_elements))
                    selected_images = random.sample(image_elements, num_to_select)
                    
                    for image in selected_images:
                        self.safe_interact_with_element(image, 'click')
                        time.sleep(random.uniform(0.5, 1.0))
                else:
                    # Select one image
                    selected_image = random.choice(image_elements)
                    self.safe_interact_with_element(selected_image, 'click')
                    time.sleep(random.uniform(0.5, 1.5))

                return True

            except Exception as e:
                print(f"Error selecting images: {str(e)}")
                return False

        except Exception as e:
            print(f"Error handling image selection: {str(e)}")
            return False

    def complete_survey_page(self):
        """Complete a single survey page with improved handling."""
        try:
            # Wait for page to load
            time.sleep(random.uniform(1.5, 3))
            
            # Track if we found and interacted with any elements
            interacted = False
            
            # Try to complete all visible questions on the page
            for attempt in range(3):  # Try up to 3 times to find elements
                if self.complete_survey():
                    interacted = True
                    break
                time.sleep(random.uniform(1, 2))
            
            return interacted
            
        except Exception as e:
            print(f"Error completing survey page: {str(e)}")
            return False

    def verify_setup(self):
        """Quick verification of browser setup."""
        try:
            print("\nVerifying browser setup...")
            self.driver.get('https://www.google.com')
            
            if 'Google' in self.driver.title:
                print("✓ Browser working correctly")
                return True
            else:
                print("❌ Browser verification failed")
                return False
                
        except Exception as e:
            print(f"❌ Verification error: {str(e)}")
            return False

    def scroll_page(self):
        """Perform natural scrolling behavior."""
        try:
            # Get page height
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll down gradually
            for i in range(0, scroll_height, 200):
                self.driver.execute_script(f"window.scrollTo(0, {i})")
                time.sleep(random.uniform(0.1, 0.3))
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0)")
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"Error scrolling page: {str(e)}")
    
    def run(self):
        """Main execution loop."""
        try:
            print("Starting Survey Junkie automation...")
            
            if not self.setup_browser():
                print("Failed to set up browser, exiting...")
                return
            
            print("\nStarting survey automation...")
            
            # Go to main page
            self.driver.get(self.base_url)
            time.sleep(random.uniform(3, 5))
            
            while True:
                try:
                    # Find and select surveys
                    surveys = self.find_available_surveys()
                    if not surveys:
                        print("No surveys found, waiting...")
                        time.sleep(30)
                        self.driver.refresh()
                        continue
                    
                    # Try each survey
                    for survey in surveys[:3]:  # Try top 3 surveys
                        print(f"\nAttempting survey worth {survey['points']} points...")
                        
                        if self.start_survey(survey):
                            if self.navigate_survey():
                                print("Survey completed!")
                            else:
                                print("Failed to complete survey")
                            
                            # Clean up windows
                            if len(self.driver.window_handles) > 1:
                                self.driver.close()
                                self.driver.switch_to.window(self.driver.window_handles[0])
                        
                        time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    print(f"Error in main loop: {str(e)}")
                    time.sleep(5)
                    continue
                
        except Exception as e:
            print(f"Fatal error: {str(e)}")
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

    def click_any_visible_button(self):
        """Try to click any visible and clickable button on the page."""
        try:
            # List of common button selectors
            button_selectors = [
                'button[type="submit"]',
                'button:not([disabled])',
                'input[type="submit"]',
                'input[type="button"]',
                '.btn',
                '.button',
                '[role="button"]',
                'a.btn',
                'button.next-button',
                'button.submit-button',
                '.next-btn',
                '.submit-btn',
                'button:contains("Next")',
                'button:contains("Submit")',
                'button:contains("Continue")'
            ]
            
            # Try each selector
            for selector in button_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            print(f"Found clickable button with selector: {selector}")
                            self.safe_interact_with_element(button, 'click')
                            time.sleep(random.uniform(0.5, 1.5))
                            return True
                except:
                    continue

            # If no buttons found with CSS selectors, try finding by text
            button_texts = ['Next', 'Submit', 'Continue', 'OK', 'Done']
            for text in button_texts:
                try:
                    xpath = f"//button[contains(text(), '{text}')] | //input[@value='{text}'] | //*[contains(@class, 'button') and contains(text(), '{text}')]"
                    buttons = self.driver.find_elements(By.XPATH, xpath)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            print(f"Found clickable button with text: {text}")
                            self.safe_interact_with_element(button, 'click')
                            time.sleep(random.uniform(0.5, 1.5))
                            return True
                except:
                    continue

            print("No clickable buttons found")
            return False

        except Exception as e:
            print(f"Error clicking any visible button: {str(e)}")
            return False

    def handle_radio_checkbox_inputs(self, elements):
        """Handle radio buttons and checkboxes in surveys.
        
        Args:
            elements: List of elements or question text to process
            
        Returns:
            bool: True if successfully handled inputs, False otherwise
        """
        try:
            # Initialize variables
            radio_inputs = []
            checkbox_inputs = []
            
            # If elements is a string (question text), find related inputs
            if isinstance(elements, (str, list)) and len(elements) > 0 and isinstance(elements[0], str):
                # Try to find radio/checkbox inputs near the question text
                for text in elements if isinstance(elements, list) else [elements]:
                    # Look for inputs using various strategies
                    xpath_patterns = [
                        f"//div[contains(text(), '{text}')]//following::input[@type='radio']",
                        f"//div[contains(text(), '{text}')]//following::input[@type='checkbox']",
                        f"//label[contains(text(), '{text}')]//preceding::input[@type='radio']",
                        f"//label[contains(text(), '{text}')]//preceding::input[@type='checkbox']",
                        "//input[@type='radio']",
                        "//input[@type='checkbox']"
                    ]
                    
                    for xpath in xpath_patterns:
                        try:
                            found_elements = self.driver.find_elements(By.XPATH, xpath)
                            for elem in found_elements:
                                if elem.get_attribute('type') == 'radio':
                                    radio_inputs.append(elem)
                                elif elem.get_attribute('type') == 'checkbox':
                                    checkbox_inputs.append(elem)
                        except:
                            continue
            else:
                # Elements are WebElements, process directly
                for elem in elements:
                    try:
                        elem_type = elem.get_attribute('type')
                        if elem_type == 'radio':
                            radio_inputs.append(elem)
                        elif elem_type == 'checkbox':
                            checkbox_inputs.append(elem)
                    except:
                        continue
            
            # Handle radio buttons (select one)
            if radio_inputs:
                # Try to find the most appropriate radio button
                selected = False
                for radio in radio_inputs:
                    try:
                        # Skip if already selected or disabled
                        if radio.is_selected() or not radio.is_enabled():
                            continue
                            
                        # Get the label text if possible
                        label_text = ''
                        try:
                            label = radio.find_element(By.XPATH, "following::label[1]")
                            label_text = label.text.lower()
                        except:
                            pass
                            
                        # Prefer positive/neutral options
                        positive_keywords = ['yes', 'agree', 'good', 'satisfied', 'positive']
                        neutral_keywords = ['neutral', 'neither', 'sometimes', 'occasionally']
                        negative_keywords = ['no', 'disagree', 'bad', 'dissatisfied', 'negative']
                        
                        if any(keyword in label_text for keyword in positive_keywords):
                            self.click_element(radio)
                            selected = True
                            break
                        elif any(keyword in label_text for keyword in neutral_keywords):
                            self.click_element(radio)
                            selected = True
                            break
                            
                # If no preferred option found, select random non-negative
                if not selected:
                    available_radios = [r for r in radio_inputs 
                                      if not r.is_selected() 
                                      and r.is_enabled()
                                      and not any(keyword in r.find_element(By.XPATH, "following::label[1]").text.lower() 
                                                for keyword in negative_keywords)]
                    if available_radios:
                        radio = random.choice(available_radios)
                        self.click_element(radio)
                        selected = True
                
                # If still no selection, pick any enabled radio
                if not selected:
                    available_radios = [r for r in radio_inputs if not r.is_selected() and r.is_enabled()]
                    if available_radios:
                        radio = random.choice(available_radios)
                        self.click_element(radio)
                        selected = True
            
            # Handle checkboxes (can select multiple)
            if checkbox_inputs:
                # Select a random number of checkboxes (1 to 3)
                num_to_select = min(random.randint(1, 3), len(checkbox_inputs))
                selected_count = 0
                
                # Shuffle checkboxes for random selection
                random.shuffle(checkbox_inputs)
                
                for checkbox in checkbox_inputs:
                    try:
                        if selected_count >= num_to_select:
                            break
                            
                        if not checkbox.is_selected() and checkbox.is_enabled():
                            self.click_element(checkbox)
                            selected_count += 1
                    except:
                        continue
            
            return bool(radio_inputs) or bool(checkbox_inputs)
            
        except Exception as e:
            print(f"Error handling radio/checkbox inputs: {str(e)}")
            return False

if __name__ == "__main__":
    # Create and run agent
    agent = SurveyJunkieAgent(
        email=os.getenv("SURVEY_JUNKIE_EMAIL"),
        password=os.getenv("SURVEY_JUNKIE_PASSWORD"),
        chrome_profile_path=os.getenv("CHROME_PROFILE_PATH")
    )
    
    agent.run()
