import os
import folium
import pandas as pd
import re
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
excel_file = os.path.join(BASE_DIR, "Europese_Hoofdsteden_1999_met_IDs.xlsx")

# Lees credentials uit GitHub Secret
creds_json = os.environ.get("GDRIVE_CREDENTIALS")
if not creds_json:
    raise RuntimeError("❌ Geen GDRIVE_CREDENTIALS secret gevonden")

creds_dict = json.loads(creds_json)

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
service = build('drive', 'v3', credentials=creds)

def get_first_photo_from_folder(folder_id):
    query = f"'{folder_id}' in parents and (mimeType contains 'image/jpeg' or mimeType contains 'image/png')"
    results = service.files().list(
        q=query, orderBy="createdTime asc", pageSize=1, fields="files(id,name)"
    ).execute()
    files = results.get('files', [])
    if files:
        file_id = files[0]['id']
        return f"https://drive.google.com/uc?export=view&id={file_id}"
    return None

def gdrive_file_id(url):
    if not isinstance(url, str):
        return None, None
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1), "file"
    match = re.search(r"folders/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1), "folder"
    return None, None

df = pd.read_excel(excel_file)
df["FotoURL"] = None

m = folium.Map(location=[54, 15], zoom_start=4)

for idx, row in df.iterrows():
    land = row["Land"]
    stad = row["Hoofdstad"]
    lat, lon = row["Lat"], row["Lon"]
    bezocht = str(row.get("Bezocht", "")).strip().upper()
    gdrive = row.get("GoogleDriveURL", "")

    foto_url = None
    if gdrive:
        file_id, kind = gdrive_file_id(gdrive)
        if kind == "file":
            foto_url = f"https://drive.google.com/uc?export=view&id={file_id}"
        elif kind == "folder":
            foto_url = get_first_photo_from_folder(file_id)

    df.at[idx, "FotoURL"] = foto_url

    if pd.notna(lat) and pd.notna(lon):
        color = "green" if bezocht == "X" else "red"
        popup_html = f"<b>{stad}, {land}</b><br>"
        popup_html += f"Bezocht: {'Ja' if color=='green' else 'Nee'}<br>"
        if gdrive:
            popup_html += f"<a href='{gdrive}' target='_blank'>📂 Google Drive map</a><br>"
        if foto_url:
            popup_html += f"<img src='{foto_url}' width='250'><br>"
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{stad}, {land}",
            icon=folium.Icon(color=color)
        ).add_to(m)

# Output
out_file = os.path.join(BASE_DIR, "index.html")
m.save(out_file)
df.to_excel(os.path.join(BASE_DIR, "Europese_Hoofdsteden_met_Fotos.xlsx"), index=False)
print(f"✅ Kaart en Excel gegenereerd")
