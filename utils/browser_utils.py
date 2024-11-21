from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import time
import random

class BrowserUtils:
    def __init__(self, driver):
        self.driver = driver

    def wait_for_element(self, by, selector, timeout=10, condition="presence"):
        """Wait for an element with better error handling."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            if condition == "presence":
                return wait.until(EC.presence_of_element_located((by, selector)))
            elif condition == "clickable":
                return wait.until(EC.element_to_be_clickable((by, selector)))
            elif condition == "visible":
                return wait.until(EC.visibility_of_element_located((by, selector)))
        except Exception as e:
            print(f"Error waiting for element: {str(e)}")
            return None

    def wait_for_element_stable(self, element, timeout=5):
        """Wait for an element to become stable (not stale) and return a fresh reference."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if element.is_displayed():
                    return element
            except:
                pass
            time.sleep(0.1)
        return None

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
                    # Try Actions click
                    ActionChains(self.driver).move_to_element(element).click().perform()
                    return True
                except:
                    return False

    def simulate_human_typing(self, element, text):
        """Simulate human-like typing with natural delays."""
        try:
            # Clear existing text
            element.clear()
            
            # Type each character with random delay
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            return True
        except Exception as e:
            print(f"Error simulating typing: {str(e)}")
            return False

    def move_mouse_naturally(self, element):
        """Move mouse in a natural curved path to element."""
        try:
            action = ActionChains(self.driver)
            
            # Get current mouse position
            current_mouse_pos = self.driver.execute_script(
                "return [window.mouseX, window.mouseY];"
            )
            
            if not current_mouse_pos or None in current_mouse_pos:
                current_mouse_pos = [0, 0]
            
            # Get element position
            element_pos = element.location
            
            # Create control points for Bezier curve
            points = self._generate_curve_points(
                current_mouse_pos[0], current_mouse_pos[1],
                element_pos['x'], element_pos['y']
            )
            
            # Move through points
            for point in points:
                action.move_by_offset(point[0], point[1])
                time.sleep(random.uniform(0.01, 0.03))
            
            action.perform()
            return True
            
        except Exception as e:
            print(f"Error moving mouse: {str(e)}")
            return False

    def _generate_curve_points(self, start_x, start_y, end_x, end_y):
        """Generate points for a natural mouse movement curve."""
        points = []
        steps = random.randint(25, 35)
        
        # Add some randomness to control points
        control1_x = start_x + (end_x - start_x) * random.uniform(0.3, 0.7)
        control1_y = start_y + (end_y - start_y) * random.uniform(0.3, 0.7)
        control2_x = start_x + (end_x - start_x) * random.uniform(0.3, 0.7)
        control2_y = start_y + (end_y - start_y) * random.uniform(0.3, 0.7)
        
        for i in range(steps):
            t = i / steps
            x = (1-t)**3 * start_x + 3*(1-t)**2 * t * control1_x + 3*(1-t) * t**2 * control2_x + t**3 * end_x
            y = (1-t)**3 * start_y + 3*(1-t)**2 * t * control1_y + 3*(1-t) * t**2 * control2_y + t**3 * end_y
            points.append([x, y])
            
        return points

    def scroll_page(self):
        """Perform natural scrolling behavior."""
        try:
            # Get page height
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            current_scroll = 0
            while current_scroll < scroll_height:
                # Random scroll amount
                scroll_amount = random.randint(100, 300)
                current_scroll += scroll_amount
                
                # Smooth scroll
                self.driver.execute_script(f"window.scrollTo({{top: {current_scroll}, behavior: 'smooth'}})")
                
                # Random pause
                time.sleep(random.uniform(0.5, 1.5))
                
            # Scroll back to top
            self.driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'})")
            return True
            
        except Exception as e:
            print(f"Error scrolling page: {str(e)}")
            return False
