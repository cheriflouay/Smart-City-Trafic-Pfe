# src/dashboard/app.py
import streamlit as st
import streamlit.components.v1 as components 
import pandas as pd
import requests
import sqlite3
import plotly.express as px
from datetime import datetime
import os
import time # 👈 Added for the reset delay
import psutil
import yaml 
import json
import paho.mqtt.client as mqtt
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# --- PAGE CONFIG MUST BE THE FIRST STREAMLIT COMMAND ---
st.set_page_config(page_title="Smart City Traffic Hub", layout="wide", page_icon="🚦")

# ==========================================
# 🔐 FEATURE 5: ENTERPRISE SECURITY (LOGIN)
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Capgemini Secure Gateway")
    st.markdown("Please authenticate to access the Smart City Operations Center.")
    st.write("*(Hint: Use admin / capgemini2026)*")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True):
            if username == "admin" and password == "capgemini2026":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Access Denied.")
    st.stop() # Stops the rest of the dashboard from loading if not logged in

# ==========================================
# 🔄 FEATURE 2: REAL-TIME AUTO-REFRESH
# ==========================================
# Silently refreshes the page data every 3 seconds (3000ms)
st_autorefresh(interval=3000, limit=None, key="data_refresh")

# API Configuration
API_URL = "http://api_layer:8000/api"

# --- Custom CSS ---
st.markdown("""
    <style>
    .main {background-color: #f4f6f9;}
    .metric-card {
        background-color: white; padding: 15px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; height: 100%;
    }
    .metric-value {font-size: 1.8rem; font-weight: bold; color: #1f77b4;}
    .metric-label {font-size: 0.9rem; color: #555;}
    .ai-card {
        background-color: #1a1a2e; padding: 15px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-align: center; color: white;
        border: 2px solid #0f3460; height: 100%;
    }
    .v2i-terminal {
        background-color: #0c0c0c; color: #00ff00; font-family: 'Courier New', Courier, monospace;
        padding: 10px; border-radius: 5px; height: 180px; overflow-y: auto; border: 1px solid #333; font-size: 0.85rem;
    }
    .hw-card {
        background-color: #f8f9fa; padding: 10px; border-radius: 8px; border-left: 4px solid #1f77b4; margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Fetch Data Functions ---
def fetch_nodes():
    try:
        response = requests.get(f"{API_URL}/nodes")
        return response.json() if response.status_code == 200 else []
    except:
        return []

def fetch_revenue_stats(node):
    try:
        response = requests.get(f"{API_URL}/stats/revenue?node_id={node}")
        return response.json() if response.status_code == 200 else {"total_revenue": 0, "total_tickets": 0}
    except:
        return {"total_revenue": 0, "total_tickets": 0}

def fetch_recent_violations(node):
    try:
        response = requests.get(f"{API_URL}/violations?limit=100&node_id={node}")
        return response.json() if response.status_code == 200 else []
    except:
        return []

def fetch_congestion_data(node, modifier):
    try:
        conn = sqlite3.connect("traffic_system.db")
        query = "SELECT * FROM traffic_metrics WHERE 1=1 "
        if node != "ALL": 
            query += f"AND node_id='{node}' "
        query += f"{modifier} ORDER BY timestamp DESC LIMIT 200"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def fetch_ai_forecast(node):
    try:
        response = requests.get(f"{API_URL}/predict/congestion?node_id={node}")
        return response.json() if response.status_code == 200 else {"forecast": "OFFLINE"}
    except:
        return {"forecast": "OFFLINE"}

def fetch_v2x_logs(node):
    try:
        conn = sqlite3.connect("traffic_system.db")
        query = "SELECT * FROM v2x_ledger WHERE 1=1 "
        if node != "ALL": 
            query += f"AND node_id='{node}' "
        query += "ORDER BY timestamp DESC LIMIT 10"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

# ==========================================
# 🎛️ SIDEBAR: DISTRIBUTED CONTROL PANEL
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Capgemini_201x_logo.svg/512px-Capgemini_201x_logo.svg.png", width=150)
st.sidebar.title("Fleet Control")
st.sidebar.markdown("---")

active_nodes = fetch_nodes()
node_options = ["ALL"] + [n["node_id"] for n in active_nodes]
selected_node = st.sidebar.selectbox("📍 Select Intersection Node", node_options)

st.sidebar.markdown("---")

# ⚡ FEATURE 1: BIDIRECTIONAL IOT CONTROL (GOD MODE)
st.sidebar.subheader("⚡ V2X Manual Override")
if st.sidebar.button("🚨 FORCE GREEN LIGHT (NODE_A)", use_container_width=True):
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        # Hits the Docker MQTT container internally
        client.connect("mqtt_broker", 1883, 60)
        cmd = {"action": "FORCE_GREEN", "duration": 15, "reason": "DASHBOARD_OVERRIDE"}
        client.publish("smartcity/node/NODE_A/command", json.dumps(cmd))
        client.disconnect()
        st.sidebar.success("✅ Priority Override Sent!")
    except Exception as e:
        st.sidebar.error("❌ IoT Network Disconnected.")

# 👇 THE NEW RESET FEATURE 
st.sidebar.markdown("---")
st.sidebar.subheader("🔄 System Reset")
if st.sidebar.button("🧹 Master System Reset", use_container_width=True):
    try:
        # 1. Clear Database
        conn = sqlite3.connect("traffic_system.db")
        cur = conn.cursor()
        cur.execute("DELETE FROM traffic_metrics")
        cur.execute("DELETE FROM violations")
        cur.execute("DELETE FROM v2x_ledger")
        try:
            cur.execute("DELETE FROM incidents") # Included just in case your DB has this table
        except:
            pass
        conn.commit()
        conn.close()

        # 2. Reboot Docker Node
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect("mqtt_broker", 1883, 60)
        client.publish("smartcity/node/NODE_A/command", json.dumps({"action": "RESET_NODE"}))
        client.disconnect()
        
        st.sidebar.success("✅ Data Cleared! Rebooting Node...")
        time.sleep(1.5) # Wait for Docker to restart the AI script
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"❌ Reset Failed: {e}")

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 ALPR Database Search")
search_query = st.sidebar.text_input("Search Plate or ID...", placeholder="e.g. 123 TU 4567")

st.sidebar.subheader("📅 Data Filter")
time_filter = st.sidebar.selectbox("Select Time Range", ["All Time", "Today", "Last 7 Days"])

sql_time_modifier = ""
if time_filter == "Today":
    sql_time_modifier = "AND date(timestamp) = date('now')"
elif time_filter == "Last 7 Days":
    sql_time_modifier = "AND date(timestamp) >= date('now', '-7 days')"

violations_data = fetch_recent_violations(selected_node)

if search_query and violations_data:
    violations_data = [v for v in violations_data if search_query.lower() in str(v.get('plate_number', '')).lower() or search_query in str(v.get('vehicle_id', ''))]

st.sidebar.markdown("---")
st.sidebar.subheader("📥 Export Business Data")
if violations_data:
    df_export = pd.DataFrame(violations_data)
    csv = df_export.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("Download Violations (CSV)", data=csv, file_name=f"capgemini_violations.csv", mime="text/csv")

st.sidebar.markdown("---")

# User Identity Logout
st.sidebar.caption("System Architect: Louay Cherif")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

# ==========================================
# MAIN DASHBOARD UI
# ==========================================
node_title = "Global Aggregation" if selected_node == "ALL" else f"Node: {selected_node}"
st.title(f"🚦 Smart City Intelligence | {node_title}")
st.markdown("Real-time monitoring of intersection congestion, AI forecasting, and Edge hardware health.")

# --- TOP ROW: Key Metrics & AI ---
stats = fetch_revenue_stats(selected_node)
col1, col2, col3, col4, col5 = st.columns([1.5, 1.5, 1, 1.5, 2])

with col1:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Total Violations</div><div class="metric-value">{stats.get('total_tickets', 0)}</div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Automated Fine Revenue</div><div class="metric-value">{stats.get('total_revenue', 0)} TND</div></div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Active Nodes</div><div class="metric-value" style="color: green; font-size: 1.2rem; margin-top:10px;">{len(active_nodes)} ONLINE</div></div>""", unsafe_allow_html=True)
with col4:
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    cpu_color = "red" if cpu_usage > 85 else "orange" if cpu_usage > 60 else "green"
    ram_color = "red" if ram_usage > 85 else "orange" if ram_usage > 60 else "green"
    
    st.markdown(f"""
        <div class="metric-card" style="text-align: left; padding: 10px 15px;">
            <div style="font-size: 0.8rem; color: #555; font-weight: bold; margin-bottom: 5px;">⚙️ Hub Hardware Load</div>
            <div style="font-size: 0.9rem;">CPU: <span style="color: {cpu_color}; font-weight: bold;">{cpu_usage}%</span></div>
            <div style="font-size: 0.9rem;">RAM: <span style="color: {ram_color}; font-weight: bold;">{ram_usage}%</span></div>
        </div>
    """, unsafe_allow_html=True)

with col5:
    ai_data = fetch_ai_forecast(selected_node)
    forecast = ai_data.get('forecast', 'UNKNOWN')
    color = "#ff4b4b" if forecast in ["HIGH", "CRITICAL"] else "#ffa500" if forecast == "MEDIUM" else "#00cc66"
    st.markdown(f"""
        <div class="ai-card">
            <div style="font-size: 0.8rem; color: #888;">🧠 Node AI Forecast</div>
            <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{forecast}</div>
        </div>
    """, unsafe_allow_html=True)

st.write("---")

# --- MIDDLE ROW: Analytics, Map & Terminal ---
col_charts, col_side = st.columns([2.5, 1])

with col_charts:
    st.subheader(f"📊 Traffic Flow Analytics ({time_filter})")
    df_cong = fetch_congestion_data(selected_node, sql_time_modifier)
    
    # 📈 FEATURE 4: BUSINESS INTELLIGENCE TAB
    chart_tabs = st.tabs(["Volume Timeline", "Congestion Distribution", "📹 Live AI Vision Feed", "📈 Business Intelligence"])
    
    with chart_tabs[0]:
        if not df_cong.empty:
            df_cong['timestamp'] = pd.to_datetime(df_cong['timestamp'])
            color_param = 'node_id' if selected_node == "ALL" and 'node_id' in df_cong.columns else None
            fig_vol = px.line(df_cong, x='timestamp', y='vehicle_count', color=color_param, title='Vehicle Volume Over Time', markers=True, height=350)
            st.plotly_chart(fig_vol, use_container_width=True)
        else:
            st.info("Awaiting traffic metrics data...")
            
    with chart_tabs[1]:
        if not df_cong.empty:
            fig_pie = px.pie(df_cong, names='congestion_level', title='Congestion State Distribution',
                             color='congestion_level', height=350,
                             color_discrete_map={'LOW':'green', 'MEDIUM':'orange', 'HIGH':'red', 'CRITICAL':'darkred'})
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Awaiting traffic metrics data...")
            
    with chart_tabs[2]:
        st.markdown("### Real-Time Intersection Feed")
        feed_node = selected_node if selected_node != "ALL" else "NODE_A"
        
        custom_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; background-color: transparent; }}
            .video-container {{ position: relative; width: 100%; max-width: 100%; border-radius: 10px; overflow: hidden; border: 2px solid #1f77b4; box-shadow: 0 4px 8px rgba(0,0,0,0.2); background-color: #000; }}
            .video-container img {{ width: 100%; display: block; object-fit: contain; }}
            .fullscreen-btn {{ 
                position: absolute; top: 15px; right: 15px; 
                background-color: rgba(0, 0, 0, 0.6); color: white; 
                border: 2px solid rgba(255,255,255,0.5); border-radius: 5px; 
                padding: 8px 15px; font-size: 14px; font-weight: bold; cursor: pointer; 
                transition: 0.3s; z-index: 10;
            }}
            .fullscreen-btn:hover {{ background-color: rgba(0, 0, 0, 0.9); border-color: white; transform: scale(1.05); }}
        </style>
        </head>
        <body>
            <div class="video-container">
                <img id="ai-video" src="http://localhost:8000/api/video_feed/{feed_node}" alt="Live AI Vision Feed">
                <button class="fullscreen-btn" onclick="openFullscreen()">⛶ Full Screen</button>
            </div>
            <script>
                var elem = document.getElementById("ai-video");
                function openFullscreen() {{
                    if (elem.requestFullscreen) {{
                        elem.requestFullscreen();
                    }} else if (elem.webkitRequestFullscreen) {{ /* Safari */
                        elem.webkitRequestFullscreen();
                    }} else if (elem.msRequestFullscreen) {{ /* IE11 */
                        elem.msRequestFullscreen();
                    }}
                }}
            </script>
        </body>
        </html>
        """
        components.html(custom_html, height=450)

    # NEW TAB: Analytics Breakdown
    with chart_tabs[3]:
        if violations_data:
            df_vio = pd.DataFrame(violations_data)
            fig_bar = px.histogram(df_vio, x="violation_type", title="Infraction Breakdown Matrix", color="violation_type", height=350)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Insufficient violation data for BI Insights.")

with col_side:
    # 🌍 FEATURE 3: DYNAMIC GEOSPATIAL MAP
    st.subheader("📍 Live Node Deployment")
    m = folium.Map(location=[36.8665, 10.1647], zoom_start=13, tiles="CartoDB dark_matter")
    marker_color = "green" if forecast == "LOW" else "orange" if forecast == "MEDIUM" else "red"
    
    folium.Marker(
        [36.8665, 10.1647],
        popup=f"Ariana Intersection<br>Status: {forecast}",
        icon=folium.Icon(color=marker_color, icon="info-sign")
    ).add_to(m)
    
    st_folium(m, height=200, use_container_width=True)

    st.subheader("🚑 V2X IoT Ledger")
    df_v2x = fetch_v2x_logs(selected_node)
    
    if not df_v2x.empty:
        log_lines = []
        for _, row in df_v2x.iterrows():
            time_str = row['timestamp'][-8:]
            log_lines.append(f"[{time_str}] {row['node_id']} | {row['vehicle_type']} | {row['latency_ms']}ms -> {row['action_taken']}")
        log_html = "<br>".join(log_lines)
    else:
        log_html = "<i>System Active. Awaiting events...</i>"
        
    st.markdown(f'<div class="v2i-terminal">{log_html}</div>', unsafe_allow_html=True)

st.write("---")

# --- BOTTOM ROW: Live Violation Evidence Log ---
st.subheader("🚨 ALPR Infraction Database")

if violations_data:
    for v in violations_data[:10]: 
        node_prefix = f"[{v.get('node_id', 'UNKNOWN')}] " if selected_node == "ALL" else ""
        with st.expander(f"{node_prefix}Violation #{v['id']} | Plate: {v.get('plate_number', 'UNKNOWN')} | {v['timestamp']}"):
            col_img, col_info = st.columns([1, 2])
            with col_img:
                if os.path.exists(v.get('image_path', '')):
                    st.image(v['image_path'], width=250)
                else:
                    st.warning("Image file missing.")
            with col_info:
                st.markdown(f"**Tracking ID:** {v.get('vehicle_id', 'N/A')} | **Type:** {v.get('violation_type', 'N/A')}")
                st.markdown(f"**Captured Speed:** {v.get('speed', 'N/A')} km/h | **Light State:** {v.get('light_state', 'N/A')}")
                st.markdown(f"### 💰 Fine: <span style='color:red;'>{v.get('fine_amount', 0)} TND</span>", unsafe_allow_html=True)
else:
    if search_query:
        st.warning(f"No records found for query: '{search_query}'")
    else:
        st.info("No violations recorded yet.")