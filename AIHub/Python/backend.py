"""
AI Hub Backend Server
A Flask-based API server that handles AI processing requests from AutoHotkey GUI.
Supports OpenAI API and can be extended to support local LLMs.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aihub.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for localhost communication

# Global state
chat_history = []
prompts = {}
config = {}

# Paths
BASE_DIR = Path(__file__).parent
PROMPTS_FILE = BASE_DIR / "prompts.json"
CONFIG_FILE = BASE_DIR / "config.json"
API_KEY_FILE = BASE_DIR / "apikey.txt"


def load_config():
    """Load configuration from file"""
    global config
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {
            "ai_provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 2000
        }
        save_config()
    logger.info(f"Configuration loaded: {config}")


def save_config():
    """Save configuration to file"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def load_prompts():
    """Load prompts from JSON file"""
    global prompts
    if PROMPTS_FILE.exists():
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
    else:
        # Default prompts
        prompts = {
            "clarify": {
                "name": "Clarify",
                "template": "Rewrite the following text for clarity and coherence without changing its meaning:\n\n{text}",
                "enabled": True
            },
            "friendly": {
                "name": "Make Friendly",
                "template": "Rewrite the following text to sound friendly and conversational:\n\n{text}",
                "enabled": True
            },
            "summarize": {
                "name": "Summarize",
                "template": "Summarize the following text clearly in 3 sentences:\n\n{text}",
                "enabled": True
            },
            "professional": {
                "name": "Professionalize",
                "template": "Rewrite the following text to sound professional and polished:\n\n{text}",
                "enabled": True
            },
            "expand": {
                "name": "Expand",
                "template": "Expand on the following text with more detail and depth:\n\n{text}",
                "enabled": False
            }
        }
        save_prompts()
    logger.info(f"Loaded {len(prompts)} prompts")


def save_prompts():
    """Save prompts to JSON file"""
    with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, indent=2)


def get_api_key():
    """Load API key from file"""
    if API_KEY_FILE.exists():
        with open(API_KEY_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None


def call_openai(messages, model=None, temperature=None, max_tokens=None):
    """Call OpenAI API"""
    try:
        import openai

        api_key = get_api_key()
        if not api_key:
            raise ValueError("OpenAI API key not found. Please create apikey.txt in the Python directory.")

        openai.api_key = api_key

        # Use config defaults if not specified
        model = model or config.get("model", "gpt-4o-mini")
        temperature = temperature if temperature is not None else config.get("temperature", 0.7)
        max_tokens = max_tokens or config.get("max_tokens", 2000)

        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content.strip()

    except ImportError:
        logger.error("OpenAI library not installed. Run: pip install openai")
        raise ValueError("OpenAI library not installed. Please run: pip install openai")
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise


def call_ai(messages, **kwargs):
    """Route to appropriate AI provider"""
    provider = config.get("ai_provider", "openai")

    if provider == "openai":
        return call_openai(messages, **kwargs)
    else:
        # Placeholder for future local LLM support
        raise ValueError(f"Unsupported AI provider: {provider}")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "provider": config.get("ai_provider", "openai"),
        "prompts_loaded": len(prompts)
    })


@app.route('/process', methods=['POST'])
def process():
    """Main processing endpoint"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        action = data.get("action")
        logger.info(f"Processing action: {action}")

        if action == "run_prompt":
            return handle_run_prompt(data)
        elif action == "chat":
            return handle_chat(data)
        elif action == "get_prompts":
            return handle_get_prompts()
        elif action == "update_prompt":
            return handle_update_prompt(data)
        elif action == "clear_history":
            return handle_clear_history()
        else:
            return jsonify({"error": f"Unknown action: {action}"}), 400

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def handle_run_prompt(data):
    """Handle prompt execution"""
    prompt_id = data.get("prompt_id")
    text = data.get("text", "")

    if not prompt_id:
        return jsonify({"error": "prompt_id is required"}), 400

    if prompt_id not in prompts:
        return jsonify({"error": f"Prompt not found: {prompt_id}"}), 404

    prompt_config = prompts[prompt_id]
    template = prompt_config.get("template", "")

    # Format the template with the text
    prompt_text = template.replace("{text}", text)

    messages = [
        {"role": "system", "content": "You are a skilled writing assistant."},
        {"role": "user", "content": prompt_text}
    ]

    result = call_ai(messages)

    logger.info(f"Prompt '{prompt_id}' executed successfully")
    return jsonify({
        "result": result,
        "prompt_id": prompt_id,
        "prompt_name": prompt_config.get("name", prompt_id)
    })


def handle_chat(data):
    """Handle chat message"""
    global chat_history

    user_message = data.get("message", "")
    if not user_message:
        return jsonify({"error": "message is required"}), 400

    # Add user message to history
    chat_history.append({"role": "user", "content": user_message})

    # Prepare messages for AI
    system_message = {"role": "system", "content": "You are a helpful AI assistant."}
    messages = [system_message] + chat_history

    # Get AI response
    reply = call_ai(messages)

    # Add assistant response to history
    chat_history.append({"role": "assistant", "content": reply})

    logger.info(f"Chat message processed. History length: {len(chat_history)}")
    return jsonify({
        "reply": reply,
        "history_length": len(chat_history)
    })


def handle_get_prompts():
    """Return all prompts"""
    return jsonify({"prompts": prompts})


def handle_update_prompt(data):
    """Update or add a prompt"""
    prompt_id = data.get("prompt_id")
    prompt_data = data.get("prompt_data")

    if not prompt_id or not prompt_data:
        return jsonify({"error": "prompt_id and prompt_data are required"}), 400

    prompts[prompt_id] = prompt_data
    save_prompts()

    logger.info(f"Prompt '{prompt_id}' updated")
    return jsonify({"status": "success", "prompt_id": prompt_id})


def handle_clear_history():
    """Clear chat history"""
    global chat_history
    chat_history = []
    logger.info("Chat history cleared")
    return jsonify({"status": "success", "message": "Chat history cleared"})


def startup():
    """Initialize the server"""
    logger.info("=" * 60)
    logger.info("AI Hub Backend Starting")
    logger.info("=" * 60)

    load_config()
    load_prompts()

    # Check for API key
    api_key = get_api_key()
    if api_key:
        logger.info("API key loaded successfully")
    else:
        logger.warning("No API key found. Create apikey.txt in the Python directory.")

    logger.info(f"Server ready on http://127.0.0.1:8765")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)


if __name__ == "__main__":
    startup()
    app.run(host='127.0.0.1', port=8765, debug=False)
