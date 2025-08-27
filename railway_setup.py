#!/usr/bin/env python3
"""
Script de configuración automática para Railway
Este script ayuda a verificar la configuración antes del deploy
"""

import os
import sys
from pathlib import Path

def check_files():
    """Verificar que todos los archivos necesarios estén presentes"""
    required_files = [
        'main.py',
        'requirements.txt',
        'pyproject.toml',
        'templates/index.html',
        'static/style.css'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Archivos faltantes:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    else:
        print("✅ Todos los archivos necesarios están presentes")
        return True

def check_environment():
    """Verificar variables de entorno"""
    required_vars = ['DISCORD_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Variables de entorno faltantes (configurar en Railway):")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    else:
        print("✅ Variables de entorno configuradas")
        return True

def check_dependencies():
    """Verificar que las dependencias estén correctas"""
    try:
        with open('requirements.txt', 'r') as f:
            deps = f.read().strip().split('\n')
        
        required_deps = ['discord.py', 'flask']
        missing_deps = []
        
        for dep in required_deps:
            if not any(dep in line for line in deps):
                missing_deps.append(dep)
        
        if missing_deps:
            print("❌ Dependencias faltantes en requirements.txt:")
            for dep in missing_deps:
                print(f"   - {dep}")
            return False
        else:
            print("✅ Dependencias correctas en requirements.txt")
            return True
    except FileNotFoundError:
        print("❌ Archivo requirements.txt no encontrado")
        return False

def main():
    print("🦇 BatBot - Verificación de configuración para Railway\n")
    
    checks = [
        ("Archivos del proyecto", check_files),
        ("Dependencias", check_dependencies),
        ("Variables de entorno", check_environment)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"🔍 Verificando {check_name}...")
        if not check_func():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 ¡Configuración completa! El bot está listo para Railway.")
        print("\n📋 Próximos pasos:")
        print("1. Subir el código a GitHub")
        print("2. Crear proyecto en Railway.app")
        print("3. Conectar repositorio de GitHub")
        print("4. Configurar variables de entorno en Railway")
        print("5. Deploy automático")
    else:
        print("❌ Hay problemas de configuración que resolver antes del deploy.")
        sys.exit(1)

if __name__ == "__main__":
    main()