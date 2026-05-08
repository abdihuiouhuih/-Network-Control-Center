import streamlit as st
from scapy.all import ARP, Ether, srp
import socket
import pandas as pd
import time

st.set_page_config(
    page_title="لوحة مراقبة الشبكة",
    page_icon="📡",
    layout="wide"
)

st.title("📡 لوحة مراقبة الشبكة")
st.caption("عرض الأجهزة المتصلة على شبكتك المحلية")


# =========================
# إعدادات الشبكة
# =========================
NETWORK = "192.168.1.1/24"


# =========================
# فحص الشبكة
# =========================
def scan_network():
    devices = []

    arp = ARP(pdst=NETWORK)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    result = srp(packet, timeout=3, verbose=0)[0]

    for _, received in result:
        ip = received.psrc
st.rerun()# -
