from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server
import pyautogui
import time
import json

# Load calibration data
try:
    with open('calibration_data.json', 'r') as f:
        calibration = json.load(f)
    
    # Screen dimensions from calibration
    screen_width = calibration['screen']['width']
    screen_height = calibration['screen']['height']
    
    # Get AirScan bounds from calibration
    airscan_bounds = {
        'min_x': min(point['airscan']['x'] for point in calibration['points'].values()),
        'max_x': max(point['airscan']['x'] for point in calibration['points'].values()),
        'min_y': min(point['airscan']['y'] for point in calibration['points'].values()),
        'max_y': max(point['airscan']['y'] for point in calibration['points'].values())
    }
    
    print("Calibração carregada com sucesso!")
except FileNotFoundError:
    print("Arquivo de calibração não encontrado. Usando valores padrão.")
    # Default values if no calibration file
    screen_width, screen_height = pyautogui.size()
    airscan_bounds = {
        'min_x': 0,
        'max_x': 1792,
        'min_y': 0,
        'max_y': 1280
    }

# Globals
mouse_pressed = False
norm_x = None
norm_y = None

def map_range(value, in_min, in_max, out_min, out_max):
    """Map a value from one range to another"""
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def update_mouse_position():
    if norm_x is not None and norm_y is not None:
        # Map AirScan coordinates to screen coordinates using calibration data
        pixel_x = int(map_range(
            norm_x,
            airscan_bounds['min_x'],
            airscan_bounds['max_x'],
            0,
            screen_width
        ))
        
        pixel_y = int(map_range(
            norm_y,
            airscan_bounds['min_y'],
            airscan_bounds['max_y'],
            0,
            screen_height
        ))

        print(f"[MOVE] AirScan({norm_x}, {norm_y}) -> Screen({pixel_x}, {pixel_y})")
        pyautogui.moveTo(pixel_x, pixel_y)

def move_mouse_x(unused_addr, x):
    global norm_x
    norm_x = x
    print(f"[OSC] Received X: {x}")
    update_mouse_position()

def move_mouse_y(unused_addr, y):
    global norm_y
    norm_y = y
    print(f"[OSC] Received Y: {y}")
    update_mouse_position()

def click_down(unused_addr, z):
    global mouse_pressed
    if z == 1 and not mouse_pressed:
        pyautogui.mouseDown()
        mouse_pressed = True
        print("[CLICK] Mouse down")
    elif z == 0 and mouse_pressed:
        pyautogui.mouseUp()
        mouse_pressed = False
        print("[CLICK] Mouse up")

# OSC Server setup
dispatcher = Dispatcher()
dispatcher.map("/airscan/blob/6/x", move_mouse_x)
dispatcher.map("/airscan/blob/6/y", move_mouse_y)
dispatcher.map("/airscan/blob/6/z", click_down)

ip = "0.0.0.0"
port = 8082

server = osc_server.ThreadingOSCUDPServer((ip, port), dispatcher)
print(f"Servidor iniciado: OSCUDP rodando em {ip}:{port}")
server.serve_forever()