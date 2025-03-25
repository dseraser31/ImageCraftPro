from flask import Flask, render_template, request, send_from_directory, jsonify
import requests
import os

app = Flask(__name__)

API_URL = "https://api.together.xyz/v1/images/generations"
API_KEY = "e0dd9f3efcee4494b30979d8142fa5433d9712b4f1e3c09a2045043fe35f06f3"
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_image():
    if request.method != 'POST':
        return jsonify({"error": "Method Not Allowed"}), 405

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    prompt = data.get('prompt')
    model = data.get('model')
    steps = min(data.get('steps', 4), 4)
    size = data.get('size', 'square')
    negative_prompt = data.get('negative_prompt', '')
    guidance = data.get('guidance', 3.5)
    output_format = data.get('output_format', 'jpeg')

    if not prompt or not model:
        return jsonify({"error": "الوصف (prompt) والنموذج (model) مطلوبان!"}), 400
    if steps < 1:
        return jsonify({"error": "عدد الخطوات يجب أن يكون بين 1 و4!"}), 400

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

    try:
        response = requests.post(API_URL, json=payload, headers=HEADERS)
        response.raise_for_status()

        result = response.json()
        if "data" in result and len(result["data"]) > 0:
            image_data = result["data"][0]
            if "url" in image_data:
                image_response = requests.get(image_data["url"])
                image_filename = f"generated_image_{os.urandom(4).hex()}.{output_format}"  # اسم فريد لكل صورة
                image_full_path = os.path.join(IMAGE_FOLDER, image_filename)
                with open(image_full_path, "wb") as f:
                    f.write(image_response.content)
                return jsonify({"image_path": f"images/{image_filename}"})
            else:
                return jsonify({"error": "لم يتم العثور على بيانات الصورة"}), 500
        else:
            return jsonify({"error": "فشل في توليد الصورة"}), 500

    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"خطأ في الاتصال بالـ API: {response.text}"}), 500
    except Exception as e:
        return jsonify({"error": f"حدث خطأ: {str(e)}"}), 500

@app.route('/static/images/<filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)