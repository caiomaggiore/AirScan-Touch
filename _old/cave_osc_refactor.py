from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server
import pyautogui
import time
import tkinter as tk
import json
from threading import Event

# Disable PyAutoGUI failsafe
pyautogui.FAILSAFE = False

# Screen dimensions
screen_width, screen_height = pyautogui.size()

# AirScan configuration
AIRSCAN_PORT = 8082  # Porta padrão do AirScan
DEFAULT_AIRSCAN_WIDTH = 1920  # Resolução padrão 1080p
DEFAULT_AIRSCAN_HEIGHT = 1080

# Calibration data
calibration_data = {
    "points": {},
    "screen": {"width": screen_width, "height": screen_height},
    "airscan": {
        "width": DEFAULT_AIRSCAN_WIDTH,
        "height": DEFAULT_AIRSCAN_HEIGHT,
        "port": AIRSCAN_PORT
    }
}

# Calibration state
calibrating = False
calibration_point_index = 0
calibration_complete = Event()

class CalibrationOverlay:
    def __init__(self):
        try:
            self.root = tk.Toplevel()  # Use Toplevel instead of Tk
            self.root.title("AirScan Calibration")
            self.root.attributes('-alpha', 0.7)  # 70% de opacidade
            self.root.attributes('-topmost', True)
            self.root.attributes('-fullscreen', True)
            self.root.configure(background='black')
            
            # Prevent window from being destroyed when clicking X
            self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
            
            # Limpar apenas os pontos de calibração
            global calibration_data
            calibration_data["points"] = {}
            
            # Canvas setup
            self.canvas = tk.Canvas(self.root, highlightthickness=0, bg='black')
            self.canvas.pack(fill='both', expand=True)
            
            # Define calibration points with larger margins
            margin = 100
            self.points = [
                {"x": margin, "y": margin, "name": "TOP_LEFT"},
                {"x": screen_width - margin, "y": margin, "name": "TOP_RIGHT"},
                {"x": screen_width - margin, "y": screen_height - margin, "name": "BOTTOM_RIGHT"},
                {"x": margin, "y": screen_height - margin, "name": "BOTTOM_LEFT"},
                {"x": screen_width // 2, "y": screen_height // 2, "name": "CENTER"}
            ]
            
            # Instructions text
            self.canvas.create_text(
                screen_width // 2, 50,
                text="Click each numbered point in sequence to calibrate\nPress ESC to cancel",
                fill='white',
                font=('Arial', 14),
                justify=tk.CENTER
            )
            
            self.draw_points()
            self.root.bind('<Escape>', lambda e: self.cleanup())
            
            # Force an initial update
            self.root.update()
        except Exception as e:
            print(f"[ERROR] Failed to create calibration window: {e}")
            self.cleanup()
    
    def draw_points(self):
        self.canvas.delete("points", "numbers")
        # Draw points and numbers
        for i, point in enumerate(self.points):
            # Current point in red, others in gray
            color = 'red' if i == calibration_point_index else 'gray'
            # Larger points for better visibility
            self.canvas.create_oval(
                point["x"] - 15, point["y"] - 15,
                point["x"] + 15, point["y"] + 15,
                fill=color, tags="points"
            )
            # Number above point
            self.canvas.create_text(
                point["x"], point["y"] - 30,
                text=str(i + 1),
                fill='white',
                font=('Arial', 16, 'bold'),
                tags="numbers"
            )
    
    def cleanup(self):
        """Clean up calibration window"""
        global calibrating, calibration_window
        
        try:
            self.root.destroy()
        except:
            pass
        
        calibrating = False
        calibration_window = None
        calibration_complete.set()
    
    def update(self):
        """Update calibration window"""
        try:
            if hasattr(self, 'root') and self.root.winfo_exists():
                self.draw_points()
                self.root.update()
                self.root.lift()  # Keep window on top
        except tk.TclError:
            self.cleanup()

calibration_window = None

# Globals
mouse_pressed = False
norm_x = None
norm_y = None


# ---------------- OSC HANDLERS ---------------- #

def map_range(value, in_min, in_max, out_min, out_max):
    """Map a value from one range to another"""
    # Prevent division by zero
    if in_max == in_min:
        return out_min
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def get_calibrated_coordinates(x, y):
    """Convert AirScan coordinates to screen coordinates using calibration data"""
    if calibration_data.get("points"):
        try:
            # Use calibration data
            x_values = [p["airscan"]["x"] for p in calibration_data["points"].values()]
            y_values = [p["airscan"]["y"] for p in calibration_data["points"].values()]
            
            min_x, max_x = min(x_values), max(x_values)
            min_y, max_y = min(y_values), max(y_values)
            
            # Use map_range with bounds checking
            screen_x = map_range(x, min_x, max_x, 0, screen_width)
            screen_y = map_range(y, min_y, max_y, 0, screen_height)
            
            return (int(screen_x), int(screen_y))
        except (KeyError, ValueError) as e:
            print(f"Error in calibration mapping: {e}")
            # Fall back to default mapping
            airscan_width = calibration_data["airscan"]["width"]
            airscan_height = calibration_data["airscan"]["height"]
            return (
                int((x / airscan_width) * screen_width),
                int((y / airscan_height) * screen_height)
            )
    else:
        # Use default mapping with 1080p resolution
        airscan_width = calibration_data["airscan"]["width"]
        airscan_height = calibration_data["airscan"]["height"]
        return (
            int((x / airscan_width) * screen_width),
            int((y / airscan_height) * screen_height)
        )

def start_calibration():
    global calibrating, calibration_window, calibration_point_index
    
    # Cleanup any existing calibration window
    if calibration_window:
        try:
            calibration_window.cleanup()
        except:
            pass
    
    calibrating = True
    calibration_point_index = 0
    calibration_data["points"] = {}
    
    try:
        calibration_window = CalibrationOverlay()
        # Força a atualização da janela
        calibration_window.root.update()
        print("Janela de calibração iniciada!")
    except Exception as e:
        print(f"[ERROR] Failed to start calibration: {e}")
        calibrating = False
        calibration_window = None

def save_calibration():
    with open('calibration_data.json', 'w') as f:
        json.dump(calibration_data, f, indent=2)
    print("Calibração salva!")

def update_mouse_position():
    global calibrating, calibration_window
    if norm_x is not None and norm_y is not None:
        try:
            pixel_x, pixel_y = get_calibrated_coordinates(norm_x, norm_y)
            print(f"[MOVE] AirScan({norm_x}, {norm_y}) -> Screen({pixel_x}, {pixel_y})")
            
            # Only move mouse if not currently calibrating or if calibration window exists
            if not calibrating or (calibration_window and hasattr(calibration_window, 'root') 
                and calibration_window.root.winfo_exists()):
                pyautogui.moveTo(pixel_x, pixel_y)
        except Exception as e:
            print(f"[ERROR] Failed to update mouse position: {e}")

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
    """Handles Z input as mouse button state"""
    global mouse_pressed, calibrating, calibration_point_index, calibration_window, norm_x, norm_y
    
    # Tempo mínimo de pressão para calibração (em segundos)
    HOLD_TIME = 1.0
    
    if calibrating:
        if z == 1:  # Início do clique
            if calibration_window and norm_x is not None and norm_y is not None:
                mouse_pressed = True
                calibration_window.press_start_time = time.time()
                print("Segure o toque para calibrar...")
                
        elif z == 0 and mouse_pressed:  # Fim do clique
            mouse_pressed = False
            if hasattr(calibration_window, 'press_start_time'):
                hold_duration = time.time() - calibration_window.press_start_time
                
                if hold_duration >= HOLD_TIME:  # Se segurou por tempo suficiente
                    point = calibration_window.points[calibration_point_index]
                    
                    # Store calibration data
                    calibration_data["points"][point["name"]] = {
                        "screen": {"x": point["x"], "y": point["y"]},
                        "airscan": {"x": norm_x, "y": norm_y}
                    }
                    print(f"Ponto {calibration_point_index + 1} calibrado: {point['name']}")
                    print(f"Tela: ({point['x']}, {point['y']})")
                    print(f"AirScan: ({norm_x}, {norm_y})")
                    
                    # Move to next point
                    calibration_point_index += 1
                    
                    # Check if calibration is complete
                    if calibration_point_index >= len(calibration_window.points):
                        save_calibration()
                        calibration_window.cleanup()
                        calibrating = False
                        calibration_window = None
                        print("Calibração concluída!")
                    else:
                        calibration_window.update()
                        print(f"Mova para o ponto {calibration_point_index + 1}")
                else:
                    print("Toque muito rápido. Segure por mais tempo para calibrar.")
    else:
        # Normal mouse operation
        if z == 1 and not mouse_pressed:
            pyautogui.mouseDown()
            mouse_pressed = True
            print("[CLICK] Mouse down")
        elif z == 0 and mouse_pressed:
            pyautogui.mouseUp()
            mouse_pressed = False
            print("[CLICK] Mouse up")


# ---------------- SERVER SETUP ---------------- #

class AirScanServer:
    def __init__(self):
        self.server = None
        self.running = False
        self.dispatcher = Dispatcher()
        self.setup_dispatcher()
    
    def setup_dispatcher(self):
        """Configure OSC message handlers"""
        self.dispatcher.map("/airscan/blob/6/x", move_mouse_x)
        self.dispatcher.map("/airscan/blob/6/y", move_mouse_y)
        self.dispatcher.map("/airscan/blob/6/z", click_down)
    
    def start(self):
        """Start the OSC server"""
        if self.running:
            return
        
        try:
            import keyboard
            def on_shift_c():
                global calibrating
                if not calibrating and keyboard.is_pressed('shift'):
                    print("\nIniciando calibração...")
                    start_calibration()
            
            keyboard.on_press_key('c', lambda _: on_shift_c())
            print("Pressione Shift+C para iniciar a calibração")
        except ImportError:
            print("Módulo keyboard não disponível - calibração deve ser iniciada manualmente")
        
        ip = "0.0.0.0"
        port = AIRSCAN_PORT
        
        print(f"\nIniciando servidor AirScan...")
        print(f"Escutando mensagens OSC em {ip}:{port}")
        
        try:
            self.server = osc_server.ThreadingOSCUDPServer((ip, port), self.dispatcher)
            self.running = True
            print(f"\nServidor iniciado: OSCUDP rodando em {ip}:{port}")
            print("Use Ctrl+C para encerrar")
            self.server.serve_forever()
        except Exception as e:
            print(f"\nErro ao iniciar servidor: {e}")
            self.running = False
    
    def stop(self):
        """Stop the OSC server"""
        if self.server and self.running:
            self.running = False
            try:
                self.server.shutdown()
                self.server.server_close()
                print("\nServidor encerrado corretamente.")
            except Exception as e:
                print(f"\nErro ao encerrar servidor: {e}")

def start_server():
    """Start the OSC server in a separate thread"""
    server = AirScanServer()
    server.start()

class AirScanApplication:
    def __init__(self):
        self.server = None
        self.root = None
        self.load_config()
        
    def load_config(self):
        """Load or create configuration"""
        global calibration_data
        
        default_config = {
            "points": {},
            "screen": {"width": screen_width, "height": screen_height},
            "airscan": {
                "width": DEFAULT_AIRSCAN_WIDTH,
                "height": DEFAULT_AIRSCAN_HEIGHT,
                "port": AIRSCAN_PORT
            }
        }
        
        calibration_data = default_config.copy()
        
        try:
            with open('calibration_data.json', 'r') as f:
                saved_data = json.load(f)
                if "points" in saved_data:
                    calibration_data["points"] = saved_data["points"]
                    print("Dados de calibração carregados!")
                else:
                    print("Arquivo de calibração encontrado, mas sem pontos válidos.")
        except FileNotFoundError:
            print("Nenhum dado de calibração encontrado. Pressione Shift+C para calibrar.")
        except json.JSONDecodeError:
            print("Arquivo de calibração corrompido. Usando configuração padrão.")
    
    def start(self):
        """Initialize and start the application"""
        # Create root window
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Create and start server
        import threading
        self.server = AirScanServer()
        server_thread = threading.Thread(target=self.server.start)
        server_thread.daemon = True
        server_thread.start()
        
        # Setup periodic UI updates
        def update():
            try:
                if calibration_window and hasattr(calibration_window, 'root'):
                    try:
                        if calibration_window.root.winfo_exists():
                            calibration_window.update()
                        else:
                            global calibrating
                            calibrating = False
                    except tk.TclError:
                        pass
                self.root.after(100, update)
            except Exception as e:
                print(f"[ERROR] Update error: {e}")
        
        # Start update loop
        self.root.after(0, update)
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.cleanup()
        except Exception as e:
            print(f"[ERROR] Main loop error: {e}")
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        global calibration_window, calibrating
        
        print("\nEncerrando aplicação...")
        
        if calibration_window:
            try:
                calibration_window.cleanup()
            except:
                pass
            calibration_window = None
            calibrating = False
        
        if self.server:
            self.server.stop()
        
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass

def main():
    app = AirScanApplication()
    app.start()

if __name__ == "__main__":
    main()
