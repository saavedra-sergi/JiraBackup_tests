import os
import requests
from requests.auth import HTTPBasicAuth
import sys
import time

def download_file(url, auth, headers, filename):
    """Descarga el archivo final al disco"""
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
        "User-Agent": "Mozilla/5.0"
    }

    # 2. Configuración del Backup (Paridad con el de tu jefe)
    endpoint_run = f"{base_url}/rest/backup/1/export/runbackup"
    payload = {
        "cbAttachments": "true",    # Incluye adjuntos
        "exportToCloud": "true",    # Obligatorio para Cloud
        "cbAvatars": "true",        # Incluye logos/iconos
        "cbCustomFields": "true",   # Campos personalizados
        "cbWorklogs": "true"        # Registro de horas
    }

    print("Iniciando proceso de backup...")
    print(f"Conectando a: {endpoint_run}...") # <-- Nueva línea de estado

    try:
        # Añadimos un timeout para que no se quede colgado eternamente
        response = requests.post(
            endpoint_run, 
            json=payload, 
            auth=auth, 
            headers=headers,
            timeout=60 # Esperamos hasta 60s a que Jira responda
        )
        
        print(f"Respuesta recibida (Status: {response.status_code})") # <-- Nueva línea

    # 3. EJECUCIÓN
    try:
        # Intento lanzar el backup
        response = requests.post(endpoint_run, json=payload, auth=auth, headers=headers)
        
        if response.status_code == 200:
            task_id = response.json().get("taskId")
            print(f"Nuevo backup solicitado. Task ID: {task_id}")
            
            # Polling (Espera)
            status = "IN_PROGRESS"
            while status in ["IN_PROGRESS", "QUEUED"]:
                print(f"Estado: {status}. Esperando 30s...")
                time.sleep(30)
                prog_resp = requests.get(f"{base_url}/rest/backup/1/export/getProgress?taskId={task_id}", auth=auth, headers=headers)
                prog_data = prog_resp.json()
                status = prog_data.get("status")
                
                if status == "SUCCESS":
                    file_id = prog_data.get("result")
                    download_url = f"{base_url}/plugins/servlet/export/download/?fileId={file_id}"
                    download_file(download_url, auth, headers, "scripts/jira_backup.zip")
                    return

        elif response.status_code == 403:
            print("Límite de 24h detectado. Saltando a descargar el último disponible...")
            # Plan B: Descargar el último progreso registrado
            progress_resp = requests.get(f"{base_url}/rest/backup/1/export/getProgress", auth=auth, headers=headers)
            if progress_resp.status_code == 200:
                file_id = progress_resp.json().get("result")
                if file_id:
                    print(f"Encontrado backup previo (ID: {file_id})")
                    download_url = f"{base_url}/plugins/servlet/export/download/?fileId={file_id}"
                    download_file(download_url, auth, headers, "scripts/jira_backup.zip")
                    return
            print("No hay backups recientes disponibles para descargar.")
            
    except Exception as e:
        print(f"Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_backup()
