import streamlit as st
import pandas as pd
from scapy.all import ARP, Ether, srp
import socket
import requests

# ----------------------------
# إعداد الصفحة
# ----------------------------
st.set_page_config(
    page_title="Network Monitor Pro",
    page_icon="🌐",
    layout="wide"
)

# ----------------------------
# تصميم احترافي
# ----------------------------
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
}

.main-title {
    text-align:center;
    color:white;
    font-size:45px;
    font-weight:bold;
}

.sub-title {
    text-align:center;
    color:#94a3b8;
    font-size:20px;
    margin-bottom:30px;
}

.device-card {
    background:#111827;
    padding:20px;
    border-radius:20px;
    border:1px solid #38bdf8;
    margin-bottom:15px;
}

.footer {
    position:fixed;
    bottom:0;
    left:0;
    width:100%;
    background:#0f172a;
    color:#38bdf8;
    text-align:center;
    padding:10px;
    border-top:1px solid #38bdf8;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# جلب اسم الشركة المصنعة من MAC
# ----------------------------
def get_vendor(mac):
    try:
        url = f"https://api.macvendors.com/{mac}"
        response = requests.get(url, timeout=3)

        if response.status_code == 200:
            return response.text

        return "غير معروف"

    except:
        return "غير معروف"

# ----------------------------
# فحص الشبكة
# ----------------------------
def scan_network(ip_range="192.168.1.1/24"):

    devices = []

    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")

    packet = ether / arp

    result = srp(packet, timeout=3, verbose=0)[0]

    for sent, received in result:

        ip = received.psrc
        mac = received.hwsrc

        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            hostname = "Unknown Device"

        vendor = get_vendor(mac)

        devices.append({
            "اسم الجهاز": hostname,
            "IP Address": ip,
            "MAC Address": mac,
            "الشركة المصنعة": vendor,
            "الحالة": "🟢 متصل"
        })

    return devices

# ----------------------------
# العنوان
# ----------------------------
st.markdown(
    "<h1 class='main-title'>🌐 Network Monitor Pro</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p class='sub-title'>فحص الأجهزة الحقيقية المتصلة بالشبكة الحالية</p>",
    unsafe_allow_html=True
)

# ----------------------------
# زر الفحص
# ----------------------------
scan_button = st.button("🔍 فحص الشبكة الآن", use_container_width=True)

# ----------------------------
# الفحص
# ----------------------------
if scan_button:

    with st.spinner("جاري فحص الشبكة..."):

        devices = scan_network()

        if devices:

            df = pd.DataFrame(devices)

            st.success(f"تم العثور على {len(devices)} جهاز")

            st.dataframe(
                df,
                use_container_width=True
            )

        else:
            st.warning("لم يتم العثور على أجهزة")

# ----------------------------
# الفوتر
# ----------------------------
st.markdown("""
<div class="footer">
هذا التطبيق مصمم من أخوك عبد الله 🚀
</div>
""", unsafe_allow_html=True)
