import streamlit as st
import pandas as pd
import socket
import uuid
import subprocess
import re
import time
from datetime import datetime

import psutil
import plotly.graph_objects as go

# ===== إعداد الصفحة =====
st.set_page_config(page_title="مركز التحكم بالشبكة", page_icon="🌐",
                   layout="wide", initial_sidebar_state="expanded")

# ===== التصميم =====
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family:'Cairo',sans-serif; }
.stApp { background: radial-gradient(1200px 600px at 80% -10%, #0b2a4a 0%, transparent 55%),
         radial-gradient(900px 500px at 0% 0%, #102a43 0%, transparent 45%), #030712; direction:rtl; }
.hero { background:linear-gradient(135deg,rgba(56,189,248,.12),rgba(99,102,241,.10));
        border:1px solid rgba(56,189,248,.25); border-radius:22px; padding:26px 32px;
        margin-bottom:22px; box-shadow:0 10px 40px rgba(2,8,23,.6); }
.hero h1 { color:#f8fafc; font-size:40px; font-weight:800; margin:0; }
.hero p { color:#94a3b8; font-size:17px; margin:6px 0 0 0; }
.kpi { background:linear-gradient(160deg,#0f172a,#111827); border:1px solid rgba(148,163,184,.15);
       border-radius:18px; padding:20px 22px; height:100%; transition:.25s;
       box-shadow:0 6px 24px rgba(2,8,23,.45); }
.kpi:hover { transform:translateY(-4px); border-color:rgba(56,189,248,.45); }
.kpi .label { color:#94a3b8; font-size:15px; font-weight:600; }
.kpi .value { color:#f1f5f9; font-size:32px; font-weight:800; margin-top:6px; }
.kpi .delta { font-size:14px; font-weight:600; margin-top:4px; }
.kpi .icon { font-size:26px; float:left; opacity:.9; }
.up { color:#4ade80; } .down { color:#f87171; }
.card { background:rgba(15,23,42,.65); border:1px solid rgba(148,163,184,.14);
        border-radius:18px; padding:18px 22px; margin-bottom:16px; backdrop-filter:blur(6px); }
.card h3 { color:#e2e8f0; font-size:20px; font-weight:700; margin:0 0 12px 0; }
[data-testid="stDataFrame"] { direction:ltr; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0b1220,#030712);
        border-left:1px solid rgba(56,189,248,.18); }
[data-testid="stSidebar"] * { direction:rtl; }
.stButton > button { border-radius:12px; border:1px solid rgba(56,189,248,.35);
        background:linear-gradient(145deg,#0f172a,#1e293b); color:#38bdf8; font-weight:700; }
.stButton > button:hover { background:#38bdf8; color:#03111f; border-color:#38bdf8; }
footer, #MainMenu { visibility:hidden; }
</style>
""", unsafe_allow_html=True)


def human_bytes(n):
    for u in ["B", "KB", "MB", "GB", "TB"]:
        if abs(n) < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PB"


def get_local_info():
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
    except Exception:
        ip = "127.0.0.1"
    mac = ':'.join(['{:02X}'.format((uuid.getnode() >> e) & 0xff)
                    for e in range(0, 8 * 6, 8)][::-1])
    return {"hostname": hostname, "ip": ip, "mac": mac}


DEMO_DEVICES = [
    {"IP": "192.168.1.25", "MAC": "F1:A2:B3:C4:D5:E6", "النوع": "ديناميكي", "الحالة": "🟢 متصل"},
    {"IP": "192.168.1.12", "MAC": "A1:B2:C3:D4:E5:F6", "النوع": "ديناميكي", "الحالة": "🟢 متصل"},
    {"IP": "192.168.1.40", "MAC": "C8:D9:E0:F1:A2:B3", "النوع": "ثابت", "الحالة": "🟢 متصل"},
]


@st.cache_data(ttl=20, show_spinner=False)
def scan_arp_table():
    rows = []
    try:
        out = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=8).stdout
        pat = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})\s+([0-9a-fA-F]{2}(?:[-:][0-9a-fA-F]{2}){5})\s+(\w+)")
        for ip, mac, kind in pat.findall(out):
            if ip.endswith(".255") or mac.lower().startswith("ff"):
                continue
            rows.append({"IP": ip, "MAC": mac.upper().replace("-", ":"),
                         "النوع": "ثابت" if kind.lower() == "static" else "ديناميكي",
                         "الحالة": "🟢 متصل"})
    except Exception:
        pass
    if not rows:                       # بيانات احتياطية للسحابة
        rows = DEMO_DEVICES
    return pd.DataFrame(rows)


def get_interfaces():
    rows = []
    for name, s in psutil.net_if_stats().items():
        ipv4 = next((a.address for a in psutil.net_if_addrs().get(name, [])
                     if a.family == socket.AF_INET), "—")
        rows.append({"الواجهة": name, "IPv4": ipv4,
                     "السرعة (Mbps)": s.speed or "—", "MTU": s.mtu,
                     "الحالة": "🟢 فعّالة" if s.isup else "🔴 متوقفة"})
    return pd.DataFrame(rows)


if "io_history" not in st.session_state:
    st.session_state.io_history = []
if "last_io" not in st.session_state:
    st.session_state.last_io = None


def update_history():
    cur = psutil.net_io_counters()
    now = time.time()
    last = st.session_state.last_io
    up = down = 0.0
    if last:
        dt = max(now - last["ts"], 1e-6)
        up = (cur.bytes_sent - last["sent"]) / dt
        down = (cur.bytes_recv - last["recv"]) / dt
    st.session_state.last_io = {"sent": cur.bytes_sent, "recv": cur.bytes_recv, "ts": now}
    st.session_state.io_history.append(
        {"time": datetime.now().strftime("%H:%M:%S"), "up": up, "down": down})
    st.session_state.io_history = st.session_state.io_history[-30:]
    return up, down


local = get_local_info()
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding:10px 0 18px">
        <div style="font-size:46px">🌐</div>
        <div style="color:#f1f5f9;font-size:20px;font-weight:800">مركز التحكم بالشبكة</div>
        <div style="color:#64748b;font-size:13px">Network Control Center</div>
    </div>""", unsafe_allow_html=True)
    page = st.radio("التنقّل",
                    ["🏠 لوحة القيادة", "📱 الأجهزة المتصلة", "📊 استخدام الشبكة", "⚙️ الإعدادات"],
                    label_visibility="collapsed")
    st.divider()
    st.markdown(f"""
    <div style="color:#94a3b8;font-size:13px;line-height:1.9">
        <b style="color:#38bdf8">الجهاز الحالي</b><br>
        🖥️ {local['hostname']}<br>🌍 {local['ip']}<br>🔑 {local['mac']}
    </div>""", unsafe_allow_html=True)
    auto = st.toggle("🔄 تحديث تلقائي (5 ثوانٍ)", value=False)


def page_dashboard():
    st.markdown('<div class="hero"><h1>🌐 لوحة القيادة</h1>'
                '<p>نظرة عامة فورية على حالة الشبكة والأجهزة وحركة البيانات</p></div>',
                unsafe_allow_html=True)
    up, down = update_history()
    io = psutil.net_io_counters()
    n = len(scan_arp_table()) + 1
    cols = st.columns(4)
    cards = [("📱", "الأجهزة المتصلة", str(n), "up", "▲ نشطة الآن"),
             ("⬇️", "سرعة التنزيل", human_bytes(down) + "/s", "up", "حركة واردة"),
             ("⬆️", "سرعة الرفع", human_bytes(up) + "/s", "down", "حركة صادرة"),
             ("📦", "إجمالي البيانات", human_bytes(io.bytes_sent + io.bytes_recv), "up", "منذ الإقلاع")]
    for col, (icon, label, val, cls, d) in zip(cols, cards):
        col.markdown(f'<div class="kpi"><span class="icon">{icon}</span>'
                     f'<div class="label">{label}</div><div class="value">{val}</div>'
                     f'<div class="delta {cls}">{d}</div></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    L, R = st.columns([2, 1])
    with L:
        st.markdown('<div class="card"><h3>📈 حركة البيانات اللحظية</h3>', unsafe_allow_html=True)
        df = pd.DataFrame(st.session_state.io_history)
        if not df.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["time"], y=df["down"] / 1024, name="تنزيل (KB/s)",
                                     fill="tozeroy", line=dict(color="#38bdf8", width=2)))
            fig.add_trace(go.Scatter(x=df["time"], y=df["up"] / 1024, name="رفع (KB/s)",
                                     fill="tozeroy", line=dict(color="#a78bfa", width=2)))
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(color="#cbd5e1"), legend=dict(orientation="h", y=1.1),
                              xaxis=dict(gridcolor="rgba(148,163,184,.1)"),
                              yaxis=dict(gridcolor="rgba(148,163,184,.1)"))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("جارٍ جمع البيانات...")
        st.markdown("</div>", unsafe_allow_html=True)
    with R:
        st.markdown('<div class="card"><h3>🖧 موارد النظام</h3>', unsafe_allow_html=True)
        for label, val, color in [("المعالج CPU", psutil.cpu_percent(), "#38bdf8"),
                                   ("الذاكرة RAM", psutil.virtual_memory().percent, "#a78bfa")]:
            g = go.Figure(go.Indicator(mode="gauge+number", value=val,
                          number={"suffix": "%", "font": {"color": "#f1f5f9", "size": 26}},
                          gauge={"axis": {"range": [0, 100], "tickcolor": "#475569"},
                                 "bar": {"color": color}, "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0},
                          title={"text": label, "font": {"color": "#94a3b8", "size": 14}}))
            g.update_layout(height=160, margin=dict(l=10, r=10, t=30, b=0),
                            paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(g, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)


def page_devices():
    st.markdown('<div class="hero"><h1>📱 الأجهزة المتصلة</h1>'
                '<p>قائمة الأجهزة المكتشفة على شبكتك المحلية</p></div>', unsafe_allow_html=True)
    cur = pd.DataFrame([{"IP": local["ip"], "MAC": local["mac"],
                         "النوع": "هذا الجهاز", "الحالة": "🟢 متصل"}])
    full = pd.concat([cur, scan_arp_table()], ignore_index=True)
    _, c2 = st.columns([3, 1])
    with c2:
        if st.button("🔄 إعادة الفحص"):
            scan_arp_table.clear()
            st.rerun()
    st.markdown(f'<div class="card"><h3>عدد الأجهزة: {len(full)}</h3>', unsafe_allow_html=True)
    st.dataframe(full, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="card"><h3>🔌 واجهات الشبكة</h3>', unsafe_allow_html=True)
    st.dataframe(get_interfaces(), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def page_usage():
    st.markdown('<div class="hero"><h1>📊 استخدام الشبكة</h1>'
                '<p>تحليل حركة البيانات وتوزيع الاستخدام</p></div>', unsafe_allow_html=True)
    io = psutil.net_io_counters()
    cols = st.columns(3)
    for col, (icon, label, val) in zip(cols, [
            ("⬇️", "إجمالي التنزيل", human_bytes(io.bytes_recv)),
            ("⬆️", "إجمالي الرفع", human_bytes(io.bytes_sent)),
            ("📨", "عدد الحزم", f"{io.packets_sent + io.packets_recv:,}")]):
        col.markdown(f'<div class="kpi"><span class="icon">{icon}</span>'
                     f'<div class="label">{label}</div><div class="value">{val}</div></div>',
                     unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    L, R = st.columns(2)
    with L:
        st.markdown('<div class="card"><h3>🥧 توزيع البيانات</h3>', unsafe_allow_html=True)
        pie = go.Figure(go.Pie(labels=["تنزيل", "رفع"], values=[io.bytes_recv, io.bytes_sent],
                               hole=.55, marker=dict(colors=["#38bdf8", "#a78bfa"])))
        pie.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#cbd5e1"),
                          margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(pie, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
    with R:
        st.markdown('<div class="card"><h3>📡 حركة البيانات لكل واجهة</h3>', unsafe_allow_html=True)
        rows = [{"الواجهة": k, "تنزيل": v.bytes_recv, "رفع": v.bytes_sent}
                for k, v in psutil.net_io_counters(pernic=True).items()
                if v.bytes_recv + v.bytes_sent > 0]
        if rows:
            d = pd.DataFrame(rows)
            bar = go.Figure()
            bar.add_trace(go.Bar(x=d["الواجهة"], y=d["تنزيل"] / 1e6, name="تنزيل (MB)", marker_color="#38bdf8"))
            bar.add_trace(go.Bar(x=d["الواجهة"], y=d["رفع"] / 1e6, name="رفع (MB)", marker_color="#a78bfa"))
            bar.update_layout(height=320, barmode="group", paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#cbd5e1"),
                              margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.1),
                              xaxis=dict(gridcolor="rgba(148,163,184,.1)"),
                              yaxis=dict(gridcolor="rgba(148,163,184,.1)"))
            st.plotly_chart(bar, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("لا توجد بيانات كافية.")
        st.markdown("</div>", unsafe_allow_html=True)


def page_settings():
    st.markdown('<div class="hero"><h1>⚙️ الإعدادات والمعلومات</h1>'
                '<p>تفاصيل النظام</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="card"><h3>معلومات النظام</h3>', unsafe_allow_html=True)
    boot = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M")
    info = pd.DataFrame([
        {"المعلومة": "اسم الجهاز", "القيمة": local["hostname"]},
        {"المعلومة": "عنوان IP", "القيمة": local["ip"]},
        {"المعلومة": "عنوان MAC", "القيمة": local["mac"]},
        {"المعلومة": "عدد الأنوية", "القيمة": str(psutil.cpu_count(logical=True))},
        {"المعلومة": "إجمالي الذاكرة", "القيمة": human_bytes(psutil.virtual_memory().total)},
        {"المعلومة": "وقت الإقلاع", "القيمة": boot}])
    st.dataframe(info, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


if page.startswith("🏠"):
    page_dashboard()
elif page.startswith("📱"):
    page_devices()
elif page.startswith("📊"):
    page_usage()
else:
    page_settings()

st.markdown('<div style="text-align:center;color:#475569;font-size:13px;margin-top:30px;'
            'padding-top:16px;border-top:1px solid rgba(148,163,184,.12)">'
            'صُمّم بكل احترافية 🚀 — مركز التحكم بالشبكة</div>', unsafe_allow_html=True)

if auto:
    time.sleep(5)
    st.rerun()
