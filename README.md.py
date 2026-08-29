import streamlit as st
import ipaddress
import socket
import subprocess
import platform
import re
import csv
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# NetworkScope - Local Network Discovery
# Single-file Streamlit application
# ============================================================

st.set_page_config(
    page_title="NetworkScope",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# CSS
# -----------------------------

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1400px;
            padding-top: 2rem;
        }

        .main-title {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            color: #777;
            margin-bottom: 2rem;
        }

        div[data-testid="stMetric"] {
            border: 1px solid rgba(128,128,128,.2);
            padding: 15px;
            border-radius: 14px;
        }

        .warning-box {
            padding: 15px;
            border-radius: 12px;
            background: rgba(255, 193, 7, .12);
            border: 1px solid rgba(255, 193, 7, .35);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Session State
# -----------------------------

if "results" not in st.session_state:
    st.session_state.results = []

if "last_network" not in st.session_state:
    st.session_state.last_network = ""

# -----------------------------
# Functions
# -----------------------------


def get_local_ip():
    """
    محاولة معرفة عنوان IPv4 المحلي للجهاز الذي يشغل Streamlit.
    لا يتم إرسال أي بيانات إلى الإنترنت.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("192.0.2.1", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "192.168.1.100"


def guess_local_network():
    """
    تخمين شبكة /24 محلية من عنوان الجهاز.
    """
    ip = get_local_ip()

    try:
        parts = ip.split(".")

        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"

    except Exception:
        pass

    return "192.168.1.0/24"


def ping(ip):
    """
    إرسال Ping واحد.
    """

    system = platform.system().lower()

    try:

        if system == "windows":

            command = [
                "ping",
                "-n",
                "1",
                "-w",
                "800",
                ip,
            ]

        else:

            command = [
                "ping",
                "-c",
                "1",
                "-W",
                "1",
                ip,
            ]

        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )

        return result.returncode == 0

    except Exception:
        return False


def get_hostname(ip):
    """
    Reverse DNS.
    """

    try:

        hostname = socket.gethostbyaddr(ip)[0]

        return hostname

    except Exception:

        return ""


def get_arp_table():
    """
    قراءة جدول ARP من الجهاز الذي يشغل التطبيق.
    """

    arp = {}

    try:

        output = subprocess.check_output(
            ["arp", "-a"],
            text=True,
            stderr=subprocess.DEVNULL,
        )

    except Exception:

        return arp

    ip_pattern = re.compile(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    )

    mac_pattern = re.compile(
        r"\b[0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5}\b"
    )

    for line in output.splitlines():

        ip_match = ip_pattern.search(line)

        mac_match = mac_pattern.search(line)

        if ip_match and mac_match:

            ip = ip_match.group(0)

            mac = mac_match.group(0)

            mac = mac.replace("-", ":").upper()

            arp[ip] = mac

    return arp


def scan_network(cidr, workers=32):

    network = ipaddress.ip_network(
        cidr,
        strict=False,
    )

    if network.version != 4:

        raise ValueError(
            "هذا الإصدار يدعم IPv4 فقط."
        )

    if not network.is_private:

        raise ValueError(
            "للحماية، استخدم شبكة IPv4 خاصة مثل 192.168.1.0/24."
        )

    hosts = list(network.hosts())

    if len(hosts) > 1024:

        raise ValueError(
            "الحد الأقصى للفحص هو 1024 عنوانًا."
        )

    arp_table = get_arp_table()

    discovered = []

    progress = st.progress(
        0,
        text="بدء فحص الشبكة...",
    )

    completed = 0

    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        futures = {
            executor.submit(
                ping,
                str(ip),
            ): str(ip)

            for ip in hosts
        }

        for future in as_completed(futures):

            ip = futures[future]

            try:

                alive = future.result()

            except Exception:

                alive = False

            if alive or ip in arp_table:

                hostname = ""

                if alive:
                    hostname = get_hostname(ip)

                discovered.append(
                    {
                        "IP": ip,
                        "MAC": arp_table.get(
                            ip,
                            "",
                        ),
                        "Hostname": hostname,
                        "Status": (
                            "نشط"
                            if alive
                            else "ظاهر في ARP"
                        ),
                    }
                )

            completed += 1

            progress.progress(
                completed / len(hosts),
                text=f"فحص {completed} من {len(hosts)}",
            )

    progress.empty()

    discovered.sort(
        key=lambda item: ipaddress.ip_address(
            item["IP"]
        )
    )

    return discovered


def export_csv(data):

    output = io.StringIO()

    writer = csv.DictWriter(
        output,
        fieldnames=[
            "IP",
            "MAC",
            "Hostname",
            "Status",
        ],
    )

    writer.writeheader()

    writer.writerows(data)

    return output.getvalue().encode(
        "utf-8-sig"
    )


# ============================================================
# Sidebar
# ============================================================

st.sidebar.title("🌐 NetworkScope")

st.sidebar.caption(
    "Local Network Discovery Tool"
)

page = st.sidebar.radio(
    "القائمة",
    [
        "لوحة التحكم",
        "فحص الشبكة",
        "بحث عن IP",
        "حول المشروع",
    ],
)

st.sidebar.divider()

st.sidebar.warning(
    "استخدم الأداة فقط على شبكة تملكها "
    "أو لديك تصريح صريح بفحصها."
)

# ============================================================
# Dashboard
# ============================================================

if page == "لوحة التحكم":

    st.markdown(
        '<div class="main-title">🌐 NetworkScope</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        "لوحة مراقبة واكتشاف الأجهزة داخل الشبكة المحلية"
        "</div>",
        unsafe_allow_html=True,
    )

    results = st.session_state.results

    total_devices = len(results)

    active_devices = sum(
        1
        for device in results
        if device["Status"] == "نشط"
    )

    arp_devices = sum(
        1
        for device in results
        if device["Status"] == "ظاهر في ARP"
    )

    mac_devices = sum(
        1
        for device in results
        if device["MAC"]
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "الأجهزة المكتشفة",
        total_devices,
    )

    col2.metric(
        "أجهزة نشطة",
        active_devices,
    )

    col3.metric(
        "ARP",
        arp_devices,
    )

    col4.metric(
        "MAC متوفر",
        mac_devices,
    )

    st.divider()

    if results:

        st.subheader(
            "📋 الأجهزة المكتشفة"
        )

        st.dataframe(
            results,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            label="⬇️ تحميل النتائج CSV",
            data=export_csv(results),
            file_name="network_devices.csv",
            mime="text/csv",
            use_container_width=True,
        )

    else:

        st.info(
            "لا توجد نتائج حتى الآن. "
            "اذهب إلى «فحص الشبكة» وابدأ عملية الفحص."
        )

# ============================================================
# Network Scanner
# ============================================================

elif page == "فحص الشبكة":

    st.title("🔎 فحص الشبكة")

    st.write(
        "أدخل نطاق الشبكة المحلية بصيغة CIDR."
    )

    st.code(
        "192.168.1.0/24",
        language="text",
    )

    default_network = guess_local_network()

    cidr = st.text_input(
        "Network CIDR",
        value=default_network,
        help=(
            "مثال: 192.168.1.0/24"
        ),
    )

    try:

        network = ipaddress.ip_network(
            cidr,
            strict=False,
        )

        host_count = len(
            list(network.hosts())
        )

        private = network.is_private

    except Exception:

        host_count = 0

        private = False

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "الشبكة",
        cidr,
    )

    col2.metric(
        "العناوين",
        host_count,
    )

    col3.metric(
        "Private Network",
        "نعم" if private else "لا",
    )

    st.divider()

    workers = st.slider(
        "عدد عمليات الفحص المتوازية",
        min_value=4,
        max_value=64,
        value=32,
    )

    if st.button(
        "🚀 بدء الفحص",
        type="primary",
        use_container_width=True,
    ):

        try:

            network = ipaddress.ip_network(
                cidr,
                strict=False,
            )

            if not network.is_private:

                st.error(
                    "يجب استخدام شبكة IPv4 خاصة."
                )

            else:

                with st.spinner(
                    "يتم فحص الشبكة..."
                ):

                    results = scan_network(
                        str(network),
                        workers,
                    )

                st.session_state.results = results

                st.session_state.last_network = str(
                    network
                )

                st.success(
                    f"انتهى الفحص — تم العثور على "
                    f"{len(results)} جهاز/عنوان."
                )

                st.rerun()

        except Exception as error:

            st.error(
                f"حدث خطأ: {error}"
            )

    if st.session_state.results:

        st.divider()

        st.subheader(
            "📋 نتائج آخر فحص"
        )

        st.dataframe(
            st.session_state.results,
            use_container_width=True,
            hide_index=True,
        )

# ============================================================
# IP Search
# ============================================================

elif page == "بحث عن IP":

    st.title("📍 البحث عن IP")

    ip_input = st.text_input(
        "أدخل IP",
        placeholder="192.168.1.10",
    ).strip()

    if ip_input:

        try:

            ipaddress.ip_address(
                ip_input
            )

            matches = [
                device
                for device in st.session_state.results
                if device["IP"] == ip_input
            ]

            if matches:

                device = matches[0]

                st.success(
                    "تم العثور على الجهاز."
                )

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "IP",
                    device["IP"],
                )

                col2.metric(
                    "MAC",
                    device["MAC"] or "غير متاح",
                )

                col3.metric(
                    "الحالة",
                    device["Status"],
                )

                st.write(
                    "Hostname:",
                    device["Hostname"]
                    or "غير متاح",
                )

            else:

                st.info(
                    "هذا الـ IP غير موجود "
                    "في نتائج آخر فحص."
                )

        except ValueError:

            st.error(
                "عنوان IP غير صحيح."
            )

# ============================================================
# About
# ============================================================

elif page == "حول المشروع":

    st.title("ℹ️ حول NetworkScope")

    st.markdown(
        """
## ما هو NetworkScope؟

NetworkScope هو مشروع مبني باستخدام **Streamlit**
لاكتشاف الأجهزة الموجودة داخل شبكة IPv4 محلية.

### الوظائف

- 🔎 اكتشاف الأجهزة المستجيبة لـ Ping
- 📡 قراءة ARP المحلي
- 💻 عرض IP
- 🆔 عرض MAC Address عندما يكون متاحًا
- 🖥️ محاولة معرفة Hostname
- 📊 Dashboard
- 🔍 البحث عن IP
- 📥 تصدير النتائج CSV

### مهم

الأداة لا تقوم بـ:

- تجاوز كلمات المرور.
- تسجيل الدخول إلى الأجهزة.
- اختراق الأجهزة.
- تجاوز صلاحيات الشبكة.
- فحص الإنترنت العام.
- الوصول إلى كاميرات أو أجهزة لا تملك تصريحًا بفحصها.

### ملاحظة تقنية

الفحص يتم من **الجهاز الذي يشغّل Streamlit**.

إذا رفعت التطبيق على خدمة Cloud، فلن يستطيع التطبيق رؤية
شبكتك المنزلية لمجرد أنك فتحت الموقع من جهازك؛ لأن عملية
الفحص تنفذ من السيرفر الذي يشغّل التطبيق.
"""
    )

    st.divider()

    st.caption(
        "NetworkScope • Streamlit Network Discovery"
    )
