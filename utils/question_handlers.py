from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
import re

class QuestionHandlers:
    def __init__(self, driver, browser_utils, ai_utils):
        self.driver = driver
        self.browser = browser_utils
        self.ai = ai_utils

    def handle_matrix_question(self, element):
        """Handle matrix-style questions with multiple rows and columns."""
        try:
            # Get question text
            question_text = self.ai.get_question_text(element)
            if not question_text:
                return False

            # Find all rows
            rows = element.find_elements(By.CSS_SELECTOR, 'tr, [role="row"]')
            if not rows:
                return False

            handled = False
            for row in rows:
                try:
                    # Get row label
                    label = row.find_element(By.CSS_SELECTOR, 'td:first-child, [role="rowheader"]').text.strip()
                    
                    # Find options in this row
                    options = row.find_elements(By.CSS_SELECTOR, 
                        'input[type="radio"], input[type="checkbox"], [role="radio"], [role="checkbox"]')
                    
                    if not options:
                        continue

                    # Get AI response for this row
                    response = self.ai.get_response(question_text + "\nFor: " + label)
                    if not response:
                        continue

                    # Parse response and select option
                    response = response.lower().strip('.,!? \n\t')
                    if response.isdigit():
                        idx = int(response) - 1
                        if 0 <= idx < len(options):
                            option = options[idx]
                            if not option.is_selected():
                                self.browser.safe_click(option)
                                time.sleep(random.uniform(0.3, 0.7))
                                handled = True

                except Exception as e:
                    print(f"Error handling matrix row: {str(e)}")
                    continue

            return handled

        except Exception as e:
            print(f"Error in handle_matrix_question: {str(e)}")
            return False

    def handle_slider_question(self, element):
        """Handle slider/range input questions."""
        try:
            question_text = self.ai.get_question_text(element)
            if not question_text:
                return False

            slider = element.find_element(By.CSS_SELECTOR, 'input[type="range"], .slider, [role="slider"]')
            if not slider:
                return False

            min_val = float(slider.get_attribute('min') or 0)
            max_val = float(slider.get_attribute('max') or 100)
            step = float(slider.get_attribute('step') or 1)

            response = self.ai.get_response(f"Slider question from {min_val} to {max_val}: {question_text}")
            if not response:
                return False

            try:
                value = float(re.search(r'\d+(?:\.\d+)?', response).group())
                value = min(max_val, max(min_val, value))
                steps = round((value - min_val) / step)
                value = min_val + (steps * step)

                self.driver.execute_script(
                    f"""
                    arguments[0].value = '{value}';
                    arguments[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    arguments[0].dispatchEvent(new Event('change', {{ bubbles: true }}));
                    """,
                    slider
                )
                
                time.sleep(random.uniform(0.3, 0.7))
                return True

            except Exception as e:
                print(f"Error setting slider value: {str(e)}")
                return False

        except Exception as e:
            print(f"Error in handle_slider_question: {str(e)}")
            return False

    def handle_dropdown_question(self, element):
        """Handle dropdown select questions."""
        try:
            question_text = self.ai.get_question_text(element)
            if not question_text:
                return False

            select_element = element.find_element(By.CSS_SELECTOR, 'select')
            if not select_element:
                return False

            select = Select(select_element)
            options = [opt.text.strip() for opt in select.options if opt.text.strip()]
            if not options:
                return False

            response = self.ai.get_response(f"Choose from options: {', '.join(options)}\n{question_text}")
            if not response:
                return False

            response = response.lower().strip('.,!? \n\t')
            if response.isdigit() and 0 <= int(response)-1 < len(options):
                select.select_by_index(int(response)-1)
                time.sleep(random.uniform(0.3, 0.7))
                return True

            for option in options:
                if response in option.lower():
                    select.select_by_visible_text(option)
                    time.sleep(random.uniform(0.3, 0.7))
                    return True

            return False

        except Exception as e:
            print(f"Error in handle_dropdown_question: {str(e)}")
            return False

    def handle_ranking_question(self, element):
        """Handle questions that require ranking items in order."""
        try:
            draggable = element.find_elements(By.CSS_SELECTOR, '[draggable="true"], [class*="draggable"]')
            if draggable:
                action_chains = ActionChains(self.driver)
                positions = list(range(len(draggable)))
                random.shuffle(positions)
                
                for i, item in enumerate(draggable):
                    target = draggable[positions[i]]
                    action_chains.drag_and_drop(item, target).perform()
                    time.sleep(random.uniform(0.5, 1.0))
                return True

            number_inputs = element.find_elements(By.CSS_SELECTOR, 'input[type="number"]')
            if number_inputs:
                numbers = list(range(1, len(number_inputs) + 1))
                random.shuffle(numbers)
                for i, input_field in enumerate(number_inputs):
                    self.browser.simulate_human_typing(input_field, str(numbers[i]))
                    time.sleep(random.uniform(0.3, 0.8))
                return True

            dropdowns = element.find_elements(By.CSS_SELECTOR, 'select')
            if dropdowns:
                numbers = list(range(1, len(dropdowns) + 1))
                random.shuffle(numbers)
                for i, dropdown in enumerate(dropdowns):
                    Select(dropdown).select_by_value(str(numbers[i]))
                    time.sleep(random.uniform(0.3, 0.8))
                return True

            return False

        except Exception as e:
            print(f"Error in handle_ranking_question: {str(e)}")
            return False

    def handle_grid_question(self):
        """Handle grid-style questions with multiple rows and columns."""
        try:
            grid_selectors = [
                '.grid-question', 'table', '[role="grid"]',
                '.matrix-question', '.matrix-table', '.survey-grid',
                '[class*="grid"]', '[class*="matrix"]'
            ]
            
            grid_element = None
            for selector in grid_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and len(elements) > 0:
                        grid_element = elements[0]
                        break
                except Exception:
                    continue

            if not grid_element:
                return False

            rows = grid_element.find_elements(By.CSS_SELECTOR, 'tr, [role="row"]')
            if not rows:
                return False

            for row in rows:
                try:
                    inputs = row.find_elements(By.CSS_SELECTOR, 
                        'input[type="radio"], input[type="checkbox"], [role="radio"], [role="checkbox"]')
                    
                    if inputs and len(inputs) > 0:
                        choice = random.randint(1, 10)
                        index = len(inputs) - 1 if choice <= 7 else random.randint(0, len(inputs) - 1)
                        self.browser.safe_click(inputs[index])
                        time.sleep(random.uniform(0.5, 1.5))
                except Exception as e:
                    print(f"Error handling grid row: {str(e)}")
                    continue

            return True

        except Exception as e:
            print(f"Error in handle_grid_question: {str(e)}")
            return False
