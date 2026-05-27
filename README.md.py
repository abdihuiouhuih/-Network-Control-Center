import streamlit as st
import pandas as pd
import socket
import uuid
import random

# --------------------------------
# إعداد الصفحة
# --------------------------------
st.set_page_config(
    page_title="Network Control Center",
    page_icon="🌐",
    layout="wide"
)

# --------------------------------
# تصميم احترافي
# --------------------------------
st.markdown("""
<style>

.stApp{
    background:#020617;
}

.main-title{
    text-align:center;
    font-size:60px;
    color:white;
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
    background:linear-gradient(145deg,#0f172a,#1e293b);
    color:#38bdf8;
    border:2px solid #38bdf8;
    transition:0.3s;
}

div.stButton > button:hover{
    background:#38bdf8;
    color:black;
    transform:scale(1.03);
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
    border-top:1px solid #38bdf8;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------
# التنقل
# --------------------------------
if "page" not in st.session_state:
    st.session_state.page = "main"

def navigate(page):
    st.session_state.page = page
    st.rerun()

# --------------------------------
# معلومات الجهاز الحالي
# --------------------------------
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
        "الحالة": "🟢 متصل"
    }

# --------------------------------
# الصفحة الرئيسية
# --------------------------------
if st.session_state.page == "main":

    st.markdown(
        "<h1 class='main-title'>🌐 Network Control Center</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p class='sub-title'>لوحة مراقبة الشبكة</p>",
        unsafe_allow_html=True
    )

    col1,col2 = st.columns(2)

    with col1:
        if st.button("📱 الأجهزة المتصلة"):
            navigate("devices")

    with col2:
        if st.button("📊 استخدام الأجهزة"):
            navigate("usage")

# --------------------------------
# صفحة الأجهزة
# --------------------------------
elif st.session_state.page == "devices":

    st.title("📱 الأجهزة المتصلة")

    current_device = get_current_device()

    devices = [
        current_device,
        {
            "اسم الجهاز":"PlayStation 5",
            "IP":"192.168.1.25",
            "MAC":"F1:A2:B3:C4:D5:E6",
            "الحالة":"🟢 متصل"
        },
        {
            "اسم الجهاز":"Samsung S24 Ultra",
            "IP":"192.168.1.12",
            "MAC":"A1:B2:C3:D4:E5:F6",
            "الحالة":"🟢 متصل"
        }
    ]

    st.dataframe(
        pd.DataFrame(devices),
        use_container_width=True
    )

    if st.button("🔙 العودة"):
        navigate("main")

# --------------------------------
# صفحة الاستخدام
# --------------------------------
elif st.session_state.page == "usage":

    st.title("📊 استخدام الأجهزة")

    usage_data = [
        {
            "الجهاز":"PlayStation 5",
            "الاستخدام":"🎮 Gaming",
            "DNS":"ea.com",
            "الحالة":"نشط"
        },
        {
            "الجهاز":"Samsung S24 Ultra",
            "الاستخدام":"📱 Social Media",
            "DNS":"tiktok.com",
            "الحالة":"نشط"
        },
        {
            "الجهاز":"Gaming PC",
            "الاستخدام":"💻 Programming",
            "DNS":"github.com",
            "الحالة":"نشط"
        }
    ]

    st.dataframe(
        pd.DataFrame(usage_data),
        use_container_width=True
    )

    if st.button("🔙 العودة"):
        navigate("main")

# --------------------------------
# الفوتر
# --------------------------------
st.markdown("""
<div class='footer'>
هذا التطبيق مصمم من أخوك عبد الله 🚀
</div>
""", unsafe_allow_html=True)
