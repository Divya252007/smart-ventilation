from datetime import datetime, timezone
import time

import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ==========================================================
# SMART VENTILATION SYSTEM
# Premium IoT Monitoring Dashboard
# ESP32 -> FastAPI -> SQLite -> Streamlit
# ==========================================================

st.set_page_config(
    page_title="Smart Ventilation | IoT Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- CONFIGURATION -----------------------

DEFAULT_API = "http://127.0.0.1:8000"

if "api_url" not in st.session_state:
    st.session_state.api_url = DEFAULT_API

if "refresh_rate" not in st.session_state:
    st.session_state.refresh_rate = 3

if "history_limit" not in st.session_state:
    st.session_state.history_limit = 500

# -------------------- PREMIUM UI --------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@500;600;700;800&display=swap');

:root {
    color-scheme: light;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #f3f7f5;
    color: #163327;
}

.block-container {
    max-width: 1550px;
    padding: 1.3rem 2rem 2rem;
}

[data-testid="stSidebar"] {
    background: #09251c;
    border-right: 1px solid #214a38;
}

[data-testid="stSidebar"] * {
    color: #e8f5ed;
}

[data-testid="stSidebar"] .stCaption {
    color: #a9c9b7;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 26px;
}

.brand-icon {
    width: 48px;
    height: 48px;
    border-radius: 15px;
    background: linear-gradient(135deg,#28d58a,#07824e);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
}

.brand-name {
    font-family: Manrope;
    font-size: 17px;
    font-weight: 800;
    color: white;
}

.brand-sub {
    font-size: 10px;
    color: #8cb9a1;
    letter-spacing: 2px;
}

.hero {
    background: linear-gradient(115deg,#09291f,#10583b,#087a4b);
    padding: 29px;
    border-radius: 23px;
    color: white;
    margin-bottom: 20px;
    box-shadow: 0 12px 35px #0b55301c;
}

.hero-label {
    color: #8df0bd;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
}

.hero-title {
    font-family: Manrope;
    font-size: clamp(25px,3vw,37px);
    font-weight: 800;
    margin: 10px 0;
}

.hero-sub {
    color: #c5e5d3;
    font-size: 14px;
}

.section-title {
    font-family: Manrope;
    font-size: 19px;
    font-weight: 800;
    color: #173b2a;
    margin: 22px 0 12px;
}

.section-caption {
    color: #82968a;
    font-size: 12px;
}

.kpi {
    background: white;
    border: 1px solid #e3eee7;
    border-radius: 18px;
    padding: 17px;
    min-height: 158px;
    box-shadow: 0 5px 20px #173d2808;
}

.kpi-label {
    font-size: 11px;
    font-weight: 800;
    color: #77877e;
    letter-spacing: .5px;
}

.kpi-icon {
    float: right;
    font-size: 22px;
}

.kpi-value {
    font-family: Manrope;
    font-size: 28px;
    font-weight: 800;
    color: #173b2a;
    margin-top: 17px;
}

.kpi-foot {
    font-size: 11px;
    color: #89978e;
    margin-top: 8px;
}

.tag {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 30px;
    font-size: 10px;
    font-weight: 800;
    margin-top: 8px;
}

.green { background: #ddf8e9; color: #087443; }
.yellow { background: #fff1cd; color: #966000; }
.red { background: #ffe3e1; color: #b42318; }
.gray { background: #edf1ef; color: #66756c; }

.panel {
    background: white;
    border: 1px solid #e3eee7;
    border-radius: 18px;
    padding: 19px;
    min-height: 145px;
    box-shadow: 0 5px 20px #173d2808;
}

.panel-title {
    font-family: Manrope;
    font-size: 15px;
    font-weight: 800;
    color: #1b412e;
    margin-bottom: 13px;
}

.panel-value {
    font-family: Manrope;
    font-size: 24px;
    font-weight: 800;
    color: #175b39;
    margin: 12px 0;
}

div[data-testid="stPlotlyChart"] {
    background: white;
    border: 1px solid #e3eee7;
    border-radius: 17px;
    padding: 8px;
}

.stButton button,
.stDownloadButton button {
    border-radius: 11px;
    font-weight: 700;
}

hr {
    border-color: #e5eee8;
}

@media(max-width: 760px) {
    .block-container {
        padding: .7rem .7rem 1.5rem;
    }
    .hero {
        padding: 20px;
        border-radius: 17px;
    }
    .kpi {
        padding: 12px;
        min-height: 140px;
    }
    .kpi-value {
        font-size: 22px;
    }
    .panel {
        padding: 14px;
    }
}
</style>
""", unsafe_allow_html=True)


# -------------------- HELPERS ----------------------------

def api_get(endpoint):
    try:
        response = requests.get(
            st.session_state.api_url.rstrip("/") + endpoint,
            timeout=3
        )
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as error:
        return None, str(error)


def is_on(value):
    return value is True or value == 1


def parse_timestamp(value):
    try:
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def badge(text, style="gray"):
    return f'<span class="tag {style}">{text}</span>'


def metric_card(title, value, icon, status, style, footer):
    st.markdown(f"""
    <div class="kpi">
        <span class="kpi-label">{title}</span>
        <span class="kpi-icon">{icon}</span>
        <div class="kpi-value">{value}</div>
        {badge(status, style)}
        <div class="kpi-foot">{footer}</div>
    </div>
    """, unsafe_allow_html=True)


def panel(title, value, description):
    st.markdown(f"""
    <div class="panel">
        <div class="panel-title">{title}</div>
        <div class="panel-value">{value}</div>
        <div class="section-caption">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def line_chart(data, column, title, color, unit):
    fig = go.Figure()

    if not data.empty and column in data.columns:
        valid = data.dropna(subset=[column])

        fig.add_trace(go.Scatter(
            x=valid["timestamp"],
            y=valid[column],
            mode="lines+markers",
            line=dict(color=color, width=3, shape="spline"),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor="rgba(16,185,129,0.08)",
            hovertemplate=(
                "%{x|%d %b %H:%M:%S}<br>"
                f"%{{y}} {unit}<extra></extra>"
            )
        ))

    fig.update_layout(
        title=title,
        height=290,
        margin=dict(l=12, r=12, t=45, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#718078"),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#edf2ee"),
        hovermode="x unified"
    )

    return fig


# -------------------- SIDEBAR ----------------------------

with st.sidebar:

    st.markdown("""
    <div class="brand">
        <div class="brand-icon">🌿</div>
        <div>
            <div class="brand-name">Smart Ventilation</div>
            <div class="brand-sub">IOT CONTROL CENTER</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.caption("MAIN MENU")

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Sensor Analytics",
            "Event History",
            "Settings",
            "Project Information"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.caption("BACKEND CONNECTION")

    st.text_input(
        "API address",
        key="api_url"
    )

    st.caption("Use 127.0.0.1 for a dashboard on the same laptop.")

    st.divider()

    st.caption("DASHBOARD PREFERENCES")

    st.selectbox(
        "Refresh interval",
        [2, 3, 5, 10],
        key="refresh_rate",
        format_func=lambda x: f"{x} seconds"
    )

    st.selectbox(
        "History records",
        [100, 250, 500, 1000, 2000],
        key="history_limit"
    )


# -------------------- AUTO REFRESH -----------------------

try:
    from streamlit_autorefresh import st_autorefresh

    st_autorefresh(
        interval=st.session_state.refresh_rate * 1000,
        key="dashboard_refresh"
    )
except ImportError:
    pass


# -------------------- GET BACKEND DATA -------------------

health, health_error = api_get("/api/health")
latest, latest_error = api_get("/api/latest")

history, history_error = api_get(
    f"/api/history?limit={st.session_state.history_limit}"
)

backend_online = health is not None and latest is not None

record = None
if latest and latest.get("available"):
    record = latest.get("data")

history_rows = history.get("data", []) if history else []

df = pd.DataFrame(history_rows)

if not df.empty and "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        utc=True,
        errors="coerce"
    )
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

last_time = parse_timestamp(record.get("timestamp")) if record else None

age = (
    (datetime.now(timezone.utc) - last_time).total_seconds()
    if last_time else None
)

esp_online = age is not None and 0 <= age <= 10

# Real readings only. No sample data.
data = record or {
    "mq135": None,
    "temperature": None,
    "humidity": None,
    "pir_motion": None,
    "mode": "UNKNOWN",
    "fan_on": None,
    "relay_on": None,
    "red_led": None,
    "green_led": None,
    "buzzer_on": None,
    "air_status": "Unavailable",
    "temperature_status": "Unavailable",
    "alert_message": ""
}


# -------------------- OVERVIEW ---------------------------

if page == "Overview":

    st.markdown("""
    <div class="hero">
        <div class="hero-label">SMART BUILDING • AIR INTELLIGENCE</div>
        <div class="hero-title">Smart Ventilation System</div>
        <div class="hero-sub">
            Real-time environmental monitoring and
            intelligent automatic ventilation control.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Device status
    c1, c2, c3 = st.columns(3)

    with c1:
        if not backend_online:
            st.error("● Backend Offline")
        else:
            st.success("● Backend Connected")

    with c2:
        if not record:
            st.warning("● Waiting for ESP32")
        elif esp_online:
            st.success("● ESP32 Online")
        else:
            st.error("● ESP32 Offline / Stale")

    with c3:
        st.info(
            "Last packet: " +
            (f"{age:.1f} seconds ago" if age is not None else "Not received")
        )

    if not backend_online:
        st.error(
            "Cannot reach the Python backend. Start it using: "
            "python -m uvicorn backend:app --host 0.0.0.0 --port 8000"
        )
        st.caption(health_error or latest_error)

    elif not record:
        st.info(
            "Backend is working. Connect the ESP32 to begin receiving "
            "actual MQ135, DHT11 and PIR readings."
        )

    elif not esp_online:
        st.warning(
            "ESP32 telemetry is stale. Displayed values are the last "
            "received measurements, not live measurements."
        )

    # Sensor cards
    st.markdown(
        '<div class="section-title">Environmental Monitoring</div>',
        unsafe_allow_html=True
    )

    a, b, c, d = st.columns(4)

    mq = data.get("mq135")
    temp = data.get("temperature")
    humidity = data.get("humidity")
    pir = data.get("pir_motion")

    air_status = str(data.get("air_status") or "Unavailable")
    air_style = {
        "good": "green",
        "moderate": "yellow",
        "poor": "red"
    }.get(air_status.lower(), "gray")

    with a:
        metric_card(
            "AIR RESPONSE · MQ135",
            f"{mq} ADC" if mq is not None else "—",
            "〰️",
            air_status.upper(),
            air_style,
            "Raw sensor reading • Not certified AQI"
        )

    temp_status = str(
        data.get("temperature_status") or "Unavailable"
    )

    with b:
        metric_card(
            "TEMPERATURE · DHT11",
            f"{temp:.1f} °C" if isinstance(temp, (int, float)) else "—",
            "🌡️",
            temp_status.upper(),
            "red" if temp_status.lower() == "high" else "green"
            if temp_status.lower() in ("normal", "safe") else "gray",
            "Room temperature"
        )

    with c:
        metric_card(
            "HUMIDITY · DHT11",
            f"{humidity:.1f} %" if isinstance(humidity, (int, float)) else "—",
            "💧",
            "LIVE" if humidity is not None and esp_online else "UNAVAILABLE",
            "green" if humidity is not None and esp_online else "gray",
            "Relative humidity"
        )

    with d:
        metric_card(
            "MOVEMENT · PIR",
            "Detected" if is_on(pir) else "No motion" if pir is not None else "—",
            "🚶",
            "MOTION" if is_on(pir) else "CLEAR" if pir is not None else "UNAVAILABLE",
            "yellow" if is_on(pir) else "green" if pir is not None else "gray",
            "Human movement detection"
        )

    # Operating conditions
    st.markdown(
        '<div class="section-title">Ventilation & Device Status</div>',
        unsafe_allow_html=True
    )

    f1, f2, f3 = st.columns(3)

    with f1:
        fan = data.get("fan_on")
        fan_value = (
            "FAN ON" if is_on(fan) else
            "FAN OFF" if fan is not None else "Unavailable"
        )
        panel(
            "🌀 Ventilation Fan",
            fan_value,
            "Relay: " + (
                "ON" if is_on(data.get("relay_on")) else
                "OFF" if data.get("relay_on") is not None else
                "Unavailable"
            )
        )

    with f2:
        mode = str(data.get("mode") or "UNKNOWN").upper()
        mode_value = {
            "INDOOR": "🏠 Indoor Mode",
            "OUTDOOR": "🌳 Outdoor Mode"
        }.get(mode, "Unavailable")
        panel(
            "📍 Sampling Mode",
            mode_value,
            "Read from the physical red toggle switch"
        )

    with f3:
        panel(
            "⚙️ Control System",
            "Automatic" if record and esp_online else "Awaiting ESP32",
            "Automatic relay logic must be implemented on the ESP32"
        )

    # Output indicators
    st.markdown(
        '<div class="section-title">Output Indicators</div>',
        unsafe_allow_html=True
    )

    o1, o2, o3 = st.columns(3)

    for col, label, key, emoji in [
        (o1, "Red Warning LED", "red_led", "🔴"),
        (o2, "Green Normal LED", "green_led", "🟢"),
        (o3, "Buzzer", "buzzer_on", "🔔")
    ]:
        with col:
            value = data.get(key)
            panel(
                f"{emoji} {label}",
                "Unavailable" if value is None else
                "ON" if is_on(value) else "OFF",
                "Reported by ESP32"
            )

    # Charts
    st.markdown(
        '<div class="section-title">Sensor History & Trends</div>',
        unsafe_allow_html=True
    )

    if df.empty:
        st.info(
            "Historical graphs will appear after the ESP32 sends "
            "its first sensor packet."
        )
    else:
        g1, g2 = st.columns(2)

        with g1:
            if "mq135" in df:
                st.plotly_chart(
                    line_chart(
                        df, "mq135", "Air Response History",
                        "#159bd1", "ADC"
                    ),
                    use_container_width=True
                )

        with g2:
            if "temperature" in df:
                st.plotly_chart(
                    line_chart(
                        df, "temperature", "Temperature History",
                        "#ed7565", "°C"
                    ),
                    use_container_width=True
                )

        g3, g4 = st.columns(2)

        with g3:
            if "humidity" in df:
                st.plotly_chart(
                    line_chart(
                        df, "humidity", "Humidity History",
                        "#13a98b", "%RH"
                    ),
                    use_container_width=True
                )

        with g4:
            if "fan_on" in df:
                fan_fig = go.Figure()
                fan_fig.add_trace(go.Scatter(
                    x=df["timestamp"],
                    y=df["fan_on"].astype(float),
                    mode="lines",
                    line=dict(
                        color="#159b65",
                        width=3,
                        shape="hv"
                    )
                ))
                fan_fig.update_layout(
                    title="Fan ON / OFF History",
                    height=290,
                    yaxis=dict(
                        tickvals=[0, 1],
                        ticktext=["OFF", "ON"],
                        range=[-0.1, 1.1]
                    ),
                    template="plotly_white"
                )
                st.plotly_chart(
                    fan_fig,
                    use_container_width=True
                )

    # Alerts
    st.markdown(
        '<div class="section-title">Alert Center</div>',
        unsafe_allow_html=True
    )

    alerts = []

    if not backend_online:
        alerts.append(("Backend connection unavailable", "red"))

    elif not record:
        alerts.append(("Waiting for first ESP32 data packet", "yellow"))

    elif not esp_online:
        alerts.append(("ESP32 communication is stale", "red"))

    if record:
        if air_status.lower() == "poor":
            alerts.append(("Poor air quality warning", "red"))
        elif air_status.lower() == "moderate":
            alerts.append(("Moderate air quality warning", "yellow"))

        if temp_status.lower() == "high":
            alerts.append(("High temperature warning", "yellow"))

        if data.get("alert_message"):
            alerts.append((str(data["alert_message"]), "yellow"))

    if not alerts:
        st.success("No active warnings reported by the device.")

    for message, style in alerts:
        st.markdown(
            f"• {badge(message, style)}",
            unsafe_allow_html=True
        )


# -------------------- SENSOR ANALYTICS -------------------

elif page == "Sensor Analytics":

    st.title("📊 Sensor Analytics")
    st.caption("Historical environmental measurements from ESP32.")

    if df.empty:
        st.info("No sensor history available yet.")
    else:
        tabs = st.tabs([
            "Air Quality",
            "Temperature",
            "Humidity",
            "Fan Activity"
        ])

        with tabs[0]:
            st.plotly_chart(
                line_chart(
                    df, "mq135", "MQ135 Raw ADC",
                    "#159bd1", "ADC"
                ),
                use_container_width=True
            )
            st.caption(
                "MQ135 readings are raw ADC values, not certified AQI "
                "or calibrated gas concentrations."
            )

        with tabs[1]:
            st.plotly_chart(
                line_chart(
                    df, "temperature", "Temperature",
                    "#ed7565", "°C"
                ),
                use_container_width=True
            )

        with tabs[2]:
            st.plotly_chart(
                line_chart(
                    df, "humidity", "Relative Humidity",
                    "#13a98b", "%RH"
                ),
                use_container_width=True
            )

        with tabs[3]:
            if "fan_on" in df:
                st.plotly_chart(
                    line_chart(
                        df, "fan_on", "Fan Activity",
                        "#159b65", "State"
                    ),
                    use_container_width=True
                )


# -------------------- EVENT HISTORY ----------------------

elif page == "Event History":

    st.title("📋 Event History")
    st.caption("Recorded sensor packets and device statuses.")

    if df.empty:
        st.info("No records have been received yet.")
    else:
        display = df.copy()
        display["timestamp"] = display["timestamp"].dt.strftime(
            "%d %b %Y %H:%M:%S UTC"
        )

        columns = [
            "timestamp",
            "mq135",
            "temperature",
            "humidity",
            "pir_motion",
            "mode",
            "fan_on",
            "relay_on",
            "air_status",
            "temperature_status",
            "alert_message"
        ]

        available = [
            col for col in columns if col in display.columns
        ]

        st.dataframe(
            display[available].iloc[::-1],
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇ Download CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="smart_ventilation_history.csv",
            mime="text/csv"
        )


# -------------------- SETTINGS ---------------------------

elif page == "Settings":

    st.title("⚙️ System Settings")

    st.caption("Dashboard preferences and project configuration.")

    st.warning(
        "The settings below are dashboard-side preferences. "
        "They do not automatically modify the ESP32 firmware."
    )

    with st.form("settings_form"):

        st.subheader("Air Quality Thresholds")

        air_warning = st.number_input(
            "MQ135 warning threshold (raw ADC)",
            min_value=0,
            max_value=4095,
            value=1500
        )

        air_poor = st.number_input(
            "MQ135 poor threshold (raw ADC)",
            min_value=0,
            max_value=4095,
            value=2200
        )

        st.subheader("Temperature")

        temp_limit = st.number_input(
            "High temperature threshold (°C)",
            min_value=0.0,
            max_value=80.0,
            value=35.0,
            step=0.5
        )

        save = st.form_submit_button(
            "Save Dashboard Preferences",
            use_container_width=True
        )

        if save:
            st.session_state.air_warning = air_warning
            st.session_state.air_poor = air_poor
            st.session_state.temp_limit = temp_limit
            st.success("Dashboard preferences saved for this session.")

    st.divider()

    st.subheader("Automatic Control Recommendations")

    st.write("""
    - Use separate ON and OFF thresholds (hysteresis).
    - Add a minimum fan run/stop time.
    - Keep automatic fan control on the ESP32.
    - Calibrate MQ135 before assigning air-quality categories.
    - Monitor DHT11 sensor communication errors.
    """)


# -------------------- PROJECT INFORMATION ---------------

elif page == "Project Information":

    st.title("🌿 Smart Ventilation System")

    st.caption(
        "ESP32-Based Smart Ventilation Monitoring and Control System"
    )

    st.markdown("""
    ### Project Objective

    Monitor environmental conditions and automatically control
    ventilation based on programmed air-quality and temperature
    conditions.

    ### Hardware Configuration

    | Hardware | ESP32 GPIO |
    |---|---:|
    | MQ135 AO | GPIO 34 |
    | DHT11 DATA | GPIO 4 |
    | PIR OUT | GPIO 27 |
    | Physical mode switch | GPIO 32 |
    | Relay IN | GPIO 26 |
    | Buzzer | GPIO 25 |
    | Red LED | GPIO 18 |
    | Green LED | GPIO 19 |

    ### Software Architecture

    ESP32 → Wi-Fi → FastAPI → SQLite → Streamlit

    ### Operating Modes

    **Indoor Mode:** MQ135 measures the indoor location.

    **Outdoor Mode:** Move the same MQ135 sensor to the outdoor
    location and select Outdoor using the physical switch.

    Only one MQ135 sensor is used, so the two locations are
    not monitored simultaneously.

    ### Hardware Safety

    - Use a suitable voltage divider for MQ135 AO.
    - Never apply a voltage above the ESP32 GPIO input limit.
    - Use appropriate driver circuitry for relay and buzzer.
    - Use a suitable separate supply for the 12V fan.
    - Verify common ground and relay module compatibility.
    """)


# -------------------- FOOTER -----------------------------

st.divider()

left, right = st.columns([3, 1])

with left:
    st.caption(
        "SMART VENTILATION SYSTEM | ESP32 + FASTAPI + SQLITE"
    )

with right:
    st.caption("Premium IoT Dashboard")