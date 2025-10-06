from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server
import pyautogui
import json
import subprocess
import sys
import os
import time
import threading
from threading import Event

# Disable PyAutoGUI failsafe
pyautogui.FAILSAFE = False

# Screen dimensions
screen_width, screen_height = pyautogui.size()

# AirScan configuration
AIRSCAN_PORT = 8082
DEFAULT_AIRSCAN_WIDTH = 1920
DEFAULT_AIRSCAN_HEIGHT = 1080

class AirScanControl:
    def __init__(self):
        self.server = None
        self.running = True
        self.mouse_pressed = False
        self.norm_x = None
        self.norm_y = None
        self.calibration_data = self.load_calibration()
        self.calibration_process = None
        self.calibration_complete = Event()
        self.last_log_time = 0
        self.log_interval = 0.5  # 500ms
        self.last_warning_time = 0
        self.warning_interval = 1.0  # 1 segundo
    
    def load_calibration(self):
        """Load calibration data from file"""
        default_config = {
            "points": {},
            "screen": {"width": screen_width, "height": screen_height},
            "airscan": {
                "width": DEFAULT_AIRSCAN_WIDTH,
                "height": DEFAULT_AIRSCAN_HEIGHT,
                "port": AIRSCAN_PORT
            }
        }
        
        try:
            with open('calibration_data.json', 'r') as f:
                data = json.load(f)
                if "points" in data and data["points"]:
                    print(f"[INFO] Dados de calibração carregados: {len(data['points'])} pontos")
                    return data
                print("[WARNING] Arquivo de calibração encontrado, mas sem pontos válidos.")
        except FileNotFoundError:
            print("[INFO] Nenhum arquivo de calibração encontrado. Usando configuração padrão.")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Erro ao decodificar arquivo de calibração: {e}")
        except Exception as e:
            print(f"[ERROR] Erro inesperado ao carregar calibração: {e}")
        
        return default_config
    
    def map_range(self, value, in_min, in_max, out_min, out_max):
        """Map a value from one range to another"""
        if in_max == in_min:
            return out_min
        return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    
    def get_calibrated_coordinates(self, x, y):
        """Convert AirScan coordinates to screen coordinates using calibration data"""
        if not self.calibration_data.get("points"):
            current_time = time.time()
            if current_time - self.last_warning_time >= self.warning_interval:
                print("[WARNING] Nenhum dado de calibração disponível. Usando mapeamento padrão.")
                self.last_warning_time = current_time
            return self.get_default_coordinates(x, y)
        
        try:
            x_values = [p["airscan"]["x"] for p in self.calibration_data["points"].values()]
            y_values = [p["airscan"]["y"] for p in self.calibration_data["points"].values()]
            
            if not x_values or not y_values:
                current_time = time.time()
                if current_time - self.last_warning_time >= self.warning_interval:
                    print("[WARNING] Dados de calibração vazios. Usando mapeamento padrão.")
                    self.last_warning_time = current_time
                return self.get_default_coordinates(x, y)
            
            min_x, max_x = min(x_values), max(x_values)
            min_y, max_y = min(y_values), max(y_values)
            
            # Validate ranges
            if min_x == max_x or min_y == max_y:
                current_time = time.time()
                if current_time - self.last_warning_time >= self.warning_interval:
                    print("[WARNING] Dados de calibração inválidos (ranges iguais). Usando mapeamento padrão.")
                    self.last_warning_time = current_time
                return self.get_default_coordinates(x, y)
            
            screen_x = self.map_range(x, min_x, max_x, 0, screen_width)
            screen_y = self.map_range(y, min_y, max_y, 0, screen_height)
            
            # Clamp coordinates to screen bounds
            screen_x = max(0, min(screen_width, screen_x))
            screen_y = max(0, min(screen_height, screen_y))
            
            return (int(screen_x), int(screen_y))
            
        except (KeyError, ValueError, TypeError) as e:
            print(f"[ERROR] Erro no mapeamento de calibração: {e}")
            return self.get_default_coordinates(x, y)
        except Exception as e:
            print(f"[ERROR] Erro inesperado no mapeamento: {e}")
            return self.get_default_coordinates(x, y)
    
    def get_default_coordinates(self, x, y):
        """Get default coordinate mapping without calibration"""
        return (
            int((x / DEFAULT_AIRSCAN_WIDTH) * screen_width),
            int((y / DEFAULT_AIRSCAN_HEIGHT) * screen_height)
        )
    
    def update_mouse_position(self):
        """Update mouse position based on AirScan coordinates"""
        if self.norm_x is not None and self.norm_y is not None:
            try:
                pixel_x, pixel_y = self.get_calibrated_coordinates(self.norm_x, self.norm_y)
                pyautogui.moveTo(pixel_x, pixel_y)
                
                # Log coordinates with throttling (500ms)
                current_time = time.time()
                if current_time - self.last_log_time >= self.log_interval:
                    print(f"[AIRSCAN] X:{self.norm_x:.2f} Y:{self.norm_y:.2f} -> Tela({pixel_x}, {pixel_y})")
                    self.last_log_time = current_time
                    
            except Exception as e:
                print(f"[ERROR] Failed to update mouse position: {e}")
    
    def handle_mouse_x(self, unused_addr, x):
        """Handle X coordinate from AirScan"""
        self.norm_x = x
        # Write coordinates to temp file for calibration process
        self.write_coordinates_to_temp()
        self.update_mouse_position()
    
    def handle_mouse_y(self, unused_addr, y):
        """Handle Y coordinate from AirScan"""
        self.norm_y = y
        # Write coordinates to temp file for calibration process
        self.write_coordinates_to_temp()
        self.update_mouse_position()
    
    def write_coordinates_to_temp(self):
        """Write current coordinates to temporary file for calibration"""
        if self.norm_x is not None and self.norm_y is not None:
            try:
                with open("airscan_coords.tmp", "w") as f:
                    json.dump({"x": self.norm_x, "y": self.norm_y}, f)
            except Exception as e:
                print(f"[WARNING] Failed to write coordinates to temp file: {e}")
    
    def handle_mouse_click(self, unused_addr, z):
        """Handle click state from AirScan"""
        if z == 1 and not self.mouse_pressed:
            pyautogui.mouseDown()
            self.mouse_pressed = True
        elif z == 0 and self.mouse_pressed:
            pyautogui.mouseUp()
            self.mouse_pressed = False
    
    def start_calibration(self):
        """Launch calibration tool"""
        try:
            # Cleanup any existing calibration process
            if self.calibration_process and self.calibration_process.poll() is None:
                print("Finalizando processo de calibração anterior...")
                self.calibration_process.terminate()
                self.calibration_process.wait()
            
            # Stop the main server temporarily
            if self.server:
                print("[CALIBRAÇÃO] Parando servidor principal para calibração...")
                self.server.shutdown()
                self.server = None
            
            # Save current directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            calibration_script = os.path.join(current_dir, "airscan_calibration.py")
            
            # Launch calibration in a new process
            self.calibration_process = subprocess.Popen([sys.executable, calibration_script])
            print("Ferramenta de calibração iniciada!")
            
            # Monitor calibration process
            self.monitor_calibration()
            
        except Exception as e:
            print(f"[ERROR] Failed to start calibration: {e}")
    
    def monitor_calibration(self):
        """Monitor calibration process and reload data when complete"""
        def monitor():
            if self.calibration_process:
                self.calibration_process.wait()
                
                # Check if calibration was cancelled
                cancelled = os.path.exists('calibration_cancelled.flag')
                if cancelled:
                    print("[CALIBRAÇÃO] Calibração cancelada pelo usuário.")
                    try:
                        os.remove('calibration_cancelled.flag')
                    except:
                        pass
                else:
                    print("Processo de calibração finalizado. Recarregando dados...")
                    self.calibration_data = self.load_calibration()
                
                self.calibration_complete.set()
                
                # Always restart the main server
                print("[CALIBRAÇÃO] Reiniciando servidor principal...")
                self.restart_server()
        
        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
    
    def restart_server(self):
        """Restart the main OSC server"""
        try:
            # Setup OSC dispatcher
            dispatcher = Dispatcher()
            dispatcher.map("/airscan/blob/6/x", self.handle_mouse_x)
            dispatcher.map("/airscan/blob/6/y", self.handle_mouse_y)
            dispatcher.map("/airscan/blob/6/z", self.handle_mouse_click)
            
            # Start OSC server
            self.server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", AIRSCAN_PORT), dispatcher)
            print(f"[INFO] Servidor AirScan reiniciado em 0.0.0.0:{AIRSCAN_PORT}")
            
            # Start server in background thread
            server_thread = threading.Thread(target=self.server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
        except Exception as e:
            print(f"[ERROR] Erro ao reiniciar servidor: {e}")
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        try:
            import keyboard
            keyboard.on_press_key('c', lambda _: 
                self.start_calibration() if keyboard.is_pressed('shift') else None)
            print("Pressione Shift+C para iniciar a calibração")
        except ImportError:
            print("Módulo keyboard não disponível")
    
    def start(self):
        """Start the AirScan control server"""
        print("=" * 50)
        print("AIRSCAN CONTROL - INICIANDO")
        print("=" * 50)
        
        # Setup OSC dispatcher
        dispatcher = Dispatcher()
        dispatcher.map("/airscan/blob/6/x", self.handle_mouse_x)
        dispatcher.map("/airscan/blob/6/y", self.handle_mouse_y)
        dispatcher.map("/airscan/blob/6/z", self.handle_mouse_click)
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Display calibration status
        if self.calibration_data.get("points"):
            print(f"[INFO] Calibração ativa: {len(self.calibration_data['points'])} pontos")
        else:
            print("[WARNING] Nenhuma calibração encontrada. Pressione Shift+C para calibrar.")
        
        # Start OSC server
        try:
            self.server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", AIRSCAN_PORT), dispatcher)
            print(f"\n[INFO] Servidor AirScan iniciado em 0.0.0.0:{AIRSCAN_PORT}")
            print("[INFO] Use Ctrl+C para encerrar")
            print("[INFO] Use Shift+C para iniciar calibração")
            print("-" * 50)
            
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            print("\n[INFO] Interrupção detectada. Encerrando servidor...")
        except OSError as e:
            if e.errno == 10048:  # Port already in use
                print(f"\n[ERROR] Porta {AIRSCAN_PORT} já está em uso. Tente fechar outros processos.")
            else:
                print(f"\n[ERROR] Erro de rede: {e}")
        except Exception as e:
            print(f"\n[ERROR] Erro inesperado ao iniciar servidor: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        print("[INFO] Limpando recursos...")
        self.running = False
        
        if self.calibration_process and self.calibration_process.poll() is None:
            print("[INFO] Finalizando processo de calibração...")
            self.calibration_process.terminate()
            try:
                self.calibration_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.calibration_process.kill()
        
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except:
                pass
        
        print("[INFO] Limpeza concluída.")

if __name__ == "__main__":
    control = AirScanControl()
    control.start()