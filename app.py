import requests
import streamlit as st
from PIL import Image


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
    "Estimate cloud base height from temperature, dew point, location, and sky photos."
)

st.warning(
    "This app is for learning and visualization purposes only. "
    "Do not use it for aviation, navigation, or safety-critical decision-making."
)

st.subheader("1. Upload a sky photo")

uploaded_file = st.file_uploader(
    "Upload a sky photo",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded sky photo", use_container_width=True)
else:
    st.info("Photo upload is optional in this first version.")

st.subheader("2. Enter location")

col1, col2 = st.columns(2)

with col1:
    latitude = st.number_input(
        "Latitude",
        value=33.5902,
        format="%.6f",
        help="Example: Fukuoka City is around 33.5902",
    )

with col2:
    longitude = st.number_input(
        "Longitude",
        value=130.4017,
        format="%.6f",
        help="Example: Fukuoka City is around 130.4017",
    )

st.subheader("3. Estimate cloud base")

if st.button("Fetch weather and estimate"):
    try:
        current = fetch_weather(latitude, longitude)

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
                "AGL means above ground level. This is a simplified estimate based on surface temperature and dew point."
            )

    except requests.RequestException as error:
        st.error(f"Failed to fetch weather data: {error}")
