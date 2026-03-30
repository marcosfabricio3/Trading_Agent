import sqlite3
import os

# La base de datos real según db_server.py es trading.db
db_path = "trading.db"

if not os.path.exists(db_path):
     # Intentamos buscarla en la raíz si el script se corre desde app/
    if os.path.exists("../trading.db"):
        db_path = "../trading.db"

if not os.path.exists(db_path):
    print(f"Error: No se encontró la base de datos en {db_path}")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # En db_server.py, un trade es "activo" si exit_price es NULL.
        # Vamos a ponerle un exit_price a todo lo que esté abierto para limpiar el bucle.
        print(f"Conectado a {db_path}. Limpiando trades zombis...")
        
        cursor.execute("UPDATE trades SET exit_price = entry_price WHERE exit_price IS NULL")
        changes = conn.total_changes
        conn.commit()
        
        print(f"Éxito: Se han 'cerrado' {changes} trades. El bucle debería detenerse ahora.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
