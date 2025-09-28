from flask import Flask, request, jsonify, render_template, send_from_directory
import threading
import os
from detector import continuous_detection
import torch
import numpy as np

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
RESULT_DIR = os.path.join(BASE_DIR, 'results')
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)

model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

color_ranges = {
    "pink": [(np.array([160, 50, 100]), np.array([170, 255, 255]))],
    "white": [(np.array([0, 0, 200]), np.array([180, 30, 255]))],
    "yellow": [(np.array([20, 100, 100]), np.array([30, 255, 255]))],
    "blue": [(np.array([100, 150, 0]), np.array([130, 255, 255]))],
    "green": [(np.array([40, 70, 70]), np.array([80, 255, 255]))],
    "light_green": [(np.array([35, 50, 70]), np.array([85, 255, 255]))],
    "purple": [(np.array([130, 50, 50]), np.array([160, 255, 255]))],
    "orange": [(np.array([10, 100, 100]), np.array([20, 255, 255]))],
    "brown": [(np.array([10, 100, 20]), np.array([20, 255, 200]))],
    "black": [(np.array([0, 0, 0]), np.array([180, 255, 50]))],
}

is_detecting = {"stop": False}
detection_thread = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_detection', methods=['POST'])
def start_detection():
    global is_detecting, detection_thread

    data = request.get_json()
    top_color = data.get("topColor", "black")
    bottom_color = data.get("bottomColor", "black")
    stream_url = "http://127.0.0.1:8000/video"  # 또는 실제 라즈베리 주소

    if detection_thread and detection_thread.is_alive():
        return jsonify({"status": "이미 탐지가 진행 중입니다."})

    is_detecting["stop"] = False
    detection_thread = threading.Thread(
        target=continuous_detection,
        args=(stream_url, top_color, bottom_color, RESULT_DIR, model, is_detecting, color_ranges)
    )
    detection_thread.start()

    return jsonify({"status": "탐지를 시작했습니다."})

@app.route('/stop_detection', methods=['POST'])
def stop_detection():
    global is_detecting
    is_detecting["stop"] = True
    return jsonify({"status": "탐지를 중단했습니다."})

@app.route('/results/<filename>')
def get_result_image(filename):
    return send_from_directory(RESULT_DIR, filename)

if __name__ == "__main__":
    app.run(debug=True)