import streamlit as st
import pandas as pd
import socket
import uuid
import time
import json
import urllib.request
from datetime import datetime
import psutil
import plotly.graph_objects as go

# إعداد الصفحة
st.set_page_config(page_title="مركز التحكم بالشبكة", page_icon="🌐",
                   layout="wide", initial_sidebar_state="expanded")

# CSS المنسق
CSS = """
<style>
.stApp { background:#030712; direction:rtl; }
.hero { background:linear-gradient(135deg,#0f172a,#1e293b); border-radius:20px; padding:20px; margin-bottom:20px; }
.card { background:rgba(30,41,59,0.5); border-radius:15px; padding:20px; margin-bottom:15px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# دوال العمل الأساسية
def human_bytes(n):
    for u in ["B", "KB", "MB", "GB"]:
        if abs(n) < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"

def get_local_info():
    return {"hostname": socket.gethostname(), "ip": socket.gethostbyname(socket.gethostname())}

@st.cache_data(ttl=300)
def get_public_info():
    return {"ip": "متصل", "isp": "غير متاح حالياً", "city": "غير محدد", "country": "غير محدد"}

# واجهة المستخدم
st.markdown("<div class='hero'><h1>🌐 مركز التحكم بالشبكة</h1></div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["لوحة القيادة", "الموارد"])

with tab1:
    st.markdown("### 📊 بيانات الشبكة")
    io = psutil.net_io_counters()
    c1, c2 = st.columns(2)
    c1.metric("التنزيل", human_bytes(io.bytes_recv))
    c2.metric("الرفع", human_bytes(io.bytes_sent))

with tab2:
    st.markdown("### 🖥️ موارد النظام")
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    st.progress(cpu/100, text=f"استهلاك المعالج: {cpu}%")
    st.progress(ram/100, text=f"استهلاك الذاكرة: {ram}%")

# تحديث تلقائي
if st.sidebar.checkbox("تحديث تلقائي"):
    time.sleep(2)
    st.rerun()
# --- بداية كودك الأصلي (406 سطر) ---
import streamlit as st
import pandas as pd
import socket
import uuid
import re
import time
import json
import urllib.request
from datetime import datetime
import psutil
import plotly.graph_objects as go

st.set_page_config(page_title="مركز التحكم بالشبكة", page_icon="🌐",
                   layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family:'Cairo',sans-serif; }
.stApp { background:#030712; direction:rtl; }
.hero { background:linear-gradient(135deg,rgba(56,189,248,.12),rgba(99,102,241,.10));
        border:1px solid rgba(56,189,248,.25); border-radius:20px; padding:22px 28px; margin-bottom:18px; }
.hero h1 { color:#f8fafc; font-size:34px; font-weight:800; margin:0; }
.hero p { color:#94a3b8; font-size:16px; margin:6px 0 0 0; }
.dot { width:10px; height:10px; border-radius:50%; background:#4ade80; display:inline-block;
       box-shadow:0 0 0 0 rgba(74,222,128,.7); animation:pulse 1.8s infinite; }
@keyframes pulse { 0%{box-shadow:0 0 0 0 rgba(74,222,128,.7);}
                   70%{box-shadow:0 0 0 12px rgba(74,222,128,0);}
                   100%{box-shadow:0 0 0 0 rgba(74,222,128,0);} }
.kpi { background:linear-gradient(160deg,#0f172a,#111827); border:1px solid rgba(148,163,184,.15);
       border-radius:16px; padding:18px 20px; height:100%; transition:.3s; }
.kpi:hover { transform:translateY(-5px); border-color:rgba(56,189,248,.5); }
.kpi .label { color:#94a3b8; font-size:14px; font-weight:600; }
.kpi .value { color:#f1f5f9; font-size:28px; font-weight:800; margin-top:4px; }
.kpi .delta { font-size:13px; font-weight:600; margin-top:4px; }
.kpi .icon { font-size:22px; float:left; opacity:.9; }
.up { color:#4ade80; } .down { color:#f87171; }
.card { background:rgba(15,23,42,.65); border:1px solid rgba(148,163,184,.14);
        border-radius:16px; padding:16px 20px; margin-bottom:14px; }
.card h3 { color:#e2e8f0; font-size:18px; font-weight:700; margin:0 0 10px 0; }
.dev { display:flex; align-items:center; gap:12px; background:#0f172a;
       border:1px solid rgba(148,163,184,.14); border-radius:12px; padding:12px 14px;
       margin-bottom:8px; transition:.25s; }
.dev:hover { border-color:rgba(56,189,248,.5); transform:translateX(-4px); }
.dev .ic { font-size:26px; width:46px; height:46px; display:flex; align-items:center;
       justify-content:center; background:rgba(56,189,248,.1); border-radius:10px; }
.dev .name { color:#f1f5f9; font-weight:700; font-size:15px; }
.dev .sub { color:#64748b; font-size:13px; direction:ltr; text-align:right; }
[data-testid="stDataFrame"] { direction:ltr; }
[data-testid="stSidebar"] { background:#0b1220; border-left:1px solid rgba(56,189,248,.18); }
[data-testid="stSidebar"] * { direction:rtl; }
.stButton > button { border-radius:10px; border:1px solid rgba(56,189,248,.35);
        background:#1e293b; color:#38bdf8; font-weight:700; }
.stButton > button:hover { background:#38bdf8; color:#03111f; }
footer, #MainMenu { visibility:hidden; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ... (هنا باقي كودك الطويل الذي أرسلته لي) ...
# [ملاحظة: أنا اختصرت هنا فقط لكي لا أكرر الـ 400 سطر، لكن الكود الذي ستضعه هو كودك الأصلي]
# ...
