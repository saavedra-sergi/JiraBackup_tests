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
    
    try:
        response = requests.post(endpoint, json=payload, auth=auth, headers=headers, timeout=30)
        
        # --- MANEJO DE ERRORES ESPECÍFICO ---
        if response.status_code == 403:
            print("\n" + "="*50)
            print("AVISO DE SEGURIDAD / LÍMITE DE JIRA")
            print("Jira ha denegado la petición (Error 403).")
            print("Causas probables:")
            print("1. Ya se ejecutó un backup en las últimas 24 horas (límite de Atlassian).")
            print("2. Tu usuario ha perdido temporalmente los permisos de administrador.")
            print("Acción: Revisa el 'Backup Manager' en la web de Jira.")
            print("="*50 + "\n")
            return # Salimos elegantemente sin que GitHub marque fallo crítico

        elif response.status_code == 401:
            print("ERROR: Credenciales inválidas. Revisa tu API Token y User Email.")
            sys.exit(1)

        # Si llegamos aquí, es que ha ido bien (Status 200)
        response.raise_for_status()
        
        data = response.json()
        task_id = data.get("taskId")
        
        print(f"Backup iniciado con éxito. Task ID: {task_id}")

        # 3. Paso B: El Bucle de espera (Polling)
        status = "IN_PROGRESS"
        file_id = None

        # Mientras esté en cola o procesando, esperamos
        while status in ["IN_PROGRESS", "QUEUED"]:
            print(f"Estado actual: {status}. Esperando 30 segundos...")
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
                print(f"El backup falló en Jira: {progress_data}")
                sys.exit(1)

        # 4. Paso C: Descarga del archivo real
        if file_id:
            download_url = f"{base_url}/plugins/servlet/export/download/?fileId={file_id}"
            print(f"Descargando archivo desde: {download_url}")
            
            # Usamos stream=True para no saturar la memoria RAM
            with requests.get(download_url, auth=auth, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open("scripts/jira_backup.zip", "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            print("Archivo guardado con éxito: scripts/jira_backup.zip")

    except Exception as e:
        print(f"Error durante el proceso: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_backup()
