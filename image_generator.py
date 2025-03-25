from flask import Flask, render_template, request, send_from_directory, jsonify
from flask_caching import Cache
import requests
import os
from PIL import Image
import io
import logging

app = Flask(__name__)

# إعداد التسجيل
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# إعداد التخزين المؤقت
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

API_URL = os.getenv("API_URL", "https://api.together.xyz/v1/images/generations")
API_KEY = os.getenv("API_KEY", "e0dd9f3efcee4494b30979d8142fa5433d9712b4f1e3c09a2045043fe35f06f3")
HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {API_KEY}"
}

IMAGE_FOLDER = os.path.join('static', 'images')
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

SIZE_OPTIONS = {
    "square": (1024, 1024),
    "youtube": (1280, 720),
    "portrait": (768, 1152),
    "landscape": (1152, 768),
    "story": (1080, 1920)
}

SUPPORTED_MODELS = [
    "black-forest-labs/FLUX.1-schnell-Free",
    "black-forest-labs/flux.1-schnell",
    "black-forest-labs/flux.1-dev",
    "stabilityai/stable-diffusion-xl-base-1.0"
]

@app.route('/')
def index():
    return render_template('index.html')

def fetch_image(payload):
    logger.debug(f"Sending request to API with payload: {payload}")
    try:
        response = requests.post(API_URL, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"API returned an error: {response.status_code} - {response.text}")
        raise

def save_compressed_image(image_url, filename):
    logger.debug(f"Fetching image from: {image_url}")
    resp = requests.get(image_url)
    resp.raise_for_status()
    img_data = resp.content
    img = Image.open(io.BytesIO(img_data))
    img = img.convert('RGB')
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    with open(os.path.join(IMAGE_FOLDER, filename), "wb") as f:
        f.write(buffer.getvalue())
    logger.debug(f"Image saved to: {filename}")
    return f"images/{filename}"

@app.route('/generate', methods=['POST'])
@cache.cached(timeout=300, key_prefix=lambda: f"generate_{request.get_json().get('seed', 'no_seed')}")
def generate_image():
    if request.method != 'POST':
        return jsonify({"error": "Method Not Allowed"}), 405

    data = request.get_json()
    if not data:
        logger.error("No data provided in request")
        return jsonify({"error": "No data provided"}), 400

    logger.debug(f"Received request data: {data}")
    
    prompt = data.get('prompt')
    model = data.get('model')
    steps = min(data.get('steps', 4), 50)
    size = data.get('size', 'square')
    negative_prompt = data.get('negative_prompt', '')
    guidance = data.get('guidance', 3.5)
    output_format = data.get('output_format', 'jpeg')
    seed = data.get('seed')  # استرجاع قيمة seed من الطلب

    if not prompt or not model:
        logger.error("Prompt or model missing")
        return jsonify({"error": "Prompt and model are required!"}), 400
    if steps < 1:
        logger.error("Invalid steps value")
        return jsonify({"error": "Steps must be at least 1!"}), 400
    if model not in SUPPORTED_MODELS:
        logger.error(f"Unsupported model: {model}")
        return jsonify({"error": f"Model '{model}' is not supported. Supported models: {SUPPORTED_MODELS}"}), 400

    width, height = SIZE_OPTIONS.get(size, (1024, 1024))
    payload = {
        "prompt": prompt,
        "model": model,
        "steps": steps,
        "height": height,
        "width": width,
        "guidance": guidance,
        "output_format": output_format,
        "response_format": "url"
    }
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt
    if seed:
        payload["seed"] = int(seed)

    try:
        result = fetch_image(payload)
        logger.debug(f"API response: {result}")
        if "data" in result and result["data"]:
            image_url = result["data"][0]["url"]
            image_filename = f"generated_image_{os.urandom(4).hex()}.{output_format}"
            image_path = save_compressed_image(image_url, image_filename)
            return jsonify({"image_path": image_path})
        else:
            logger.error("No image data in API response")
            return jsonify({"error": "Failed to generate image: No data returned"}), 502
    except requests.exceptions.HTTPError as e:
        error_msg = f"API request failed: {e.response.status_code} - {e.response.text}"
        logger.error(error_msg)
        if e.response.status_code == 404:
            return jsonify({"error": "Image generation API not found. Please check the API endpoint or model."}), 502
        return jsonify({"error": error_msg}), 502
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    cache.clear()
    logger.info("Cache cleared successfully")
    return jsonify({"message": "Cache cleared successfully"}), 200

@app.route('/static/images/<filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)