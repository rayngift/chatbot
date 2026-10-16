# 🔬 Science Study Chatbot

An AI chatbot agent that helps students answer scientific questions and study more effectively. It uses large language models through the [OpenRouter](https://openrouter.ai) API and provides a simple web interface for chatting.

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage](#usage)
- [Security](#security)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

## Features

- Answers questions across scientific subjects (physics, chemistry, biology, mathematics, etc.)
- Explains concepts step by step, adapted to a student's level
- Keeps conversation history so you can continue a study session
- Lightweight web interface, no framework needed on the front end
- Model access through OpenRouter, so you can switch models easily

## Demo

<!-- TODO: add a screenshot or GIF of the interface -->
<!-- ![Screenshot](docs/screenshot.png) -->

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python |
| AI provider | OpenRouter API |
| Frontend | HTML (`static/index.html`) |
| Config | `python-dotenv` |
| Storage | Local chat history files |

<!-- TODO: add your web framework (Flask, FastAPI, ...) -->

## Project Structure

```
chat/
├── .gitignore
├── README.md
└── chatbot/
    ├── main.py            # Backend and chatbot logic
    ├── example.env        # Template for environment variables
    ├── .gitignore
    └── static/
        └── index.html     # Web interface
```

The `chat_history/` folder is created automatically at runtime and is not tracked by Git.

## Getting Started

### Prerequisites

- Python 3.9 or newer
- An OpenRouter account and API key ([get one here](https://openrouter.ai/keys))
- Git

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/rayngift/chatbot.git
   cd chatbot/chatbot
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS / Linux
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   <!-- TODO: generate the file with: pip freeze > requirements.txt -->

## Configuration

1. Copy the template:

   ```bash
   copy example.env .env        # Windows
   cp example.env .env          # macOS / Linux
   ```

2. Open `.env` and add your own key:

   ```
   OPENROUTER_API_KEY=your_key_here
   ```

> ⚠️ Never commit `.env` or share your API key. It is already listed in `.gitignore`.

## Usage

Start the application:

```bash
python main.py
```

<!-- TODO: if you use uvicorn/flask, replace with the exact command, e.g.:
uvicorn main:app --reload -->

Then open the address shown in the terminal (for example `http://localhost:8000`) in your browser and start asking questions.

**Example prompts**

- "Explain photosynthesis in simple terms."
- "Walk me through solving a quadratic equation step by step."
- "Quiz me on Newton's three laws."
- "What is the difference between mitosis and meiosis?"

## Security

- API keys are loaded from environment variables and never stored in the code.
- `.env`, chat history, and archive files are excluded through `.gitignore`.
- If a key is ever exposed, revoke it immediately from the OpenRouter dashboard.

## Roadmap

- [ ] Quiz and flashcard generation mode
- [ ] Support for LaTeX / math formula rendering
- [ ] Subject selection (physics, chemistry, biology, ...)
- [ ] Upload a PDF course and ask questions about it
- [ ] Multi-language interface (French / English)

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push the branch: `git push origin feature/my-feature`
5. Open a Pull Request

## License

<!-- TODO: choose a license (MIT is a common choice) and add a LICENSE file -->
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Author

Made by [rayngift](https://github.com/rayngift)  
