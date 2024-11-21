from web_agent import WebAgent
import time
import random
import signal
import sys
import json
def signal_handler(sig, frame):
    print('\nGracefully shutting down...')
    sys.exit(0)
def load_config():
    """Load proxy configuration."""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except:
        return None
def main():
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Load configuration
    config = load_config()
    proxy = config.get('proxy') if config else None
    
    # Initialize the web agent
    agent = WebAgent(headless=False, proxy=proxy)
    
    try:
        # Navigate to Survey Junkie
        print("Navigating to Survey Junkie...")
        if not agent.navigate_to("https://www.surveyjunkie.com"):
            print("Failed to access Survey Junkie. Please try again later.")
            return
        
        # Add random delays between actions
        time.sleep(random.uniform(2, 4))
        
        # Task description for logging in and finding surveys
        task = """
        1. Look for a sign-in button or link
        2. If not signed in, click the sign-in button
        3. Once on the dashboard, look for available surveys
        4. For each available survey:
           - Check the estimated time and points
           - Start the survey if it's worthwhile (>50 points per minute)
           - Answer questions thoughtfully with realistic responses
           - Complete the survey
        5. If no surveys are available, wait and refresh
        
        Important:
        - Act like a real user, don't click too quickly
        - Give realistic, consistent answers
        - Take natural pauses between actions
        - If asked verification questions, answer carefully
        - Use human-like typing and clicking behavior
        """
        
        # Execute the task
        print("Starting survey tasks...")
        agent.execute_task(task)
        
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
    finally:
        # Always close the browser properly
        print("\nClosing browser...")
        agent.close()
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\nExiting...')
