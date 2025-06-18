# Add to top of views.py
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow warnings

from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators import gzip
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import FanSettings

import cv2
import mediapipe as mp
import serial
import time
import math
import numpy as np

# Initialize global variables
cap = cv2.VideoCapture(0)
mpHands = mp.solutions.hands
hands = mpHands.Hands(static_image_mode=False, max_num_hands=1, 
                     min_detection_confidence=0.5, min_tracking_confidence=0.5)
mpDraw = mp.solutions.drawing_utils

# Speed settings
onSpeed = 155  # Medium speed when turning on
offSpeed = 0   # Speed when turning off
speed = 155    # Current speed

# Initialize serial connection
arduino_connected = False
arduino = None
try:
    arduino = serial.Serial(port='COM3', baudrate=9600, timeout=1, write_timeout=2)
    time.sleep(2)  # Wait for connection to establish
    arduino_connected = True
except Exception as e:
    print(f"Failed to connect to Arduino: {str(e)}")
    arduino_connected = False

@login_required
def fan_control(request):
    fan_settings, created = FanSettings.objects.get_or_create(user=request.user)
    return render(request, 'fan_control.html', {
        'fan_settings': fan_settings,
        'arduino_connected': arduino_connected
    })

@gzip.gzip_page
def video_feed(request):
    return StreamingHttpResponse(gen_frames(), content_type="multipart/x-mixed-replace;boundary=frame")

def gen_frames():
    global arduino, arduino_connected, onSpeed, offSpeed, speed
    
    while True:
        success, img = cap.read()
        if not success:
            break
        
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(imgRGB)
        
        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                # FUNCTION TO CALCULATE ANGLES OF FINGER
                def calculate_angle(a, b, c):
                    """Calculate the angle (in degrees) between three points (a, b, c)."""
                    ba = [a[0] - b[0], a[1] - b[1]]
                    bc = [c[0] - b[0], c[1] - b[1]]
                    
                    dot_product = ba[0] * bc[0] + ba[1] * bc[1]
                    magnitude_ba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
                    magnitude_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)

                    if magnitude_ba == 0 or magnitude_bc == 0:
                        return 0

                    cosine_angle = dot_product / (magnitude_ba * magnitude_bc)
                    cosine_angle = max(-1, min(1, cosine_angle))
                    try:
                        angle = math.degrees(math.acos(cosine_angle))
                    except ValueError:
                        angle = 0
                    return angle

                # FUNCTION FOR FINDING IF FINGERS ARE CURLED OR NOT
                def is_finger_curled(mcp, pip, dip, tip):
                    """Determine if a finger is curled based on the angles at its joints."""
                    angle_pip = calculate_angle(mcp, pip, dip)
                    angle_dip = calculate_angle(pip, dip, tip)
                    return angle_pip < 160 or angle_dip < 160

                # Function to Turn-On
                def turn_on(handLms, img_shape):
                    h, w, c = img_shape
                    
                    thumb_tip = handLms.landmark[4]
                    thumb_pip = handLms.landmark[3]
                    index_finger_tip = handLms.landmark[8]
                    index_finger_dip = handLms.landmark[7]
                    middle_finger_tip = handLms.landmark[12]
                    middle_finger_mcp = handLms.landmark[9]
                    ring_finger_tip = handLms.landmark[16]
                    ring_finger_mcp = handLms.landmark[13]
                    pinky_tip = handLms.landmark[20]
                    pinky_dip = handLms.landmark[19]

                    thumb_tip_y = int(thumb_tip.y * h)
                    thumb_pip_y = int(thumb_pip.y * h)
                    index_finger_tip_y = int(index_finger_tip.y * h)
                    index_finger_dip_y = int(index_finger_dip.y * h)
                    middle_finger_tip_y = int(middle_finger_tip.y * h)
                    middle_finger_mcp_y = int(middle_finger_mcp.y * h)
                    ring_finger_tip_y = int(ring_finger_tip.y * h)
                    ring_finger_mcp_y = int(ring_finger_mcp.y * h)
                    pinky_tip_y = int(pinky_tip.y * h)
                    pinky_dip_y = int(pinky_dip.y * h)

                    fingers = {
                        'middle': [handLms.landmark[i] for i in [9, 10, 11, 12]],
                        'ring': [handLms.landmark[i] for i in [13, 14, 15, 16]],
                    }

                    all_fingers_curled = True
                    for finger_name, landmarks in fingers.items():
                        mcp = (int(landmarks[0].x * w), int(landmarks[0].y * h))
                        pip = (int(landmarks[1].x * w), int(landmarks[1].y * h))
                        dip = (int(landmarks[2].x * w), int(landmarks[2].y * h))
                        tip = (int(landmarks[3].x * w), int(landmarks[3].y * h))
                        
                        if not is_finger_curled(mcp, pip, dip, tip):
                            all_fingers_curled = False
                            break
                        
                    if all_fingers_curled and (index_finger_dip_y > index_finger_tip_y) and (pinky_dip_y > pinky_tip_y):
                        return True
                    return False

                # Function to Turn-off
                def turn_off(handLms, img_shape):
                    h, w, c = img_shape
                    
                    thumb_tip = handLms.landmark[4]
                    thumb_pip = handLms.landmark[3]
                    index_finger_tip = handLms.landmark[8]
                    index_finger_dip = handLms.landmark[7]
                    middle_finger_tip = handLms.landmark[12]
                    middle_finger_dip = handLms.landmark[11]
                    ring_finger_tip = handLms.landmark[16]
                    ring_finger_dip = handLms.landmark[15]
                    pinky_tip = handLms.landmark[20]
                    pinky_dip = handLms.landmark[19]

                    thumb_tip_y = int(thumb_tip.y * h)
                    thumb_pip_y = int(thumb_pip.y * h)
                    index_finger_tip_y = int(index_finger_tip.y * h)
                    index_finger_dip_y = int(index_finger_dip.y * h)
                    middle_finger_tip_y = int(middle_finger_tip.y * h)
                    middle_finger_dip_y = int(middle_finger_dip.y * h)
                    ring_finger_tip_y = int(ring_finger_tip.y * h)
                    ring_finger_dip_y = int(ring_finger_dip.y * h)
                    pinky_tip_y = int(pinky_tip.y * h)
                    pinky_dip_y = int(pinky_dip.y * h)

                    fingers = {
                        'thumb': [handLms.landmark[i] for i in [1, 2, 3, 4]],
                        'index': [handLms.landmark[i] for i in [5, 6, 7, 8]],
                        'middle': [handLms.landmark[i] for i in [9, 10, 11, 12]],
                        'ring': [handLms.landmark[i] for i in [13, 14, 15, 16]],
                        'pinky': [handLms.landmark[i] for i in [17, 18, 19, 20]],
                    }

                    all_fingers_curled = False
                    for finger_name, landmarks in fingers.items():
                        mcp = (int(landmarks[0].x * w), int(landmarks[0].y * h))
                        pip = (int(landmarks[1].x * w), int(landmarks[1].y * h))
                        dip = (int(landmarks[2].x * w), int(landmarks[2].y * h))
                        tip = (int(landmarks[3].x * w), int(landmarks[3].y * h))
                        
                        if not is_finger_curled(mcp, pip, dip, tip):
                            all_fingers_curled = True
                            break

                    if all_fingers_curled and (thumb_tip_y < thumb_pip_y) and (index_finger_tip_y < index_finger_dip_y) and (middle_finger_tip_y < middle_finger_dip_y) and (ring_finger_tip_y < ring_finger_dip_y) and (pinky_tip_y < pinky_dip_y):
                        return True
                    return False

                # Function to speed down
                def speed_down(handLms, img_shape):
                    h, w, c = img_shape
                    
                    thumb_tip = handLms.landmark[4]
                    thumb_mcp = handLms.landmark[2]
                    index_finger_tip = handLms.landmark[8]
                    middle_finger_tip = handLms.landmark[12]
                    ring_finger_tip = handLms.landmark[16]
                    pinky_tip = handLms.landmark[20]

                    thumb_tip_y = int(thumb_tip.y * h)
                    thumb_mcp_y = int(thumb_mcp.y * h)
                    index_finger_tip_y = int(index_finger_tip.y * h)
                    middle_finger_tip_y = int(middle_finger_tip.y * h)
                    ring_finger_tip_y = int(ring_finger_tip.y * h)
                    pinky_tip_y = int(pinky_tip.y * h)

                    fingers = {
                        'index': [handLms.landmark[i] for i in [5, 6, 7, 8]],
                        'middle': [handLms.landmark[i] for i in [9, 10, 11, 12]],
                        'ring': [handLms.landmark[i] for i in [13, 14, 15, 16]],
                        'pinky': [handLms.landmark[i] for i in [17, 18, 19, 20]],
                    }

                    all_fingers_curled = True
                    for finger_name, landmarks in fingers.items():
                        mcp = (int(landmarks[0].x * w), int(landmarks[0].y * h))
                        pip = (int(landmarks[1].x * w), int(landmarks[1].y * h))
                        dip = (int(landmarks[2].x * w), int(landmarks[2].y * h))
                        tip = (int(landmarks[3].x * w), int(landmarks[3].y * h))
                        
                        if not is_finger_curled(mcp, pip, dip, tip):
                            all_fingers_curled = False
                            break

                    if all_fingers_curled and (thumb_tip_y > thumb_mcp_y) and (index_finger_tip_y < thumb_mcp_y) and (middle_finger_tip_y < thumb_mcp_y) and (ring_finger_tip_y < thumb_mcp_y) and (pinky_tip_y < thumb_mcp_y):
                        return True
                    return False

                # Function to speed-up
                def speed_up(handLms, img_shape):
                    h, w, c = img_shape
                    
                    thumb_tip = handLms.landmark[4]
                    thumb_mcp = handLms.landmark[2]
                    index_finger_tip = handLms.landmark[8]
                    middle_finger_tip = handLms.landmark[12]
                    ring_finger_tip = handLms.landmark[16]
                    pinky_tip = handLms.landmark[20]

                    thumb_tip_y = int(thumb_tip.y * h)
                    thumb_mcp_y = int(thumb_mcp.y * h)
                    index_finger_tip_y = int(index_finger_tip.y * h)
                    middle_finger_tip_y = int(middle_finger_tip.y * h)
                    ring_finger_tip_y = int(ring_finger_tip.y * h)
                    pinky_tip_y = int(pinky_tip.y * h)

                    fingers = {
                        'index': [handLms.landmark[i] for i in [5, 6, 7, 8]],
                        'middle': [handLms.landmark[i] for i in [9, 10, 11, 12]],
                        'ring': [handLms.landmark[i] for i in [13, 14, 15, 16]],
                        'pinky': [handLms.landmark[i] for i in [17, 18, 19, 20]],
                    }

                    all_fingers_curled = True
                    for finger_name, landmarks in fingers.items():
                        mcp = (int(landmarks[0].x * w), int(landmarks[0].y * h))
                        pip = (int(landmarks[1].x * w), int(landmarks[1].y * h))
                        dip = (int(landmarks[2].x * w), int(landmarks[2].y * h))
                        tip = (int(landmarks[3].x * w), int(landmarks[3].y * h))
                        
                        if not is_finger_curled(mcp, pip, dip, tip):
                            all_fingers_curled = False
                            break

                    if all_fingers_curled and (thumb_tip_y < thumb_mcp_y) and (index_finger_tip_y > thumb_mcp_y) and (middle_finger_tip_y > thumb_mcp_y) and (ring_finger_tip_y > thumb_mcp_y) and (pinky_tip_y > thumb_mcp_y):
                        return True
                    return False

                # Methods to Decrease Speed
                def decrease_speed():
                    global speed
                    if speed > 0:
                        speed -= 50
                        speed = max(speed, 0)
                    return speed

                # Methods to Increase Speed
                def increase_speed():
                    global speed
                    if speed < 255:
                        speed += 50
                        speed = min(speed, 255)
                    return speed

                # Gesture detection and handling
                img_shape = img.shape

                if turn_on(handLms, img_shape):
                    current_gesture = "Turn On Fan & Speed Set to Medium"
                    cv2.putText(img, str('Turn On'), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 223, 0), 2)
                    if arduino_connected:
                        try:
                            arduino.write(b'1')
                            arduino.write(str(onSpeed).encode())
                            print("=========================================")
                            print(current_gesture)
                            print(f"Sent {onSpeed} to Arduino")

                            time.sleep(1)
                            response = arduino.readline().decode('utf-8').strip()
                            if response:
                                print("Arduino response: Speed set to Medium")
                                print("=========================================")
                            else:
                                print("No response from Arduino")
                                print("=========================================")
                        except Exception as e:
                            print(f"Error communicating with Arduino: {str(e)}")
                            arduino_connected = False

                elif turn_off(handLms, img_shape):
                    current_gesture = "Turn Off Fan & Speed Set to speed Zero"
                    cv2.putText(img, str('Turn Off'), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 223, 0), 2)
                    if arduino_connected:
                        try:
                            arduino.write(b'0')
                            arduino.write(str(offSpeed).encode())
                            print("=========================================")
                            print(current_gesture)
                            print(f"Sent {offSpeed} to Arduino")

                            time.sleep(1)
                            response = arduino.readline().decode('utf-8').strip()
                            if response:
                                print("Arduino response: Speed set to Zero")
                                print("=========================================")
                            else:
                                print("No response from Arduino")
                                print("=========================================")
                        except Exception as e:
                            print(f"Error communicating with Arduino: {str(e)}")
                            arduino_connected = False

                elif speed_down(handLms, img_shape):
                    current_gesture = "Decrease Speed"
                    cv2.putText(img, str('Decrease Speed'), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 223, 0), 2)
                    if arduino_connected:
                        try:
                            arduino.write(b'2')
                            if speed > 0:
                                speed = decrease_speed()
                                arduino.write(str(speed).encode())
                                print("=========================================")
                                print(current_gesture)
                                print(f"Sent {speed} to Arduino")

                                time.sleep(1)
                                response = arduino.readline().decode('utf-8').strip()
                                if response:
                                    print("Arduino response: Speed decreased")
                                    print("=========================================")
                                else:
                                    print("No response from Arduino")
                                    print("=========================================")
                        except Exception as e:
                            print(f"Error communicating with Arduino: {str(e)}")
                            arduino_connected = False

                elif speed_up(handLms, img_shape):
                    current_gesture = "Medium Speed"
                    cv2.putText(img, str('Increase Speed'), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 223, 0), 2)
                    if arduino_connected:
                        try:
                            arduino.write(b'3')
                            if speed < 255:
                                speed = increase_speed()
                                arduino.write(str(speed).encode())
                                print("=========================================")
                                if speed == 255:
                                    current_gesture = "Max Speed"
                                print(current_gesture)
                                print(f"Sent {speed} to Arduino")

                                time.sleep(1)
                                response = arduino.readline().decode('utf-8').strip()
                                if response:
                                    print("Arduino response: Speed increased")
                                    print("=========================================")
                                else:
                                    print("No response from Arduino")
                                    print("=========================================")
                        except Exception as e:
                            print(f"Error communicating with Arduino: {str(e)}")
                            arduino_connected = False

                # Draw hand landmarks
                for id, lm in enumerate(handLms.landmark):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.putText(img, str(id), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                
                mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)
        
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@csrf_exempt
def update_speed(request):   
    if request.method == 'POST':
        speed = int(request.POST.get('speed', 155))
        if arduino_connected:
            try:
                arduino.write(str(speed).encode())
            except Exception as e:
                print(f"Error updating speed: {str(e)}")
        fan_settings = FanSettings.objects.get(user=request.user)
        fan_settings.speed = speed
        fan_settings.save()
        return JsonResponse({'status': 'success', 'speed': speed})
    return JsonResponse({'status': 'error'})

@csrf_exempt
def toggle_power(request):
    if request.method == 'POST':
        fan_settings = FanSettings.objects.get(user=request.user)
        fan_settings.is_on = not fan_settings.is_on
        fan_settings.save()
        if arduino_connected:
            try:
                arduino.write(b'1' if fan_settings.is_on else b'0')
            except Exception as e:
                print(f"Error toggling power: {str(e)}")
        return JsonResponse({'status': 'success', 'is_on': fan_settings.is_on})
    return JsonResponse({'status': 'error'})