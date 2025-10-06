#!/usr/bin/env python3
"""
Script de teste para verificar se a calibração está sendo reconhecida
"""

import json
import os

def test_calibration_data():
    """Testa se os dados de calibração estão sendo reconhecidos"""
    print("=" * 50)
    print("TESTE DE RECONHECIMENTO DE CALIBRACAO v1.1")
    print("=" * 50)
    
    # Verificar se o arquivo existe
    calibration_file = "AirScan_Calibration_Data_v1.1.json"
    
    if not os.path.exists(calibration_file):
        print(f"[ERRO] Arquivo {calibration_file} nao encontrado!")
        return False
    
    print(f"[OK] Arquivo {calibration_file} encontrado")
    
    # Carregar dados
    try:
        with open(calibration_file, 'r') as f:
            data = json.load(f)
        print("[OK] Arquivo JSON carregado com sucesso")
    except Exception as e:
        print(f"[ERRO] Erro ao carregar JSON: {e}")
        return False
    
    # Verificar estrutura
    required_keys = ["points", "screen", "airscan"]
    for key in required_keys:
        if key in data:
            print(f"[OK] Chave '{key}' encontrada")
        else:
            print(f"[ERRO] Chave '{key}' ausente")
            return False
    
    # Verificar pontos de calibração
    points = data.get("points", {})
    if points:
        print(f"[OK] {len(points)} pontos de calibração encontrados:")
        for point_name, point_data in points.items():
            screen_pos = point_data.get("screen", {})
            airscan_pos = point_data.get("airscan", {})
            print(f"  - {point_name}: Tela({screen_pos.get('x', 'N/A')}, {screen_pos.get('y', 'N/A')}) -> AirScan({airscan_pos.get('x', 'N/A'):.2f}, {airscan_pos.get('y', 'N/A'):.2f})")
    else:
        print("[AVISO] Nenhum ponto de calibração encontrado")
        print("        Execute a calibração primeiro!")
        return False
    
    # Verificar informações da calibração
    level = data.get("calibration_level", "N/A")
    version = data.get("calibration_version", "N/A")
    total_points = data.get("total_points", 0)
    
    print(f"[OK] Nível de calibração: {level}")
    print(f"[OK] Versão: {version}")
    print(f"[OK] Total de pontos: {total_points}")
    
    print("\n" + "=" * 50)
    print("CALIBRACAO RECONHECIDA COM SUCESSO!")
    print("O sistema de controle deve funcionar corretamente.")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    test_calibration_data()
