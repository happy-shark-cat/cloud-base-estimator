import requests
import streamlit as st
from PIL import Image
import folium
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation


def estimate_cloud_base_m(temperature_c: float, dew_point_c: float) -> float:
    """
    Estimate cloud base height above ground level.
    Simple LCL approximation: cloud base ≒ 125 × (T - Td) meters.
    """
    spread = max(0.0, temperature_c - dew_point_c)
    return 125.0 * spread


def fetch_weather(latitude: float, longitude: float) -> dict:
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


st.set_page_config(
    page_title="Cloud Base Estimator",
    page_icon="☁️",
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

# Default location: Fukuoka City
if "latitude" not in st.session_state:
    st.session_state.latitude = 33.5902

if "longitude" not in st.session_state:
    st.session_state.longitude = 130.4017


st.subheader("1. Upload a sky photo")

uploaded_file = st.file_uploader(
    "Upload a sky photo",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded sky photo", use_container_width=True)
else:
    st.info("Photo upload is optional in this version.")


st.subheader("2. Select location")

st.write(
    "Use your current location or click on the map to select a location."
)

st.write("### Get current location")

location = streamlit_geolocation()

if location:
    current_lat = location.get("latitude")
    current_lon = location.get("longitude")
    accuracy = location.get("accuracy")

    if current_lat is not None and current_lon is not None:
        st.session_state.latitude = float(current_lat)
        st.session_state.longitude = float(current_lon)

        if accuracy is not None:
            st.success(
                f"Current location set: "
                f"{st.session_state.latitude:.6f}, {st.session_state.longitude:.6f} "
                f"(accuracy: about {accuracy:.0f} m)"
            )
        else:
            st.success(
                f"Current location set: "
                f"{st.session_state.latitude:.6f}, {st.session_state.longitude:.6f}"
            )

st.write("### Select location on map")

m = folium.Map(
    location=[st.session_state.latitude, st.session_state.longitude],
    zoom_start=12,
)

folium.Marker(
    [st.session_state.latitude, st.session_state.longitude],
    popup="Selected location",
    tooltip="Selected location",
).add_to(m)

map_data = st_folium(
    m,
    width=700,
    height=450,
)

if map_data and map_data.get("last_clicked"):
    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lon = map_data["last_clicked"]["lng"]

    st.session_state.latitude = clicked_lat
    st.session_state.longitude = clicked_lon

    st.info(
        f"Map location selected: "
        f"{st.session_state.latitude:.6f}, {st.session_state.longitude:.6f}"
    )

col1, col2 = st.columns(2)

with col1:
    st.session_state.latitude = st.number_input(
        "Latitude",
        value=float(st.session_state.latitude),
        format="%.6f",
    )

with col2:
    st.session_state.longitude = st.number_input(
        "Longitude",
        value=float(st.session_state.longitude),
        format="%.6f",
    )


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
            estimated_height = estimate_cloud_base_m(temperature, dew_point)

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
                f"Cloud base ≒ 125 × ({temperature} - {dew_point}) = {estimated_height:.0f} m",
                language="text",
            )

            st.caption(
                "AGL means above ground level. "
                "This is a simplified estimate based on surface temperature and dew point."
            )

    except requests.RequestException as error:
        st.error(f"Failed to fetch weather data: {error}")
