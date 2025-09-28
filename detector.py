import cv2
import time
import os
import numpy as np

def run_detection(frame, top_color, bottom_color, model, color_ranges):
    if top_color not in color_ranges or bottom_color not in color_ranges:
        return []

    target_upper_lower_hsv = {
        "upper": color_ranges[top_color],
        "lower": color_ranges[bottom_color],
    }

    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    detections = model(img_rgb).xyxy[0].cpu().numpy()

    def get_valid_pixels(image):
        skin_lower = np.array([0, 30, 60], dtype=np.uint8)
        skin_upper = np.array([20, 150, 255], dtype=np.uint8)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        skin_mask = cv2.inRange(hsv, skin_lower, skin_upper)
        mask_inv = cv2.bitwise_not(skin_mask)
        return image[mask_inv > 0]

    def is_color_in_range(image, hsv_ranges):
        valid_pixels = get_valid_pixels(image)
        if len(valid_pixels) == 0:
            return False
        hsv_pixels = cv2.cvtColor(valid_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3)
        mask = np.zeros(len(hsv_pixels), dtype=bool)
        for lower, upper in hsv_ranges:
            in_range = np.all((hsv_pixels >= lower) & (hsv_pixels <= upper), axis=1)
            mask |= in_range
        ratio = np.sum(mask) / len(mask)
        return ratio > 0.25

    detected_persons = []

    for i, (*box, conf, cls) in enumerate(detections):
        if int(cls) != 0 or conf < 0.5:
            continue
        x1, y1, x2, y2 = map(int, box)
        if (y2 - y1) < 100:
            continue

        full_height = y2 - y1
        margin_x = int((x2 - x1) * 0.1)
        margin_y = int(full_height * 0.1)

        upper_y1 = y1 + margin_y
        upper_y2 = y1 + int(full_height * 0.45)
        lower_y1 = y1 + int(full_height * 0.45)
        lower_y2 = y2 - margin_y

        upper_img = frame[upper_y1:upper_y2, x1 + margin_x:x2 - margin_x]
        lower_img = frame[lower_y1:lower_y2, x1 + margin_x:x2 - margin_x]

        if is_color_in_range(upper_img, target_upper_lower_hsv["upper"]) and \
           is_color_in_range(lower_img, target_upper_lower_hsv["lower"]):
            crop_img = frame[y1:y2, x1:x2]
            detected_persons.append(crop_img)

    return detected_persons

def continuous_detection(stream_url, top_color, bottom_color, result_dir, model, stop_flag, color_ranges):
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        print("스트림 열기 실패")
        return

    while not stop_flag["stop"]:
        ret, frame = cap.read()
        if not ret:
            print("프레임 읽기 실패")
            break

        detected_persons = run_detection(frame, top_color, bottom_color, model, color_ranges)

        # 기존 결과 폴더 내용 삭제
        for f in os.listdir(result_dir):
            os.remove(os.path.join(result_dir, f))

        # 탐지된 사람 크롭 이미지 저장
        for i, img in enumerate(detected_persons):
            filename = f"detection_{int(time.time())}_{i}.jpg"
            cv2.imwrite(os.path.join(result_dir, filename), img)

        time.sleep(0.1)

    cap.release()

