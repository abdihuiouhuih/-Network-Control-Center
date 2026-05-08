import streamlit as st
import pandas as pd

# إعدادات الصفحة
st.set_page_config(page_title="Network Control", page_icon="🌐", layout="centered")

# CSS لجعل الأزرار كبيرة والواجهة أنيقة
st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        height: 60px;
        font-size: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        text-align: center;
        color: #888;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# إدارة التنقل بين الواجهات
if 'page' not in st.session_state:
    st.session_state.page = 'home'

def go_to(page_name):
    st.session_state.page = page_name

# --- الواجهة الرئيسية (القائمة) ---
if st.session_state.page == 'home':
    st.markdown("<h1 style='text-align: center;'>🌐 النظام الشامل لمعرفة أجهزة الشبكة</h1>", unsafe_allow_html=True)
    st.write("<p style='text-align: center;'>اختر القسم الذي تريد استكشافه من القائمة أدناه:</p>", unsafe_allow_html=True)
    st.write("")

    if st.button("📱 قائمة الأجهزة والآيبيات"):
        go_to('devices')
    
    if st.button("🌍 مراقبة المواقع والنشاط"):
        go_to('activity')
    
    if st.button("🔐 بيانات الشبكة السرية"):
        go_to('security')

# --- واجهة الأجهزة والآيبيات ---
elif st.session_state.page == 'devices':
    st.header("📱 الأجهزة والآيبيات المتصلة")
    st.write("تفاصيل الأجهزة المتصلة حالياً بالشبكة:")
    
    devices_data = pd.DataFrame({
        "اسم الجهاز": ["هاتف ذكي", "Xiaomi Pad 7", "Samsung S24 Ultra", "جهاز الكمبيوتر"],
        "الآي بي (IP)": ["192.168.1.15", "192.168.1.20", "192.168.1.22", "192.168.1.10"],
        "الاستخدام": ["منخفض", "متوسط", "عالي", "عالي جداً"]
    })
    st.table(devices_data)
    
    if st.button("🔙 العودة للقائمة الرئيسية"):
        go_to('home')

# --- واجهة مراقبة المواقع ---
elif st.session_state.page == 'activity':
    st.header("🌍 سجل المواقع والنشاط")
    st.write("المواقع التي يتم تصفحها حالياً عبر الشبكة:")
    
    sites_data = pd.DataFrame({
        "الجهاز": ["192.168.1.10", "192.168.1.20", "192.168.1.22"],
        "الموقع الحالي": ["github.com", "google.com.sa", "youtube.com"],
        "الحالة": ["نشط الآن", "خامل", "بث فيديو"]
    })
    st.dataframe(sites_data, use_container_width=True)
    
    if st.button("🔙 العودة للقائمة الرئيسية"):
        go_to('home')

# --- واجهة بيانات الشبكة ---
elif st.session_state.page == 'security':
    st.header("🔐 بيانات الوصول للشبكة")
    st.write("معلومات الشبكة الخاصة بك:")
    
    with st.container():
        st.info(f"**اسم الشبكة (SSID):** Abdullah_Home_Network")
        st.warning(f"**نوع الحماية:** WPA2-PSK (AES)")
        
        if st.button("🔑 إظهار الرقم السري"):
            st.success("الرمز هو: **Abdullah@2026**")
    
    if st.button("🔙 العودة للقائمة الرئيسية"):
        go_to('home')

# --- الحقوق الثابتة في الأسفل ---
st.markdown(f"""
    <div class="footer">
        <hr>
        هذا التطبيق مصمم بواسطة أخوك <b>عبد الله</b>
    </div>
    """, unsafe_allow_html=True)
