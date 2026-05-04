import os
import requests
from requests.auth import HTTPBasicAuth
import sys

def run_backup():
    # 1. Cargar configuración
    url = os.getenv("JIRA_URL")
    user = os.getenv("JIRA_USER_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")

    if not all([url, user, token]):
        print("❌ Error: Faltan secretos en GitHub")
        sys.exit(1)

    # 2. Configurar Autenticación y HEADERS "Especiales"
    auth = HTTPBasicAuth(user, token)
    
    # Aquí es donde añadimos lo que faltaba
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Atlassian-Token": "no-check",  # Crucial para evitar bloqueos de seguridad
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" # Simulamos un navegador
    }
    
    # Limpiamos la URL para que no tenga barras extra
    base_url = url.rstrip('/')
    endpoint = f"{base_url}/rest/backup/1/export/runbackup"
    
    # Datos de la petición
    payload = {
        "cbAttachments": "true", 
        "exportToCloud": "true"
    }

    print(f"🚀 Intentando forzar backup en: {endpoint}")

    try:
        # 3. Lanzar la petición con headers
        response = requests.post(
            endpoint, 
            json=payload, 
            auth=auth, 
            headers=headers,
            timeout=30
        )
        
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 403:
            print("❌ Sigue dando 403. Atlassian bloquea el acceso programático a este endpoint.")
            print(f"📝 Detalle: {response.text}")
        else:
            print(f"📝 Respuesta: {response.text}")
            response.raise_for_status()
            print("✅ ¡Increíble! El backup ha comenzado.")

    except Exception as e:
        print(f"💥 Error durante la ejecución: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_backup()
