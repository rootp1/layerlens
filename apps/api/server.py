from dotenv import load_dotenv
import os

import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
from layerlens_lint import analyze as lint_analyze

from services.dive_service import analyze_docker_image
from services.ai_service import generate_response

app = Flask(__name__)
CORS(app)

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

prompt = "You are a software engineer specializing in Containerization. You are highly skilled in analyzing and improving Docker images using tools such as Dive"

@app.route('/analyze', methods=['POST'])
def analyze_image():
    data = request.json
    try:
        image_name = data.get('image_name')
        dockerfile = data.get('dockerfile')
    except:
        return jsonify({"error": "Invalid JSON"}), 400

    if not image_name:
        return jsonify({"error": "No image_name provided"}), 400

    analysis_results = analyze_docker_image(image_name)

    # analyze_docker_image always returns a dict: either {'error': '...'} for a
    # rejected/failed scan, or the full {'image_name', 'stats', 'output'} shape.
    if 'error' in analysis_results:
        return jsonify({"error": analysis_results['error']}), 422

    string_results = str(analysis_results)
    if len(string_results) > 5000:
        # Assuming that a token is roughly equivalent to a character.
        # This might need adjustment depending on how you define a token.
        string_results = string_results[-5000:]
    print(string_results)
    response = generate_response(string_results, prompt, dockerfile)
    if response:
        return jsonify({
            "analysis": response,
            "stats": analysis_results['stats'],
            "poweredBy": "Featherless.ai"
        })
    else:
        return jsonify({"error": "The AI model failed to generate an analysis. Please try again."}), 502


@app.route('/lint', methods=['POST'])
def lint_dockerfile():
    data = request.json
    try:
        dockerfile = data.get('dockerfile')
    except:
        return jsonify({"error": "Invalid JSON"}), 400

    if not dockerfile or not dockerfile.strip():
        return jsonify({"error": "No dockerfile provided"}), 400

    result = lint_analyze(dockerfile)
    return jsonify(result.to_dict())


@app.route('/', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello, World!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
