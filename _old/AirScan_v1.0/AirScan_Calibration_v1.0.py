import tkinter as tk
import json
import time
import threading
from collections import deque
import os
import atexit
from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server

# Screen dimensions
import pyautogui
screen_width, screen_height = pyautogui.size()

# AirScan configuration
AIRSCAN_PORT = 8030
DEFAULT_AIRSCAN_WIDTH = 1920
DEFAULT_AIRSCAN_HEIGHT = 1080

class CalibrationPoint:
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name
        self.airscan_data = {"x": deque(maxlen=500), "y": deque(maxlen=500)}  # 5 seconds at ~100Hz
        self.start_time = None
        self.is_capturing = False
        self.last_data_time = None
        self.capture_duration = 5.0  # 5 seconds of continuous data
        self.data_interruption_threshold = 0.5  # 500ms max gap between data points
        self.is_ready = True  # Green state - ready to receive data
        self.is_collecting = False  # Red state - actively collecting data
    
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
        
        # Calculate simple average without numpy
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
        
        # Check if we have continuous data for 5 seconds
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

class CalibrationWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AirScan Calibration")
        self.root.attributes('-alpha', 0.8)
        self.root.attributes('-topmost', True)
        self.root.attributes('-fullscreen', True)
        self.root.configure(background='black')
        
        # Center the window and bring to front
        self.root.lift()
        self.root.focus_force()
        
        # Setup canvas
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg='black')
        self.canvas.pack(fill='both', expand=True)
        
        # OSC status variables
        self.osc_connected = False
        self.last_osc_data_time = 0
        self.current_x = None
        self.current_y = None
        self.data_count = 0
        
        # Pause system between points
        self.pause_start_time = None
        self.pause_duration = 5.0  # 5 seconds pause
        self.is_pausing = False
        
        # Force window to appear
        self.root.update()
        self.root.deiconify()
        
        # Define calibration points at screen edges
        self.points = [
            CalibrationPoint(0, 0, "TOP_LEFT"),  # Top-left corner
            CalibrationPoint(screen_width - 1, 0, "TOP_RIGHT"),  # Top-right corner
            CalibrationPoint(screen_width - 1, screen_height - 1, "BOTTOM_RIGHT"),  # Bottom-right corner
            CalibrationPoint(0, screen_height - 1, "BOTTOM_LEFT"),  # Bottom-left corner
            CalibrationPoint(screen_width // 2, screen_height // 2, "CENTER")  # Center
        ]
        
        self.current_point_index = 0
        self.calibration_complete = False
        
        # Start OSC server
        self.start_osc_server()
        
        # Show first point
        self.show_current_point()
        
        # Bind escape key
        self.root.bind('<Escape>', lambda e: self.cleanup())
    
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
            self.finish_calibration()
        else:
            # Reset capture state and show next point
            point = self.points[self.current_point_index]
            point.force_ready()  # Force to ready state
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
    
    def show_current_point(self):
        """Show the current calibration point"""
        self.canvas.delete("all")
        
        point = self.points[self.current_point_index]
        
        # OSC Status - Top right corner (discrete)
        current_time = time.time()
        osc_status = "OSC: DESCONECTADO"
        osc_color = "red"
        
        if self.osc_connected and (current_time - self.last_osc_data_time) < 2.0:
            osc_status = f"OSC: OK ({self.data_count})"
            osc_color = "green"
        elif self.osc_connected:
            osc_status = "OSC: SEM DADOS"
            osc_color = "orange"
        
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
                fill='cyan',
                font=('Arial', 10),
                justify=tk.RIGHT
            )
        
        # Show instructions based on point status or pause
        if self.is_pausing:
            # Pause state - show next point
            next_point_index = self.current_point_index + 1
            elapsed = time.time() - self.pause_start_time
            remaining = max(0, self.pause_duration - elapsed)
            
            # Check if this is the last point
            if self.current_point_index >= len(self.points) - 1:
                status_text = f"Ponto {self.current_point_index + 1} de 5 - CONCLUÍDO!\n"
                status_text += f"🟡 FINALIZANDO... {remaining:.1f}s restantes\n"
                status_text += "Toque no ponto amarelo para encerrar\n"
                status_text += "a calibração"
            else:
                status_text = f"Ponto {self.current_point_index + 1} de 5 - CONCLUÍDO!\n"
                status_text += f"🟡 REPOSICIONANDO... {remaining:.1f}s restantes\n"
                status_text += f"Vá para o Ponto {next_point_index + 1} (próximo)\n"
                status_text += "Aguarde o sinal verde para começar"
        else:
            # Normal point state
            status_text = f"Ponto {self.current_point_index + 1} de 5 - {point.name}\n"
            status = point.get_status()
            
            if status == "collecting":
                elapsed = time.time() - point.start_time
                remaining = max(0, 5.0 - elapsed)
                status_text += f"🔴 COLETANDO DADOS... {remaining:.1f}s restantes\n"
                status_text += "Mantenha a mão FIRME sobre o ponto vermelho\n"
                status_text += "NÃO MOVA até completar 5 segundos!"
            elif status == "ready":
                status_text += "🟢 PRONTO PARA RECEBER DADOS\n"
                status_text += "Posicione a mão sobre o ponto verde\n"
                status_text += "Aguarde a detecção do AirScan"
            else:
                status_text += "🟡 AGUARDANDO...\n"
                status_text += "Posicione a mão sobre o ponto\n"
                status_text += "Aguarde a detecção do AirScan"
        
        status_text += "\n\nESC para cancelar"
        
        # Position instructions in center-top area
        self.canvas.create_text(
            screen_width // 2, 80,
            text=status_text,
            fill='white',
            font=('Arial', 16, 'bold'),
            justify=tk.CENTER
        )
        
        # Draw point with status-based color
        radius = 20
        
        if self.is_pausing:
            # During pause, show next point in yellow
            next_point = self.points[self.current_point_index + 1] if self.current_point_index + 1 < len(self.points) else point
            color = 'yellow'  # Yellow - repositioning
            # Draw next point instead of current
            point_to_draw = next_point
        else:
            # Normal state - show current point
            status = point.get_status()
            if status == "collecting":
                color = 'red'  # Red - actively collecting data
            elif status == "ready":
                color = 'green'  # Green - ready to receive data
            else:
                color = 'yellow'  # Yellow - waiting
            point_to_draw = point
        
        self.canvas.create_oval(
            point_to_draw.x - radius, point_to_draw.y - radius,
            point_to_draw.x + radius, point_to_draw.y + radius,
            fill=color,
            outline='white',
            width=3
        )
        
        # Draw crosshair
        self.canvas.create_line(
            point_to_draw.x - radius - 10, point_to_draw.y,
            point_to_draw.x + radius + 10, point_to_draw.y,
            fill='white', width=2
        )
        self.canvas.create_line(
            point_to_draw.x, point_to_draw.y - radius - 10,
            point_to_draw.x, point_to_draw.y + radius + 10,
            fill='white', width=2
        )
        
        # Show progress if collecting or pausing
        if self.is_pausing:
            # Pause progress
            elapsed = time.time() - self.pause_start_time
            if elapsed <= self.pause_duration:
                progress = elapsed / self.pause_duration
                width = 400
                height = 40
                x = screen_width // 2 - width // 2
                y = screen_height - 150  # Moved up to avoid overlap
                
                # Background
                self.canvas.create_rectangle(
                    x, y, x + width, y + height,
                    fill='darkgray',
                    outline='white',
                    width=3
                )
                
                # Progress bar
                self.canvas.create_rectangle(
                    x, y, x + width * progress, y + height,
                    fill='yellow'
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
                    fill='white',
                    font=('Arial', 16, 'bold')
                )
                
                # Next point info
                if self.current_point_index >= len(self.points) - 1:
                    next_point_text = "Toque no ponto amarelo para encerrar"
                else:
                    next_point_text = f"Próximo: Ponto {self.current_point_index + 2} de 5"
                self.canvas.create_text(
                    screen_width // 2, y + height + 30,
                    text=next_point_text,
                    fill='cyan',
                    font=('Arial', 12)
                )
                
        elif point.is_collecting and point.start_time:
            # Collection progress
            elapsed = time.time() - point.start_time
            if elapsed <= 5.0:
                progress = elapsed / 5.0
                width = 400
                height = 40
                x = screen_width // 2 - width // 2
                y = screen_height - 150  # Moved up to avoid overlap
                
                # Background
                self.canvas.create_rectangle(
                    x, y, x + width, y + height,
                    fill='darkgray',
                    outline='white',
                    width=3
                )
                
                # Progress bar
                self.canvas.create_rectangle(
                    x, y, x + width * progress, y + height,
                    fill='red'
                )
                
                # Progress text
                remaining = max(0, 5.0 - elapsed)
                progress_text = f"COLETANDO: {remaining:.1f}s restantes ({progress * 100:.0f}%)"
                self.canvas.create_text(
                    screen_width // 2, y + height // 2,
                    text=progress_text,
                    fill='white',
                    font=('Arial', 16, 'bold')
                )
                
                # Data count
                data_count_text = f"Dados coletados: {len(point.airscan_data['x'])} pontos"
                self.canvas.create_text(
                    screen_width // 2, y + height + 30,
                    text=data_count_text,
                    fill='cyan',
                    font=('Arial', 12)
                )
    
    def handle_osc_data(self, x, y):
        """Handle incoming OSC data"""
        if self.calibration_complete:
            return
        
        # Update OSC status
        self.osc_connected = True
        self.last_osc_data_time = time.time()
        self.current_x = x
        self.current_y = y
        self.data_count += 1
        
        # If pausing, don't process data
        if self.is_pausing:
            if self.is_pause_complete():
                self.end_pause()
                self.show_current_point()
            return
            
        point = self.points[self.current_point_index]
        
        # Check for interruption if currently capturing
        if point.is_capturing:
            if point.check_interruption():
                # Force update display to show green state
                self.show_current_point()
                return
        
        # Start capturing if we receive data and point is ready
        if point.is_ready and not point.is_capturing:
            point.start_capture()
            self.show_current_point()  # Update display
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
            with open('AirScan_Calibration_Data_v1.0.json', 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {
                "points": {},
                "screen": {"width": screen_width, "height": screen_height},
                "airscan": {
                    "width": DEFAULT_AIRSCAN_WIDTH,
                    "height": DEFAULT_AIRSCAN_HEIGHT,
                    "port": AIRSCAN_PORT
                }
            }
        
        # Update point data
        data["points"][point.name] = {
            "screen": {"x": point.x, "y": point.y},
            "airscan": {"x": avg_pos["x"], "y": avg_pos["y"]}
        }
        
        # Save to file
        with open('AirScan_Calibration_Data_v1.0.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"[CALIBRAÇÃO] Dados salvos para {point.name}:")
        print(f"  Tela: ({point.x}, {point.y})")
        print(f"  AirScan: ({avg_pos['x']:.2f}, {avg_pos['y']:.2f})")
        print(f"[CALIBRAÇÃO] Arquivo AirScan_Calibration_Data_v1.0.json atualizado!")
    
    def finish_calibration(self):
        """Complete the calibration process"""
        self.calibration_complete = True
        self.cleanup()
        print("Calibração concluída! Você pode fechar esta janela.")
    
    def cleanup(self):
        """Clean up resources"""
        print("[CALIBRAÇÃO] Cancelando calibração...")
        self.calibration_complete = True
        
        if hasattr(self, 'server') and self.server:
            self.server.shutdown()
        
        # Create a flag file to indicate calibration was cancelled
        try:
            with open('calibration_cancelled.flag', 'w') as f:
                f.write('cancelled')
        except:
            pass
            
        self.root.quit()
    
    def start_osc_server(self):
        """Start OSC server to receive coordinates"""
        try:
            dispatcher = Dispatcher()
            
            def handle_x(unused_addr, x):
                self.current_x = x
                if hasattr(self, 'current_y') and self.current_y is not None:
                    self.handle_osc_data(x, self.current_y)
            
            def handle_y(unused_addr, y):
                self.current_y = y
                if hasattr(self, 'current_x') and self.current_x is not None:
                    self.handle_osc_data(self.current_x, y)
            
            dispatcher.map("/airscan/blob/6/x", handle_x)
            dispatcher.map("/airscan/blob/6/y", handle_y)
            
            # Start server in a separate thread
            self.server = osc_server.ThreadingOSCUDPServer(
                ("0.0.0.0", AIRSCAN_PORT),  # Use same port as main server
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
            print("[CALIBRAÇÃO] Iniciando janela de calibração...")
            
            # Force window to appear immediately
            self.root.update()
            self.root.lift()
            self.root.focus_force()
            
            # Start update loop
            def update():
                if not self.calibration_complete:
                    self.show_current_point()
                    self.root.update()
                self.root.after(100, update)  # Update every 100ms
            
            # Start the update loop
            self.root.after(0, update)
            
            print("[CALIBRAÇÃO] Janela de calibração ativa!")
            print("[CALIBRAÇÃO] Aguardando dados do AirScan...")
            print(f"[CALIBRAÇÃO] Servidor OSC escutando em 0.0.0.0:{AIRSCAN_PORT}")
            
            self.root.mainloop()
            
        except Exception as e:
            print(f"[ERROR] Erro durante a calibração: {e}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    calibration = CalibrationWindow()
    calibration.start()