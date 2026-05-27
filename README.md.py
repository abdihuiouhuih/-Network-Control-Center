import streamlit as st
import pandas as pd
import socket
import uuid
import random

# -----------------------------
# إعداد الصفحة
# -----------------------------
st.set_page_config(
    page_title="Network Monitor Pro",
    page_icon="🌐",
    layout="wide"
)

# -----------------------------
# CSS احترافي
# -----------------------------
st.markdown("""
<style>

.stApp{
    background:#020817;
}

.main-title{
    text-align:center;
    color:white;
    font-size:55px;
    font-weight:bold;
    margin-top:-20px;
}

.sub-title{
    text-align:center;
    color:#94a3b8;
    font-size:24px;
    margin-bottom:50px;
}

div.stButton > button{
    width:100%;
    height:220px;
    border-radius:30px;
    font-size:35px;
    font-weight:bold;
    background:linear-gradient(145deg,#1e293b,#0f172a);
    color:#38bdf8;
    border:3px solid #38bdf8;
    transition:0.3s;
}

div.stButton > button:hover{
    transform:scale(1.03);
    background:#38bdf8;
    color:#0f172a;
}

.footer{
    position:fixed;
    bottom:0;
    left:0;
    width:100%;
    background:#0f172a;
    color:#38bdf8;
    text-align:center;
    padding:12px;
    font-weight:bold;
    border-top:1px solid #38bdf8;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# التنقل بين الصفحات
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "main"

def navigate(page):
    st.session_state.page = page
    st.rerun()

# -----------------------------
# جلب معلومات الجهاز الحالي
# -----------------------------
def get_current_device():

    hostname = socket.gethostname()

    try:
        ip = socket.gethostbyname(hostname)
    except:
        ip = "127.0.0.1"

    mac = ':'.join([
        '{:02x}'.format((uuid.getnode() >> ele) & 0xff)
        for ele in range(0,8*6,8)
    ][::-1])

    return {
        "اسم الجهاز": hostname,
        "IP": ip,
        "MAC": mac,
        "نوع الاتصال": "WiFi"
    }

# -----------------------------
# توليد أجهزة وهمية ديناميكية
# -----------------------------
def generate_devices():

    current = get_current_device()

    devices = [
        current,
        {
            "اسم الجهاز":"Samsung Phone",
            "IP":"192.168.1.15",
            "MAC":"A1:B2:C3:D4:E5:F6",
            "نوع الاتصال":"WiFi"
        },
        {
            "اسم الجهاز":"Xiaomi Tablet",
            "IP":"192.168.1.20",
            "MAC":"B2:C3:D4:E5:F6:G7",
            "نوع الاتصال":"WiFi"
        },
        {
            "اسم الجهاز":"Gaming PC",
            "IP":"192.168.1.25",
            "MAC":"C3:D4:E5:F6:G7:H8",
            "نوع الاتصال":"Ethernet"
        }
    ]

    return devices

# -----------------------------
# أنشطة تقريبية
# -----------------------------
activities = [
    "🎮 Gaming",
    "📺 Streaming",
    "🌐 Browsing",
    "💻 Programming",
    "📱 Social Media"
]

websites = [
    "youtube.com",
    "github.com",
    "tiktok.com",
    "netflix.com",
    "xboxlive.com"
]

# -----------------------------
# الصفحة الرئيسية
# -----------------------------
if st.session_state.page == "main":

    st.markdown(
        "<h1 class='main-title'>🌐 Network Monitor Pro</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p class='sub-title'>لوحة تحكم الشبكة الذكية</p>",
        unsafe_allow_html=True
    )

    col1,col2 = st.columns(2)

    with col1:
        if st.button("📱 الأجهزة المتصلة"):
            navigate("devices")

    with col2:
        if st.button("📊 نشاط الأجهزة"):
            navigate("usage")

# -----------------------------
# صفحة الأجهزة
# -----------------------------
elif st.session_state.page == "devices":

    st.title("📱 الأجهزة المتصلة بالشبكة")

    devices = generate_devices()

    df = pd.DataFrame(devices)

    st.dataframe(df, use_container_width=True)

    if st.button("🔙 العودة"):
        navigate("main")

# -----------------------------
# صفحة النشاط
# -----------------------------
elif st.session_state.page == "usage":

    st.title("📊 نشاط الأجهزة")

    devices = generate_devices()

    usage_data = []

    for device in devices:

        usage_data.append({
            "اسم الجهاز": device["اسم الجهاز"],
            "IP": device["IP"],
            "النشاط الحالي": random.choice(activities),
            "الموقع المستخدم": random.choice(websites),
            "استهلاك الشبكة": random.choice([
                "منخفض",
                "متوسط",
                "عالي",
                "عالي جداً"
            ])
        })

    usage_df = pd.DataFrame(usage_data)

    st.dataframe(
        usage_df,
        use_container_width=True
    )

    if st.button("🔙 العودة"):
        navigate("main")

# -----------------------------
# الفوتر
# -----------------------------
st.markdown("""
<div class='footer'>
هذا التطبيق مصمم من أخوك عبد الله 🚀
</div>
""", unsafe_allow_html=True)
