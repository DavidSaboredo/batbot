#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Verificación Post-Deploy para BatBot en Railway
Este script ayuda a verificar que el bot esté funcionando correctamente después del deploy.
"""

import os
import sys
import requests
import json
from datetime import datetime

def print_header(title):
    """Imprime un encabezado formateado"""
    print("\n" + "="*50)
    print(f" {title}")
    print("="*50)

def check_environment_variables():
    """Verifica que las variables de entorno estén configuradas"""
    print_header("🔧 VERIFICACIÓN DE VARIABLES DE ENTORNO")
    
    required_vars = {
        'DISCORD_TOKEN': 'Token del bot de Discord',
        'PORT': 'Puerto para el servidor Flask (opcional)'
    }
    
    all_good = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            if var == 'DISCORD_TOKEN':
                # Mostrar solo los primeros y últimos caracteres del token
                masked_value = f"{value[:8]}...{value[-8:]}"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            if var == 'PORT':
                print(f"⚠️  {var}: No configurado (usará puerto por defecto)")
            else:
                print(f"❌ {var}: NO CONFIGURADO - {description}")
                all_good = False
    
    return all_good

def check_required_files():
    """Verifica que todos los archivos necesarios estén presentes"""
    print_header("📁 VERIFICACIÓN DE ARCHIVOS")
    
    required_files = {
        'main.py': 'Archivo principal del bot',
        'requirements.txt': 'Dependencias de Python',
        'Procfile': 'Configuración de Railway',
        'templates/index.html': 'Template del dashboard web',
        'static/style.css': 'Estilos del dashboard'
    }
    
    all_files_present = True
    
    for file_path, description in required_files.items():
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✅ {file_path}: {file_size} bytes - {description}")
        else:
            print(f"❌ {file_path}: NO ENCONTRADO - {description}")
            all_files_present = False
    
    return all_files_present

def check_dependencies():
    """Verifica las dependencias en requirements.txt"""
    print_header("📦 VERIFICACIÓN DE DEPENDENCIAS")
    
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            requirements = f.read().strip().split('\n')
        
        required_deps = ['discord.py', 'flask']
        found_deps = []
        
        for req in requirements:
            req = req.strip()
            if req and not req.startswith('#'):
                dep_name = req.split('>=')[0].split('==')[0].strip()
                found_deps.append(dep_name)
                print(f"✅ {req}")
        
        missing_deps = [dep for dep in required_deps if dep not in found_deps]
        
        if missing_deps:
            print(f"❌ Dependencias faltantes: {', '.join(missing_deps)}")
            return False
        else:
            print(f"✅ Todas las dependencias requeridas están presentes")
            return True
            
    except FileNotFoundError:
        print("❌ requirements.txt no encontrado")
        return False
    except Exception as e:
        print(f"❌ Error leyendo requirements.txt: {e}")
        return False

def check_main_py_config():
    """Verifica la configuración en main.py"""
    print_header("⚙️ VERIFICACIÓN DE CONFIGURACIÓN")
    
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = {
            'VALID_VOICE_CHANNELS': 'Lista de canales de voz válidos',
            'ROLE_SYSTEM': 'Sistema de roles progresivos',
            'Flask': 'Servidor web Flask',
            'discord.Client': 'Cliente de Discord'
        }
        
        all_configured = True
        
        for check, description in checks.items():
            if check in content:
                print(f"✅ {check}: Configurado - {description}")
            else:
                print(f"❌ {check}: NO ENCONTRADO - {description}")
                all_configured = False
        
        # Verificar si hay IDs de canales configurados
        if 'VALID_VOICE_CHANNELS = [' in content:
            # Extraer la lista de canales
            start = content.find('VALID_VOICE_CHANNELS = [')
            end = content.find(']', start) + 1
            channels_section = content[start:end]
            
            # Contar números que parecen IDs de Discord (18-19 dígitos)
            import re
            channel_ids = re.findall(r'\b\d{17,19}\b', channels_section)
            
            if channel_ids:
                print(f"✅ Canales configurados: {len(channel_ids)} canales")
                for i, channel_id in enumerate(channel_ids[:3], 1):  # Mostrar solo los primeros 3
                    print(f"   Canal {i}: {channel_id}")
                if len(channel_ids) > 3:
                    print(f"   ... y {len(channel_ids) - 3} más")
            else:
                print("⚠️  No se encontraron IDs de canales válidos")
                print("   Recuerda actualizar VALID_VOICE_CHANNELS con los IDs reales")
        
        return all_configured
        
    except FileNotFoundError:
        print("❌ main.py no encontrado")
        return False
    except Exception as e:
        print(f"❌ Error leyendo main.py: {e}")
        return False

def test_web_dashboard(url=None):
    """Intenta acceder al dashboard web si se proporciona una URL"""
    if not url:
        print_header("🌐 DASHBOARD WEB")
        print("⚠️  URL no proporcionada")
        print("   Después del deploy, prueba acceder a tu URL de Railway")
        print("   Ejemplo: https://batbot-production.up.railway.app")
        return None
    
    print_header(f"🌐 PROBANDO DASHBOARD: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Dashboard accesible (Status: {response.status_code})")
            
            # Verificar contenido básico
            content = response.text.lower()
            if 'batcompany discord bot' in content:
                print("✅ Contenido del dashboard correcto")
            else:
                print("⚠️  Contenido del dashboard no reconocido")
            
            return True
        else:
            print(f"❌ Dashboard no accesible (Status: {response.status_code})")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando al dashboard: {e}")
        return False

def generate_deployment_checklist():
    """Genera una checklist para después del deploy"""
    print_header("📋 CHECKLIST POST-DEPLOY")
    
    checklist = [
        "🔍 Verificar que el bot aparezca online en Discord",
        "💬 Probar comando !voice_stats en un canal de texto",
        "🎤 Conectarse a un canal de voz monitoreado",
        "⏱️  Esperar unos minutos y verificar que se asigne un rol",
        "🌐 Acceder al dashboard web desde la URL de Railway",
        "📊 Verificar que el dashboard muestre información correcta",
        "⚙️ Probar comando !config (solo administradores)",
        "🧪 Probar comando !roletest (solo administradores)",
        "📈 Monitorear logs en Railway por errores",
        "💰 Verificar uso de recursos en Railway Dashboard"
    ]
    
    print("\nDespués del deploy en Railway, verifica:")
    for item in checklist:
        print(f"  □ {item}")
    
    print("\n🎯 URLs importantes:")
    print("  • Railway Dashboard: https://railway.app/dashboard")
    print("  • Discord Developer Portal: https://discord.com/developers/applications")
    print("  • Tu bot dashboard: [URL_DE_RAILWAY]/")

def main():
    """Función principal"""
    print("🦇 BatBot - Verificación de Deploy en Railway")
    print(f"Ejecutado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ejecutar todas las verificaciones
    env_ok = check_environment_variables()
    files_ok = check_required_files()
    deps_ok = check_dependencies()
    config_ok = check_main_py_config()
    
    # Resumen final
    print_header("📊 RESUMEN DE VERIFICACIÓN")
    
    checks = [
        ("Variables de entorno", env_ok),
        ("Archivos requeridos", files_ok),
        ("Dependencias", deps_ok),
        ("Configuración", config_ok)
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 ¡TODAS LAS VERIFICACIONES PASARON!")
        print("✅ El proyecto está listo para deploy en Railway")
    else:
        print("⚠️  ALGUNAS VERIFICACIONES FALLARON")
        print("❌ Revisa los errores antes de hacer deploy")
    
    # Generar checklist
    generate_deployment_checklist()
    
    # Información adicional
    print_header("ℹ️  INFORMACIÓN ADICIONAL")
    print("📖 Guías disponibles:")
    print("  • RAILWAY_MIGRATION.md - Guía completa de migración")
    print("  • CONFIGURAR_RAILWAY.md - Configuración detallada")
    print("  • SUBIR_A_GITHUB.md - Opciones para subir a GitHub")
    
    print("\n🔧 Para probar el dashboard después del deploy:")
    print("  python verificar_deploy.py --test-url https://tu-url-railway.app")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    # Verificar si se pasó una URL para probar
    if len(sys.argv) > 2 and sys.argv[1] == "--test-url":
        test_url = sys.argv[2]
        test_web_dashboard(test_url)
    else:
        exit_code = main()
        sys.exit(exit_code)