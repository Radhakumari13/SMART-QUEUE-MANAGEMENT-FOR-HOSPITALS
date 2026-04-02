import streamlit as st
import pandas as pd
import time
import json
import os
from datetime import datetime
from utils import add_patient, get_queue, next_patient, calculate_wait_time

# ─────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Smart Queue Management",
    page_icon="🏥",
    layout="wide"
)

# ─────────────────────────────────────────
# Session State Initialization
# ─────────────────────────────────────────
if "served_patients" not in st.session_state:
    st.session_state.served_patients = []   # list of dicts: name, token, priority, served_at
if "checked_in" not in st.session_state:
    st.session_state.checked_in = set()     # set of tokens that have checked in
if "token_priority" not in st.session_state:
    st.session_state.token_priority = {}    # maps str(token) -> priority label
if "token_patient_type" not in st.session_state:
    st.session_state.token_patient_type = {}  # maps str(token) -> patient type
if "last_served" not in st.session_state:
    st.session_state.last_served = None

# ─────────────────────────────────────────
# Priority Configuration
# ─────────────────────────────────────────
PRIORITY_CONFIG = {
    "🔴 Emergency": {"color": "#fde8e8", "border": "#e53935", "sort": 0, "wait_multiplier": 0.5},
    "🟡 Urgent":    {"color": "#fff8e1", "border": "#f9a825", "sort": 1, "wait_multiplier": 0.75},
    "🟢 Normal":    {"color": "#f0f2f6", "border": "#4a90d9", "sort": 2, "wait_multiplier": 1.0},
}

# Patient type configuration — icon and label for each type
PATIENT_TYPE_CONFIG = {
    "👨 Male":   {"icon": "👨", "color": "#e8f0fe"},
    "👩 Female": {"icon": "👩", "color": "#fce4ec"},
    "👶 Child":  {"icon": "👶", "color": "#fff9e6"},
    "👴 Senior": {"icon": "👴", "color": "#f3e5f5"},
}

def get_patient_type_label(type_str):
    """Match a stored type string back to a full label key."""
    for label in PATIENT_TYPE_CONFIG:
        if type_str in label:
            return label
    return "👨 Male"

def get_patient_type_icon(type_str):
    """Return just the emoji icon for a patient type."""
    label = get_patient_type_label(type_str)
    return PATIENT_TYPE_CONFIG[label]["icon"]

def get_priority_label(priority_str):
    """Match a stored priority string back to a full label key."""
    for label in PRIORITY_CONFIG:
        if priority_str in label:
            return label
    return "🟢 Normal"

def format_countdown(wait_minutes):
    """Convert fractional minutes into a readable countdown string."""
    if wait_minutes <= 0:
        return "Now"
    hours   = int(wait_minutes) // 60
    minutes = int(wait_minutes) % 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes} min"

# ─────────────────────────────────────────
# 1. Title
# ─────────────────────────────────────────
st.title("🏥 Smart Queue Management System")
st.caption("Efficient patient flow management for small hospitals")
st.divider()

# ─────────────────────────────────────────
# 2. Statistics Dashboard
# ─────────────────────────────────────────
st.subheader("📊 Queue Statistics")

queue = get_queue()

# Attach priority from session state
for patient in queue:
    patient["priority"] = st.session_state.token_priority.get(
        str(patient.get("token")), "🟢 Normal"
    )

total_waiting    = len(queue)
total_served     = len(st.session_state.served_patients)
checked_in_count = sum(1 for p in queue if p.get("token") in st.session_state.checked_in)
emergency_count  = sum(1 for p in queue if "Emergency" in p.get("priority", ""))
child_count      = sum(
    1 for p in queue
    if "Child" in st.session_state.token_patient_type.get(str(p.get("token")), "")
)

if total_waiting > 0:
    avg_wait = sum(
        calculate_wait_time(i + 1) *
        PRIORITY_CONFIG.get(get_priority_label(p.get("priority", "Normal")), {}).get("wait_multiplier", 1.0)
        for i, p in enumerate(queue)
    ) / total_waiting
else:
    avg_wait = 0

s1, s2, s3, s4, s5, s6 = st.columns(6)
with s1: st.metric("🧍 Waiting",       total_waiting)
with s2: st.metric("✅ Served Today",  total_served)
with s3: st.metric("📍 Checked In",    checked_in_count)
with s4: st.metric("⏱️ Avg Wait",      f"{avg_wait:.0f} min")
with s5: st.metric("🔴 Emergency",     emergency_count)
with s6: st.metric("👶 Children",      child_count)

st.divider()

# ─────────────────────────────────────────
# 3. Patient Registration
# ─────────────────────────────────────────
st.subheader("📋 Patient Registration")

rc1, rc2, rc3, rc4 = st.columns([3, 2, 2, 1])

with rc1:
    patient_name = st.text_input("Patient Name", placeholder="Enter patient's full name")

with rc2:
    priority = st.selectbox(
        "Priority Level",
        options=["🟢 Normal", "🟡 Urgent", "🔴 Emergency"],
        index=0
    )

with rc3:
    patient_type = st.selectbox(
        "Patient Type",
        options=["👨 Male", "👩 Female", "👶 Child", "👴 Senior"],
        index=0
    )

with rc4:
    st.write(""); st.write("")   # vertical spacing
    get_token_btn = st.button("🎫 Get Token", use_container_width=True, type="primary")

if get_token_btn:
    if patient_name.strip() == "":
        st.warning("⚠️ Please enter a patient name before getting a token.")
    else:
        token = add_patient(patient_name.strip())
        st.session_state.token_priority[str(token)]     = priority
        st.session_state.token_patient_type[str(token)] = patient_type
        pt_icon = get_patient_type_icon(patient_type)
        st.success(
            f"✅ Token **#{token}** assigned to **{patient_name.strip()}** "
            f"| {priority} | {pt_icon} {patient_type.split(' ', 1)[-1]}"
        )

st.divider()

# ─────────────────────────────────────────
# 4. Search & Filter
# ─────────────────────────────────────────
st.subheader("🔍 Search & Filter Queue")

fc1, fc2, fc3 = st.columns([3, 2, 2])

with fc1:
    search_query = st.text_input(
        "Search by name or token number",
        placeholder="e.g. Ravi or 5"
    )

with fc2:
    filter_priority = st.multiselect(
        "Filter by Priority",
        options=["🔴 Emergency", "🟡 Urgent", "🟢 Normal"],
        default=["🔴 Emergency", "🟡 Urgent", "🟢 Normal"]
    )

with fc3:
    filter_type = st.multiselect(
        "Filter by Patient Type",
        options=["👨 Male", "👩 Female", "👶 Child", "👴 Senior"],
        default=["👨 Male", "👩 Female", "👶 Child", "👴 Senior"]
    )

st.divider()

# ─────────────────────────────────────────
# 5. Queue Display
# ─────────────────────────────────────────
st.subheader("👥 Current Queue")

ref_col, _ = st.columns([1, 6])
with ref_col:
    if st.button("🔄 Refresh"):
        st.rerun()

# Sort by priority (Emergency → Urgent → Normal)
queue_sorted = sorted(
    queue,
    key=lambda p: PRIORITY_CONFIG.get(
        get_priority_label(p.get("priority", "Normal")), {}
    ).get("sort", 2)
)

# Apply search filter
if search_query.strip():
    sq = search_query.strip().lower()
    queue_sorted = [
        p for p in queue_sorted
        if sq in p.get("name", "").lower() or sq in str(p.get("token", ""))
    ]

# Apply priority filter
if filter_priority:
    queue_sorted = [
        p for p in queue_sorted
        if get_priority_label(p.get("priority", "Normal")) in filter_priority
    ]

# Apply patient type filter
if filter_type:
    queue_sorted = [
        p for p in queue_sorted
        if get_patient_type_label(
            st.session_state.token_patient_type.get(str(p.get("token")), "👨 Male")
        ) in filter_type
    ]

if not queue_sorted:
    if not queue:
        st.info("🎉 The queue is currently empty. No patients waiting.")
    else:
        st.info("🔍 No patients match your search or filter criteria.")
else:
    st.caption(f"Showing **{len(queue_sorted)}** of **{len(queue)}** patient(s)")

    for index, patient in enumerate(queue_sorted):
        position   = index + 1
        name       = patient.get("name", "Unknown")
        token      = patient.get("token", "N/A")
        p_label    = get_priority_label(patient.get("priority", "Normal"))
        cfg        = PRIORITY_CONFIG.get(p_label, PRIORITY_CONFIG["🟢 Normal"])
        is_checked = token in st.session_state.checked_in

        # Patient type for this token
        pt_raw   = st.session_state.token_patient_type.get(str(token), "👨 Male")
        pt_label = get_patient_type_label(pt_raw)
        pt_icon  = PATIENT_TYPE_CONFIG[pt_label]["icon"]

        # Compute priority-adjusted wait time
        raw_wait  = calculate_wait_time(position)
        wait_time = raw_wait * cfg["wait_multiplier"]
        countdown = format_countdown(wait_time)

        # Override styling for next-in-line
        if position == 1:
            card_color   = "#e6f4ea"
            border_color = "#34a853"
            pos_badge    = "🟢 <b>Next in Line</b>"
        else:
            card_color   = cfg["color"]
            border_color = cfg["border"]
            pos_badge    = f"📍 Position #{position}"

        checkin_status = "✅ Checked In" if is_checked else "⬜ Not Checked In"

        card_col, btn_col = st.columns([7, 1])

        with card_col:
            st.markdown(
                f"""
                <div style="
                    background-color: {card_color};
                    border-radius: 10px;
                    padding: 14px 18px;
                    margin-bottom: 8px;
                    border-left: 6px solid {border_color};
                ">
                    <b style="font-size:16px;">{pt_icon} {name}</b>
                    &nbsp;&nbsp;<span style="font-size:13px; color:#666;">{p_label}</span>
                    &nbsp;<span style="font-size:12px; color:#888;">· {pt_label}</span><br>
                    🎫 Token: <b>#{token}</b> &nbsp;|&nbsp;
                    {pos_badge} &nbsp;|&nbsp;
                    ⏱️ Est. Wait: <b>{countdown}</b> &nbsp;|&nbsp;
                    {checkin_status}
                </div>
                """,
                unsafe_allow_html=True
            )

        with btn_col:
            # Check-in toggle
            btn_icon = "✅" if not is_checked else "↩️"
            btn_help = "Mark as checked in" if not is_checked else "Undo check-in"
            if st.button(btn_icon, key=f"checkin_{token}", help=btn_help):
                if is_checked:
                    st.session_state.checked_in.discard(token)
                else:
                    st.session_state.checked_in.add(token)
                st.rerun()

st.divider()

# ─────────────────────────────────────────
# 6. Doctor Panel
# ─────────────────────────────────────────
st.subheader("🩺 Doctor Panel")

dc1, dc2 = st.columns([2, 4])

with dc1:
    next_btn = st.button("➡️ Call Next Patient", use_container_width=True, type="primary")

with dc2:
    if next_btn:
        served = next_patient()
        if served:
            token_key = str(served.get("token"))

            # Save to history
            st.session_state.served_patients.append({
                "name":         served.get("name"),
                "token":        served.get("token"),
                "patient_type": st.session_state.token_patient_type.get(token_key, "👨 Male"),
                "priority":     st.session_state.token_priority.get(token_key, "🟢 Normal"),
                "served_at":    datetime.now().strftime("%H:%M:%S")
            })

            # Clean up state for served patient
            st.session_state.checked_in.discard(served.get("token"))
            st.session_state.last_served = served

            st.success(
                f"🔔 Now serving: **{served.get('name')}** — "
                f"Token **#{served.get('token')}**"
            )
            st.rerun()
        else:
            st.info("✅ The queue is empty. No patients to call.")

# Show last served reminder below the button
if st.session_state.last_served:
    ls = st.session_state.last_served
    st.caption(f"Last called: **{ls.get('name')}** (Token #{ls.get('token')})")

st.divider()

# ─────────────────────────────────────────
# 7. Served History & Export to CSV
# ─────────────────────────────────────────
st.subheader("📁 Served Patient History")

if not st.session_state.served_patients:
    st.info("No patients have been served yet today.")
else:
    df = pd.DataFrame(st.session_state.served_patients)
    df.columns = ["Patient Name", "Token #", "Patient Type", "Priority", "Served At"]
    df.index   = df.index + 1   # 1-based index

    st.dataframe(df, use_container_width=True)

    # Export button
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Export to CSV",
        data=csv_bytes,
        file_name=f"queue_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )