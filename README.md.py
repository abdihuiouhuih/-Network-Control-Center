import streamlit as st
import socket
import platform
import pandas as pd
import uuid

# --------------------------
# إعداد الصفحة
# --------------------------
st.set_page_config(
    page_title="Network Monitor Pro",
    page_icon="🌐",
    layout="wide"
)

# --------------------------
# CSS احترافي
# --------------------------
st.markdown("""
<style>

.stApp{
    background-color:#0b1120;
}

.main-title{
    text-align:center;
    color:white;
    font-size:50px;
    font-weight:bold;
}

.sub-title{
    text-align:center;
    color:#94a3b8;
    font-size:22px;
    margin-bottom:40px;
}

.info-box{
    background:#111827;
    padding:25px;
    border-radius:20px;
    border:1px solid #38bdf8;
    margin-bottom:20px;
}

div.stButton > button{
    width:100%;
    height:70px;
    border-radius:20px;
    font-size:25px;
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
    background:#111827;
    color:#38bdf8;
    text-align:center;
    padding:10px;
    font-weight:bold;
}

</style>
""", unsafe_allow_html=True)

# --------------------------
# عنوان التطبيق
# --------------------------
st.markdown(
    "<h1 class='main-title'>🌐 Network Monitor Pro</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p class='sub-title'>معلومات الشبكة والجهاز الحالي بشكل مباشر</p>",
    unsafe_allow_html=True
)

# --------------------------
# معلومات الجهاز
# --------------------------
def get_device_info():

    hostname = socket.gethostname()

    try:
        ip_address = socket.gethostbyname(hostname)
    except:
        ip_address = "غير معروف"

    mac = ':'.join([
        '{:02x}'.format((uuid.getnode() >> elements) & 0xff)
        for elements in range(0,8*6,8)
    ][::-1])

    system = platform.system()
    processor = platform.processor()

    return {
        "اسم الجهاز": hostname,
        "عنوان IP": ip_address,
        "MAC Address": mac,
        "نظام التشغيل": system,
        "المعالج": processor
    }

# --------------------------
# زر التحديث
# --------------------------
if st.button("🔄 تحديث معلومات الشبكة"):

    info = get_device_info()

    df = pd.DataFrame({
        "المعلومة": list(info.keys()),
        "القيمة": list(info.values())
    })

    st.success("تم تحديث المعلومات بنجاح")

    st.dataframe(
        df,
        use_container_width=True
    )

# --------------------------
# معلومات إضافية
# --------------------------
st.markdown("""
<div class='info-box'>

<h3 style='color:#38bdf8;'>📡 ملاحظات مهمة</h3>

<ul style='color:white;font-size:18px;'>

<li>التطبيق يتغير حسب الجهاز والشبكة الحالية</li>

<li>إذا دخلت شبكة ثانية سيتغير الـ IP تلقائياً</li>

<li>Streamlit Cloud لا يسمح بفحص كل أجهزة الشبكة الداخلية</li>

<li>لفحص الأجهزة الحقيقية بالكامل شغل التطبيق محلياً على الكمبيوتر</li>

</ul>

</div>
""", unsafe_allow_html=True)

# --------------------------
# الفوتر
# --------------------------
st.markdown("""
<div class='footer'>
هذا التطبيق مصمم من أخوك عبد الله 🚀
</div>
""", unsafe_allow_html=True)
