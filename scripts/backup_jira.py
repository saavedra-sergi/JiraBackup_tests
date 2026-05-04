import os
import requests
from requests.auth import HTTPBasicAuth
import sys
import time

def run_backup():
    # 1. Configuración de credenciales
    url = os.getenv("JIRA_URL")
    user = os.getenv("JIRA_USER_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")

    if not all([url, user, token]):
        print("❌ Error: Faltan secretos en GitHub")
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
    
    try:
        response = requests.post(endpoint, json=payload, auth=auth, headers=headers)
        response.raise_for_status()
        
        # Extraemos el taskId que nos da Jira para seguir el progreso
        data = response.json()
        task_id = data.get("taskId")
        print(f"✅ Backup iniciado. ID de tarea: {task_id}")

        # 3. Paso B: El Bucle de espera (Polling)
        status = "IN_PROGRESS"
        file_id = None

        # Mientras esté en cola o procesando, esperamos
        while status in ["IN_PROGRESS", "QUEUED"]:
            print(f"⏳ Estado actual: {status}. Esperando 30 segundos...")
            time.sleep(30)
            
            # Consultamos el progreso usando el taskId
            progress_url = f"{base_url}/rest/backup/1/export/getProgress?taskId={task_id}"
            progress_resp = requests.get(progress_url, auth=auth, headers=headers)
            progress_data = progress_resp.json()
            
            status = progress_data.get("status")
            
            if status == "SUCCESS":
                file_id = progress_data.get("result")
                print("🎉 ¡Backup completado en el servidor!")
                break
            elif status == "FAILED":
                print(f"❌ El backup falló en Jira: {progress_data}")
                sys.exit(1)

        # 4. Paso C: Descarga del archivo real
        if file_id:
            download_url = f"{base_url}/plugins/servlet/export/download/?fileId={file_id}"
            print(f"📥 Descargando archivo desde: {download_url}")
            
            # Usamos stream=True para no saturar la memoria RAM
            with requests.get(download_url, auth=auth, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open("scripts/jira_backup.zip", "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            print("💾 Archivo guardado con éxito: scripts/jira_backup.zip")

    except Exception as e:
        print(f"💥 Error durante el proceso: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_backup()
