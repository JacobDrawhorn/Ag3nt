import os
import time
import sys
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from bs4 import BeautifulSoup
from openai import OpenAI
import openai
from dotenv import load_dotenv
import traceback
import random
from selenium.webdriver import ActionChains

class WebAgent:
    def __init__(self, headless=False, proxy=None, firefox_profile_path=None, chrome_profile_path=None):
        """Initialize the web agent with the specified browser and profile."""
        self.headless = headless
        self.proxy = proxy
        self.driver = None
        self.setup_openai()
        
        print("Setting up browser...")
        print(f"Operating System: {platform.platform()}")
        print(f"Python Version: {sys.version}")
        
        # Try Firefox first
        try:
            print("Attempting to use Firefox...")
            options = FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            
            # Add Firefox profile if specified
            if firefox_profile_path:
                print(f"Using Firefox profile from: {firefox_profile_path}")
                options.set_preference('profile', firefox_profile_path)
            
            # Add stealth settings
            options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            options.set_preference("privacy.trackingprotection.enabled", False)
            options.set_preference("network.http.referer.spoofSource", True)
            options.set_preference("javascript.enabled", True)
            options.set_preference("dom.webnotifications.enabled", False)
            options.set_preference("media.navigator.enabled", False)
            options.set_preference("media.peerconnection.enabled", False)
            
            # Add proxy if specified
            if proxy and proxy.get('host') and proxy.get('port'):
                options.set_preference("network.proxy.type", 1)
                options.set_preference("network.proxy.http", proxy['host'])
                options.set_preference("network.proxy.http_port", int(proxy['port']))
                options.set_preference("network.proxy.ssl", proxy['host'])
                options.set_preference("network.proxy.ssl_port", int(proxy['port']))
            
            service = FirefoxService()
            self.driver = webdriver.Firefox(service=service, options=options)
            print("Firefox browser setup successful!")
            self.wait = WebDriverWait(self.driver, 10)
            self.driver.maximize_window()
            
            # Execute stealth script
            self.inject_stealth_scripts()
            return
            
        except Exception as e:
            print(f"Failed to initialize Firefox: {str(e)}")
        
        # Fall back to Chrome if Firefox fails
        try:
            print("\nAttempting to use Chrome...")
            options = ChromeOptions()
            if headless:
                options.add_argument('--headless=new')
            
            # Add Chrome profile if specified
            if chrome_profile_path:
                print(f"Using Chrome profile from: {chrome_profile_path}")
                options.add_argument(f'--user-data-dir={chrome_profile_path}')
            
            # Add proxy if specified
            if proxy and proxy.get('host') and proxy.get('port'):
                options.add_argument(f'--proxy-server={proxy["host"]}:{proxy["port"]}')
            
            # Add stealth settings
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-blink-features')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--ignore-ssl-errors')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=IsolateOrigins,site-per-process')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-setuid-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-accelerated-2d-canvas')
            options.add_argument('--disable-browser-side-navigation')
            options.add_argument('--disable-site-isolation-trials')
            options.add_argument('--lang=en-US,en;q=0.9')
            options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Add experimental options
            options.add_experimental_option('useAutomationExtension', False)
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            
            service = ChromeService()
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Execute CDP commands to mask automation
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "platform": "Windows",
                "acceptLanguage": "en-US,en;q=0.9",
                "userAgentMetadata": {
                    "brands": [
                        {"brand": "Google Chrome", "version": "120"},
                        {"brand": "Chromium", "version": "120"},
                        {"brand": "Not=A?Brand", "version": "24"}
                    ],
                    "fullVersion": "120.0.6099.129",
                    "platform": "Windows",
                    "platformVersion": "10.0.0",
                    "architecture": "x86",
                    "model": "",
                    "mobile": False,
                    "bitness": "64",
                    "wow64": False
                }
            })
            
            # Execute stealth script
            self.inject_stealth_scripts()
            
            print("Chrome browser setup successful!")
            self.wait = WebDriverWait(self.driver, 10)
            return
            
        except Exception as e:
            print(f"Failed to initialize Chrome: {str(e)}")
            raise Exception("Failed to initialize any browser")
            
    def inject_stealth_scripts(self):
        """Inject stealth scripts to avoid detection."""
        try:
            # Advanced stealth script
            stealth_script = """
                // Override property descriptors
                (() => {
                    const elementDescriptor = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetHeight');
                    
                    // Overwrite the offsetHeight and offsetWidth with random variations
                    Object.defineProperties(HTMLElement.prototype, {
                        'offsetHeight': {
                            ...elementDescriptor,
                            get: function() {
                                const height = elementDescriptor.get.call(this);
                                return height + Math.random() * 0.01;
                            }
                        },
                        'offsetWidth': {
                            ...elementDescriptor,
                            get: function() {
                                const width = elementDescriptor.get.call(this);
                                return width + Math.random() * 0.01;
                            }
                        }
                    });
                    
                    // Override navigator properties
                    Object.defineProperties(navigator, {
                        'webdriver': {
                            get: () => undefined
                        },
                        'plugins': {
                            get: () => {
                                return {
                                    length: 5,
                                    item: () => ({
                                        type: 'application/x-shockwave-flash',
                                        enabledPlugin: true,
                                        description: 'Shockwave Flash',
                                        suffixes: 'swf',
                                        filename: 'flash.dll'
                                    }),
                                    namedItem: () => null,
                                    refresh: () => {}
                                };
                            }
                        },
                        'languages': {
                            get: () => ['en-US', 'en']
                        },
                        'platform': {
                            get: () => 'Win32'
                        }
                    });
                    
                    // Add Chrome runtime
                    window.chrome = {
                        app: {
                            InstallState: {
                                DISABLED: 'disabled',
                                INSTALLED: 'installed',
                                NOT_INSTALLED: 'not_installed'
                            },
                            RunningState: {
                                CANNOT_RUN: 'cannot_run',
                                READY_TO_RUN: 'ready_to_run',
                                RUNNING: 'running'
                            },
                            getDetails: function() {},
                            getIsInstalled: function() {},
                            installState: function() {},
                            isInstalled: false,
                            runningState: function() {}
                        },
                        runtime: {
                            OnInstalledReason: {
                                CHROME_UPDATE: 'chrome_update',
                                INSTALL: 'install',
                                SHARED_MODULE_UPDATE: 'shared_module_update',
                                UPDATE: 'update'
                            },
                            OnRestartRequiredReason: {
                                APP_UPDATE: 'app_update',
                                OS_UPDATE: 'os_update',
                                PERIODIC: 'periodic'
                            },
                            PlatformArch: {
                                ARM: 'arm',
                                ARM64: 'arm64',
                                MIPS: 'mips',
                                MIPS64: 'mips64',
                                X86_32: 'x86-32',
                                X86_64: 'x86-64'
                            },
                            PlatformNaclArch: {
                                ARM: 'arm',
                                MIPS: 'mips',
                                MIPS64: 'mips64',
                                X86_32: 'x86-32',
                                X86_64: 'x86-64'
                            },
                            PlatformOs: {
                                ANDROID: 'android',
                                CROS: 'cros',
                                LINUX: 'linux',
                                MAC: 'mac',
                                OPENBSD: 'openbsd',
                                WIN: 'win'
                            },
                            RequestUpdateCheckStatus: {
                                NO_UPDATE: 'no_update',
                                THROTTLED: 'throttled',
                                UPDATE_AVAILABLE: 'update_available'
                            }
                        }
                    };
                    
                    // Add permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({state: Notification.permission}) :
                            originalQuery(parameters)
                    );
                    
                    // Override performance behavior
                    const performance = window.performance;
                    const originalGetEntries = performance.getEntries;
                    performance.getEntries = function() {
                        const entries = originalGetEntries.call(performance);
                        const clean = entries.map(entry => {
                            if (entry.name.includes('chrome-extension://')) {
                                entry.name = entry.name.replace('chrome-extension://', 'https://');
                            }
                            return entry;
                        });
                        return clean;
                    };
                    
                    // Override canvas fingerprinting
                    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                    HTMLCanvasElement.prototype.toDataURL = function(type) {
                        if (type === 'image/png' && this.width === 220 && this.height === 30) {
                            return originalToDataURL.apply(this, arguments);
                        }
                        
                        const context = this.getContext('2d');
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < imageData.data.length; i += 4) {
                            imageData.data[i] = imageData.data[i] + Math.floor(Math.random() * 10);
                            imageData.data[i+1] = imageData.data[i+1] + Math.floor(Math.random() * 10);
                            imageData.data[i+2] = imageData.data[i+2] + Math.floor(Math.random() * 10);
                        }
                        context.putImageData(imageData, 0, 0);
                        return originalToDataURL.apply(this, arguments);
                    };
                    
                    // Override audio fingerprinting
                    const context = new AudioContext();
                    if (context.createOscillator) {
                        const originalCreateOscillator = context.createOscillator.bind(context);
                        context.createOscillator = function() {
                            const oscillator = originalCreateOscillator();
                            const originalStart = oscillator.start.bind(oscillator);
                            oscillator.start = function() {
                                this.frequency.value = this.frequency.value + Math.random() * 0.01;
                                return originalStart();
                            };
                            return oscillator;
                        };
                    }
                })();
            """
            
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': stealth_script
            })
            
        except Exception as e:
            print(f"Error injecting stealth scripts: {str(e)}")
            
    def setup_openai(self):
        """Configure OpenAI API."""
        load_dotenv()
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
    def navigate_to(self, url):
        """Navigate to a URL with advanced verification handling."""
        try:
            print(f"Navigating to {url}...")
            self.driver.get(url)
            time.sleep(random.uniform(2, 4))
            
            # Check for various verification challenges
            if self.is_verification_needed():
                print("\nVerification challenge detected")
                print("Please complete the verification in the browser window")
                print("The browser window will stay open for manual verification")
                print("You can press Ctrl+C when you're done")
                
                # Wait for verification to complete
                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        if self.wait_for_verification():
                            print("\nVerification completed successfully")
                            time.sleep(random.uniform(1, 2))
                            return True
                    except Exception as e:
                        print(f"\nVerification attempt {retry_count + 1} failed: {str(e)}")
                    retry_count += 1
                    time.sleep(random.uniform(5, 10))
                
                print("\nMaximum verification attempts reached")
                return False
            
            return True
            
        except Exception as e:
            print(f"Navigation error: {str(e)}")
            return False
            
    def is_verification_needed(self):
        """Check if verification is needed."""
        try:
            # Check for common verification elements
            verification_indicators = [
                "iframe[src*='recaptcha']",
                "iframe[src*='captcha']",
                "iframe[src*='challenge']",
                "#captcha",
                ".g-recaptcha",
                "[data-sitekey]",
                "iframe[title*='reCAPTCHA']",
                "iframe[title*='security check']",
                "iframe[title*='challenge']",
                "#challenge-running",
                "#challenge-form",
                "#cf-challenge-running"
            ]
            
            for indicator in verification_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, indicator)
                    if element and element.is_displayed():
                        print("\nreCAPTCHA detected")
                        return True
                except:
                    continue
            
            # Check page title and content
            if any(x in self.driver.title.lower() for x in ['security check', 'verification', 'captcha', 'challenge']):
                return True
            
            page_text = self.driver.page_source.lower()
            if any(x in page_text for x in ['please verify', 'security check', 'are you human', 'prove you are human']):
                return True
            
            return False
            
        except Exception as e:
            print(f"Error checking for verification: {str(e)}")
            return False
            
    def wait_for_verification(self, timeout=300):
        """Wait for verification to complete."""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if not self.is_verification_needed():
                    # Additional checks to ensure we're past verification
                    time.sleep(random.uniform(1, 2))
                    if not self.is_verification_needed():
                        return True
                time.sleep(2)
            return False
        except Exception as e:
            print(f"Error waiting for verification: {str(e)}")
            return False
            
    def find_element(self, selector, by=By.CSS_SELECTOR, wait=True):
        """Find an element on the page using various selection methods."""
        try:
            if wait:
                element = self.wait.until(
                    EC.presence_of_element_located((by, selector))
                )
            else:
                element = self.driver.find_element(by, selector)
            return element
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Error finding element {selector}: {str(e)}")
            return None
            
    def click_element(self, selector, by=By.CSS_SELECTOR):
        """Click an element on the page."""
        element = self.find_element(selector, by)
        if element:
            try:
                self.simulate_human_click(element)
                return True
            except Exception as e:
                print(f"Error clicking element {selector}: {str(e)}")
        return False
        
    def input_text(self, selector, text, by=By.CSS_SELECTOR):
        """Input text into a form field."""
        element = self.find_element(selector, by)
        if element:
            try:
                self.simulate_human_typing(element, text)
                return True
            except Exception as e:
                print(f"Error inputting text to {selector}: {str(e)}")
        return False
        
    def get_page_content(self):
        """Get the current page's HTML content and parse it with BeautifulSoup."""
        try:
            html = self.driver.page_source
            return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            print(f"Error getting page content: {str(e)}")
            return None
            
    def analyze_page(self, task_description):
        """Use OpenAI to analyze the page content and determine next actions."""
        try:
            content = self.get_page_content()
            if not content:
                return None
                
            # Extract visible text and important elements
            text_content = content.get_text(strip=True)
            links = [a.get('href', '') for a in content.find_all('a', href=True)]
            buttons = [button.get_text(strip=True) for button in content.find_all(['button', 'input'])]
            
            # Extract form fields and their labels
            forms = content.find_all('form')
            form_fields = []
            for form in forms:
                inputs = form.find_all(['input', 'select', 'textarea'])
                for input_field in inputs:
                    field_type = input_field.get('type', 'text')
                    field_name = input_field.get('name', '')
                    field_id = input_field.get('id', '')
                    label = form.find('label', {'for': field_id})
                    label_text = label.get_text(strip=True) if label else ''
                    form_fields.append({
                        'type': field_type,
                        'name': field_name,
                        'id': field_id,
                        'label': label_text
                    })
            
            # Prepare prompt for OpenAI with enhanced context
            prompt = f"""
            Task: {task_description}
            
            Current Page Analysis:
            {text_content[:1000]}...
            
            Available Links: {links[:10]}
            Available Buttons: {buttons[:10]}
            Form Fields: {form_fields[:10]}
            
            Given this is a survey website, consider:
            1. Is this a login page, survey list, or survey question?
            2. If it's a survey question, what type of response is expected?
            3. Are there any point values or time estimates shown?
            4. Is there a progress indicator?
            
            Based on this information, what should be the next action?
            Provide the action in a structured format:
            - Action Type: [CLICK, INPUT, NAVIGATE, WAIT]
            - Target: [selector or URL]
            - Value: [text to input if applicable]
            - Reason: [brief explanation of this action]
            """
            
            try:
                client = openai.OpenAI()
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=150
                )
                
                return response.choices[0].message.content
                
            except Exception as api_error:
                print(f"OpenAI API error: {str(api_error)}")
                traceback.print_exc()
                return None
            
        except Exception as e:
            print(f"Error analyzing page: {str(e)}")
            traceback.print_exc()
            return None
            
    def handle_verification(self):
        """Handle verification challenges like captchas."""
        try:
            if not self.is_browser_alive():
                return False
                
            # Look for common verification elements
            page_source = self.driver.page_source.lower()
            
            # Check for reCAPTCHA
            if 'recaptcha' in page_source:
                print("\nreCAPTCHA detected")
                try:
                    # Switch to reCAPTCHA iframe if present
                    iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                    for iframe in iframes:
                        if 'recaptcha' in iframe.get_attribute('src').lower():
                            print("Please solve the reCAPTCHA in the browser window")
                            return True
                except:
                    pass
            
            # Check for hCaptcha
            elif 'hcaptcha' in page_source:
                print("\nhCaptcha detected")
                try:
                    iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                    for iframe in iframes:
                        if 'hcaptcha' in iframe.get_attribute('src').lower():
                            print("Please solve the hCaptcha in the browser window")
                            return True
                except:
                    pass
            
            # Check for other verification methods
            verification_texts = [
                'verify you are human',
                'prove you are human',
                'bot check',
                'security check',
                'captcha'
            ]
            
            if any(text in page_source for text in verification_texts):
                print("\nVerification challenge detected")
                print("Please complete the verification in the browser window")
                return True
            
            return False
            
        except Exception as e:
            if self.is_browser_alive():
                print(f"Error handling verification: {str(e)}")
            return False
            
    def is_browser_alive(self):
        """Check if the browser window is still open and accessible."""
        try:
            # Try to get the current window handle
            self.driver.current_window_handle
            return True
        except:
            return False
            
    def execute_task(self, task):
        """Execute a task with natural delays and error handling."""
        try:
            # Parse task with OpenAI
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes web pages and provides guidance on completing tasks."},
                    {"role": "user", "content": f"Analyze this task and provide step-by-step instructions on how to complete it: {task}"}
                ]
            )
            
            instructions = response.choices[0].message.content
            print("\nTask Analysis:")
            print(instructions)
            
            # Execute the task with natural delays
            self.simulate_human_behavior()
            
        except Exception as e:
            print(f"Error executing task: {str(e)}")
            
    def simulate_human_behavior(self):
        """Simulate natural human browsing behavior."""
        try:
            # Random scrolling
            scroll_amount = random.randint(100, 500)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 2))
            
            # Random mouse movements
            actions = ActionChains(self.driver)
            for _ in range(random.randint(3, 7)):
                x = random.randint(0, 500)
                y = random.randint(0, 500)
                actions.move_by_offset(x, y)
                time.sleep(random.uniform(0.1, 0.3))
            actions.perform()
            
            # Random pauses
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            print(f"Error simulating human behavior: {str(e)}")
            
    def close(self):
        """Close the browser and clean up resources."""
        try:
            self.driver.quit()
        except Exception as e:
            print(f"Error closing browser: {str(e)}")
            
    def add_random_delay(self):
        """Add a random delay between actions to simulate human behavior."""
        base_delay = random.uniform(1, 3)
        
        # Occasionally add longer delays
        if random.random() < 0.1:
            base_delay += random.uniform(1, 2)
        
        # Add micro-variations
        micro_delay = random.uniform(-0.1, 0.1)
        
        time.sleep(base_delay + micro_delay)

    def simulate_human_typing(self, element, text):
        """Simulate human-like typing behavior."""
        try:
            if self.is_browser_alive():
                for char in text:
                    element.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.3))  # Random delay between keystrokes
                    
                    # Occasionally add a longer pause
                    if random.random() < 0.1:
                        time.sleep(random.uniform(0.5, 1.0))
        except:
            pass

    def simulate_human_click(self, element):
        """Simulate human-like clicking behavior."""
        try:
            if self.is_browser_alive():
                action = ActionChains(self.driver)
                
                # Move to a random position near the element
                element_size = element.size
                x_offset = random.randint(-10, 10)
                y_offset = random.randint(-10, 10)
                
                # Move mouse gradually
                action.move_to_element(element)
                action.move_by_offset(x_offset, y_offset)
                action.pause(random.uniform(0.1, 0.3))
                
                # Sometimes move back to center
                if random.random() < 0.3:
                    action.move_by_offset(-x_offset, -y_offset)
                    action.pause(random.uniform(0.1, 0.2))
                
                # Click with random delay
                action.click()
                action.pause(random.uniform(0.1, 0.3))
                action.perform()
                
                # Add random delay after click
                time.sleep(random.uniform(0.5, 1.5))
        except:
            pass

    def move_mouse_randomly(self):
        """Move the mouse to random positions to simulate human behavior."""
        try:
            if self.is_browser_alive():
                action = ActionChains(self.driver)
                viewport_width = self.driver.execute_script("return window.innerWidth;")
                viewport_height = self.driver.execute_script("return window.innerHeight;")
                
                # Move to 2-4 random positions with human-like curves
                for _ in range(random.randint(2, 4)):
                    # Generate curve points
                    points = []
                    start_x = random.randint(0, viewport_width)
                    start_y = random.randint(0, viewport_height)
                    end_x = random.randint(0, viewport_width)
                    end_y = random.randint(0, viewport_height)
                    
                    # Create Bezier curve points
                    control_x = (start_x + end_x) // 2 + random.randint(-100, 100)
                    control_y = (start_y + end_y) // 2 + random.randint(-100, 100)
                    
                    # Move along curve
                    for t in range(0, 100, 10):
                        t = t / 100
                        x = int((1-t)**2 * start_x + 2*(1-t)*t*control_x + t**2*end_x)
                        y = int((1-t)**2 * start_y + 2*(1-t)*t*control_y + t**2*end_y)
                        action.move_by_offset(x, y)
                        action.pause(random.uniform(0.01, 0.03))
                    
                    # Add random pauses
                    if random.random() < 0.3:
                        action.pause(random.uniform(0.1, 0.3))
                
                action.perform()
        except:
            pass

    def scroll_randomly(self):
        """Scroll the page randomly to simulate human behavior."""
        try:
            if self.is_browser_alive():
                viewport_height = self.driver.execute_script("return window.innerHeight;")
                page_height = self.driver.execute_script("return document.body.scrollHeight;")
                
                # Scroll to 2-4 random positions with smooth scrolling
                for _ in range(random.randint(2, 4)):
                    current_scroll = self.driver.execute_script("return window.pageYOffset;")
                    target_scroll = random.randint(0, page_height - viewport_height)
                    
                    # Scroll in smaller increments for smoothness
                    steps = random.randint(5, 10)
                    scroll_increment = (target_scroll - current_scroll) / steps
                    
                    for step in range(steps):
                        next_scroll = current_scroll + scroll_increment
                        self.driver.execute_script(f"window.scrollTo(0, {next_scroll});")
                        time.sleep(random.uniform(0.05, 0.15))
                        current_scroll = next_scroll
                    
                    # Sometimes pause at a position
                    if random.random() < 0.3:
                        time.sleep(random.uniform(0.5, 1.5))
        except:
            pass
