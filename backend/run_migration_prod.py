#!/usr/bin/env python3
"""
Script para ejecutar migración en producción desde la terminal
================================================================

Uso:
    python run_migration_prod.py --url https://pqrs-backend.onrender.com --key tu-clave-secreta-2024

Este script:
1. Verifica el estado actual de la base de datos
2. Ejecuta la migración completa
3. Verifica el resultado
4. Muestra un reporte detallado
"""

import argparse
import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any


class Colors:
    """Colores ANSI para terminal"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Imprime un encabezado destacado"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_success(text: str):
    """Imprime mensaje de éxito"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Imprime mensaje de error"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Imprime mensaje de advertencia"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    """Imprime mensaje informativo"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def check_database_status(base_url: str) -> Dict[str, Any]:
    """Verifica el estado actual de la base de datos"""
    print_info("Verificando estado de la base de datos...")
    
    try:
        response = requests.get(f"{base_url}/api/migrations/status", timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "ok":
            print_success("Conexión a base de datos exitosa")
            
            stats = data.get("statistics", {})
            print(f"  • Total de tablas: {stats.get('total_tables', 0)}")
            print(f"  • Tablas esperadas: {stats.get('expected_tables', 0)}")
            print(f"  • Completitud: {stats.get('completeness_percentage', 0):.1f}%")
            
            # Mostrar conteo de registros
            counts = data.get("record_counts", {})
            if counts:
                print("\n  Registros por tabla:")
                for table, count in counts.items():
                    print(f"    - {table}: {count}")
            
            return data
        else:
            print_error("Error en el estado de la base de datos")
            return data
            
    except requests.exceptions.RequestException as e:
        print_error(f"Error conectando al servidor: {str(e)}")
        sys.exit(1)
    except json.JSONDecodeError:
        print_error("Error decodificando respuesta del servidor")
        sys.exit(1)


def run_migration(base_url: str, migration_key: str) -> Dict[str, Any]:
    """Ejecuta la migración completa"""
    print_info("Ejecutando migración completa...")
    print_warning("Esto puede tomar 30-60 segundos, por favor espera...")
    
    try:
        headers = {
            "X-Migration-Key": migration_key,
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{base_url}/api/migrations/run/status",
            headers=headers,
            timeout=120  # 2 minutos de timeout
        )
        response.raise_for_status()
        data = response.json()
        
        return data
        
    except requests.exceptions.Timeout:
        print_error("Timeout: La migración está tomando más tiempo del esperado")
        print_info("Verifica el estado con: /api/migrations/status")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print_error("Error de autenticación: Clave de migración inválida")
        else:
            print_error(f"Error HTTP {e.response.status_code}: {e.response.text}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print_error(f"Error ejecutando migración: {str(e)}")
        sys.exit(1)


def display_migration_results(data: Dict[str, Any]):
    """Muestra los resultados de la migración"""
    status = data.get("status")
    
    if status == "success":
        print_success("MIGRACIÓN COMPLETADA EXITOSAMENTE")
        
        total_results = data.get("total_results", 0)
        total_errors = data.get("total_errors", 0)
        
        print(f"\n📊 Resumen:")
        print(f"  • Total de operaciones: {total_results}")
        print(f"  • Errores encontrados: {total_errors}")
        print(f"  • Timestamp: {data.get('timestamp', 'N/A')}")
        
        # Mostrar resultados
        results = data.get("results", [])
        if results:
            print(f"\n📝 Resultados ({min(len(results), 20)} de {len(results)}):")
            for result in results[:20]:
                if "✓" in result:
                    print_success(result.replace("✓ ", ""))
                elif "⚠" in result:
                    print_warning(result.replace("⚠ ", ""))
                elif "❌" in result:
                    print_error(result.replace("❌ ", ""))
                else:
                    print(f"  {result}")
        
        # Mostrar errores si existen
        errors = data.get("errors", [])
        if errors:
            print(f"\n⚠️  Errores ({len(errors)}):")
            for error in errors[:10]:
                print_error(error)
        
        # Mostrar algunos logs
        logs = data.get("logs", [])
        if logs:
            print(f"\n📋 Últimos logs:")
            for log in logs[-10:]:
                print(f"  {log}")
                
    elif status == "already_running":
        print_warning("Ya hay una migración en ejecución")
        print_info("Espera unos minutos e intenta nuevamente")
        print_info("O verifica el estado con: /api/migrations/status")
        sys.exit(1)
        
    elif status == "error":
        print_error("ERROR EN LA MIGRACIÓN")
        
        message = data.get("message", "Error desconocido")
        print(f"\n❌ Mensaje: {message}")
        
        errors = data.get("errors", [])
        if errors:
            print(f"\n⚠️  Errores ({len(errors)}):")
            for error in errors:
                print_error(error)
        
        traceback = data.get("traceback")
        if traceback:
            print(f"\n🔍 Traceback:")
            print(traceback)
        
        sys.exit(1)
    else:
        print_error(f"Estado desconocido: {status}")
        print(json.dumps(data, indent=2))
        sys.exit(1)


def verify_final_state(base_url: str):
    """Verifica el estado final después de la migración"""
    print_info("Verificando estado final de la base de datos...")
    
    try:
        response = requests.get(f"{base_url}/api/migrations/status", timeout=30)
        response.raise_for_status()
        data = response.json()
        
        stats = data.get("statistics", {})
        completeness = stats.get("completeness_percentage", 0)
        total_tables = stats.get("total_tables", 0)
        
        print(f"  • Total de tablas: {total_tables}")
        print(f"  • Completitud: {completeness:.1f}%")
        
        if completeness >= 100:
            print_success("Base de datos completamente migrada")
        elif completeness >= 90:
            print_warning(f"Base de datos casi completa ({completeness:.1f}%)")
        else:
            print_error(f"Base de datos incompleta ({completeness:.1f}%)")
            
    except Exception as e:
        print_error(f"Error verificando estado final: {str(e)}")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Ejecuta migración completa en base de datos de producción",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Migración en producción
  python run_migration_prod.py --url https://pqrs-backend.onrender.com --key tu-clave-secreta-2024

  # Solo verificar estado (sin migrar)
  python run_migration_prod.py --url https://pqrs-backend.onrender.com --status-only

  # Migración en local
  python run_migration_prod.py --url http://localhost:8000 --key tu-clave-secreta-2024
        """
    )
    
    parser.add_argument(
        "--url",
        required=True,
        help="URL del backend (ej: https://pqrs-backend.onrender.com)"
    )
    parser.add_argument(
        "--key",
        default="tu-clave-secreta-2024",
        help="Clave secreta de migración (default: tu-clave-secreta-2024)"
    )
    parser.add_argument(
        "--status-only",
        action="store_true",
        help="Solo verificar estado sin ejecutar migración"
    )
    
    args = parser.parse_args()
    
    # Limpiar URL (remover trailing slash)
    base_url = args.url.rstrip("/")
    
    # Banner inicial
    print_header("MIGRACIÓN DE BASE DE DATOS - PRODUCCIÓN")
    print(f"🌐 URL: {base_url}")
    print(f"🔑 Key: {'*' * (len(args.key) - 4)}{args.key[-4:]}")
    print(f"🕐 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Paso 1: Verificar estado inicial
    print_header("1. VERIFICACIÓN INICIAL")
    initial_status = check_database_status(base_url)
    
    if args.status_only:
        print_info("Modo solo-lectura: No se ejecutará migración")
        return
    
    # Paso 2: Ejecutar migración
    print_header("2. EJECUTANDO MIGRACIÓN")
    migration_result = run_migration(base_url, args.key)
    
    # Paso 3: Mostrar resultados
    print_header("3. RESULTADOS")
    display_migration_results(migration_result)
    
    # Paso 4: Verificar estado final
    print_header("4. VERIFICACIÓN FINAL")
    verify_final_state(base_url)
    
    # Banner final
    print_header("✅ PROCESO COMPLETADO")
    print_success("La migración se ejecutó correctamente")
    print_info("Verifica el frontend para confirmar que todo funciona bien")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}⚠ Proceso interrumpido por el usuario{Colors.ENDC}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.FAIL}❌ Error inesperado: {str(e)}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
