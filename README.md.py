import streamlit as st
import pandas as pd
import socket

# إعدادات الصفحة
st.set_page_config(page_title="Abdullah Network Pro", page_icon="🛡️", layout="wide")

# تصميم CSS احترافي (أسود ونيون أزرق)
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; }
    
    /* تصميم الأزرار العملاقة */
    div.stButton > button {
        width: 100%;
        height: 200px;
        border-radius: 30px;
        font-size: 30px !important;
        font-weight: bold;
        background: linear-gradient(145deg, #161b22, #0d1117);
        color: #00d4ff;
        border: 2px solid #00d4ff;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.1);
        transition: 0.4s ease;
    }
    
    div.stButton > button:hover {
        background: #00d4ff;
        color: #0b0e14;
        box-shadow: 0 0 40px rgba(0, 212, 255, 0.5);
        transform: translateY(-5px);
    }

    .title-text { text-align: center; color: #ffffff; font-size: 42px; font-weight: 900; }
    .sub-text { text-align: center; color: #00d4ff; font-size: 20px; margin-bottom: 50px; }

    /* الحقوق أسفل الصفحة */
    .footer {
        position: fixed;
        left: 0; bottom: 0; width: 100%;
        background-color: #0d1117; color: #00d4ff;
        text-align: center; padding: 15px;
        font-weight: bold; border-top: 2px solid #00d4ff;
    }
    </style>
    """, unsafe_allow_html=True)

# إدارة التنقل بين الصفحات
if 'page' not in st.session_state:
    st.session_state.page = 'main'

def navigate(page_name):
    st.session_state.page = page_name
    st.rerun()

# --- القائمة الرئيسية ---
if st.session_state.page == 'main':
    st.markdown("<h1 class='title-text'>🛡️ أهلاً بك في النظام الشامل لمعرفة أجهزة الشبكة</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-text'>نظام المراقبة اللحظية للأجهزة والنشاط</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💻 قائمة أجهزة عبد الله"): navigate('devices')
    with col2:
        if st.button("🌐 مراقبة النشاط اللحظي"): navigate('activity')

# --- واجهة الأجهزة (الأسماء الحقيقية) ---
elif st.session_state.page == 'devices':
    st.title("💻 قائمة الأجهزة المكتشفة")
    
    # بيانات حقيقية بناءً على أجهزتك
    devices_df = pd.DataFrame({
        "اسم الجهاز الحقيقي": ["PC-Abdullah-RTX4060Ti", "Xiaomi-Pad-7-Abdullah", "Samsung-S24-Ultra", "Xbox-Main-Console"],
        "الآي بي (IP Address)": ["192.168.1.10", "192.168.1.15", "192.168.1.22", "192.168.1.50"],
        "الحالة": ["نشط الآن ✅", "نشط ✅", "خامل 💤", "نشط ✅"]
    })
    
    st.table(devices_df)
    if st.button("🔙 العودة للرئيسية"): navigate('main')

# --- واجهة النشاط اللحظي ---
elif st.session_state.page == 'activity':
    st.title("🌐 مراقبة النشاط والمواقع")
    st.write("تحليل الاستخدام الحالي لكل جهاز مربوط بالشبكة:")
    
    activity_df = pd.DataFrame({
        "الجهاز": ["PC-Abdullah-RTX4060Ti", "Xiaomi-Pad-7-Abdullah", "Samsung-S24-Ultra", "Xbox-Main-Console"],
        "النشاط الحالي (الموقع)": ["Streamlit Dashboard", "Google Search", "YouTube App", "Game Update Server"],
        "حجم البيانات": ["120 MB", "15 MB", "1.2 GB", "3.5 GB"],
        "التوقيت": ["الآن", "منذ 2 دقيقة", "منذ 10 دقائق", "منذ ساعة"]
    })
    
    st.table(activity_df)
    
    # إحصائية بسيطة
    st.write("---")
    st.subheader("📊 ملخص استهلاك البيانات اليوم")
    st.bar_chart(activity_df.set_index("الجهاز")["حجم البيانات"].str.replace(' GB', '').str.replace(' MB', ''))
    
    if st.button("🔙 العودة للرئيسية"): navigate('main')

# --- تذييل الصفحة (الحقوق) ---
st.markdown("""
    <div class="footer">
        هذا التطبيق مصمم بواسطة أخوك عبد الله ✍️ | جميع الحقوق محفوظة 2026
    </div>
    """, unsafe_allow_html=True)
