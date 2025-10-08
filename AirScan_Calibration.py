import tkinter as tk
import json
import time
import threading
from collections import deque
import os
import atexit
import socket
import subprocess
import sys
from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server

# Screen dimensions
import pyautogui
screen_width, screen_height = pyautogui.size()

# ====================================
# CONFIGURAÇÃO DO AIRSCAN
# ====================================
AIRSCAN_MODE = "Arena"  # Opções: "Arena" ou "Cave"
AIRSCAN_PORT = 8030

# Configurações padrão por modo
MODE_CONFIG = {
    "Arena": {
        "blob_id": 5,
        "width": 1920,
        "height": 1080
    },
    "Cave": {
        "blob_id": 6,
        "width": 1920,
        "height": 1080
    }
}

# Carrega configuração do modo selecionado
if AIRSCAN_MODE not in MODE_CONFIG:
    print(f"[ERROR] Modo '{AIRSCAN_MODE}' inválido! Use 'Arena' ou 'Cave'")
    sys.exit(1)

CURRENT_CONFIG = MODE_CONFIG[AIRSCAN_MODE]
BLOB_ID = CURRENT_CONFIG["blob_id"]
DEFAULT_AIRSCAN_WIDTH = CURRENT_CONFIG["width"]
DEFAULT_AIRSCAN_HEIGHT = CURRENT_CONFIG["height"]

print(f"[CALIBRAÇÃO] Modo selecionado: {AIRSCAN_MODE} (Blob {BLOB_ID})")

class CalibrationPoint:
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name
        self.airscan_data = {"x": deque(maxlen=500), "y": deque(maxlen=500)}
        self.start_time = None
        self.is_capturing = False
        self.last_data_time = None
        self.capture_duration = 5.0
        self.data_interruption_threshold = 0.5
        self.is_ready = True
        self.is_collecting = False
    
    def start_capture(self):
        """Start capturing data for this point"""
        self.start_time = time.time()
        self.last_data_time = self.start_time
        self.is_capturing = True
        self.is_ready = False
        self.is_collecting = True
        self.airscan_data["x"].clear()
        self.airscan_data["y"].clear()
        print(f"[CALIBRAÇÃO] Iniciando captura para {self.name}...")
    
    def add_data(self, x, y):
        """Add new coordinate data"""
        if not self.is_capturing:
            return False
            
        current_time = time.time()
        
        # Check for data interruption
        if self.last_data_time and (current_time - self.last_data_time) > self.data_interruption_threshold:
            print(f"[CALIBRAÇÃO] Interrupção detectada! Reiniciando captura para {self.name}")
            self.reset_capture()
            return False
        
        # Add data
        self.airscan_data["x"].append(x)
        self.airscan_data["y"].append(y)
        self.last_data_time = current_time
        
        # Check if we have enough continuous data
        if self.capture_complete():
            print(f"[CALIBRAÇÃO] Captura completa para {self.name}!")
            return True
            
        return True
    
    def check_interruption(self):
        """Check for data interruption and reset if needed"""
        if not self.is_capturing or not self.last_data_time:
            return False
            
        current_time = time.time()
        if (current_time - self.last_data_time) > self.data_interruption_threshold:
            print(f"[CALIBRAÇÃO] Interrupção detectada! Reiniciando captura para {self.name}")
            self.reset_capture()
            return True
        return False
    
    def get_average(self):
        """Calculate average position from captured data"""
        if not self.airscan_data["x"] or not self.airscan_data["y"]:
            return None
        
        avg_x = sum(self.airscan_data["x"]) / len(self.airscan_data["x"])
        avg_y = sum(self.airscan_data["y"]) / len(self.airscan_data["y"])
            
        return {
            "x": float(avg_x),
            "y": float(avg_y)
        }
    
    def capture_complete(self):
        """Check if we have enough continuous data (5 seconds worth)"""
        if not self.is_capturing or not self.start_time or not self.last_data_time:
            return False
        
        continuous_duration = self.last_data_time - self.start_time
        return continuous_duration >= self.capture_duration
    
    def reset_capture(self):
        """Reset capture state"""
        self.is_capturing = False
        self.is_collecting = False
        self.is_ready = True
        self.start_time = None
        self.last_data_time = None
        self.airscan_data["x"].clear()
        self.airscan_data["y"].clear()
        print(f"[CALIBRAÇÃO] Captura resetada para {self.name} - pronto para receber dados")
    
    def force_ready(self):
        """Force point to ready state"""
        self.is_capturing = False
        self.is_collecting = False
        self.is_ready = True
        self.start_time = None
        self.last_data_time = None
    
    def get_status(self):
        """Get current status for visual feedback"""
        if self.is_collecting:
            return "collecting"  # Red
        elif self.is_ready:
            return "ready"  # Green
        else:
            return "waiting"  # Yellow

class CalibrationLevelSelector:
    def __init__(self, parent):
        self.parent = parent
        self.selected_level = None
        self.levels = {
            "basic": {
                "name": "BÁSICO",
                "points": 5,
                "description": "Calibração rápida com 5 pontos",
                "time": "~25 segundos",
                "accuracy": "Boa para uso geral"
            },
            "advanced": {
                "name": "AVANÇADO", 
                "points": 9,
                "description": "Calibração precisa com 9 pontos",
                "time": "~45 segundos",
                "accuracy": "Excelente precisão"
            },
            "professional": {
                "name": "PROFISSIONAL",
                "points": 13,
                "description": "Calibração máxima com 13 pontos",
                "time": "~65 segundos", 
                "accuracy": "Precisão máxima"
            }
        }
    
    def generate_points(self, level):
        """Generate calibration points based on level"""
        if level == "basic":
            return self._generate_basic_points()
        elif level == "advanced":
            return self._generate_advanced_points()
        elif level == "professional":
            return self._generate_professional_points()
        return []
    
    def _generate_basic_points(self):
        """Generate 5 basic points (corners + center)"""
        return [
            CalibrationPoint(0, 0, "TOP_LEFT"),
            CalibrationPoint(screen_width - 1, 0, "TOP_RIGHT"),
            CalibrationPoint(screen_width - 1, screen_height - 1, "BOTTOM_RIGHT"),
            CalibrationPoint(0, screen_height - 1, "BOTTOM_LEFT"),
            CalibrationPoint(screen_width // 2, screen_height // 2, "CENTER")
        ]
    
    def _generate_advanced_points(self):
        """Generate 9 advanced points (corners + edges + center)"""
        return [
            # Corners
            CalibrationPoint(0, 0, "TOP_LEFT"),
            CalibrationPoint(screen_width - 1, 0, "TOP_RIGHT"),
            CalibrationPoint(screen_width - 1, screen_height - 1, "BOTTOM_RIGHT"),
            CalibrationPoint(0, screen_height - 1, "BOTTOM_LEFT"),
            # Edges
            CalibrationPoint(screen_width // 2, 0, "TOP_CENTER"),
            CalibrationPoint(screen_width - 1, screen_height // 2, "RIGHT_CENTER"),
            CalibrationPoint(screen_width // 2, screen_height - 1, "BOTTOM_CENTER"),
            CalibrationPoint(0, screen_height // 2, "LEFT_CENTER"),
            # Center
            CalibrationPoint(screen_width // 2, screen_height // 2, "CENTER")
        ]
    
    def _generate_professional_points(self):
        """Generate 13 professional points (corners + edges + quarters + center)"""
        return [
            # Corners
            CalibrationPoint(0, 0, "TOP_LEFT"),
            CalibrationPoint(screen_width - 1, 0, "TOP_RIGHT"),
            CalibrationPoint(screen_width - 1, screen_height - 1, "BOTTOM_RIGHT"),
            CalibrationPoint(0, screen_height - 1, "BOTTOM_LEFT"),
            # Edges
            CalibrationPoint(screen_width // 2, 0, "TOP_CENTER"),
            CalibrationPoint(screen_width - 1, screen_height // 2, "RIGHT_CENTER"),
            CalibrationPoint(screen_width // 2, screen_height - 1, "BOTTOM_CENTER"),
            CalibrationPoint(0, screen_height // 2, "LEFT_CENTER"),
            # Quarters
            CalibrationPoint(screen_width // 4, screen_height // 4, "TOP_LEFT_QUARTER"),
            CalibrationPoint(3 * screen_width // 4, screen_height // 4, "TOP_RIGHT_QUARTER"),
            CalibrationPoint(3 * screen_width // 4, 3 * screen_height // 4, "BOTTOM_RIGHT_QUARTER"),
            CalibrationPoint(screen_width // 4, 3 * screen_height // 4, "BOTTOM_LEFT_QUARTER"),
            # Center
            CalibrationPoint(screen_width // 2, screen_height // 2, "CENTER")
        ]

class CalibrationWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AirScan Calibration v1.1")
        self.root.attributes('-alpha', 0.9)
        self.root.attributes('-topmost', True)
        self.root.attributes('-fullscreen', True)
        self.root.configure(background='#1a1a1a')
        
        # Center the window and bring to front
        self.root.lift()
        self.root.focus_force()
        
        # Setup canvas
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg='#1a1a1a')
        self.canvas.pack(fill='both', expand=True)
        
        # Setup keyboard bindings
        self.setup_keyboard_bindings()
        
        # OSC status variables
        self.osc_connected = False
        self.last_osc_data_time = 0
        self.current_x = None
        self.current_y = None
        self.data_count = 0
        
        # Pause system between points
        self.pause_start_time = None
        self.pause_duration = 5.0
        self.is_pausing = False
        
        # Calibration state
        self.calibration_complete = False
        self.current_point_index = 0
        self.points = []
        self.waiting_for_final_touch = False
        
        # Level selector
        self.level_selector = CalibrationLevelSelector(self)
        self.showing_level_selector = True
        self.selected_level = None
    
    def is_port_in_use(self, port):
        """Check if a port is in use"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.bind(('0.0.0.0', port))
                return False
        except OSError:
            return True
    
    def wait_for_port_free(self, port, timeout=10):
        """Wait for port to become free"""
        print(f"[CALIBRAÇÃO] Aguardando porta {port} ficar livre...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if not self.is_port_in_use(port):
                print(f"[CALIBRAÇÃO] Porta {port} está livre!")
                return True
            time.sleep(0.5)
        
        print(f"[CALIBRAÇÃO] Timeout aguardando porta {port} ficar livre")
        return False
    
    def kill_processes_using_port(self, port):
        """Kill processes using the specified port"""
        try:
            if os.name == 'nt':  # Windows
                # Find processes using the port
                result = subprocess.run(
                    ['netstat', '-ano'], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'UDP' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            try:
                                subprocess.run(['taskkill', '/F', '/PID', pid], 
                                             capture_output=True, timeout=5)
                                print(f"[CALIBRAÇÃO] Processo {pid} usando porta {port} finalizado")
                            except:
                                pass
            else:  # Linux/Mac
                subprocess.run(['fuser', '-k', f'{port}/udp'], 
                             capture_output=True, timeout=5)
                print(f"[CALIBRAÇÃO] Processos usando porta {port} finalizados")
                
        except Exception as e:
            print(f"[CALIBRAÇÃO] Erro ao finalizar processos na porta {port}: {e}")
    
    def setup_keyboard_bindings(self):
        """Setup keyboard event bindings"""
        # Bind ESC key to cancel calibration (multiple ways to ensure it works)
        self.root.bind('<Escape>', self.on_escape_pressed)
        self.root.bind('<KeyPress-Escape>', self.on_escape_pressed)
        self.root.bind_all('<Escape>', self.on_escape_pressed)  # Global binding
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        # Make sure the window can receive keyboard events
        self.root.focus_set()
        # Don't use grab_set as it might interfere with ESC
        # self.root.grab_set()  # Grab focus to ensure ESC works
        
        print("[CALIBRAÇÃO] Pressione ESC para cancelar a calibração")
    
    def on_escape_pressed(self, event=None):
        """Handle ESC key press to cancel calibration"""
        print("[CALIBRAÇÃO] ESC pressionado - cancelando calibração...")
        self.cleanup()
    
    def on_window_close(self):
        """Handle window close event (X button)"""
        print("[CALIBRAÇÃO] Janela fechada - cancelando calibração...")
        self.cleanup()
    
    def show_level_selector(self):
        """Show level selection interface"""
        self.showing_level_selector = True
        self.canvas.delete("all")
        
        # Title
        self.canvas.create_text(
            screen_width // 2, 100,
            text="AIRSCAN CALIBRATION v1.1",
            fill='#00ff88',
            font=('Arial', 32, 'bold'),
            justify=tk.CENTER
        )
        
        self.canvas.create_text(
            screen_width // 2, 150,
            text="Escolha o nível de calibração:",
            fill='#ffffff',
            font=('Arial', 18),
            justify=tk.CENTER
        )
        
        # Level options
        y_start = 250
        level_height = 120
        level_spacing = 20
        
        for i, (level_key, level_info) in enumerate(self.level_selector.levels.items()):
            y_pos = y_start + i * (level_height + level_spacing)
            
            # Level box
            box_width = 600
            box_height = level_height
            x_pos = screen_width // 2 - box_width // 2
            
            # Box background
            self.canvas.create_rectangle(
                x_pos, y_pos,
                x_pos + box_width, y_pos + box_height,
                fill='#2a2a2a',
                outline='#00ff88',
                width=2,
                tags=f"level_{level_key}"
            )
            
            # Level name
            self.canvas.create_text(
                x_pos + box_width // 2, y_pos + 25,
                text=level_info["name"],
                fill='#00ff88',
                font=('Arial', 20, 'bold'),
                tags=f"level_{level_key}"
            )
            
            # Level details
            details_text = f"{level_info['points']} pontos • {level_info['time']} • {level_info['accuracy']}"
            self.canvas.create_text(
                x_pos + box_width // 2, y_pos + 55,
                text=details_text,
                fill='#cccccc',
                font=('Arial', 14),
                tags=f"level_{level_key}"
            )
            
            # Description
            self.canvas.create_text(
                x_pos + box_width // 2, y_pos + 85,
                text=level_info["description"],
                fill='#ffffff',
                font=('Arial', 12),
                tags=f"level_{level_key}"
            )
        
        # Instructions
        self.canvas.create_text(
            screen_width // 2, screen_height - 100,
            text="Clique no nível desejado para iniciar a calibração",
            fill='#ffffff',
            font=('Arial', 16),
            justify=tk.CENTER
        )
        
        self.canvas.create_text(
            screen_width // 2, screen_height - 70,
            text="ESC para cancelar",
            fill='#888888',
            font=('Arial', 14),
            justify=tk.CENTER
        )
        
        # Bind click events
        self.canvas.bind("<Button-1>", self.on_level_click)
    
    def on_level_click(self, event):
        """Handle level selection click"""
        if not self.showing_level_selector:
            return
        
        # Check which level was clicked
        for level_key, level_info in self.level_selector.levels.items():
            y_start = 250
            level_height = 120
            level_spacing = 20
            level_index = list(self.level_selector.levels.keys()).index(level_key)
            y_pos = y_start + level_index * (level_height + level_spacing)
            
            box_width = 600
            x_pos = screen_width // 2 - box_width // 2
            
            if (x_pos <= event.x <= x_pos + box_width and 
                y_pos <= event.y <= y_pos + level_height):
                
                self.selected_level = level_key
                self.start_calibration(level_key)
                break
    
    def start_calibration(self, level):
        """Start calibration with selected level"""
        self.showing_level_selector = False
        self.selected_level = level
        
        # Generate points for selected level
        self.points = self.level_selector.generate_points(level)
        self.current_point_index = 0
        
        print(f"[CALIBRAÇÃO] Iniciando calibração {level.upper()} com {len(self.points)} pontos")
        
        # Show first point
        self.show_current_point()
    
    def show_current_point(self):
        """Show the current calibration point"""
        self.canvas.delete("all")
        
        if self.showing_level_selector:
            return
        
        point = self.points[self.current_point_index]
        
        # OSC Status - Top right corner (discrete)
        current_time = time.time()
        osc_status = "OSC: DESCONECTADO"
        osc_color = "#ff4444"
        
        if self.osc_connected and (current_time - self.last_osc_data_time) < 2.0:
            osc_status = f"OSC: OK ({self.data_count})"
            osc_color = "#44ff44"
        elif self.osc_connected:
            osc_status = "OSC: SEM DADOS"
            osc_color = "#ffaa44"
        
        # Show OSC status in top right corner
        self.canvas.create_text(
            screen_width - 100, 30,
            text=osc_status,
            fill=osc_color,
            font=('Arial', 12, 'bold'),
            justify=tk.RIGHT
        )
        
        # Show current coordinates in top right corner
        if self.current_x is not None and self.current_y is not None:
            coord_text = f"X:{self.current_x:.1f} Y:{self.current_y:.1f}"
            self.canvas.create_text(
                screen_width - 100, 50,
                text=coord_text,
                fill='#44aaff',
                font=('Arial', 10),
                justify=tk.RIGHT
            )
        
        # Show level info at top center with proper spacing
        level_info = self.level_selector.levels[self.selected_level]
        level_text = f"{level_info['name']} - {level_info['points']} pontos"
        self.canvas.create_text(
            screen_width // 2, 30,
            text=level_text,
            fill='#00ff88',
            font=('Arial', 16, 'bold'),
            justify=tk.CENTER
        )
        
        # Show point info with proper spacing
        point_text = f"Ponto {self.current_point_index + 1} de {len(self.points)} - {point.name}"
        self.canvas.create_text(
            screen_width // 2, 60,
            text=point_text,
            fill='#ffffff',
            font=('Arial', 14, 'bold'),
            justify=tk.CENTER
        )
        
        # Show status instructions with proper spacing
        if self.waiting_for_final_touch:
            # Waiting for final touch state
            status_text = f"✅ CALIBRAÇÃO CONCLUÍDA!\n"
            status_text += f"Todos os {len(self.points)} pontos foram capturados\n\n"
            status_text += "🟡 TOQUE NO PONTO AMARELO PARA FINALIZAR\n"
            status_text += "Posicione a mão sobre o ponto amarelo\n"
            status_text += "e toque para encerrar a calibração"
        elif self.is_pausing:
            # Pause state - show next point
            next_point_index = self.current_point_index + 1
            elapsed = time.time() - self.pause_start_time
            remaining = max(0, self.pause_duration - elapsed)
            
            status_text = f"CONCLUÍDO!\n"
            status_text += f"🟡 REPOSICIONANDO... {remaining:.1f}s restantes\n"
            status_text += f"Vá para o Ponto {next_point_index + 1} (próximo)\n"
            status_text += "Aguarde o sinal verde para começar"
        else:
            # Normal point state
            status = point.get_status()
            
            if status == "collecting":
                elapsed = time.time() - point.start_time
                remaining = max(0, 5.0 - elapsed)
                status_text = f"🔴 COLETANDO DADOS... {remaining:.1f}s restantes\n"
                status_text += "Mantenha a mão FIRME sobre o ponto vermelho\n"
                status_text += "NÃO MOVA até completar 5 segundos!"
            elif status == "ready":
                status_text = f"🟢 PRONTO PARA RECEBER DADOS\n"
                status_text += "Posicione a mão sobre o ponto verde\n"
                status_text += "Aguarde a detecção do AirScan"
            else:
                status_text = f"🟡 AGUARDANDO...\n"
                status_text += "Posicione a mão sobre o ponto\n"
                status_text += "Aguarde a detecção do AirScan"
        
        # Position status instructions with proper spacing
        self.canvas.create_text(
            screen_width // 2, 100,
            text=status_text,
            fill='#ffffff',
            font=('Arial', 16, 'bold'),
            justify=tk.CENTER
        )
        
        # Show ESC instruction at bottom with proper spacing
        self.canvas.create_text(
            screen_width // 2, screen_height - 50,
            text="ESC para cancelar",
            fill='#888888',
            font=('Arial', 14),
            justify=tk.CENTER
        )
        
        # Draw point with status-based color
        radius = 25
        
        if self.waiting_for_final_touch:
            # Show yellow point at center for final touch
            color = '#ffaa00'  # Yellow - final touch
            point_to_draw = type('obj', (object,), {'x': screen_width // 2, 'y': screen_height // 2})
        elif self.is_pausing:
            # During pause, show next point in yellow
            next_point = self.points[self.current_point_index + 1] if self.current_point_index + 1 < len(self.points) else point
            color = '#ffaa00'  # Yellow - repositioning
            point_to_draw = next_point
        else:
            # Normal state - show current point
            status = point.get_status()
            if status == "collecting":
                color = '#ff4444'  # Red - actively collecting data
            elif status == "ready":
                color = '#44ff44'  # Green - ready to receive data
            else:
                color = '#ffaa00'  # Yellow - waiting
            point_to_draw = point
        
        # Draw point with glow effect
        self.canvas.create_oval(
            point_to_draw.x - radius - 5, point_to_draw.y - radius - 5,
            point_to_draw.x + radius + 5, point_to_draw.y + radius + 5,
            fill=color,
            outline='',
            tags="point_glow"
        )
        
        self.canvas.create_oval(
            point_to_draw.x - radius, point_to_draw.y - radius,
            point_to_draw.x + radius, point_to_draw.y + radius,
            fill=color,
            outline='#ffffff',
            width=3,
            tags="point_main"
        )
        
        # Draw crosshair
        self.canvas.create_line(
            point_to_draw.x - radius - 15, point_to_draw.y,
            point_to_draw.x + radius + 15, point_to_draw.y,
            fill='#ffffff', width=3
        )
        self.canvas.create_line(
            point_to_draw.x, point_to_draw.y - radius - 15,
            point_to_draw.x, point_to_draw.y + radius + 15,
            fill='#ffffff', width=3
        )
        
        # Show progress if collecting or pausing (but not when waiting for final touch)
        if self.is_pausing and not self.waiting_for_final_touch:
            # Pause progress
            elapsed = time.time() - self.pause_start_time
            if elapsed <= self.pause_duration:
                progress = elapsed / self.pause_duration
                width = 500
                height = 50
                x = screen_width // 2 - width // 2
                y = screen_height - 150
                
                # Background
                self.canvas.create_rectangle(
                    x, y, x + width, y + height,
                    fill='#2a2a2a',
                    outline='#ffffff',
                    width=3
                )
                
                # Progress bar
                self.canvas.create_rectangle(
                    x, y, x + width * progress, y + height,
                    fill='#ffaa00'
                )
                
                # Progress text
                remaining = max(0, self.pause_duration - elapsed)
                if self.current_point_index >= len(self.points) - 1:
                    progress_text = f"FINALIZANDO: {remaining:.1f}s restantes ({progress * 100:.0f}%)"
                else:
                    progress_text = f"REPOSICIONANDO: {remaining:.1f}s restantes ({progress * 100:.0f}%)"
                self.canvas.create_text(
                    screen_width // 2, y + height // 2,
                    text=progress_text,
                    fill='#ffffff',
                    font=('Arial', 18, 'bold')
                )
                
                # Next point info
                if self.current_point_index >= len(self.points) - 1:
                    next_point_text = "Toque no ponto amarelo para encerrar"
                else:
                    next_point_text = f"Próximo: Ponto {self.current_point_index + 2} de {len(self.points)}"
                self.canvas.create_text(
                    screen_width // 2, y + height + 30,
                    text=next_point_text,
                    fill='#44aaff',
                    font=('Arial', 14)
                )
                
        elif point.is_collecting and point.start_time:
            # Collection progress
            elapsed = time.time() - point.start_time
            if elapsed <= 5.0:
                progress = elapsed / 5.0
                width = 500
                height = 50
                x = screen_width // 2 - width // 2
                y = screen_height - 150
                
                # Background
                self.canvas.create_rectangle(
                    x, y, x + width, y + height,
                    fill='#2a2a2a',
                    outline='#ffffff',
                    width=3
                )
                
                # Progress bar
                self.canvas.create_rectangle(
                    x, y, x + width * progress, y + height,
                    fill='#ff4444'
                )
                
                # Progress text
                remaining = max(0, 5.0 - elapsed)
                progress_text = f"COLETANDO: {remaining:.1f}s restantes ({progress * 100:.0f}%)"
                self.canvas.create_text(
                    screen_width // 2, y + height // 2,
                    text=progress_text,
                    fill='#ffffff',
                    font=('Arial', 18, 'bold')
                )
                
                # Data count
                data_count_text = f"Dados coletados: {len(point.airscan_data['x'])} pontos"
                self.canvas.create_text(
                    screen_width // 2, y + height + 30,
                    text=data_count_text,
                    fill='#44aaff',
                    font=('Arial', 14)
                )
    
    def start_pause(self):
        """Start pause between points"""
        self.is_pausing = True
        self.pause_start_time = time.time()
        print(f"[CALIBRAÇÃO] Pausa iniciada - {self.pause_duration}s para reposicionamento")
    
    def is_pause_complete(self):
        """Check if pause is complete"""
        if not self.is_pausing or not self.pause_start_time:
            return False
        return time.time() - self.pause_start_time >= self.pause_duration
    
    def end_pause(self):
        """End pause and prepare for next point"""
        self.is_pausing = False
        self.pause_start_time = None
        
        # Move to next point
        self.current_point_index += 1
        if self.current_point_index >= len(self.points):
            # Last point completed - wait for user touch to finish
            self.waiting_for_final_touch = True
            print(f"[CALIBRAÇÃO] Último ponto concluído - Aguardando toque do usuário para finalizar")
        else:
            # Reset capture state and show next point
            point = self.points[self.current_point_index]
            point.force_ready()
            print(f"[CALIBRAÇÃO] Pausa finalizada - Ponto {self.current_point_index + 1} pronto para receber dados")
    
    def show_success_message(self, point):
        """Show success message for completed point"""
        print("=" * 50)
        print(f"✅ PONTO {self.current_point_index + 1} SALVO COM SUCESSO!")
        print("=" * 50)
        print(f"📍 Nome: {point.name}")
        print(f"🖥️  Tela: ({point.x}, {point.y})")
        avg_pos = point.get_average()
        if avg_pos:
            print(f"📡 AirScan: ({avg_pos['x']:.2f}, {avg_pos['y']:.2f})")
        print(f"📊 Dados coletados: {len(point.airscan_data['x'])} pontos")
        print(f"💾 Arquivo: AirScan_Calibration_Data.json atualizado")
        print("=" * 50)
    
    def handle_osc_data(self, x, y):
        """Handle incoming OSC data"""
        if self.calibration_complete or self.showing_level_selector:
            return
        
        # Update OSC status
        self.osc_connected = True
        self.last_osc_data_time = time.time()
        self.current_x = x
        self.current_y = y
        self.data_count += 1
        
        # Check if waiting for final touch
        if self.waiting_for_final_touch:
            # Detect touch on the yellow point to finish calibration
            center_x = screen_width // 2
            center_y = screen_height // 2
            radius = 30  # Slightly larger radius for easier touch detection
            
            # Check if the touch is within the yellow point area
            if (abs(x - center_x) <= radius and abs(y - center_y) <= radius):
                print("[CALIBRAÇÃO] Toque detectado no ponto amarelo - finalizando calibração!")
                self.finish_calibration()
                return
        
        # If pausing, check if we should end pause
        if self.is_pausing:
            # Normal pause logic - wait for timeout
            if self.is_pause_complete():
                self.end_pause()
                self.show_current_point()
            return
            
        point = self.points[self.current_point_index]
        
        # Check for interruption if currently capturing
        if point.is_capturing:
            if point.check_interruption():
                self.show_current_point()
                return
        
        # Start capturing if we receive data and point is ready
        if point.is_ready and not point.is_capturing:
            point.start_capture()
            self.show_current_point()
            return
        
        # Add data point (this will handle interruption detection)
        if point.is_capturing:
            success = point.add_data(x, y)
            
            # Update display after each data point
            self.show_current_point()
            
            # Check if capture is complete
            if point.capture_complete():
                avg_pos = point.get_average()
                if avg_pos:
                    print(f"[CALIBRAÇÃO] Ponto {self.current_point_index + 1} capturado com sucesso!")
                    print(f"[CALIBRAÇÃO] Posição média: X={avg_pos['x']:.2f}, Y={avg_pos['y']:.2f}")
                    print(f"[CALIBRAÇÃO] Dados coletados: {len(point.airscan_data['x'])} pontos")
                    
                    # Save calibration data for this point
                    self.save_point_data(point, avg_pos)
                    
                    # Show success message
                    self.show_success_message(point)
                    
                    # Start pause before next point
                    self.start_pause()
                    self.show_current_point()
                else:
                    print(f"[CALIBRAÇÃO] Erro: dados insuficientes para {point.name}")
                    point.reset_capture()
                    self.show_current_point()
    
    def save_point_data(self, point, avg_pos):
        """Save calibration data for a point"""
        try:
            with open('AirScan_Calibration_Data.json', 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {
                "points": {},
                "screen": {"width": screen_width, "height": screen_height},
                "airscan": {
                    "width": DEFAULT_AIRSCAN_WIDTH,
                    "height": DEFAULT_AIRSCAN_HEIGHT,
                    "port": AIRSCAN_PORT
                },
                "calibration_level": self.selected_level,
                "calibration_version": "1.1"
            }
        
        # Update point data
        data["points"][point.name] = {
            "screen": {"x": point.x, "y": point.y},
            "airscan": {"x": avg_pos["x"], "y": avg_pos["y"]}
        }
        
        # Update calibration info
        data["calibration_level"] = self.selected_level
        data["calibration_version"] = "1.1"
        data["total_points"] = len(self.points)
        
        # Save to file
        with open('AirScan_Calibration_Data.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"[CALIBRAÇÃO] Dados salvos para {point.name}:")
        print(f"  Tela: ({point.x}, {point.y})")
        print(f"  AirScan: ({avg_pos['x']:.2f}, {avg_pos['y']:.2f})")
        print(f"[CALIBRAÇÃO] Arquivo AirScan_Calibration_Data.json atualizado!")
    
    def finish_calibration(self):
        """Complete the calibration process"""
        print("\n" + "=" * 60)
        print("✅ CALIBRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        self.calibration_complete = True
        
        # Stop OSC server first
        if hasattr(self, 'server') and self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
                print("[CALIBRAÇÃO] Servidor OSC encerrado")
            except Exception as e:
                print(f"[WARNING] Erro ao encerrar servidor: {e}")
        
        # Wait a bit for port to be released
        time.sleep(1)
        
        # Destroy window properly
        try:
            self.root.after_cancel(self.update_job) if hasattr(self, 'update_job') else None
            self.root.quit()
            self.root.destroy()
            print("[CALIBRAÇÃO] Janela encerrada com sucesso")
        except Exception as e:
            print(f"[WARNING] Erro ao fechar janela: {e}")
        
        # Show completion message
        print("\n[CALIBRAÇÃO] Processo de calibração finalizado com sucesso!")
        print(f"[INFO] Modo configurado: {AIRSCAN_MODE} (Blob {BLOB_ID})")
        print(f"[INFO] Para iniciar o controle, execute: python AirScan_Control.py")
        print("=" * 60 + "\n")
        
        # Exit cleanly
        sys.exit(0)
    
    def cleanup(self):
        """Clean up resources when calibration is cancelled"""
        print("\n" + "=" * 60)
        print("⚠️  CALIBRAÇÃO CANCELADA")
        print("=" * 60)
        self.calibration_complete = True
        
        # Stop OSC server
        if hasattr(self, 'server') and self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
                print("[CALIBRAÇÃO] Servidor OSC encerrado")
            except Exception as e:
                print(f"[WARNING] Erro ao encerrar servidor: {e}")
        
        # Wait a bit for port to be released
        time.sleep(1)
        
        # Create a flag file to indicate calibration was cancelled
        try:
            with open('calibration_cancelled.flag', 'w') as f:
                f.write('cancelled')
            print("[CALIBRAÇÃO] Arquivo de cancelamento criado")
        except:
            pass
        
        # Destroy window and exit
        try:
            self.root.after_cancel(self.update_job) if hasattr(self, 'update_job') else None
            self.root.quit()
            self.root.destroy()
            print("[CALIBRAÇÃO] Janela encerrada")
        except Exception as e:
            print(f"[WARNING] Erro ao fechar janela: {e}")
        
        print("\n[CALIBRAÇÃO] Sistema encerrado")
        print(f"[INFO] Modo estava configurado: {AIRSCAN_MODE} (Blob {BLOB_ID})")
        print(f"[INFO] Para iniciar o controle, execute: python AirScan_Control.py")
        print("=" * 60 + "\n")
        sys.exit(0)
    
    
    def start_osc_server(self):
        """Start OSC server to receive coordinates"""
        try:
            # Check if port is available before starting server
            if self.is_port_in_use(AIRSCAN_PORT):
                print(f"[CALIBRAÇÃO] Porta {AIRSCAN_PORT} está em uso. Tentando liberar...")
                if not self.wait_for_port_free(AIRSCAN_PORT, timeout=5):
                    print(f"[CALIBRAÇÃO] Forçando liberação da porta {AIRSCAN_PORT}...")
                    self.kill_processes_using_port(AIRSCAN_PORT)
                    time.sleep(2)  # Give time for port to be released
            
            dispatcher = Dispatcher()
            
            def handle_x(unused_addr, x):
                self.current_x = x
                if hasattr(self, 'current_y') and self.current_y is not None:
                    self.handle_osc_data(x, self.current_y)
            
            def handle_y(unused_addr, y):
                self.current_y = y
                if hasattr(self, 'current_x') and self.current_x is not None:
                    self.handle_osc_data(self.current_x, y)
            
            dispatcher.map(f"/airscan/blob/{BLOB_ID}/x", handle_x)
            dispatcher.map(f"/airscan/blob/{BLOB_ID}/y", handle_y)
            
            # Start server in a separate thread
            self.server = osc_server.ThreadingOSCUDPServer(
                ("0.0.0.0", AIRSCAN_PORT),
                dispatcher
            )
            server_thread = threading.Thread(target=self.server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            print(f"[CALIBRAÇÃO] Servidor OSC iniciado em 0.0.0.0:{AIRSCAN_PORT}")
            
        except Exception as e:
            print(f"[ERROR] Erro ao iniciar servidor OSC: {e}")
            self.osc_connected = False
    
    def start(self):
        """Start the calibration window"""
        try:
            print("[CALIBRAÇÃO] Iniciando janela de calibração v1.1...")
            
            # Start OSC server first
            self.start_osc_server()
            
            # Force window to appear immediately
            self.root.update()
            self.root.lift()
            self.root.focus_force()
            
            # Start update loop
            def update():
                if not self.calibration_complete:
                    if self.showing_level_selector:
                        self.show_level_selector()
                    else:
                        self.show_current_point()
                    
                    # Ensure window stays focused for ESC to work
                    self.root.focus_set()
                    try:
                        self.root.update()
                    except:
                        # Window was destroyed
                        return
                    # Only continue loop if not complete
                    self.update_job = self.root.after(100, update)
                else:
                    # Calibration complete, stop update loop
                    print("[CALIBRAÇÃO] Loop de atualização encerrado")
            
            # Start the update loop
            self.update_job = self.root.after(0, update)
            
            print("[CALIBRAÇÃO] Janela de calibração v1.1 ativa!")
            print("[CALIBRAÇÃO] Aguardando seleção de nível...")
            print(f"[CALIBRAÇÃO] Servidor OSC escutando em 0.0.0.0:{AIRSCAN_PORT}")
            print(f"[CALIBRAÇÃO] Modo: {AIRSCAN_MODE} (Blob {BLOB_ID})")
            print("[CALIBRAÇÃO] Pressione ESC para cancelar a qualquer momento")
            
            self.root.mainloop()
            
        except KeyboardInterrupt:
            print("\n[CALIBRAÇÃO] Interrupção detectada (Ctrl+C)")
            self.cleanup()
        except Exception as e:
            print(f"[ERROR] Erro durante a calibração: {e}")
            import traceback
            traceback.print_exc()
            self.cleanup()

if __name__ == "__main__":
    calibration = CalibrationWindow()
    calibration.start()
