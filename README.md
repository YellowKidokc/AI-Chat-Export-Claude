# AI Hub - AutoHotkey + Python AI Assistant

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)
![AutoHotkey](https://img.shields.io/badge/AutoHotkey-v2.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A powerful, modular AI assistant that combines **AutoHotkey's UI capabilities** with **Python's AI processing power**. Transform your text workflow with hotkey-driven AI enhancements, customizable prompts, and an integrated chat interface.

## 🎯 Overview

AI Hub is a hybrid desktop application designed for seamless AI-powered text processing:

- **AutoHotkey Frontend**: Provides GUI, hotkeys, and text capture/replacement
- **Python Backend**: Handles AI processing via OpenAI API (with future support for local LLMs)
- **Modular Architecture**: Easy to extend, customize, and iterate without breaking existing functionality

### Key Features

✨ **Quick Text Processing**
- Select text anywhere, press a hotkey, get AI-enhanced results instantly
- Built-in prompts: Clarify, Make Friendly, Summarize, Fix Grammar, Professionalize, and more

💬 **Chat Interface**
- Full conversation history with AI
- Context-aware responses
- Export and clear history

🎨 **Customizable Prompts**
- Create, edit, enable/disable prompts via GUI
- JSON-based configuration for easy sharing
- Template system with variable substitution

⚡ **Hotkey Workflow**
- `Ctrl+Shift+H` - Toggle main GUI
- `Ctrl+Shift+P` - Quick popup menu
- `Ctrl+Shift+Q` - Quick Clarify selected text
- `Ctrl+Shift+F` - Make text friendly
- `Ctrl+Shift+G` - Fix grammar

🔧 **Easy Configuration**
- Simple API key setup
- Model selection (GPT-4o-mini by default)
- Temperature and token controls

---

## 📁 Project Structure

```
AI-Chat-Export-Claude/
│
├── AIHub/
│   ├── AutoHotkey/
│   │   ├── main.ahk              # Entry point - hotkeys and initialization
│   │   ├── gui_tabs.ahk          # GUI tab creation and management
│   │   ├── api_bridge.ahk        # HTTP communication with Python backend
│   │   └── utils.ahk             # Utility functions (text capture, JSON, etc.)
│   │
│   └── Python/
│       ├── backend.py            # Flask API server
│       ├── prompts.json          # Prompt templates configuration
│       ├── config.json           # Backend configuration
│       ├── requirements.txt      # Python dependencies
│       └── apikey.txt.example    # API key template
│
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.7+** - [Download Python](https://www.python.org/downloads/)
2. **AutoHotkey v2.0+** - [Download AutoHotkey v2](https://www.autohotkey.com/download/ahk-v2.exe)
3. **OpenAI API Key** - [Get your API key](https://platform.openai.com/api-keys)

### Installation

#### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/AI-Chat-Export-Claude.git
cd AI-Chat-Export-Claude
```

#### Step 2: Set Up Python Backend

```bash
# Navigate to Python directory
cd AIHub/Python

# Install dependencies
pip install -r requirements.txt

# Create API key file
copy apikey.txt.example apikey.txt
# Edit apikey.txt and add your OpenAI API key
```

#### Step 3: Run the Application

```bash
# Option 1: AutoHotkey starts backend automatically
# Just run the AutoHotkey script:
AIHub\AutoHotkey\main.ahk

# Option 2: Start backend manually (optional)
cd AIHub/Python
python backend.py
# Then run: AIHub\AutoHotkey\main.ahk
```

#### Step 4: First Use

1. Press `Ctrl+Shift+H` to open the main GUI
2. Check the **Settings** tab to verify backend is running
3. Try selecting some text anywhere and pressing `Ctrl+Shift+Q` to clarify it!

---

## 📖 Usage Guide

### Quick Actions Tab

Process text quickly with pre-configured prompts:

1. Select text anywhere in any application
2. Press `Ctrl+Shift+P` for quick popup OR use specific hotkeys:
   - `Ctrl+Shift+Q` - Clarify text
   - `Ctrl+Shift+F` - Make friendly
   - `Ctrl+Shift+G` - Fix grammar
3. The processed text replaces your selection automatically

**Manual Input:**
1. Open main GUI (`Ctrl+Shift+H`)
2. Go to **Quick Actions** tab
3. Paste or type text in the input box
4. Select a prompt from dropdown
5. Click "Process Text"

### Chat Tab

Have conversations with AI:

1. Open main GUI (`Ctrl+Shift+H`)
2. Go to **Chat** tab
3. Type your message in the input box
4. Click "Send" (or press `Ctrl+Enter`)
5. View conversation history in the main area

**Tips:**
- Chat maintains context across messages in a session
- Click "Clear History" to start fresh
- Click "Copy Chat" to export conversation

### Prompts Tab

Manage your prompt library:

1. Open main GUI (`Ctrl+Shift+H`)
2. Go to **Prompts** tab
3. View all available prompts with their status
4. **Toggle Enabled**: Select a prompt and click "Toggle Enabled"
5. **Edit Prompt**: Double-click a prompt to view its template
6. Prompts are stored in `AIHub/Python/prompts.json`

**Creating Custom Prompts:**

Edit `AIHub/Python/prompts.json`:

```json
{
  "custom_prompt_id": {
    "name": "My Custom Prompt",
    "template": "Your instruction here:\n\n{text}",
    "enabled": true,
    "description": "What this prompt does"
  }
}
```

The `{text}` placeholder will be replaced with the selected/input text.

### Settings Tab

Configure the application:

- **Backend Status**: Check if Python server is running
- **Start Backend**: Manually start the backend if needed
- **AI Provider**: Select OpenAI (local LLM support coming soon)
- **Model**: Choose which OpenAI model to use
- **API Key**: Location of your API key file

---

## 🔧 Configuration

### Backend Configuration

Edit `AIHub/Python/config.json`:

```json
{
  "ai_provider": "openai",
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Parameters:**
- `ai_provider`: "openai" (more providers coming soon)
- `model`: OpenAI model to use (e.g., "gpt-4", "gpt-4o-mini", "gpt-3.5-turbo")
- `temperature`: Creativity level (0.0 - 2.0, lower = more focused)
- `max_tokens`: Maximum response length

### Customizing Hotkeys

Edit `AIHub/AutoHotkey/main.ahk` to change hotkeys:

```autohotkey
; Change this line to customize the main GUI hotkey
^+h::  ; Currently: Ctrl+Shift+H
```

**AutoHotkey Hotkey Syntax:**
- `^` = Ctrl
- `+` = Shift
- `!` = Alt
- `#` = Win

Example: `^!p::` = Ctrl+Alt+P

---

## 🏗️ Architecture

### Communication Flow

```
┌──────────────┐
│     User     │
└──────┬───────┘
       │ (selects text, presses hotkey)
       ↓
┌──────────────────────────────────┐
│   AutoHotkey Frontend            │
│  ┌────────────────────────────┐  │
│  │ GUI (gui_tabs.ahk)         │  │
│  │ - Quick Actions            │  │
│  │ - Chat Interface           │  │
│  │ - Prompt Management        │  │
│  │ - Settings                 │  │
│  └────────────┬───────────────┘  │
│               │                   │
│  ┌────────────▼───────────────┐  │
│  │ API Bridge (api_bridge.ahk)│  │
│  │ - HTTP requests            │  │
│  │ - JSON serialization       │  │
│  │ - Process management       │  │
│  └────────────┬───────────────┘  │
└───────────────┼───────────────────┘
                │ HTTP POST (JSON)
                │ http://127.0.0.1:8765/process
                ↓
┌────────────────────────────────────┐
│   Python Backend (Flask)           │
│  ┌──────────────────────────────┐  │
│  │ backend.py                   │  │
│  │ - /process endpoint          │  │
│  │ - run_prompt action          │  │
│  │ - chat action                │  │
│  │ - prompt management          │  │
│  └─────────┬────────────────────┘  │
│            │                        │
│            ↓                        │
│  ┌──────────────────────────────┐  │
│  │ OpenAI API                   │  │
│  │ - gpt-4o-mini (default)      │  │
│  │ - Chat completion            │  │
│  └──────────────────────────────┘  │
└────────────────────────────────────┘
```

### Why This Architecture?

1. **Separation of Concerns**
   - AutoHotkey handles UI/UX and system integration
   - Python handles AI logic and API communication

2. **Independent Evolution**
   - Update UI without touching AI logic
   - Swap AI providers without changing frontend
   - Add new features modularly

3. **Easy Testing**
   - Test backend independently via HTTP requests
   - Test frontend with mock responses

4. **Future-Proof**
   - Add local LLM support without changing AHK code
   - Replace Flask with FastAPI easily
   - Add web interface alongside AHK GUI

---

## 🛠️ Development

### Adding New Prompts

1. Edit `AIHub/Python/prompts.json`
2. Add your prompt following the structure:
   ```json
   "your_id": {
     "name": "Display Name",
     "template": "Your instruction with {text} placeholder",
     "enabled": true,
     "description": "What it does"
   }
   ```
3. Restart backend or click "Refresh Prompts" in GUI

### Adding New Hotkey Actions

Edit `AIHub/AutoHotkey/main.ahk`:

```autohotkey
; Add new hotkey
^+y:: {  ; Ctrl+Shift+Y
    if !AppInitialized
        Initialize()

    Text := CaptureSelection()
    if IsEmpty(Text)
        return

    Result := RunPrompt("your_prompt_id", Text)
    if (Result != "")
        ReplaceSelection(Result)
}
```

### Extending the Backend

Add new endpoints in `AIHub/Python/backend.py`:

```python
@app.route('/custom', methods=['POST'])
def custom_endpoint():
    data = request.json
    # Your logic here
    return jsonify({"result": "success"})
```

### Creating New GUI Tabs

Edit `AIHub/AutoHotkey/gui_tabs.ahk` and add your tab creation function:

```autohotkey
CreateYourTab(GuiObj) {
    GuiObj.Add("Text", "x20 y40", "Your content here")
    ; Add more controls...
}
```

---

## 🔍 Troubleshooting

### Backend Won't Start

**Problem**: Error message "Failed to start Python backend"

**Solutions:**
1. Verify Python is installed: `python --version`
2. Install dependencies: `pip install -r requirements.txt`
3. Check `aihub.log` for error details
4. Manually start backend: `python AIHub/Python/backend.py`
5. Ensure port 8765 is not in use

### API Key Errors

**Problem**: "OpenAI API key not found" or authentication errors

**Solutions:**
1. Create `AIHub/Python/apikey.txt` (copy from `apikey.txt.example`)
2. Paste your OpenAI API key in the file (just the key, no quotes)
3. Verify key is valid at [OpenAI Platform](https://platform.openai.com/api-keys)
4. Restart the backend

### Text Not Being Replaced

**Problem**: Processed text doesn't replace selection

**Solutions:**
1. Ensure you have text selected when pressing hotkey
2. Try with a simple text editor (Notepad) first
3. Some applications block clipboard operations
4. Check if hotkey conflicts with other software

### Hotkeys Not Working

**Problem**: Pressing hotkeys does nothing

**Solutions:**
1. Check if AutoHotkey script is running (look for tray icon)
2. Restart the script: Right-click tray icon → Reload
3. Check for hotkey conflicts with other software
4. Run AutoHotkey as administrator if needed

---

## 📝 API Reference

### Backend Endpoints

#### POST `/health`
Health check endpoint

**Response:**
```json
{
  "status": "running",
  "timestamp": "2025-01-15T10:30:00",
  "provider": "openai",
  "prompts_loaded": 7
}
```

#### POST `/process`

Main processing endpoint

**Run Prompt:**
```json
{
  "action": "run_prompt",
  "prompt_id": "clarify",
  "text": "Your text here"
}
```

**Response:**
```json
{
  "result": "Processed text here",
  "prompt_id": "clarify",
  "prompt_name": "Clarify"
}
```

**Chat:**
```json
{
  "action": "chat",
  "message": "Hello, how are you?"
}
```

**Response:**
```json
{
  "reply": "AI response here",
  "history_length": 2
}
```

**Get Prompts:**
```json
{
  "action": "get_prompts"
}
```

**Response:**
```json
{
  "prompts": {
    "clarify": {
      "name": "Clarify",
      "template": "...",
      "enabled": true
    }
  }
}
```

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Report Bugs**: Open an issue with details and reproduction steps
2. **Suggest Features**: Describe your idea and use case
3. **Submit Pull Requests**: Fork, create a branch, make changes, and PR
4. **Share Prompts**: Create a prompt library and share with the community
5. **Improve Documentation**: Fix typos, add examples, clarify instructions

---

## 📜 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

- Built with [AutoHotkey v2](https://www.autohotkey.com/)
- Powered by [OpenAI API](https://platform.openai.com/)
- Flask web framework

---

## 🗺️ Roadmap

### Version 1.1
- [ ] Local LLM support (Ollama, LM Studio)
- [ ] Prompt templates with multiple variables
- [ ] Batch processing for multiple files
- [ ] Export/import prompt libraries

### Version 1.2
- [ ] Web interface (alongside AHK GUI)
- [ ] Voice input support
- [ ] Multi-language support
- [ ] Prompt marketplace/sharing

### Version 2.0
- [ ] Plugin system for custom AI providers
- [ ] Advanced context management
- [ ] Team collaboration features
- [ ] Cloud sync for settings and prompts

---

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/AI-Chat-Export-Claude/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/AI-Chat-Export-Claude/discussions)
- **Email**: your.email@example.com

---

## ⭐ Star History

If you find this project useful, please consider giving it a star on GitHub!

---

**Made with ❤️ by the AI Hub community**
