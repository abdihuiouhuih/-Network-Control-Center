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


@st.cache_data(ttl=300, show_spinner=False)
def get_public_info():
    try:
        req = urllib.request.Request(
            "http://ip-api.com/json/?fields=status,country,city,isp,query,lat,lon",
            headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=5).read().decode())
        if data.get("status") == "success":
            return {"ip": data.get("query", "—"), "isp": data.get("isp", "—"),
                    "city": data.get("city", "—"), "country": data.get("country", "—"),
                    "lat": data.get("lat"), "lon": data.get("lon")}
    except Exception:
        pass
    return {"ip": "غير متاح", "isp": "—", "city": "—", "country": "—", "lat": None, "lon": None}


@st.cache_data(ttl=15, show_spinner=False)
def measure_latency():
    targets = [("Google", "8.8.8.8", 53), ("Cloudflare", "1.1.1.1", 53)]
    results = []
    for name, host, port in targets:
        t0 = time.time()
        ok = True
        try:
            s = socket.create_connection((host, port), timeout=2)
            s.close()
        except Exception:
            ok = False
        ms = (time.time() - t0) * 1000 if ok else None
        results.append({"name": name, "host": host,
                        "txt": f"{ms:.0f} ms" if ms else "—",
                        "ms": ms if ms else 999})
    return results


def quality_label(ms):
    if ms is None or ms >= 999:
        return "غير متصل", "#f87171"
    if ms < 30:
        return "ممتاز", "#4ade80"
    if ms < 80:
        return "جيد", "#38bdf8"
    if ms < 150:
        return "متوسط", "#fbbf24"
    return "ضعيف", "#f87171"


def device_icon(ip, kind):
    last = ip.rsplit(".", 1)[-1]
    if last in ("1", "254"):
        return "📡"
    if kind == "هذا الجهاز":
        return "💻"
    return "📱"


DEMO_DEVICES = [
    {"IP": "192.168.1.1", "MAC": "AC:DE:48:00:11:22", "النوع": "ثابت", "الحالة": "🟢 متصل"},
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
    if not rows:
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
    st.markdown("<div style='text-align:center;padding:10px 0 18px'>"
                "<div style='font-size:46px'>🌐</div>"
                "<div style='color:#f1f5f9;font-size:20px;font-weight:800'>مركز التحكم بالشبكة</div>"
                "<div style='color:#64748b;font-size:13px'>Network Control Center</div></div>",
                unsafe_allow_html=True)
    page = st.radio("التنقّل",
                    ["🏠 لوحة القيادة", "📱 الأجهزة المتصلة", "📊 استخدام الشبكة",
                     "🌍 معلومات الاتصال", "⚙️ الإعدادات"],
                    label_visibility="collapsed")
    st.divider()
    st.markdown("<div style='color:#94a3b8;font-size:13px;line-height:1.9'>"
                "<b style='color:#38bdf8'>الجهاز الحالي</b><br>"
                f"🖥️ {local['hostname']}<br>🌍 {local['ip']}<br>🔑 {local['mac']}</div>",
                unsafe_allow_html=True)
    auto = st.toggle("🔄 تحديث تلقائي (5 ثوانٍ)", value=False)


def hero(title, sub):
    st.markdown(f"<div class='hero'><h1>{title}</h1><p>{sub}</p></div>", unsafe_allow_html=True)


def kpi(col, icon, label, val, cls="", delta=""):
    extra = f"<div class='delta {cls}'>{delta}</div>" if delta else ""
    col.markdown(f"<div class='kpi'><span class='icon'>{icon}</span>"
                 f"<div class='label'>{label}</div><div class='value'>{val}</div>{extra}</div>",
                 unsafe_allow_html=True)


def page_dashboard():
    lat = measure_latency()
    best = min((r["ms"] for r in lat), default=999)
    ql, qc = quality_label(best)
    hero("🌐 لوحة القيادة",
         f"<span class='dot'></span> النظام يعمل &nbsp;|&nbsp; "
         f"<span style='color:{qc}'>جودة الاتصال: {ql} ({best:.0f}ms)</span> &nbsp;|&nbsp; "
         f"🕐 {datetime.now().strftime('%H:%M:%S')}")
    up, down = update_history()
    io = psutil.net_io_counters()
    n = len(scan_arp_table()) + 1
    c = st.columns(4)
    kpi(c[0], "📱", "الأجهزة المتصلة", str(n), "up", "▲ نشطة الآن")
    kpi(c[1], "⬇️", "سرعة التنزيل", human_bytes(down) + "/s", "up", "حركة واردة")
    kpi(c[2], "⬆️", "سرعة الرفع", human_bytes(up) + "/s", "down", "حركة صادرة")
    kpi(c[3], "📦", "إجمالي البيانات", human_bytes(io.bytes_sent + io.bytes_recv), "up", "منذ الإقلاع")
    st.markdown("<br>", unsafe_allow_html=True)
    L, R = st.columns([2, 1])
    with L:
        st.markdown("<div class='card'><h3>📈 حركة البيانات اللحظية</h3>", unsafe_allow_html=True)
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
        st.markdown("<div class='card'><h3>🖧 موارد النظام</h3>", unsafe_allow_html=True)
        for label, val, color in [("CPU", psutil.cpu_percent(), "#38bdf8"),
                                   ("RAM", psutil.virtual_memory().percent, "#a78bfa")]:
            g = go.Figure(go.Indicator(mode="gauge+number", value=val,
                          number={"suffix": "%", "font": {"color": "#f1f5f9", "size": 24}},
                          gauge={"axis": {"range": [0, 100], "tickcolor": "#475569"},
                                 "bar": {"color": color}, "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0},
                          title={"text": label, "font": {"color": "#94a3b8", "size": 13}}))
            g.update_layout(height=150, margin=dict(l=10, r=10, t=28, b=0),
                            paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(g, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)


def page_devices():
    hero("📱 الأجهزة المتصلة", "قائمة الأجهزة المكتشفة على شبكتك المحلية")
    cur = pd.DataFrame([{"IP": local["ip"], "MAC": local["mac"],
                         "النوع": "هذا الجهاز", "الحالة": "🟢 متصل"}])
    full = pd.concat([cur, scan_arp_table()], ignore_index=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        q = st.text_input("بحث", "", label_visibility="collapsed",
                          placeholder="🔍 ابحث بعنوان IP أو MAC")
    with c2:
        if st.button("🔄 إعادة الفحص"):
            scan_arp_table.clear()
            st.rerun()
    if q:
        full = full[full.apply(lambda r: q.lower() in str(r["IP"]).lower()
                               or q.lower() in str(r["MAC"]).lower(), axis=1)]
    st.markdown(f"<div class='card'><h3>عدد الأجهزة: {len(full)}</h3>", unsafe_allow_html=True)
    for _, r in full.iterrows():
        ic = device_icon(r["IP"], r["النوع"])
        st.markdown(f"<div class='dev'><div class='ic'>{ic}</div>"
                    f"<div style='flex:1'><div class='name'>{r['IP']}</div>"
                    f"<div class='sub'>{r['MAC']} • {r['النوع']}</div></div>"
                    f"<div style='color:#4ade80;font-weight:700'>{r['الحالة']}</div></div>",
                    unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'><h3>🔌 واجهات الشبكة</h3>", unsafe_allow_html=True)
    st.dataframe(get_interfaces(), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def page_usage():
    hero("📊 استخدام الشبكة", "تحليل حركة البيانات وتوزيع الاستخدام")
    io = psutil.net_io_counters()
    c = st.columns(3)
    kpi(c[0], "⬇️", "إجمالي التنزيل", human_bytes(io.bytes_recv))
    kpi(c[1], "⬆️", "إجمالي الرفع", human_bytes(io.bytes_sent))
    kpi(c[2], "📨", "عدد الحزم", f"{io.packets_sent + io.packets_recv:,}")
    st.markdown("<br>", unsafe_allow_html=True)
    L, R = st.columns(2)
    with L:
        st.markdown("<div class='card'><h3>🥧 توزيع البيانات</h3>", unsafe_allow_html=True)
        pie = go.Figure(go.Pie(labels=["تنزيل", "رفع"], values=[io.bytes_recv, io.bytes_sent],
                               hole=.55, marker=dict(colors=["#38bdf8", "#a78bfa"])))
        pie.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#cbd5e1"),
                          margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(pie, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
    with R:
        st.markdown("<div class='card'><h3>📡 حركة البيانات لكل واجهة</h3>", unsafe_allow_html=True)
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


def page_connection():
    hero("🌍 معلومات الاتصال", "عنوان IP العام والمزوّد وجودة الاتصال بالإنترنت")
    pub = get_public_info()
    c = st.columns(4)
    kpi(c[0], "🌐", "IP العام", pub["ip"])
    kpi(c[1], "🏢", "مزوّد الخدمة", pub["isp"])
    kpi(c[2], "📍", "المدينة", pub["city"])
    kpi(c[3], "🗺️", "الدولة", pub["country"])
    st.markdown("<br>", unsafe_allow_html=True)
    L, R = st.columns(2)
    with L:
        st.markdown("<div class='card'><h3>⚡ اختبار جودة الاتصال</h3>", unsafe_allow_html=True)
        if st.button("🚀 إعادة الاختبار"):
            measure_latency.clear()
            st.rerun()
        for r in measure_latency():
            ql, qc = quality_label(r["ms"])
            st.markdown(f"<div class='dev'><div class='ic'>⚡</div>"
                        f"<div style='flex:1'><div class='name'>{r['name']}</div>"
                        f"<div class='sub'>{r['host']}</div></div>"
                        f"<div style='text-align:left'>"
                        f"<div style='color:{qc};font-weight:800;font-size:18px'>{r['txt']}</div>"
                        f"<div style='color:{qc};font-size:12px'>{ql}</div></div></div>",
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with R:
        st.markdown("<div class='card'><h3>📍 الموقع التقريبي</h3>", unsafe_allow_html=True)
        if pub["lat"] and pub["lon"]:
            st.map(pd.DataFrame([{"lat": pub["lat"], "lon": pub["lon"]}]), zoom=9)
        else:
            st.info("تعذّر تحديد الموقع الجغرافي.")
        st.markdown("</div>", unsafe_allow_html=True)


def page_settings():
    hero("⚙️ الإعدادات والمعلومات", "تفاصيل النظام")
    st.markdown("<div class='card'><h3>معلومات النظام</h3>", unsafe_allow_html=True)
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
elif page.startswith("🌍"):
    page_connection()
else:
    page_settings()

st.markdown("<div style='text-align:center;color:#475569;font-size:13px;margin-top:30px;"
            "padding-top:16px;border-top:1px solid rgba(148,163,184,.12)'>"
            "صُمّم بكل احترافية 🚀 — مركز التحكم بالشبكة</div>", unsafe_allow_html=True)

if auto:
    time.sleep(5)
    st.rerun()
