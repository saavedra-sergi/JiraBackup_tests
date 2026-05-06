import os
import requests
from requests.auth import HTTPBasicAuth
import sys
import time

def download_file(url, auth, headers, filename):
    print(f"Intentando descargar archivo desde: {url}")
    try:
        with requests.get(url, auth=auth, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Archivo guardado con éxito: {filename}")
        return True
    except Exception as e:
        print(f"Error durante la descarga: {e}")
        return False

def run_backup():
    # 1. Configuración
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
        "User-Agent": "Mozilla/5.0"
    }

    endpoint_run = f"{base_url}/rest/backup/1/export/runbackup"
    
    payload = {
        "cbAttachments": True,
        "exportToCloud": True
    }

    print("Iniciando proceso de backup profesional...")

    # 2. Bloque Try/Except Robusto
    try:
        print(f"Conectando a Jira: {endpoint_run}")
        response = requests.post(endpoint_run, json=payload, auth=auth, headers=headers, timeout=60)
        print(f"Respuesta recibida (Status: {response.status_code})")

        if response.status_code == 200:
            task_id = response.json().get("taskId")
            print(f"Nuevo backup solicitado. Task ID: {task_id}")
            
            status = "IN_PROGRESS"
            while status in ["IN_PROGRESS", "QUEUED"]:
                print(f"⏳ Estado: {status}. Esperando 30s...")
                time.sleep(30)
                prog_resp = requests.get(f"{base_url}/rest/backup/1/export/getProgress?taskId={task_id}", auth=auth, headers=headers)
                prog_data = prog_resp.json()
                status = prog_data.get("status")
                
                if status == "SUCCESS":
                    file_id = prog_data.get("result")
                    d_url = f"{base_url}/plugins/servlet/export/download/?fileId={file_id}"
                    download_file(d_url, auth, headers, "scripts/jira_backup.zip")
                    return
        elif response.status_code == 403:
            print("⚠️ Error 403: Acceso denegado.")
            # Esto nos dirá la razón real del bloqueo
            reason = response.headers.get('X-Seraph-LoginReason')
            auth_status = response.headers.get('X-Authentication-Denied-Reason')
            
            print(f"🔍 Motivo de Jira (Seraph): {reason}")
            print(f"🔍 Motivo de Autenticación: {auth_status}")
            
            # El resto del Plan B...
        
        else:
            print(f"Error de Jira: {response.text}")

    except Exception as e:
        print(f"Error crítico en el script: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_backup()
