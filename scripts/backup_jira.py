payload = {
    "cbAttachments": "true", # ¿Quieres incluir archivos adjuntos?
    "exportToCloud": "true"
}

response = requests.post(
    f"{JIRA_URL}/rest/backup/1/export/runbackup",
    json=payload,
    auth=auth
)

print(response.json())
