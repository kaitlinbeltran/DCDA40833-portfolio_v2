import pandas as pd
import requests
import folium
from folium import IFrame
from pathlib import Path
from urllib.parse import quote

BASE_DIR = Path(__file__).resolve().parent

# -----------------------------
# MAPBOX SETTINGS
# -----------------------------
ACCESS_TOKEN = "pk.eyJ1Ijoia25iZWx0cmFuIiwiYSI6ImNtbHRtdjY0YjAxeDYzaHEza2U5Z21kNWwifQ.FgPKid1mboThBtUvISfO-Q"
STYLE_URL = "mapbox://styles/knbeltran/cmmjqti87001u01rz4zcf9ffr"

# Convert Mapbox style URL to tile URL for Folium
style_parts = STYLE_URL.replace("mapbox://styles/", "").split("/")
username = style_parts[0]
style_id = style_parts[1]

tiles_url = (
    f"https://api.mapbox.com/styles/v1/{username}/{style_id}/tiles/256/"
    f"{{z}}/{{x}}/{{y}}@2x?access_token={ACCESS_TOKEN}"
)

# -----------------------------
# READ CSV
# -----------------------------
df = pd.read_csv(BASE_DIR / "hometown_locations.csv")

# -----------------------------
# GEOCODING FUNCTION
# -----------------------------
def geocode_address(address: str, access_token: str):
    encoded_address = quote(address)
    url = (
        f"https://api.mapbox.com/search/geocode/v6/forward"
        f"?q={encoded_address}&access_token={access_token}"
    )

    response = requests.get(url)
    data = response.json()

    if "features" in data and len(data["features"]) > 0:
        coords = data["features"][0]["geometry"]["coordinates"]
        lon, lat = coords[0], coords[1]
        return lat, lon
    else:
        return None, None

# -----------------------------
# GEOCODE ALL LOCATIONS
# -----------------------------
latitudes = []
longitudes = []

for address in df["Address"]:
    lat, lon = geocode_address(address, ACCESS_TOKEN)
    latitudes.append(lat)
    longitudes.append(lon)

df["Latitude"] = latitudes
df["Longitude"] = longitudes

# Drop rows that failed to geocode
df = df.dropna(subset=["Latitude", "Longitude"])

# Optional: save geocoded version
df.to_csv(BASE_DIR / "hometown_locations_geocoded.csv", index=False)

# -----------------------------
# MAP CENTER
# -----------------------------
center_lat = df["Latitude"].mean()
center_lon = df["Longitude"].mean()

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=11,
    tiles=tiles_url,
    attr="Mapbox"
)

# -----------------------------
# TYPE-BASED MARKER COLORS
# -----------------------------
color_dict = {
    "Restaurant": "red",
    "Recreation": "green",
    "Cultural": "purple",
    "Shopping": "orange",
    "Local Business": "blue",
    "Worship": "cadetblue"
}

# -----------------------------
# ADD MARKERS WITH POPUPS
# -----------------------------
for _, row in df.iterrows():
    location_type = row["Type"]
    marker_color = color_dict.get(location_type, "gray")

    popup_html = f"""
    <div style="width:250px;">
        <h4>{row['Name']}</h4>
        <p><strong>Type:</strong> {row['Type']}</p>
        <p>{row['Description']}</p>
        <img src="{row['Image_URL']}" width="230">
    </div>
    """

    iframe = IFrame(html=popup_html, width=270, height=320)
    popup = folium.Popup(iframe, max_width=300)

    folium.Marker(
        location=[row["Latitude"], row["Longitude"]],
        popup=popup,
        tooltip=row["Name"],
        icon=folium.Icon(color=marker_color, icon="info-sign")
    ).add_to(m)

# -----------------------------
# SAVE MAP
# -----------------------------
m.save(BASE_DIR / "hometown_map.html")

print("Map created successfully! Saved as hometown_map.html")
