payload = {
    "cbAttachments": "true", # ¿Quieres incluir archivos adjuntos?
    "exportToCloud": "true"
}

response = requests.post(
    f"{JIRA_URL}/rest/backup/1/export/runbackup",
    json=payload,
    auth=auth
)

# Esto imprimirá el código (401, 403, 400, etc.) y el texto del error
print(f"Status Code: {response.status_code}")
print(f"Respuesta de Jira: {response.text}")

# Esto forzará al script a fallar si hay un error, pero habiendo impreso lo de arriba
response.raise_for_status()

