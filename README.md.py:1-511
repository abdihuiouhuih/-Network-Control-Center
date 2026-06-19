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

# ================================================================
# إعداد الصفحة
# ================================================================
st.set_page_config(
    page_title="مركز التحكم بالشبكة",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ================================================================
# التصميم الاحترافي (RTL + ثيم داكن عصري)
# ================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

html, body, [class*="css"]  { font-family: 'Cairo', sans-serif; }

.stApp {
    background: radial-gradient(1200px 600px at 80% -10%, #0b2a4a 0%, transparent 55%),
                radial-gradient(900px 500px at 0% 0%, #102a43 0%, transparent 45%),
                #030712;
    direction: rtl;
}

/* العناوين */
.hero {
    background: linear-gradient(135deg, rgba(56,189,248,.12), rgba(99,102,241,.10));
    border: 1px solid rgba(56,189,248,.25);
    border-radius: 22px;
    padding: 26px 32px;
    margin-bottom: 22px;
    box-shadow: 0 10px 40px rgba(2,8,23,.6);
}
.hero h1 {
    color: #f8fafc; font-size: 40px; font-weight: 800; margin: 0;
    letter-spacing: -1px;
}
.hero p { color: #94a3b8; font-size: 17px; margin: 6px 0 0 0; }

/* بطاقات المؤشرات */
.kpi {
    background: linear-gradient(160deg, #0f172a, #111827);
    border: 1px solid rgba(148,163,184,.15);
    border-radius: 18px;
    padding: 20px 22px;
    height: 100%;
    transition: .25s;
    box-shadow: 0 6px 24px rgba(2,8,23,.45);
}
.kpi:hover { transform: translateY(-4px); border-color: rgba(56,189,248,.45); }
.kpi .label { color: #94a3b8; font-size: 15px; font-weight: 600; }
.kpi .value { color: #f1f5f9; font-size: 34px; font-weight: 800; margin-top: 6px; }
.kpi .delta { font-size: 14px; font-weight: 600; margin-top: 4px; }
.kpi .icon  { font-size: 26px; float: left; opacity: .9; }
.up   { color: #4ade80; }
.down { color: #f87171; }

/* بطاقة عامة */
.card {
    background: rgba(15,23,42,.65);
    border: 1px solid rgba(148,163,184,.14);
    border-radius: 18px;
    padding: 18px 22px;
    margin-bottom: 16px;
    backdrop-filter: blur(6px);
}
.card h3 { color: #e2e8f0; font-size: 20px; font-weight: 700; margin: 0 0 12px 0; }

/* الجداول */
[data-testid="stDataFrame"] { direction: ltr; }

/* الشريط الجانبي */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1220, #030712);
    border-left: 1px solid rgba(56,189,248,.18);
}
[data-testid="stSidebar"] * { direction: rtl; }

/* أزرار */
.stButton > button {
    border-radius: 12px;
    border: 1px solid rgba(56,189,248,.35);
    background: linear-gradient(145deg,#0f172a,#1e293b);
    color: #38bdf8; font-weight: 700;
}
.stButton > button:hover { background:#38bdf8; color:#03111f; border-color:#38bdf8; }

/* شارة الحالة */
.badge { padding: 4px 12px; border-radius: 999px; font-size: 13px; font-weight: 700; }
.badge-on  { background: rgba(74,222,128,.15); color:#4ade80; border:1px solid rgba(74,222,128,.4);}
.badge-off { background: rgba(248,113,113,.15); color:#f87171; border:1px solid rgba(248,113,113,.4);}

footer, #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ================================================================
# دوال جمع بيانات الشبكة (حقيقية)
# ================================================================
def human_bytes(n: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def get_local_info() -> dict:
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
    except Exception:
        ip = "127.0.0.1"
    mac = ':'.join([
        '{:02X}'.format((uuid.getnode() >> ele) & 0xff)
        for ele in range(0, 8 * 6, 8)
    ][::-1])
    return {"hostname": hostname, "ip": ip, "mac": mac}


@st.cache_data(ttl=20, show_spinner=False)
def scan_arp_table() -> pd.DataFrame:
    """قراءة جدول ARP الحقيقي للأجهزة المتصلة بالشبكة."""
    rows = []
    try:
        out = subprocess.run(
            ["arp", "-a"], capture_output=True, text=True, timeout=8
        ).stdout
        pat = re.compile(
            r"(\d{1,3}(?:\.\d{1,3}){3})\s+([0-9a-fA-F]{2}(?:[-:][0-9a-fA-F]{2}){5})\s+(\w+)"
        )
        for ip, mac, kind in pat.findall(out):
            if ip.endswith(".255") or mac.lower() in ("ff-ff-ff-ff-ff-ff", "ff:ff:ff:ff:ff:ff"):
                continue
            rows.append({
                "IP": ip,
                "MAC": mac.upper().replace("-", ":"),
                "النوع": "ثابت" if kind.lower() == "static" else "ديناميكي",
                "الحالة": "🟢 متصل",
            })
    except Exception:
        pass
    return pd.DataFrame(rows)


@st.cache_data(ttl=5, show_spinner=False)
def net_io_snapshot() -> dict:
    io = psutil.net_io_counters()
    return {
        "sent": io.bytes_sent,
        "recv": io.bytes_recv,
        "packets_sent": io.packets_sent,
        "packets_recv": io.packets_recv,
        "ts": time.time(),
    }


def get_interfaces() -> pd.DataFrame:
    rows = []
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    for name, st_ in stats.items():
        ipv4 = next(
            (a.address for a in addrs.get(name, []) if a.family == socket.AF_INET),
            "—",
        )
        rows.append({
            "الواجهة": name,
            "IPv4": ipv4,
            "السرعة (Mbps)": st_.speed or "—",
            "MTU": st_.mtu,
            "الحالة": "🟢 فعّالة" if st_.isup else "🔴 متوقفة",
        })
    return pd.DataFrame(rows)


# ================================================================
# تتبّع معدل النقل في session للرسوم البيانية
# ================================================================
if "io_history" not in st.session_state:
    st.session_state.io_history = []
if "last_io" not in st.session_state:
    st.session_state.last_io = None


def update_history():
    cur = psutil.net_io_counters()
    now = time.time()
    last = st.session_state.last_io
    up_rate = down_rate = 0.0
    if last is not None:
        dt = max(now - last["ts"], 1e-6)
        up_rate = (cur.bytes_sent - last["sent"]) / dt
        down_rate = (cur.bytes_recv - last["recv"]) / dt
    st.session_state.last_io = {"sent": cur.bytes_sent, "recv": cur.bytes_recv, "ts": now}
    st.session_state.io_history.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "up": up_rate,
        "down": down_rate,
    })
    st.session_state.io_history = st.session_state.io_history[-30:]
    return up_rate, down_rate


# ================================================================
# الشريط الجانبي (التنقّل)
# ================================================================
local = get_local_info()
with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center;padding:10px 0 18px">
            <div style="font-size:46px">🌐</div>
            <div style="color:#f1f5f9;font-size:20px;font-weight:800">مركز التحكم بالشبكة</div>
            <div style="color:#64748b;font-size:13px">Network Control Center</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page = st.radio(
        "التنقّل",
        ["🏠 لوحة القيادة", "📱 الأجهزة المتصلة", "📊 استخدام الشبكة", "⚙️ الإعدادات"],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown(
        f"""
        <div style="color:#94a3b8;font-size:13px;line-height:1.9">
            <b style="color:#38bdf8">الجهاز الحالي</b><br>
            🖥️ {local['hostname']}<br>
            🌍 {local['ip']}<br>
            🔑 {local['mac']}
        </div>
        """,
        unsafe_allow_html=True,
    )
    auto = st.toggle("🔄 تحديث تلقائي (5 ثوانٍ)", value=False)


# ================================================================
# الصفحة: لوحة القيادة
# ================================================================
def page_dashboard():
    st.markdown(
        """
        <div class="hero">
            <h1>🌐 لوحة القيادة</h1>
            <p>نظرة عامة فورية على حالة الشبكة والأجهزة وحركة البيانات</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    up_rate, down_rate = update_history()
    io = psutil.net_io_counters()
    devices = scan_arp_table()
    n_devices = len(devices) + 1  # + الجهاز الحالي

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        (c1, "📱", "الأجهزة المتصلة", str(n_devices), "up", "▲ نشطة الآن"),
        (c2, "⬇️", "سرعة التنزيل", human_bytes(down_rate) + "/s", "up", "حركة واردة"),
        (c3, "⬆️", "سرعة الرفع", human_bytes(up_rate) + "/s", "down", "حركة صادرة"),
        (c4, "📦", "إجمالي البيانات", human_bytes(io.bytes_sent + io.bytes_recv), "up", "منذ الإقلاع"),
    ]
    for col, icon, label, value, cls, delta in cards:
        col.markdown(
            f"""
            <div class="kpi">
                <span class="icon">{icon}</span>
                <div class="label">{label}</div>
                <div class="value">{value}</div>
                <div class="delta {cls}">{delta}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([2, 1])

    with left:
        st.markdown('<div class="card"><h3>📈 حركة البيانات اللحظية</h3>', unsafe_allow_html=True)
        hist = st.session_state.io_history
        if hist:
            df = pd.DataFrame(hist)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["time"], y=df["down"] / 1024, name="تنزيل (KB/s)",
                fill="tozeroy", line=dict(color="#38bdf8", width=2),
            ))
            fig.add_trace(go.Scatter(
                x=df["time"], y=df["up"] / 1024, name="رفع (KB/s)",
                fill="tozeroy", line=dict(color="#a78bfa", width=2),
            ))
            fig.update_layout(
                height=300, margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#cbd5e1"), legend=dict(orientation="h", y=1.1),
                xaxis=dict(gridcolor="rgba(148,163,184,.1)"),
                yaxis=dict(gridcolor="rgba(148,163,184,.1)"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("جارٍ جمع البيانات...")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card"><h3>🖧 موارد النظام</h3>', unsafe_allow_html=True)
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        for label, val, color in [("المعالج CPU", cpu, "#38bdf8"), ("الذاكرة RAM", mem, "#a78bfa")]:
            gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=val,
                number={"suffix": "%", "font": {"color": "#f1f5f9", "size": 26}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#475569"},
                    "bar": {"color": color},
                    "bgcolor": "rgba(0,0,0,0)",
                    "borderwidth": 0,
                },
                title={"text": label, "font": {"color": "#94a3b8", "size": 14}},
            ))
            gauge.update_layout(height=160, margin=dict(l=10, r=10, t=30, b=0),
                                paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(gauge, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)


# ================================================================
# الصفحة: الأجهزة المتصلة
# ================================================================
def page_devices():
    st.markdown(
        """
        <div class="hero">
            <h1>📱 الأجهزة المتصلة</h1>
            <p>قائمة الأجهزة المكتشفة فعليًا على شبكتك المحلية (ARP)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cur = pd.DataFrame([{
        "IP": local["ip"], "MAC": local["mac"],
        "النوع": "هذا الجهاز", "الحالة": "🟢 متصل",
    }])
    arp = scan_arp_table()
    full = pd.concat([cur, arp], ignore_index=True)

    c1, c2 = st.columns([3, 1])
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


# ================================================================
# الصفحة: استخدام الشبكة
# ================================================================
def page_usage():
    st.markdown(
        """
        <div class="hero">
            <h1>📊 استخدام الشبكة</h1>
            <p>تحليل حركة البيانات وتوزيع الاستخدام حسب الواجهات</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    io = psutil.net_io_counters()
    c1, c2, c3 = st.columns(3)
    for col, icon, label, val in [
        (c1, "⬇️", "إجمالي التنزيل", human_bytes(io.bytes_recv)),
        (c2, "⬆️", "إجمالي الرفع", human_bytes(io.bytes_sent)),
        (c3, "📨", "عدد الحزم", f"{io.packets_sent + io.packets_recv:,}"),
    ]:
        col.markdown(
            f"""<div class="kpi"><span class="icon">{icon}</span>
            <div class="label">{label}</div>
            <div class="value">{val}</div></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns(2)

    with left:
        st.markdown('<div class="card"><h3>🥧 توزيع البيانات</h3>', unsafe_allow_html=True)
        pie = go.Figure(go.Pie(
            labels=["تنزيل", "رفع"],
            values=[io.bytes_recv, io.bytes_sent],
            hole=.55, marker=dict(colors=["#38bdf8", "#a78bfa"]),
        ))
        pie.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="#cbd5e1"),
                          margin=dict(l=10, r=10, t=10, b=10),
                          legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(pie, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card"><h3>📡 حركة البيانات لكل واجهة</h3>', unsafe_allow_html=True)
        per_nic = psutil.net_io_counters(pernic=True)
        rows = [{"الواجهة": k, "تنزيل": v.bytes_recv, "رفع": v.bytes_sent}
                for k, v in per_nic.items() if v.bytes_recv + v.bytes_sent > 0]
        if rows:
            dfn = pd.DataFrame(rows)
            bar = go.Figure()
            bar.add_trace(go.Bar(x=dfn["الواجهة"], y=dfn["تنزيل"] / 1e6,
                                 name="تنزيل (MB)", marker_color="#38bdf8"))
            bar.add_trace(go.Bar(x=dfn["الواجهة"], y=dfn["رفع"] / 1e6,
                                 name="رفع (MB)", marker_color="#a78bfa"))
            bar.update_layout(height=320, barmode="group",
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(color="#cbd5e1"),
                              margin=dict(l=10, r=10, t=10, b=10),
                              legend=dict(orientation="h", y=1.1),
                              xaxis=dict(gridcolor="rgba(148,163,184,.1)"),
                              yaxis=dict(gridcolor="rgba(148,163,184,.1)"))
            st.plotly_chart(bar, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("لا توجد بيانات كافية.")
        st.markdown("</div>", unsafe_allow_html=True)


# ================================================================
# الصفحة: الإعدادات
# ================================================================
def page_settings():
    st.markdown(
        """
        <div class="hero">
            <h1>⚙️ الإعدادات والمعلومات</h1>
            <p>تفاصيل النظام وإعدادات لوحة المراقبة</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="card"><h3>معلومات النظام</h3>', unsafe_allow_html=True)
    boot = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M")
    info = pd.DataFrame([
        {"المعلومة": "اسم الجهاز", "القيمة": local["hostname"]},
        {"المعلومة": "عنوان IP", "القيمة": local["ip"]},
        {"المعلومة": "عنوان MAC", "القيمة": local["mac"]},
        {"المعلومة": "عدد الأنوية", "القيمة": str(psutil.cpu_count(logical=True))},
        {"المعلومة": "إجمالي الذاكرة", "القيمة": human_bytes(psutil.virtual_memory().total)},
        {"المعلومة": "وقت الإقلاع", "القيمة": boot},
    ])
    st.dataframe(info, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="card"><h3>حول التطبيق</h3>'
        '<p style="color:#94a3b8;line-height:2">'
        'مركز التحكم بالشبكة — لوحة مراقبة احترافية مبنية باستخدام Streamlit و psutil و Plotly. '
        'تعرض بيانات حقيقية لحركة الشبكة والأجهزة المتصلة وموارد النظام.'
        '</p></div>',
        unsafe_allow_html=True,
    )


# ================================================================
# التوجيه
# ================================================================
if page.startswith("🏠"):
    page_dashboard()
elif page.startswith("📱"):
    page_devices()
elif page.startswith("📊"):
    page_usage()
else:
    page_settings()

st.markdown(
    """
    <div style="text-align:center;color:#475569;font-size:13px;margin-top:30px;
                padding-top:16px;border-top:1px solid rgba(148,163,184,.12)">
        صُمّم بكل احترافية 🚀 — مركز التحكم بالشبكة
    </div>
    """,
    unsafe_allow_html=True,
)

# تحديث تلقائي
if auto:
    time.sleep(5)
    st.rerun()
