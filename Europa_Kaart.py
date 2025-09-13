import os
import folium
import pandas as pd

# Basisdir = de map waar dit script staat
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Excel-bestand met data
excel_file = os.path.join(BASE_DIR, "Europese_Hoofdsteden_1999_met_IDs.xlsx")

# Lees Excel in
df = pd.read_excel(excel_file)

# Maak kaart
m = folium.Map(location=[54, 15], zoom_start=4)

for _, row in df.iterrows():
    land = row["Land"]
    stad = row["Hoofdstad"]
    lat = row["Lat"]
    lon = row["Lon"]
    bezocht = str(row.get("Bezocht", "")).strip().upper()
    gdrive = row.get("GoogleDriveURL", "")

    if pd.notna(lat) and pd.notna(lon):
        # marker kleur
        color = "green" if bezocht == "X" else "red"

        # zoek foto in folder die gelijk heet aan de hoofdstad
        photo_path = None
        city_folder = os.path.join(BASE_DIR, stad)
        if os.path.exists(city_folder):
            for f in os.listdir(city_folder):
                if f.lower().endswith((".jpg", ".jpeg", ".png")):
                    photo_path = os.path.join(city_folder, f)
                    break

        # popup html
        popup_html = f"<b>{stad}, {land}</b><br>"
        popup_html += f"Bezocht: {'Ja' if color=='green' else 'Nee'}<br>"

        if gdrive and isinstance(gdrive, str):
            popup_html += f"<a href='{gdrive}' target='_blank'>📂 Google Drive map</a><br>"

        if photo_path:
            rel_path = os.path.relpath(photo_path, BASE_DIR)
            popup_html += f"<img src='{rel_path}' width='250'><br>"

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{stad}, {land}",
            icon=folium.Icon(color=color)
        ).add_to(m)

# opslaan
out_file = os.path.join(BASE_DIR, "europese_hoofdsteden.html")
m.save(out_file)
print(f"✅ Kaart opgeslagen: {out_file}")
