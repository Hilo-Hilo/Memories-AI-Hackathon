# Setup Instructions

This guide explains how to set up the development environment for the Memories AI Hackathon project.

## Prerequisites

- Python 3.10 or higher
- UV package manager (install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Webcam (for Hume AI expression measurement)

## Environment Setup

### 1. Create Virtual Environment with UV

```bash
uv venv
```

### 2. Activate Virtual Environment

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
uv pip install -e .
```

This will install the package in editable mode with all required dependencies:
- opencv-python (webcam capture)
- hume (Hume AI SDK)
- requests (Memories.ai API)
- python-dotenv (environment variables)
- numpy (image processing)

## API Keys Setup

Create a `.env` file in the project root with your API keys:

```bash
MEM_AI_API_KEY=your_memories_ai_key_here
HUME_API_KEY=your_hume_ai_key_here
PATH_TO_TEST_VIDEO=/path/to/your/test/video.mov
```

### Getting API Keys

- **Memories.ai**: Sign up at https://memories.ai and create an API key
- **Hume AI**: Sign up at https://www.hume.ai and generate an API key

## Running the Scripts

### Memories.ai API Tests

Test all Memories.ai capabilities:
```bash
python testing/api-testing/api_test.py
```

Test chat sessions:
```bash
python testing/api-testing/test_list_sessions.py
```

### Hume AI Live Expression Measurement

Run the live webcam expression analyzer:
```bash
python testing/hume-ai-api-testing/live_expression_webcam.py
```

This script will:
- Capture frames from your webcam at 1Hz (1 per second)
- Analyze facial expressions using Hume AI
- Display the top 5 emotions detected with confidence scores
- Run continuously until you press Ctrl+C

## Project Structure

```
memories-ai-hackathon/
├── .env                              # API keys (gitignored)
├── pyproject.toml                    # UV project configuration
├── CLAUDE.md                         # Claude Code instructions
├── SETUP.md                          # This file
├── src/
│   └── memories_ai_app/              # Main application package
│       └── __init__.py
├── memories_ai_api_docs/             # Memories.ai API documentation
├── hume-expression-measurement-docs/ # Hume AI API documentation
└── testing/
    ├── api-testing/                  # Memories.ai tests
    │   ├── api_test.py
    │   └── test_list_sessions.py
    └── hume-ai-api-testing/          # Hume AI tests
        └── live_expression_webcam.py
```

## Troubleshooting

### Webcam Not Found
If the webcam script fails to open the camera:
- Check that your webcam is connected and not in use by another application
- On macOS, grant Terminal camera permissions in System Preferences > Security & Privacy

### API Key Errors
- Ensure your `.env` file is in the project root directory
- Check that API keys are valid and have not expired
- Verify there are no extra spaces or quotes around the keys

### Dependency Issues
If you encounter installation issues:
```bash
uv pip install --upgrade pip
uv pip install -e . --force-reinstall
```

## Development Dependencies

Install development tools:
```bash
uv pip install -e ".[dev]"
```

This includes:
- pytest (testing)
- black (code formatting)
- ruff (linting)
