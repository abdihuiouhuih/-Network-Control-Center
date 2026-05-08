import streamlit as st
import pandas as pd

# إعدادات الصفحة
st.set_page_config(page_title="Network Monitor Pro", page_icon="🌐", layout="wide")

# تصميم الواجهة بالألوان والخطوط والأزرار الكبيرة
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    
    /* تصميم الأزرار العملاقة لتكون واضحة وبسيطة */
    div.stButton > button {
        width: 100%;
        height: 250px;
        border-radius: 30px;
        font-size: 35px !important;
        font-weight: bold;
        background: linear-gradient(145deg, #1e293b, #0f172a);
        color: #38bdf8;
        border: 3px solid #38bdf8;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        transition: 0.3s;
    }
    
    div.stButton > button:hover {
        background: #38bdf8;
        color: #0f172a;
        transform: scale(1.03);
    }

    .main-title { text-align: center; color: white; font-size: 48px; font-weight: bold; margin-top: -20px; }
    .sub-title { text-align: center; color: #94a3b8; font-size: 24px; margin-bottom: 60px; }

    /* الحقوق في أسفل الصفحة */
    .footer {
        position: fixed;
        left: 0; bottom: 0; width: 100%;
        background-color: #0f172a; color: #38bdf8;
        text-align: center; padding: 15px;
        font-weight: bold; border-top: 1px solid #38bdf8;
        z-index: 100;
    }
    </style>
    """, unsafe_allow_html=True)

# إدارة التنقل (Navigation)
if 'page' not in st.session_state:
    st.session_state.page = 'main'

def navigate(page_name):
    st.session_state.page = page_name
    st.rerun()

# --- الواجهة الرئيسية ---
if st.session_state.page == 'main':
    st.markdown("<h1 class='main-title'>اهلا بك في النظام الشامل لمعرفة الاجهزة على الشبكة</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>اضغط على أحد الخيارات الكبيرة أدناه للمتابعة</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📱 قائمة أجهزة الشبكة"):
            navigate('devices')
    with col2:
        if st.button("📊 استخدام الأجهزة"):
            navigate('usage')

# --- واجهة قائمة الأجهزة ---
elif st.session_state.page == 'devices':
    st.markdown("<h1 style='text-align: center; color: white;'>📱 قائمة الأجهزة المتصلة حالياً</h1>", unsafe_allow_html=True)
    
    devices_df = pd.DataFrame({
        "اسم الجهاز الحقيقي": ["كمبيوتر عبد الله الشخصي", "جهاز لوحي (Xiaomi)", "جوال سامسونج الترا", "جهاز إكس بوكس"],
        "رقم التعريف (IP)": ["192.168.1.10", "192.168.1.15", "192.168.1.22", "192.168.1.50"],
        "طريقة الاتصال": ["كابل شبكة", "واي فاي", "واي فاي", "واي فاي"]
    })
    
    st.table(devices_df)
    if st.button("🔙 العودة للقائمة الرئيسية"):
        navigate('main')

# --- واجهة استخدام الأجهزة (المواقع والنشاط) ---
elif st.session_state.page == 'usage':
    st.markdown("<h1 style='text-align: center; color: white;'>📊 نشاط واستخدام الأجهزة الآن</h1>", unsafe_allow_html=True)
    
    # تحديث المسميات بناءً على طلبك
    usage_df = pd.DataFrame({
        "اسم الجهاز": ["كمبيوتر عبد الله الشخصي", "جهاز لوحي (Xiaomi)", "جوال سامسونج الترا", "جهاز إكس بوكس"],
        "استخدام الجهاز (النشاط)": ["تطوير وبرمجة (GitHub)", "مشاهدة (YouTube)", "تصفح (Social Media)", "لعب أونلاين (Gaming)"],
        "الموقع المفتوح حالياً": ["github.com/abdullah", "youtube.com/watch", "tiktok.com/feed", "xboxlive.com/play"],
        "كمية البيانات": ["متوسط", "عالي", "عالي", "عالي جداً"]
    })
    
    st.table(usage_df)
    
    if st.button("🔙 العودة للقائمة الرئيسية"):
        navigate('main')

# --- الحقوق الثابتة ---
st.markdown("""
    <div class="footer">
        هذا التطبيق مصمم من أخوك عبد الله
    </div>
    """, unsafe_allow_html=True)
