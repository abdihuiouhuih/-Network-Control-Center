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
