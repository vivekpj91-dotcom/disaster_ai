import os
import uuid

import pandas as pd
import requests
import streamlit as st


st.set_page_config(
    page_title="DisasterAssist AI",
    layout="centered",
    initial_sidebar_state="collapsed",
)

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000/api")


def init_state() -> None:
    defaults = {
        "session_id": f"st-{uuid.uuid4()}",
        "token": None,
        "email": None,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "chat_history": [],
        "incidents_list": [],
        "current_tab": "Home",
        "backend_status": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()

custom_css = """
<style>
    :root {
        --blue: #0b63ce;
        --blue-dark: #083b82;
        --blue-soft: #edf6ff;
        --red: #dc2626;
        --red-soft: #fee2e2;
        --green: #15803d;
        --green-soft: #dcfce7;
        --ink: #102033;
        --muted: #61738a;
        --line: #d7e4f2;
        --bg: #f4f8fc;
        --card: #ffffff;
    }

    .stApp {
        background: var(--bg);
        color: var(--ink);
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    section[data-testid="stSidebar"] {
        display: none !important;
    }

    .main .block-container {
        max-width: 460px;
        padding: 1.25rem 1rem 6.5rem !important;
        margin: 0 auto;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    .app-shell {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 16px 36px rgba(8, 59, 130, 0.10);
        margin-bottom: 12px;
    }

    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 12px;
    }

    .brand-title {
        font-size: 1.45rem;
        font-weight: 850;
        letter-spacing: 0;
        color: var(--blue-dark);
        margin: 0;
    }

    .brand-subtitle {
        margin: 2px 0 0 0;
        color: var(--muted);
        font-size: 0.86rem;
    }

    .status-pill {
        border-radius: 999px;
        padding: 7px 11px;
        font-size: 0.75rem;
        font-weight: 750;
        white-space: nowrap;
    }

    .status-ok {
        background: var(--green-soft);
        color: var(--green);
    }

    .status-offline {
        background: var(--red-soft);
        color: var(--red);
    }

    .mobile-card {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 16px;
        margin: 12px 0;
        box-shadow: 0 10px 22px rgba(16, 32, 51, 0.06);
    }

    .metric-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin: 12px 0;
    }

    .metric-tile {
        background: var(--blue-soft);
        border: 1px solid #cfe5ff;
        border-radius: 14px;
        padding: 12px;
    }

    .metric-label {
        color: var(--muted);
        font-size: 0.76rem;
        margin-bottom: 4px;
    }

    .metric-value {
        color: var(--ink);
        font-size: 1rem;
        font-weight: 800;
    }

    .alert-card {
        background: var(--red-soft);
        border: 1px solid #fecaca;
        border-left: 6px solid var(--red);
        border-radius: 16px;
        padding: 14px;
        margin: 12px 0;
        color: #7f1d1d;
    }

    .section-title {
        color: var(--ink);
        font-size: 1.15rem;
        font-weight: 820;
        margin: 0 0 6px 0;
    }

    .section-copy {
        color: var(--muted);
        font-size: 0.9rem;
        margin: 0;
    }

    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #ffffff;
        border-top: 1px solid var(--line);
        box-shadow: 0 -12px 30px rgba(16, 32, 51, 0.08);
        padding: 8px 10px 12px;
        z-index: 9999;
    }

    .stButton > button {
        border-radius: 12px;
        border: 1px solid #b9d6ff;
        background: #ffffff;
        color: var(--blue-dark);
        font-weight: 760;
        min-height: 42px;
    }

    .stButton > button:hover {
        border-color: var(--blue);
        color: var(--blue);
        background: var(--blue-soft);
    }

    div[data-testid="stForm"] button {
        background: var(--red) !important;
        color: #ffffff !important;
        border-color: var(--red) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: var(--blue-soft);
        border-radius: 14px;
        padding: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        color: var(--blue-dark);
        font-weight: 750;
    }

    [data-testid="stDataFrame"], [data-testid="stTable"] {
        border-radius: 14px;
        overflow: hidden;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


def api_headers() -> dict:
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def check_backend() -> dict:
    try:
        res = requests.get(f"{API_BASE_URL}/health", timeout=3)
        if res.status_code == 200:
            return {"online": True, "detail": res.json()}
    except Exception:
        pass
    return {"online": False, "detail": None}


def call_chat_api(prompt: str) -> dict:
    payload = {
        "message": prompt,
        "session_id": st.session_state.session_id,
        "latitude": st.session_state.latitude,
        "longitude": st.session_state.longitude,
    }
    try:
        res = requests.post(f"{API_BASE_URL}/chat", json=payload, headers=api_headers(), timeout=30)
        if res.status_code == 200:
            st.session_state.backend_status = True
            return res.json()
        return {
            "response": f"Backend returned HTTP {res.status_code}: {res.text}",
            "session_id": st.session_state.session_id,
            "is_authenticated": st.session_state.token is not None,
            "incident_logged": None,
        }
    except Exception:
        st.session_state.backend_status = False
        return {
            "response": "Backend is offline. Start FastAPI on port 8000 or set API_BASE_URL correctly.",
            "session_id": st.session_state.session_id,
            "is_authenticated": st.session_state.token is not None,
            "incident_logged": None,
        }


def render_header() -> None:
    health = check_backend()
    st.session_state.backend_status = health["online"]
    status_class = "status-ok" if health["online"] else "status-offline"
    status_text = "Backend online" if health["online"] else "Backend offline"
    st.markdown(
        f"""
        <div class="app-shell">
            <div class="topbar">
                <div>
                    <p class="brand-title">DisasterAssist AI</p>
                    <p class="brand-subtitle">Emergency operations mobile console</p>
                </div>
                <span class="status-pill {status_class}">{status_text}</span>
            </div>
            <div class="metric-grid">
                <div class="metric-tile">
                    <div class="metric-label">Location</div>
                    <div class="metric-value">{st.session_state.latitude:.2f}, {st.session_state.longitude:.2f}</div>
                </div>
                <div class="metric-tile">
                    <div class="metric-label">Session</div>
                    <div class="metric-value">{st.session_state.session_id[:8]}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_settings() -> None:
    with st.expander("Connection, location, and account"):
        lat_in = st.number_input("Latitude", value=st.session_state.latitude, format="%.6f")
        lon_in = st.number_input("Longitude", value=st.session_state.longitude, format="%.6f")
        if lat_in != st.session_state.latitude or lon_in != st.session_state.longitude:
            st.session_state.latitude = lat_in
            st.session_state.longitude = lon_in
            st.success("Coordinates updated.")

        st.caption(f"API endpoint: {API_BASE_URL}")
        if st.session_state.token:
            st.info(f"Signed in as {st.session_state.email}")
            if st.button("Logout", key="logout_hdr_btn", use_container_width=True):
                st.session_state.token = None
                st.session_state.email = None
                st.session_state.session_id = f"st-{uuid.uuid4()}"
                st.session_state.chat_history = []
                st.rerun()
        else:
            login_email = st.text_input("Email", value="user@example.com", key="login_email_hdr")
            login_pass = st.text_input("Password", type="password", key="login_pass_hdr")
            if st.button("Sign in", key="login_hdr_btn", use_container_width=True):
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/auth/token",
                        json={"email": login_email, "password": login_pass},
                        timeout=10,
                    )
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.token = data["access_token"]
                        st.session_state.email = login_email
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
                except Exception:
                    st.error("Backend is offline. Start FastAPI first.")


render_header()
render_settings()

current_tab = st.session_state.current_tab

if current_tab == "Home":
    st.markdown(
        """
        <div class="alert-card">
            <strong>Active Alert</strong><br>
            Tsunami Watch issued for the coastal San Francisco Bay Area. Stay away from beaches and low-lying shoreline zones.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="mobile-card"><p class="section-title">Response Dashboard</p><p class="section-copy">Nearby safe places, medical facilities, and backend connection status.</p></div>', unsafe_allow_html=True)

    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["Shelters", "Hospitals", "System"])

    shelters = [
        {"Name": "Civic Center Gymnasium", "Lat": 37.7749, "Lon": -122.4194, "Status": "OPEN", "Spots Left": 108, "Address": "99 Grove St"},
        {"Name": "Golden Gate Park Pavilion", "Lat": 37.7694, "Lon": -122.4862, "Status": "OPEN", "Spots Left": 10, "Address": "501 Stanyan St"},
        {"Name": "Mission High School Auditorium", "Lat": 37.7618, "Lon": -122.4272, "Status": "FULL", "Spots Left": 0, "Address": "3750 18th St"},
    ]
    hospitals = [
        {"Name": "Zuckerberg SF General Hospital", "Status": "OPERATIONAL", "Trauma Center": "Level 1", "Phone": "(415) 206-8000"},
        {"Name": "UCSF Medical Center at Mission Bay", "Status": "OPERATIONAL", "Trauma Center": "No", "Phone": "(415) 353-3000"},
        {"Name": "Saint Francis Memorial Hospital", "Status": "OVERLOADED", "Trauma Center": "No", "Phone": "(415) 353-6000"},
    ]

    with sub_tab1:
        st.map(pd.DataFrame({"lat": [s["Lat"] for s in shelters], "lon": [s["Lon"] for s in shelters]}))
        st.dataframe(pd.DataFrame(shelters), use_container_width=True, hide_index=True)

    with sub_tab2:
        st.dataframe(pd.DataFrame(hospitals), use_container_width=True, hide_index=True)

    with sub_tab3:
        health_label = "Connected" if st.session_state.backend_status else "Offline"
        st.markdown(
            f"""
            <div class="mobile-card">
                <p class="section-title">Backend Connection</p>
                <p class="section-copy">Status: <strong>{health_label}</strong></p>
                <p class="section-copy">Endpoint: <strong>{API_BASE_URL}</strong></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

elif current_tab == "Chat":
    st.markdown('<div class="mobile-card"><p class="section-title">AI Assistant</p><p class="section-copy">Ask about shelters, weather, evacuation routes, damage, or emergency supplies.</p></div>', unsafe_allow_html=True)

    chat_tab1, chat_tab2 = st.tabs(["Chat", "History"])

    with chat_tab1:
        for chat in st.session_state.chat_history:
            with st.chat_message(chat["role"]):
                st.write(chat["content"])

        if user_prompt := st.chat_input("Ask DisasterAssist..."):
            st.session_state.chat_history.append({"role": "user", "content": user_prompt})
            st.rerun()

    with chat_tab2:
        if not st.session_state.chat_history:
            st.info("No messages in this session yet.")
        else:
            for c in st.session_state.chat_history:
                st.text(f"[{c['role'].upper()}] {c['content']}")

    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        latest_prompt = st.session_state.chat_history[-1]["content"]
        with st.spinner("Contacting backend agents..."):
            res_data = call_chat_api(latest_prompt)
            response_text = res_data["response"]
            if res_data.get("incident_logged"):
                st.session_state.incidents_list.append(res_data["incident_logged"])

        st.session_state.chat_history.append({"role": "assistant", "content": response_text})
        st.rerun()

elif current_tab == "Emergency":
    st.markdown(
        """
        <div class="alert-card">
            <strong>Emergency Mode</strong><br>
            Use this only for high-priority rescue, injury, fire, flooding, collapse, or trapped-person reports.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("emergency_dispatch_form"):
        contact_phone = st.text_input("Contact phone", placeholder="(555) 019-2831")
        disaster_details = st.text_area("Immediate hazard", placeholder="Example: trapped by rising water near Market St.")
        submit_btn = st.form_submit_button("Send emergency alert")

    if submit_btn:
        if not disaster_details:
            st.error("Please supply distress details.")
        else:
            with st.spinner("Sending emergency alert to backend..."):
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/chat",
                        json={
                            "message": f"CRITICAL EMERGENCY. Phone: {contact_phone}. Details: {disaster_details}",
                            "session_id": st.session_state.session_id,
                            "latitude": st.session_state.latitude,
                            "longitude": st.session_state.longitude,
                        },
                        headers=api_headers(),
                        timeout=30,
                    )
                    data = res.json()
                    st.success("Emergency alert submitted.")
                    st.write(data["response"])
                    if data.get("incident_logged"):
                        st.session_state.incidents_list.append(data["incident_logged"])
                except Exception:
                    st.error("Backend is offline. Start FastAPI before sending alerts.")

elif current_tab == "Vision":
    st.markdown('<div class="mobile-card"><p class="section-title">Damage Assessment</p><p class="section-copy">Upload a JPG or PNG to assess visible structural, road, fire, or flood hazards.</p></div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        st.image(uploaded_file, caption="Selected photo", use_container_width=True)
        if st.button("Evaluate damage", use_container_width=True):
            with st.spinner("Uploading to backend..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data_form = {"latitude": str(st.session_state.latitude), "longitude": str(st.session_state.longitude)}
                try:
                    res = requests.post(f"{API_BASE_URL}/upload", files=files, data=data_form, headers=api_headers(), timeout=60)
                    if res.status_code == 200:
                        analysis_data = res.json()
                        hazard = analysis_data["hazard_level"]
                        if hazard in ["HIGH", "CRITICAL"]:
                            st.error(f"Hazard level: {hazard}")
                        else:
                            st.success(f"Hazard level: {hazard}")
                        st.write(analysis_data["analysis"])
                        for item in analysis_data.get("recommendations", []):
                            st.write(f"- {item}")
                    else:
                        st.error(res.json().get("detail", "Upload failed."))
                except Exception:
                    st.error("Backend is offline. Failed to run damage assessment.")

elif current_tab == "Checklist":
    st.markdown('<div class="mobile-card"><p class="section-title">Preparedness Kit</p><p class="section-copy">Generate a checklist based on household size and disaster type.</p></div>', unsafe_allow_html=True)

    dt_choice = st.selectbox("Disaster target", ["Flood", "Cyclone", "Earthquake", "Wildfire", "Heatwave"])
    h_size = st.slider("Household size", 1, 10, 3)
    pets = st.checkbox("Pets in household")
    kids = st.checkbox("Children in household")

    if st.button("Generate checklist", use_container_width=True):
        with st.spinner("Contacting backend..."):
            prompt = f"Generate a preparedness checklist for a {dt_choice} with household size of {h_size}, pets={pets}, children={kids}."
            api_data = call_chat_api(prompt)
            st.success("Checklist ready.")
            st.write(api_data["response"])


def nav_label(name: str) -> str:
    return f"* {name}" if st.session_state.current_tab == name else name


st.markdown("<div class='bottom-nav'>", unsafe_allow_html=True)
nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns(5)

with nav_col1:
    if st.button(nav_label("Home"), key="nav_home", use_container_width=True):
        st.session_state.current_tab = "Home"
        st.rerun()
with nav_col2:
    if st.button(nav_label("Chat"), key="nav_chat", use_container_width=True):
        st.session_state.current_tab = "Chat"
        st.rerun()
with nav_col3:
    if st.button(nav_label("Alert"), key="nav_emergency", use_container_width=True):
        st.session_state.current_tab = "Emergency"
        st.rerun()
with nav_col4:
    if st.button(nav_label("Scan"), key="nav_vision", use_container_width=True):
        st.session_state.current_tab = "Vision"
        st.rerun()
with nav_col5:
    if st.button(nav_label("Kit"), key="nav_checklist", use_container_width=True):
        st.session_state.current_tab = "Checklist"
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
