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

if "detected_networks" not in st.session_state:
    st.session_state.detected_networks = []


# -----------------------------
# Helpers
# -----------------------------

def is_private_ipv4(ip):
    """Return True only for RFC1918 private IPv4 addresses."""
    try:
        return ipaddress.ip_address(ip).version == 4 and ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def get_local_ip():
    """
    محاولة معرفة IPv4 المحلي للجهاز الذي يشغل Streamlit.
    لا يتم إرسال أي بيانات إلى الإنترنت.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("192.0.2.1", 80))
        ip = sock.getsockname()[0]
        sock.close()

        if is_private_ipv4(ip):
            return ip

    except Exception:
        pass

    return ""


def get_local_networks():
    """
    محاولة اكتشاف الشبكات المحلية من الجهاز الذي يشغل Streamlit.
    Windows: ipconfig
    Linux: ip -4 addr
    """
    networks = set()
    system = platform.system().lower()

    try:
        if system == "windows":
            output = subprocess.check_output(
                ["ipconfig"],
                text=True,
                stderr=subprocess.DEVNULL,
                encoding="utf-8",
                errors="ignore",
            )

            current_ip = None
            for line in output.splitlines():
                ip_match = re.search(
                    r"IPv4[^:]*:\s*([0-9]{1,3}(?:\.[0-9]{1,3}){3})",
                    line,
                    re.IGNORECASE,
                )

                if ip_match:
                    current_ip = ip_match.group(1)
                    continue

                mask_match = re.search(
                    r"Subnet Mask[^:]*:\s*([0-9]{1,3}(?:\.[0-9]{1,3}){3})",
                    line,
                    re.IGNORECASE,
                )

                if mask_match and current_ip:
                    try:
                        network = ipaddress.ip_network(
                            f"{current_ip}/{mask_match.group(1)}",
                            strict=False,
                        )

                        if network.version == 4 and network.is_private:
                            networks.add(str(network))

                    except ValueError:
                        pass

                    current_ip = None

        elif system == "linux":
            output = subprocess.check_output(
                ["ip", "-4", "addr"],
                text=True,
                stderr=subprocess.DEVNULL,
            )

            for match in re.finditer(
                r"inet\s+(\d{1,3}(?:\.\d{1,3}){3})/(\d+)",
                output,
            ):
                ip = match.group(1)
                prefix = match.group(2)

                try:
                    network = ipaddress.ip_network(
                        f"{ip}/{prefix}",
                        strict=False,
                    )

                    if network.is_private:
                        networks.add(str(network))

                except ValueError:
                    pass

    except Exception:
        pass

    # Fallback: infer a /24 from the local IP.
    if not networks:
        local_ip = get_local_ip()

        if local_ip:
            try:
                networks.add(
                    str(
                        ipaddress.ip_network(
                            f"{local_ip}/24",
                            strict=False,
                        )
                    )
                )
            except ValueError:
                pass

    return sorted(
        networks,
        key=lambda value: (
            ipaddress.ip_network(value).network_address,
            ipaddress.ip_network(value).prefixlen,
        ),
    )


def normalize_network_input(value):
    """
    Accept:
      192.168.1.25       -> 192.168.1.0/24
      192.168.1.0/24    -> 192.168.1.0/24
    """
    value = value.strip()

    if not value:
        raise ValueError("أدخل IP أو Network CIDR.")

    if "/" in value:
        network = ipaddress.ip_network(value, strict=False)
    else:
        ip = ipaddress.ip_address(value)

        if ip.version != 4:
            raise ValueError("الإصدار الحالي يدعم IPv4 فقط.")

        if not ip.is_private:
            raise ValueError(
                "للحماية، استخدم IP خاص داخل الشبكة المحلية، "
                "مثل 192.168.1.25 أو 10.0.0.20."
            )

        # Default assumption for a single IP.
        # The user can enter CIDR explicitly if their LAN is not /24.
        network = ipaddress.ip_network(
            f"{ip}/24",
            strict=False,
        )

    if network.version != 4:
        raise ValueError("الإصدار الحالي يدعم IPv4 فقط.")

    if not network.is_private:
        raise ValueError(
            "هذه الأداة مخصصة للشبكات المحلية الخاصة فقط "
            "(مثل 192.168.x.x أو 10.x.x.x أو 172.16-31.x.x)."
        )

    hosts = list(network.hosts())

    if len(hosts) > 1024:
        raise ValueError(
            "الحد الأقصى للفحص هو 1024 عنوانًا."
        )

    return network


def ping(ip):
    """إرسال Ping واحد."""

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
    """Reverse DNS."""

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
            encoding="utf-8",
            errors="ignore",
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
            mac = mac_match.group(0).replace("-", ":").upper()
            arp[ip] = mac

    return arp


def scan_network(cidr, workers=32):
    """
    فحص شبكة IPv4 محلية خاصة.
    يتم الفحص من الجهاز الذي يشغل Streamlit.
    """

    network = normalize_network_input(cidr)

    hosts = list(network.hosts())
    arp_table = get_arp_table()
    discovered = []

    progress = st.progress(
        0,
        text=f"بدء فحص {network}...",
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

            # Ping + ARP:
            # Some devices/firewalls do not answer ICMP but can still
            # appear in the local ARP table.
            if alive or ip in arp_table:
                hostname = get_hostname(ip) if alive else ""

                discovered.append(
                    {
                        "IP": ip,
                        "MAC": arp_table.get(ip, ""),
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
        key=lambda item: ipaddress.ip_address(item["IP"])
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

    return output.getvalue().encode("utf-8-sig")


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

    col1.metric("الأجهزة المكتشفة", total_devices)
    col2.metric("أجهزة نشطة", active_devices)
    col3.metric("ARP", arp_devices)
    col4.metric("MAC متوفر", mac_devices)

    if st.session_state.last_network:
        st.caption(
            f"آخر شبكة تم فحصها: {st.session_state.last_network}"
        )

    st.divider()

    if results:

        st.subheader("📋 الأجهزة المكتشفة")

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
        "أدخل IP واحدًا أو Network CIDR. "
        "إذا أدخلت IP فقط، سيُفترض /24 تلقائيًا."
    )

    st.code(
        "192.168.1.25  →  192.168.1.0/24\n"
        "192.168.1.0/24 →  192.168.1.0/24",
        language="text",
    )

    # Auto-detect networks
    detected = get_local_networks()
    st.session_state.detected_networks = detected

    if detected:
        st.success(
            "الشبكات المحلية المكتشفة على الجهاز: "
            + ", ".join(detected)
        )

        selected = st.selectbox(
            "اختيار شبكة مكتشفة",
            ["—"] + detected,
        )
    else:
        selected = "—"
        st.info(
            "تعذر اكتشاف الشبكة تلقائيًا. يمكنك إدخال IP أو CIDR يدويًا."
        )

    cidr_or_ip = st.text_input(
        "IP أو Network CIDR",
        value=(
            selected
            if selected != "—"
            else (get_local_ip() or "192.168.1.25")
        ),
        placeholder="مثال: 192.168.1.25 أو 192.168.1.0/24",
        help=(
            "IP منفرد = يفترض /24. "
            "إذا كانت شبكتك /23 أو /16 مثلًا، أدخل CIDR صراحة."
        ),
    ).strip()

    try:
        network = normalize_network_input(cidr_or_ip)
        host_count = len(list(network.hosts()))

        col1, col2, col3 = st.columns(3)

        col1.metric("الشبكة التي سيتم فحصها", str(network))
        col2.metric("عدد العناوين", host_count)
        col3.metric("Private Network", "نعم")

        if "/" not in cidr_or_ip:
            st.warning(
                "تم افتراض /24 لأنك أدخلت IP فقط. "
                "إذا كانت الشبكة تستخدم قناعًا مختلفًا، أدخل CIDR الصحيح."
            )

    except Exception as error:
        network = None
        st.error(str(error))

    st.divider()

    workers = st.slider(
        "عدد عمليات الفحص المتوازية",
        min_value=4,
        max_value=64,
        value=32,
    )

    if st.button(
        "🚀 بدء فحص الشبكة",
        type="primary",
        use_container_width=True,
        disabled=network is None,
    ):

        try:

            with st.spinner(
                f"يتم فحص {network}..."
            ):
                results = scan_network(
                    str(network),
                    workers,
                )

            st.session_state.results = results
            st.session_state.last_network = str(network)

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

        st.subheader("📋 نتائج آخر فحص")

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

    st.write(
        "هذه الصفحة للبحث داخل نتائج آخر فحص. "
        "للعثور على أجهزة جديدة، استخدم «فحص الشبكة»."
    )

    ip_input = st.text_input(
        "أدخل IP",
        placeholder="192.168.1.10",
    ).strip()

    if ip_input:

        try:

            ipaddress.ip_address(ip_input)

            matches = [
                device
                for device in st.session_state.results
                if device["IP"] == ip_input
            ]

            if matches:

                device = matches[0]

                st.success("تم العثور على الجهاز.")

                col1, col2, col3 = st.columns(3)

                col1.metric("IP", device["IP"])
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
                    device["Hostname"] or "غير متاح",
                )

            else:

                st.info(
                    "هذا الـIP غير موجود في نتائج آخر فحص. "
                    "ارجع إلى «فحص الشبكة» وأعد الفحص إذا كنت تتوقع وجوده."
                )

        except ValueError:

            st.error("عنوان IP غير صحيح.")


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
- 🧭 اكتشاف الشبكة المحلية تلقائيًا
- ⌨️ قبول IP منفرد أو CIDR

### مهم

الأداة لا تقوم بـ:

- تجاوز كلمات المرور.
- تسجيل الدخول إلى الأجهزة.
- اختراق الأجهزة.
- تجاوز صلاحيات الشبكة.
- فحص الإنترنت العام.
- الوصول إلى كاميرات أو أجهزة لا تملك تصريحًا بفحصها.

### ملاحظة تقنية مهمة

الفحص يتم من **الجهاز الذي يشغّل Streamlit**.

إذا شغّلت التطبيق على جهازك داخل شبكة منزلية،
فسيستطيع فحص الشبكة المحلية التي يستطيع جهازك الوصول إليها.

أما إذا رفعت التطبيق على خدمة Cloud،
فلن يستطيع التطبيق رؤية شبكتك المنزلية لمجرد أنك فتحت الموقع من جهازك؛
لأن عملية الفحص تنفذ من السيرفر الذي يشغّل التطبيق.
"""
    )

    st.divider()

    st.caption(
        "NetworkScope • Streamlit Network Discovery"
    )
