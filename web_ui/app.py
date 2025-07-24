from flask import Flask, render_template, request, jsonify
import cv2
import base64
import numpy as np
import threading
import logging
import traceback
import os
import requests
import re
import time

# === Logger Setup ===
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# === Configuration ===
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("MODEL_NAME", "llava:7b")

# === Prompts ===
PERSON_PROMPT = """Analyze this image and provide a detailed description of:\n1. If a person is present, identify:\n   - Age range (e.g., \"Age: 18-25 years\")\n   - Gender (\"Male\" or \"Female\")\n   - Clothing type, color, and accessories\n2. Describe the surrounding environment (indoor/outdoor, objects, time of day if possible)\n\nRespond in this format:\nAge: XX-XX years\nGender: Male/Female\nClothing: [description]\nEnvironment: [description]"""

CHAT_PROMPT = """You are an AI assistant that can analyze images. The user has uploaded an image and is asking you questions about it. 
Provide helpful, accurate, and detailed responses about what you can see in the image. 
If the user asks about something not visible in the image, politely let them know.

User question: {question}"""

# === API Connection Test ===
def test_api_connection():
    """Test if the Ollama API is reachable"""
    try:
        test_url = OLLAMA_API_URL.replace('/api/generate', '/api/tags')
        response = requests.get(test_url, timeout=10)
        if response.status_code == 200:
            logging.info("✓ Ollama API is reachable")
            return True
        else:
            logging.error(f"✗ Ollama API returned status code: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"✗ Cannot connect to Ollama API: {e}")
        return False

# === Retry Helper ===
def retry_post(url, payload, retries=3, delay=5):
    for attempt in range(retries):
        try:
            logging.info(f"Attempting API call {attempt+1}/{retries} to {url}")
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            logging.info(f"✓ API call successful on attempt {attempt+1}")
            return response
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error during retry {attempt+1}/{retries}: {http_err} - Status: {http_err.response.status_code}")
            if http_err.response.status_code >= 500:
                logging.error(f"Server error response: {http_err.response.text[:200]}")
        except requests.exceptions.Timeout as timeout_err:
            logging.error(f"Timeout error during retry {attempt+1}/{retries}: {timeout_err}")
        except requests.exceptions.ConnectionError as conn_err:
            logging.error(f"Connection error during retry {attempt+1}/{retries}: {conn_err}")
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Request exception during retry {attempt+1}/{retries}: {req_err}")
        except Exception as e:
            logging.error(f"Unexpected error during retry {attempt+1}/{retries}: {e}")
        
        if attempt < retries - 1:
            logging.info(f"Waiting {delay} seconds before retry...")
            time.sleep(delay)
    
    logging.error(f"All {retries} API call attempts failed")
    return None

# === Analyzer Class ===
class RealTimeAnalyzer:
    def parse_response(self, response_text):
        def extract(pattern, label):
            try:
                return re.search(pattern, response_text, re.IGNORECASE).group(1)
            except:
                logging.warning(f"Could not parse {label}")
                return "Unknown"

        return {
            "age": extract(r"Age:\s*([^\n]+)", "age"),
            "gender": extract(r"Gender:\s*([^\n]+)", "gender"),
            "clothing": extract(r"Clothing:\s*([^\n]+)", "clothing"),
            "environment": extract(r"Environment:\s*([^\n]+)", "environment"),
        }

    def analyze_image(self, image_np):
        try:
            logging.info("Starting image analysis...")
            
            # Resize and encode image
            resized = cv2.resize(image_np, (512, 512))
            _, img_encoded = cv2.imencode('.jpg', resized)
            if not _:
                logging.error("Failed to encode image to JPEG")
                return None
                
            image_base64 = base64.b64encode(img_encoded).decode('utf-8')
            logging.info(f"Image encoded to base64, size: {len(image_base64)} characters")

            payload = {
                "model": MODEL_NAME,
                "prompt": PERSON_PROMPT,
                "images": [image_base64],
                "stream": False
            }
            
            logging.info(f"Sending request to API with model: {MODEL_NAME}")
            response = retry_post(OLLAMA_API_URL, payload)
            
            if response is None:
                logging.error("Failed to get valid response after retries from Ollama API.")
                return {"error": "API connection failed after retries"}
                
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' not in content_type:
                logging.error(f"Unexpected content type: {content_type}")
                logging.error(f"Response text: {response.text[:500]}")
                return {"error": f"Invalid API response format: {content_type}"}
            
            # Parse JSON response
            try:
                response_data = response.json()
                logging.info(f"Received JSON response: {list(response_data.keys())}")
            except ValueError as json_err:
                logging.error(f"Error parsing JSON: {json_err}")
                logging.error(f"Response text: {response.text[:500]}")
                return {"error": "Invalid JSON response from API"}
            
            # Extract response text
            output = response_data.get("response", "")
            if not output:
                logging.warning("Empty response from API")
                return {"error": "Empty response from API"}
                
            logging.info(f"API response received, length: {len(output)} characters")
            logging.info(f"Response preview: {output[:200]}...")
            
            # Parse the response
            result = self.parse_response(output)
            result["raw_response"] = output  # Include raw response for debugging
            
            logging.info("Analysis completed successfully")
            return result
            
        except cv2.error as cv_err:
            logging.error(f"OpenCV error during image processing: {cv_err}")
            return {"error": "Image processing failed"}
        except Exception as e:
            logging.error(f"Unexpected error during analysis: {e}")
            traceback.print_exc()
            return {"error": f"Analysis failed: {str(e)}"}
    
    def chat_with_image(self, image_np, user_message):
        """Chat about an image with the user"""
        try:
            logging.info(f"Starting chat with message: {user_message[:50]}...")
            
            # Resize and encode image
            resized = cv2.resize(image_np, (512, 512))
            _, img_encoded = cv2.imencode('.jpg', resized)
            if not _:
                logging.error("Failed to encode image to JPEG")
                return None
                
            image_base64 = base64.b64encode(img_encoded).decode('utf-8')
            logging.info(f"Image encoded for chat, size: {len(image_base64)} characters")

            # Format the chat prompt with user's question
            formatted_prompt = CHAT_PROMPT.format(question=user_message)
            
            payload = {
                "model": MODEL_NAME,
                "prompt": formatted_prompt,
                "images": [image_base64],
                "stream": False
            }
            
            logging.info(f"Sending chat request to API with model: {MODEL_NAME}")
            response = retry_post(OLLAMA_API_URL, payload)
            
            if response is None:
                logging.error("Failed to get valid response after retries from Ollama API.")
                return {"error": "API connection failed after retries"}
                
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' not in content_type:
                logging.error(f"Unexpected content type: {content_type}")
                logging.error(f"Response text: {response.text[:500]}")
                return {"error": f"Invalid API response format: {content_type}"}
            
            # Parse JSON response
            try:
                response_data = response.json()
                logging.info(f"Received chat JSON response: {list(response_data.keys())}")
            except ValueError as json_err:
                logging.error(f"Error parsing JSON: {json_err}")
                logging.error(f"Response text: {response.text[:500]}")
                return {"error": "Invalid JSON response from API"}
            
            # Extract response text
            output = response_data.get("response", "")
            if not output:
                logging.warning("Empty response from API")
                return {"error": "Empty response from API"}
                
            logging.info(f"Chat API response received, length: {len(output)} characters")
            logging.info(f"Chat response preview: {output[:200]}...")
            
            logging.info("Chat completed successfully")
            return {"response": output}
            
        except cv2.error as cv_err:
            logging.error(f"OpenCV error during chat image processing: {cv_err}")
            return {"error": "Image processing failed"}
        except Exception as e:
            logging.error(f"Unexpected error during chat: {e}")
            traceback.print_exc()
            return {"error": f"Chat failed: {str(e)}"}

analyzer = RealTimeAnalyzer()
app = Flask(__name__, static_folder="static", template_folder="templates")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        logging.info("Received analyze request")
        
        if 'image' not in request.files:
            logging.warning("No image file in request")
            return jsonify({"error": "No image uploaded"}), 400
            
        file = request.files['image']
        if file.filename == '':
            logging.warning("Empty filename in request")
            return jsonify({"error": "No image selected"}), 400
            
        logging.info(f"Processing image: {file.filename}, size: {file.content_length if hasattr(file, 'content_length') else 'unknown'} bytes")
        
        try:
            file_bytes = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        except Exception as decode_err:
            logging.error(f"Failed to decode image: {decode_err}")
            return jsonify({"error": "Failed to decode image file"}), 400
            
        if img is None:
            logging.error("OpenCV failed to decode image - possibly invalid format")
            return jsonify({"error": "Invalid image format"}), 400
            
        logging.info(f"Image decoded successfully: {img.shape}")
        
        result = analyzer.analyze_image(img)
        
        if result is None:
            logging.error("Analyzer returned None")
            return jsonify({"error": "Analysis failed - no result"}), 500
            
        if "error" in result:
            logging.error(f"Analysis error: {result['error']}")
            return jsonify(result), 500
            
        logging.info("Analysis completed successfully")
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Unexpected error in /analyze endpoint: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat messages about the uploaded image"""
    try:
        logging.info("Received chat request")
        
        if 'image' not in request.files:
            logging.warning("No image file in chat request")
            return jsonify({"error": "No image uploaded"}), 400
            
        if 'message' not in request.form:
            logging.warning("No message in chat request")
            return jsonify({"error": "No message provided"}), 400
            
        file = request.files['image']
        user_message = request.form['message']
        
        if file.filename == '':
            logging.warning("Empty filename in chat request")
            return jsonify({"error": "No image selected"}), 400
            
        if not user_message.strip():
            logging.warning("Empty message in chat request")
            return jsonify({"error": "No message provided"}), 400
            
        logging.info(f"Processing chat for image: {file.filename}, message: {user_message[:50]}...")
        
        try:
            file_bytes = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        except Exception as decode_err:
            logging.error(f"Failed to decode image in chat: {decode_err}")
            return jsonify({"error": "Failed to decode image file"}), 400
            
        if img is None:
            logging.error("OpenCV failed to decode image in chat - possibly invalid format")
            return jsonify({"error": "Invalid image format"}), 400
            
        logging.info(f"Image decoded successfully for chat: {img.shape}")
        
        result = analyzer.chat_with_image(img, user_message)
        
        if result is None:
            logging.error("Chat analyzer returned None")
            return jsonify({"error": "Chat failed - no result"}), 500
            
        if "error" in result:
            logging.error(f"Chat error: {result['error']}")
            return jsonify(result), 500
            
        logging.info("Chat completed successfully")
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Unexpected error in /chat endpoint: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    logging.info("=== Real-time Scene Analyzer Starting ===")
    logging.info(f"Ollama API URL: {OLLAMA_API_URL}")
    logging.info(f"Model: {MODEL_NAME}")
    
    # Test API connection at startup
    if not test_api_connection():
        logging.warning("⚠️  Ollama API is not reachable. Please ensure:")
        logging.warning("   1. Ollama is installed and running")
        logging.warning("   2. The model 'llava:7b' is available (run: ollama pull llava:7b)")
        logging.warning("   3. API URL is correct: " + OLLAMA_API_URL)
        logging.warning("   Server will start anyway, but image analysis will fail.")
    
    logging.info("Starting Flask server on http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
