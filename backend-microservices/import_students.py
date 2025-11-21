"""
Script para importar estudiantes desde Excel a la base de datos
"""
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import get_connection

def import_students_from_excel(excel_path):
    """Importa estudiantes desde un archivo Excel"""
    
    # Leer el archivo Excel
    print(f"📖 Leyendo archivo: {excel_path}")
    try:
        df = pd.read_excel(excel_path)
        print(f"✅ Archivo leído correctamente. Total de filas: {len(df)}")
    except Exception as e:
        print(f"❌ Error al leer el archivo: {e}")
        return
    
    # Mostrar las primeras filas para verificar
    print("\n📋 Primeras 3 filas del Excel:")
    print(df.head(3))
    
    # Mostrar nombres de columnas
    print(f"\n📊 Columnas encontradas: {list(df.columns)}")
    
    # Conectar a la base de datos
    conn = get_connection()
    cursor = conn.cursor()
    
    # Contadores
    inserted = 0
    updated = 0
    errors = 0
    
    print("\n🔄 Procesando estudiantes...")
    
    for index, row in df.iterrows():
        try:
            # Extraer datos (ajusta los nombres de columnas según tu Excel)
            # Intentar diferentes nombres de columnas comunes
            matricula = None
            nombre = None
            carrera = None
            semestre = None
            email = None
            
            # Buscar matrícula
            for col in ['Matricula', 'matricula', 'MATRICULA', 'Matrícula', 'ID', 'id']:
                if col in df.columns and pd.notna(row.get(col)):
                    matricula = str(row[col]).strip()
                    break
            
            # Buscar nombre
            for col in ['Nombre', 'nombre', 'NOMBRE', 'Alumno', 'alumno', 'ALUMNO']:
                if col in df.columns and pd.notna(row.get(col)):
                    nombre = str(row[col]).strip()
                    break
            
            # Buscar carrera
            for col in ['Carrera', 'carrera', 'CARRERA', 'Programa', 'programa']:
                if col in df.columns and pd.notna(row.get(col)):
                    carrera = str(row[col]).strip()
                    break
            
            # Buscar semestre
            for col in ['Semestre', 'semestre', 'SEMESTRE', 'Sem', 'sem']:
                if col in df.columns and pd.notna(row.get(col)):
                    try:
                        semestre = int(row[col])
                    except:
                        semestre = None
                    break
            
            # Buscar email
            for col in ['Email', 'email', 'EMAIL', 'Correo', 'correo', 'CORREO']:
                if col in df.columns and pd.notna(row.get(col)):
                    email = str(row[col]).strip()
                    break
            
            # Validar que al menos tengamos matrícula
            if not matricula:
                print(f"⚠️  Fila {index + 1}: Sin matrícula, omitiendo...")
                errors += 1
                continue
            
            # Si no hay nombre, usar "Estudiante [Matrícula]"
            if not nombre:
                nombre = f"Estudiante {matricula}"
            
            # Verificar si el estudiante ya existe
            cursor.execute("SELECT matricula FROM students WHERE matricula = ?", (matricula,))
            existing = cursor.fetchone()
            
            if existing:
                # Actualizar estudiante existente
                cursor.execute("""
                    UPDATE students 
                    SET nombre = ?, carrera = ?, semestre = ?, email = ?
                    WHERE matricula = ?
                """, (nombre, carrera, semestre, email, matricula))
                updated += 1
                print(f"🔄 Actualizado: {matricula} - {nombre}")
            else:
                # Insertar nuevo estudiante
                cursor.execute("""
                    INSERT INTO students (matricula, nombre, carrera, semestre, email)
                    VALUES (?, ?, ?, ?, ?)
                """, (matricula, nombre, carrera, semestre, email))
                inserted += 1
                print(f"✅ Insertado: {matricula} - {nombre}")
        
        except Exception as e:
            errors += 1
            print(f"❌ Error en fila {index + 1}: {e}")
            continue
    
    # Guardar cambios
    conn.commit()
    conn.close()
    
    # Resumen
    print("\n" + "="*50)
    print("📊 RESUMEN DE IMPORTACIÓN")
    print("="*50)
    print(f"✅ Estudiantes insertados: {inserted}")
    print(f"🔄 Estudiantes actualizados: {updated}")
    print(f"❌ Errores: {errors}")
    print(f"📈 Total procesado: {inserted + updated + errors}")
    print("="*50)

if __name__ == "__main__":
    # Ruta al archivo Excel (ajusta según sea necesario)
    excel_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alumnos.xlsx")
    
    if not os.path.exists(excel_path):
        print(f"❌ No se encontró el archivo: {excel_path}")
        print("\n💡 Coloca el archivo 'alumnos.xlsx' en la carpeta raíz del proyecto")
        print("   O especifica la ruta correcta en el script")
        sys.exit(1)
    
    print("🚀 IMPORTADOR DE ESTUDIANTES")
    print("="*50)
    
    import_students_from_excel(excel_path)
    
    print("\n✨ ¡Importación completada!")
