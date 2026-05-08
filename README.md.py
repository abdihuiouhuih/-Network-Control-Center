import streamlit as st
import subprocess
import socket
import pandas as pd
import platform
import re

st.set_page_config(
    page_title="Network Security Scanner",
    page_icon="📡",
    layout="wide"
)

st.title("📡 Network Security Scanner")
st.caption("فحص الأجهزة المتصلة بالشبكة المحلية")

# =========================
# تحديد نوع الجهاز
# =========================
def detect_device_type(name):
    name = name.lower()

    if "iphone" in name:
        return "iPhone"

    if "android" in name:
        return "Android"

    if "samsung" in name:
        return "Samsung Device"

    if "windows" in name or "desktop" in name:
        return "Windows PC"

    if "macbook" in name or "imac" in name:
        return "Apple Computer"

    return "Unknown"


# =========================
# فحص الشبكة
# =========================
def scan_network():

    devices = []

    try:

        if platform.system() == "Windows":
            output = subprocess.check_output(
                "arp -a",
                shell=True
            ).decode(errors="ignore")

        else:
            output = subprocess.check_output(
                ["arp", "-a"]
            ).decode(errors="ignore")

        ips = re.findall(
            r"([0-9]+(?:\\.[0-9]+){3})",
            output
        )

        unique_ips = list(set(ips))

        for ip in unique_ips:

            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except:
                hostname = "Unknown"

            device_type = detect_device_type(hostname)

            devices.append({
                "اسم الجهاز": hostname,
                "نوع الجهاز": device_type,
                "IP": ip,
                "الحالة": "متصل"
            })

    except Exception as e:
        st.error(f"Error: {e}")

    return devices


# =========================
# زر الفحص
# =========================
if st.button("🔍 فحص الشبكة"):

    with st.spinner("جاري الفحص..."):

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


# =========================
# معلومات
# =========================
st.info("يشغل داخل نفس الشبكة المحلية فقط")
