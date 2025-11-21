"""
Script para inicializar y migrar la base de datos
Ejecutar una sola vez antes de iniciar los servicios
"""
from database import init_database, migrate_from_json

if __name__ == "__main__":
    print("=" * 60)
    print("INICIALIZACIÓN DE BASE DE DATOS SQL")
    print("=" * 60)
    print()
    
    print("1. Creando tablas...")
    init_database()
    print()
    
    print("2. Migrando datos de JSON a SQL...")
    migrate_from_json()
    print()
    
    print("=" * 60)
    print("✓ BASE DE DATOS LISTA PARA USAR")
    print("=" * 60)
    print()
    print("Ahora puedes iniciar los servicios con INICIO_RAPIDO.bat")
