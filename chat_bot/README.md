# 🤖 Advanced AI Chatbot

A modern web-based chatbot interface that supports both **local Ollama models** and **Google Gemini API**, built with Gradio.

## ✨ Features

### 🔄 Dual Mode Support
- **🤖 Ollama (Local)**: Chat with locally installed LLM models
- **🌟 Gemini (API)**: Use Google's powerful Gemini AI via API

### 🎨 Enhanced UI
- Modern, responsive design with improved layout
- Configuration panel for easy mode switching
- Real-time status updates
- Copy-to-clipboard functionality for chat messages
- Export chat history feature

### ⚙️ Advanced Configuration
- Dynamic model selection for Ollama
- Secure API key input for Gemini
- Model refresh functionality
- Timeout handling and error management

## 🚀 Quick Start

### Prerequisites
1. **For Ollama Mode**: Install and run [Ollama](https://ollama.ai/)
2. **For Gemini Mode**: Get your [Google AI API Key](https://makersuite.google.com/app/apikey)

### Installation

1. Clone or download the project files
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python ollama_chatbot_gradio.py
   ```

4. Open your browser and navigate to the provided URL (typically `http://localhost:7860`)

## 🔧 Configuration

### Ollama Setup
1. Install Ollama from [https://ollama.ai/](https://ollama.ai/)
2. Pull your desired model:
   ```bash
   ollama pull llama3.2
   ```
3. Ensure Ollama is running on `localhost:11434`

### Gemini API Setup
1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. In the app, select "🌟 Gemini (API)" mode
3. Enter your API key in the configuration panel
4. Click "🔑 Setup API Key"

## 📋 Usage

1. **Select Mode**: Choose between Ollama (Local) or Gemini (API)
2. **Configure**: 
   - For Ollama: Select your preferred model
   - For Gemini: Enter and setup your API key
3. **Chat**: Type your message and press Enter or click Send
4. **Export**: Save your conversation history using the Export button
5. **Clear**: Reset the chat history with the Clear button

## 🛠️ Technical Details

### Dependencies
- `gradio`: Web interface framework
- `requests`: HTTP client for Ollama API
- `google-generativeai`: Official Google Gemini API client
- `typing-extensions`: Type hints support

### Architecture
- **Modular Design**: Separate functions for each AI backend
- **Error Handling**: Comprehensive error management and user feedback
- **State Management**: Persistent chat history during session
- **Dynamic UI**: Context-aware interface updates

### API Endpoints
- **Ollama**: `http://localhost:11434/api/generate`
- **Gemini**: Google AI REST API via official Python client

## 🔒 Security Notes

- API keys are handled securely and not stored permanently
- Input validation and sanitization
- Timeout protection for API calls
- No sensitive data logging

## 🎯 Features Comparison

| Feature | Ollama (Local) | Gemini (API) |
|---------|----------------|--------------|
| Privacy | ✅ Fully private | ⚠️ Cloud-based |
| Speed | 🐌 Depends on hardware | ⚡ Very fast |
| Cost | 💰 Free (after setup) | 💳 Pay-per-use |
| Models | 🔧 Limited selection | 🌟 Latest Gemini models |
| Internet | ❌ Not required | ✅ Required |

## 🚨 Troubleshooting

### Ollama Issues
- Ensure Ollama is running: `ollama serve`
- Check available models: `ollama list`
- Verify port 11434 is accessible

### Gemini Issues
- Verify your API key is valid
- Check your Google Cloud billing setup
- Ensure internet connectivity

### General Issues
- Restart the application
- Check console for error messages
- Verify all dependencies are installed

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve this chatbot!

## 📄 License

This project is open source and available under the MIT License.

---

**Made with ❤️ by Lebi | Powered by Ollama + Gemini + Gradio**
