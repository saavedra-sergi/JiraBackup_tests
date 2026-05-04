import os
import requests
from requests.auth import HTTPBasicAuth
import sys
import time

def download_file(url, auth, headers, filename):
    """Función auxiliar para descargar el archivo"""
    print(f"📥 Descargando archivo desde: {url}")
    try:
        with requests.get(url, auth=auth, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"💾 Archivo guardado con éxito: {filename}")
        return True
    except Exception as e:
        print(f"❌ Error al descargar: {e}")
        return False

def run_backup():
    # 1. Configuración de credenciales
    url = os.getenv("JIRA_URL")
    user = os.getenv("JIRA_USER_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")

    if not all([url, user, token]):
        print("Error: Faltan secretos en GitHub")
        sys.exit(1)

    auth = HTTPBasicAuth(user, token)
    base_url = url.rstrip('/')
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Atlassian-Token": "no-check",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    # 2. Paso A: Lanzar la petición de Backup
    endpoint = f"{base_url}/rest/backup/1/export/runbackup"
    payload = {"cbAttachments": "true", "exportToCloud": "true"}

    print(f"🚀 Lanzando petición de backup a Jira...")
    
    response = requests.post(run_url, json=payload, auth=auth, headers=headers)

    if response.status_code == 200:
        task_id = response.json().get("taskId")
        print(f"✅ Nuevo backup iniciado. Task ID: {task_id}")
        # Aquí iría tu bucle 'while' de espera que ya programamos...
        # (Por brevedad, asumo que el bucle termina dándote un file_id)
        # ... lógica de polling ...
        
    elif response.status_code == 403:
        print("⚠️ Jira denegó el nuevo backup (límite de 48h).")
        print("🔄 Buscando el último backup existente para descargar...")
        
        # --- INTENTO 2: DESCARGAR EL ÚLTIMO EXITOSO ---
        last_url = f"{base_url}/rest/backup/1/export/lastsuccessful"
        last_resp = requests.get(last_url, auth=auth, headers=headers)
        
        if last_resp.status_code == 200 and last_resp.text:
            # Jira devuelve directamente el nombre del archivo o un string
            file_id = last_resp.text.strip('"') 
            print(f"📂 Encontrado backup previo: {file_id}")
            
            download_url = f"{base_url}/plugins/servlet/export/download/?fileId={file_id}"
            download_file(download_url, auth, headers, "scripts/jira_backup.zip")
        else:
            print("❌ No se encontró ningún backup previo disponible.")
            sys.exit(1)
    else:
        print(f"❌ Error inesperado: {response.status_code}")
        sys.exit(1)

if __name__ == "__main__":
    run_backup()
