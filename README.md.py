import streamlit as st
import pandas as pd
import nmap
import socket
import platform
import uuid
import subprocess

# ---------------------------
# إعداد الصفحة
# ---------------------------
st.set_page_config(
    page_title="Network Scanner Pro",
    page_icon="🌐",
    layout="wide"
)

# ---------------------------
# CSS احترافي
# ---------------------------
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
}

.sub-title{
    text-align:center;
    color:#94a3b8;
    font-size:22px;
    margin-bottom:40px;
}

div.stButton > button{
    width:100%;
    height:80px;
    border-radius:20px;
    font-size:28px;
    font-weight:bold;
    background:#38bdf8;
    color:black;
    border:none;
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
}

</style>
""", unsafe_allow_html=True)

# ---------------------------
# عنوان التطبيق
# ---------------------------
st.markdown(
    "<h1 class='main-title'>🌐 Network Scanner Pro</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p class='sub-title'>فحص الأجهزة الحقيقية داخل الشبكة</p>",
    unsafe_allow_html=True
)

# ---------------------------
# تحديد الشبكة
# ---------------------------
def get_network():

    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)

    parts = ip.split('.')

    network = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"

    return network

# ---------------------------
# فحص الشبكة
# ---------------------------
def scan_network():

    nm = nmap.PortScanner()

    network = get_network()

    nm.scan(hosts=network, arguments='-sn')

    devices = []

    for host in nm.all_hosts():

        try:
            hostname = socket.gethostbyaddr(host)[0]
        except:
            hostname = "Unknown Device"

        mac = "غير معروف"
        vendor = "غير معروف"

        try:
            addresses = nm[host]['addresses']

            if 'mac' in addresses:
                mac = addresses['mac']

            if 'vendor' in nm[host]:
                vendor_data = nm[host]['vendor']

                if mac in vendor_data:
                    vendor = vendor_data[mac]

        except:
            pass

        devices.append({
            "اسم الجهاز الحقيقي": hostname,
            "IP الحقيقي": host,
            "MAC Address": mac,
            "الشركة المصنعة": vendor,
            "الحالة": "🟢 متصل"
        })

    return devices

# ---------------------------
# زر الفحص
# ---------------------------
if st.button("🔍 فحص الشبكة الحقيقية"):

    with st.spinner("جاري فحص الشبكة..."):

        try:

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

        except Exception as e:

            st.error(str(e))

# ---------------------------
# معلومات مهمة
# ---------------------------
st.info("""
هذا التطبيق يعرض:
- أسماء الأجهزة الحقيقية
- IP الحقيقي
- MAC الحقيقي
- الأجهزة المتصلة بالشبكة الحالية
""")

# ---------------------------
# الفوتر
# ---------------------------
st.markdown("""
<div class='footer'>
هذا التطبيق مصمم من أخوك عبد الله 🚀
</div>
""", unsafe_allow_html=True)
