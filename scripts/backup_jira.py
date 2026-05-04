import os
import requests
from requests.auth import HTTPBasicAuth
import sys
import time

def download_file(url, auth, headers, filename):
    """Función para descargar el archivo .zip"""
    print(f"📥 Intentando descargar archivo desde: {url}")
    try:
        with requests.get(url, auth=auth, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            # Aseguramos que la carpeta scripts existe
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"💾 Archivo guardado con éxito: {filename}")
        return True
    except Exception as e:
        print(f"❌ Error durante la descarga: {e}")
        return False

def run_backup():
    # 1. Credenciales
    url = os.getenv("JIRA_URL")
    user = os.getenv("JIRA_USER_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")

    if not all([url, user, token]):
        print("❌ Error: Faltan secretos (JIRA_URL, USER_EMAIL o TOKEN) en GitHub")
        sys.exit(1)

    auth = HTTPBasicAuth(user, token)
    base_url = url.rstrip('/')
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Atlassian-Token": "no-check",
        "User-Agent": "Mozilla/5.0"
    }

    # 2. Definición de rutas (URLs)
    endpoint_run = f"{base_url}/rest/backup/1/export/runbackup"
    endpoint_last = f"{base_url}/rest/backup/1/export/lastsuccessful"
    endpoint_progress = f"{base_url}/rest/backup/1/export/getProgress"

    print("🚀 Iniciando proceso de backup...")

    # 3. INTENTO 1: Lanzar nuevo backup
    try:
        response = requests.post(endpoint_run, json={"cbAttachments": "true", "exportToCloud": "true"}, auth=auth, headers=headers)
        
        if response.status_code == 200:
            task_id = response.json().get("taskId")
            print(f"✅ Nuevo backup solicitado. Task ID: {task_id}")
            
            # Bucle de espera (Polling)
            status = "IN_PROGRESS"
            while status in ["IN_PROGRESS", "QUEUED"]:
                print(f"⏳ Procesando... ({status}). Esperando 30s.")
                time.sleep(30)
                prog_resp = requests.get(f"{endpoint_progress}?taskId={task_id}", auth=auth, headers=headers)
                prog_data = prog_resp.json()
                status = prog_data.get("status")
                
                if status == "SUCCESS":
                    file_id = prog_data.get("result")
                    download_url = f"{base_url}/plugins/servlet/export/download/?fileId={file_id}"
                    download_file(download_url, auth, headers, "scripts/jira_backup.zip")
                    return

        elif response.status_code == 403:
            print("⚠️ Jira denegó el nuevo backup (límite de 24/48h).")
            print("🔄 Plan C: Consultando estado del último backup ejecutado...")
            
            # Intentamos obtener el progreso general (sin taskId)
            progress_url = f"{base_url}/rest/backup/1/export/getProgress"
            last_resp = requests.get(progress_url, auth=auth, headers=headers)
            print(f"📡 Respuesta de Progreso (Status {last_resp.status_code}): {last_resp.text}")

            if last_resp.status_code == 200:
                data = last_resp.json()
                # Buscamos el ID del archivo en el campo 'result'
                file_id = data.get("result")
                
                if file_id:
                    print(f"📂 ¡Encontrado! ID de archivo: {file_id}")
                    download_url = f"{base_url}/plugins/servlet/export/download/?fileId={file_id}"
                    if download_file(download_url, auth, headers, "scripts/jira_backup.zip"):
                        print("✅ Finalizado con éxito usando el último backup disponible.")
                        return
                else:
                    print("❌ El backup existe pero el archivo ya no está disponible para descarga (Atlassian los borra tras 4h-24h).")
            
            sys.exit(1)

    except Exception as e:
        print(f"💥 Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_backup()
