# AI Web Agent

An intelligent web automation agent capable of navigating websites and completing online tasks using AI-driven decision making.

## Features

- Automated web navigation and interaction
- AI-powered decision making using OpenAI GPT
- Robust element detection and interaction
- Error handling and recovery
- Support for complex multi-step tasks

## Prerequisites

- Python 3.7+
- Chrome browser installed
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
cd [repo-directory]
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Basic usage example:
```python
from web_agent import WebAgent

# Initialize the agent
agent = WebAgent(headless=False)

# Execute a task
agent.execute_task("Navigate to Wikipedia and search for 'Artificial Intelligence'")

# Clean up
agent.close()
```

2. Run the example script:
```bash
python example.py
```

## Features

The WebAgent provides several key methods:

- `navigate_to(url)`: Navigate to a specific URL
- `find_element(selector)`: Find an element on the page
- `click_element(selector)`: Click an element
- `input_text(selector, text)`: Input text into a form field
- `execute_task(task_description)`: Execute a complex task using AI

## Error Handling

The agent includes robust error handling for common scenarios:
- Network issues
- Missing elements
- Navigation failures
- Invalid selectors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
