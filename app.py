import requests
import streamlit as st
from PIL import Image
import folium
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation


# -----------------------------
# Calculation
# -----------------------------
def estimate_cloud_base_m(temperature_c: float, dew_point_c: float) -> float:
    """
    Estimate cloud base height above ground level.
    Simple LCL approximation:
    Cloud base height ≒ 125 × (Temperature - Dew point) meters
    """
    spread = max(0.0, temperature_c - dew_point_c)
    return 125.0 * spread


# -----------------------------
# Weather API
# -----------------------------
def fetch_weather(latitude: float, longitude: float) -> dict:
    """
    Fetch current weather data from Open-Meteo.
    """
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,dew_point_2m,cloud_cover",
        "timezone": "auto",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    return data.get("current", {})


# -----------------------------
# Streamlit page settings
# -----------------------------
st.set_page_config(
    page_title="Cloud Base Estimator",
    page_icon="☁️",
    layout="centered",
)

st.title("☁️ Cloud Base Estimator")

st.write(
    "Estimate cloud base height from temperature and dew point. "
    "Sky photo upload is optional and used for visual reference only."
)

st.warning(
    "This app is for learning and visualization purposes only. "
    "Do not use it for aviation, navigation, or safety-critical decision-making."
)


# -----------------------------
# Session state initialization
# -----------------------------
# Default location: Fukuoka City
DEFAULT_LATITUDE = 33.5902
DEFAULT_LONGITUDE = 130.4017
DEFAULT_ZOOM = 12

if "latitude" not in st.session_state:
    st.session_state.latitude = DEFAULT_LATITUDE

if "longitude" not in st.session_state:
    st.session_state.longitude = DEFAULT_LONGITUDE

if "map_center" not in st.session_state:
    st.session_state.map_center = [
        st.session_state.latitude,
        st.session_state.longitude,
    ]

if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = DEFAULT_ZOOM


# -----------------------------
# 1. Photo upload
# -----------------------------
st.subheader("1. Upload a sky photo")

uploaded_file = st.file_uploader(
    "Upload a sky photo",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(
        image,
        caption="Uploaded sky photo",
        use_container_width=True,
    )
else:
    st.info("Photo upload is optional in this version.")


# -----------------------------
# 2. Location selection
# -----------------------------
st.subheader("2. Select location")

st.write(
    "Use your current location or move the map and click the point "
    "where you want to estimate cloud base height."
)

# Current location
st.write("### Use current location")

location = streamlit_geolocation()

if isinstance(location, dict):
    current_lat = location.get("latitude")
    current_lon = location.get("longitude")
    accuracy = location.get("accuracy")

    if current_lat is not None and current_lon is not None:
        st.session_state.latitude = float(current_lat)
        st.session_state.longitude = float(current_lon)

        st.session_state.map_center = [
            st.session_state.latitude,
            st.session_state.longitude,
        ]
        st.session_state.map_zoom = 13

        if accuracy is not None:
            st.success(
                f"Current location set: "
                f"{st.session_state.latitude:.6f}, "
                f"{st.session_state.longitude:.6f} "
                f"(accuracy: about {accuracy:.0f} m)"
            )
        else:
            st.success(
                f"Current location set: "
                f"{st.session_state.latitude:.6f}, "
                f"{st.session_state.longitude:.6f}"
            )


# Map selection
st.write("### Select location on map")

st.caption(
    "Drag the map to move around. Click on the map to select the estimation point."
)

m = folium.Map(
    location=st.session_state.map_center,
    zoom_start=st.session_state.map_zoom,
    control_scale=True,
)

folium.Marker(
    location=[
        st.session_state.latitude,
        st.session_state.longitude,
    ],
    popup="Selected location",
    tooltip="Selected location",
).add_to(m)

map_data = st_folium(
    m,
    width=700,
    height=450,
    returned_objects=[
        "last_clicked",
        "center",
        "zoom",
    ],
    key="location_map",
)

if map_data:
    # Keep current map view when user drags or zooms the map
    center = map_data.get("center")
    if isinstance(center, dict):
        center_lat = center.get("lat")
        center_lng = center.get("lng")

        if center_lat is not None and center_lng is not None:
            st.session_state.map_center = [
                center_lat,
                center_lng,
            ]

    zoom = map_data.get("zoom")
    if zoom is not None:
        st.session_state.map_zoom = zoom

    # Update selected point when user clicks on the map
    last_clicked = map_data.get("last_clicked")
    if isinstance(last_clicked, dict):
        clicked_lat = last_clicked.get("lat")
        clicked_lon = last_clicked.get("lng")

        if clicked_lat is not None and clicked_lon is not None:
            st.session_state.latitude = float(clicked_lat)
            st.session_state.longitude = float(clicked_lon)

            st.info(
                f"Map location selected: "
                f"{st.session_state.latitude:.6f}, "
                f"{st.session_state.longitude:.6f}"
            )


# Manual latitude / longitude input
st.write("### Confirm or edit coordinates")

col1, col2 = st.columns(2)

with col1:
    latitude_input = st.number_input(
        "Latitude",
        value=float(st.session_state.latitude),
        format="%.6f",
    )

with col2:
    longitude_input = st.number_input(
        "Longitude",
        value=float(st.session_state.longitude),
        format="%.6f",
    )

# Reflect manual input
st.session_state.latitude = float(latitude_input)
st.session_state.longitude = float(longitude_input)


# -----------------------------
# 3. Estimate cloud base
# -----------------------------
st.subheader("3. Estimate cloud base")

if st.button("Fetch weather and estimate"):
    try:
        current = fetch_weather(
            st.session_state.latitude,
            st.session_state.longitude,
        )

        temperature = current.get("temperature_2m")
        dew_point = current.get("dew_point_2m")
        cloud_cover = current.get("cloud_cover")
        observed_time = current.get("time")

        if temperature is None or dew_point is None:
            st.error("Could not retrieve temperature or dew point data.")
        else:
            estimated_height = estimate_cloud_base_m(
                float(temperature),
                float(dew_point),
            )

            st.metric(
                label="Estimated cloud base height",
                value=f"{estimated_height:.0f} m AGL",
            )

            st.write("### Selected location")
            st.write(f"- Latitude: {st.session_state.latitude:.6f}")
            st.write(f"- Longitude: {st.session_state.longitude:.6f}")

            st.write("### Weather data")
            st.write(f"- Time: {observed_time}")
            st.write(f"- Temperature: {temperature} °C")
            st.write(f"- Dew point: {dew_point} °C")
            st.write(f"- Cloud cover: {cloud_cover} %")

            st.write("### Calculation")
            st.code(
                f"Cloud base ≒ 125 × ({temperature} - {dew_point}) "
                f"= {estimated_height:.0f} m",
                language="text",
            )

            st.caption(
                "AGL means above ground level. "
                "This is a simplified estimate based on surface temperature and dew point."
            )

    except requests.RequestException as error:
        st.error(f"Failed to fetch weather data: {error}")
