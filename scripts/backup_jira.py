import os
import requests
from requests.auth import HTTPBasicAuth
import sys

def run_backup():
    # 1. Leer variables
    url = os.getenv("JIRA_URL")
    user = os.getenv("JIRA_USER_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")

    if not all([url, user, token]):
        print("❌ Error: Faltan secretos en GitHub")
        sys.exit(1)

    auth = HTTPBasicAuth(user, token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    # 2. Configurar la petición
    # Nota: Algunos Jira Cloud usan /rest/backup/1/export/runbackup
    endpoint = f"{url.rstrip('/')}/rest/backup/1/export/runbackup"
    payload = {"cbAttachments": "true", "exportToCloud": "true"}

    print(f"🚀 Lanzando backup en: {endpoint}")

    try:
        response = requests.post(endpoint, json=payload, auth=auth, headers=headers)
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📝 Respuesta: {response.text}")
        
        response.raise_for_status()
        print("✅ Backup iniciado correctamente")

    except Exception as e:
        print(f"💥 Error crítico durante la ejecución: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_backup()
