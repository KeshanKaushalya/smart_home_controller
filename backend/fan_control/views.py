# Add to top of views.py
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow warnings

from django.shortcuts import render, redirect  # Add this import
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



# Initialize camera and hand detection globally
cap = cv2.VideoCapture(0)
mpHands = mp.solutions.hands
hands = mpHands.Hands(static_image_mode=False, max_num_hands=1, 
                     min_detection_confidence=0.5, min_tracking_confidence=0.5)
mpDraw = mp.solutions.drawing_utils

# Initialize serial connection (modify as needed)
try:
    arduino = serial.Serial(port='COM12', baudrate=9600, timeout=1, write_timeout=2)
    time.sleep(2)
    arduino_connected = True
except:
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
    while True:
        success, img = cap.read()
        if not success:
            break
        
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(imgRGB)
        
        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                # Your gesture detection logic here
                # ...
                
                mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)
        
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@csrf_exempt
def update_speed(request):   
    if request.method == 'POST':
        speed = int(request.POST.get('speed', 155))
        # Update Arduino and database
        if arduino_connected:
            arduino.write(str(speed).encode())
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
        # Update Arduino
        if arduino_connected:
            arduino.write(b'1' if fan_settings.is_on else b'0')
        return JsonResponse({'status': 'success', 'is_on': fan_settings.is_on})
    return JsonResponse({'status': 'error'})