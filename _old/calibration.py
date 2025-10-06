import tkinter as tk
from tkinter import ttk
import json
from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server
import threading
import time

class CalibrationOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes('-alpha', 0.7)  # Semi transparente
        self.root.attributes('-topmost', True)  # Sempre no topo
        self.root.attributes('-fullscreen', True)  # Tela cheia
        
        # Obtém dimensões da tela
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Pontos de calibração (cantos e centro)
        self.calibration_points = [
            {"x": 50, "y": 50, "name": "TOP_LEFT"},  # Canto superior esquerdo
            {"x": self.screen_width - 50, "y": 50, "name": "TOP_RIGHT"},  # Canto superior direito
            {"x": 50, "y": self.screen_height - 50, "name": "BOTTOM_LEFT"},  # Canto inferior esquerdo
            {"x": self.screen_width - 50, "y": self.screen_height - 50, "name": "BOTTOM_RIGHT"},  # Canto inferior direito
            {"x": self.screen_width // 2, "y": self.screen_height // 2, "name": "CENTER"}  # Centro
        ]
        
        # Dados de calibração
        self.calibration_data = {
            "screen": {"width": self.screen_width, "height": self.screen_height},
            "points": {}
        }
        
        self.current_point = 0
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # Configurações OSC
        self.dispatcher = Dispatcher()
        self.dispatcher.map("/airscan/blob/6/x", self.on_x)
        self.dispatcher.map("/airscan/blob/6/y", self.on_y)
        self.dispatcher.map("/airscan/blob/6/z", self.on_click)
        
        # Variáveis para armazenar coordenadas do AirScan
        self.current_x = None
        self.current_y = None
        
        # Iniciar servidor OSC em uma thread separada
        self.server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", 8083), self.dispatcher)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Iniciar calibração
        self.draw_current_point()
        
        # Bind da tecla ESC para sair
        self.root.bind('<Escape>', lambda e: self.cleanup())
        
        # Label com instruções
        self.instruction_label = tk.Label(
            self.root,
            text="Aponte para o ponto vermelho e clique para calibrar\nPressione ESC para sair",
            font=("Arial", 14),
            bg='white'
        )
        self.instruction_label.pack(pady=20)

    def draw_current_point(self):
        self.canvas.delete("all")  # Limpa o canvas
        
        # Desenha todos os pontos em cinza
        for point in self.calibration_points:
            self.canvas.create_oval(
                point["x"] - 10, point["y"] - 10,
                point["x"] + 10, point["y"] + 10,
                fill='gray'
            )
        
        # Desenha o ponto atual em vermelho
        current = self.calibration_points[self.current_point]
        self.canvas.create_oval(
            current["x"] - 10, current["y"] - 10,
            current["x"] + 10, current["y"] + 10,
            fill='red'
        )

    def on_x(self, unused_addr, x):
        self.current_x = x

    def on_y(self, unused_addr, y):
        self.current_y = y

    def on_click(self, unused_addr, z):
        if z == 1 and self.current_x is not None and self.current_y is not None:
            # Salva os dados de calibração
            point_name = self.calibration_points[self.current_point]["name"]
            self.calibration_data["points"][point_name] = {
                "screen": {
                    "x": self.calibration_points[self.current_point]["x"],
                    "y": self.calibration_points[self.current_point]["y"]
                },
                "airscan": {
                    "x": self.current_x,
                    "y": self.current_y
                }
            }
            
            # Avança para o próximo ponto
            self.current_point += 1
            if self.current_point >= len(self.calibration_points):
                self.save_calibration()
                self.cleanup()
            else:
                self.draw_current_point()

    def save_calibration(self):
        with open('calibration_data.json', 'w') as f:
            json.dump(self.calibration_data, f, indent=2)
        print("Calibração salva em calibration_data.json")

    def cleanup(self):
        self.server.shutdown()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = CalibrationOverlay()
    app.run()