import streamlit as st
import pandas as pd
import socket
import uuid
import subprocess
import re
import time
import json
import urllib.request
from datetime import datetime

import psutil
import plotly.graph_objects as go

# ================================================================
# إعداد الصفحة
# ================================================================
st.set_page_config(page_title="مركز التحكم بالشبكة", page_icon="🌐",
                   layout="wide", initial_sidebar_state="expanded")

# ================================================================
# التصميم الاحترافي (RTL + ثيم داكن + حركات)
# ================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
html, body, [class*="css"] { font-family:'Cairo',sans-serif; }
.stApp { background: radial-gradient(1200px 600px at 80% -10%, #0b2a4a 0%, transparent 55%),
         radial-gradient(900px 500px at 0% 0%, #102a43 0%, transparent 45%), #030712; direction:rtl; }

/* الشريط العلوي */
.topbar { display:flex; justify-content:space-between; align-items:center;
          background:linear-gradient(135deg,rgba(56,189,248,.12),rgba(99,102,241,.10));
          border:1px solid rgba(56,189,248,.25); border-radius:20px;
          padding:16px 26px; margin-bottom:20px; box-shadow:0 10px 40px rgba(2,8,23,.6); }
.topbar .brand { color:#f8fafc; font-size:26px; font-weight:900; }
.topbar .brand small { color:#64748b; font-size:13px; font-weight:600; }
.topbar .meta { color:#cbd5e1; font-size:14px; text-align:left; line-height:1.7; }
.live { display:inline-flex; align-items:center; gap:8px; color:#4ade80; font-weight:700; }
.dot { width:10px; height:10px; border-radius:50%; background:#4ade80;
       box-shadow:0 0 0 0 rgba(74,222,128,.7); animation:pulse 1.8s infinite; }
@keyframes pulse { 0%{box-shadow:0 0 0 0 rgba(74,222,128,.7);}
                   70%{box-shadow:0 0 0 12px rgba(74,222,128,0);}
                   100%{box-shadow:0 0 0 0 rgba(74,222,128,0);} }

.hero { background:linear-gradient(135deg,rgba(56,189,248,.12),rgba(99,102,241,.10));
        border:1px solid rgba(56,189,248,.25); border-radius:22px; padding:24px 30px;
        margin-bottom:20px; }
.hero h1 { color:#f8fafc; font-size:36px; font-weight:800; margin:0; }
.hero p { color:#94a3b8; font-size:16px; margin:6px 0 0 0; }

.kpi { position:relative; overflow:hidden; background:linear-gradient(160deg,#0f172a,#111827);
       border:1px sol
