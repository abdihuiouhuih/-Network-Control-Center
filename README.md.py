import streamlit as st
import pandas as pd

# إعدادات الصفحة الفخمة
st.set_page_config(page_title="Network Master Pro", page_icon="🌐", layout="wide")

# تصميم CSS احترافي للأزرار والواجهة
st.markdown("""
    <style>
    /* تغيير خلفية الصفحة */
    .stApp {
        background-color: #0e1117;
    }
    
    /* تصميم الأزرار العملاقة */
    div.stButton > button {
        width: 100%;
        height: 150px;
        border-radius: 20px;
        font-size: 25px !important;
        font-weight: bold;
        background: linear-gradient(145deg, #1e293b, #0f172a);
        color: #38bdf8;
        border: 2px solid #38bdf8;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(56, 189, 248, 0.2);
    }
    
    div.stButton > button:hover {
        background: #38bdf8;
        color: #0f172a;
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(56, 189, 248, 0.4);
    }

    /* نص العنوان */
    .main-header {
        text-align: center;
        color: #f8fafc;
        font-size: 40px;
        font-weight: 900;
        margin-bottom: 10px;
    }
    
    .sub-header {
        text-align: center;
        color: #94a3b8;
        font-size: 18px;
        margin-bottom: 40px;
    }

    /* الحقوق في الأسفل */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0f172a;
        color: #38bdf8;
        text-align: center;
        padding: 15px;
        font-weight: bold;
        border-top: 1px solid #38bdf8;
    }
    </style>
    """, unsafe_allow_html=True)

# إدارة الصفحات (Navigation)
if 'page' not in st.session_state:
    st.session_state.page = 'main'

def navigate_to(page_name):
    st.session_state.page = page_name

# --- واجهة القائمة الرئيسية (أزرار كبيرة) ---
if st.session_state.page == 'main':
    st.markdown("<h1 class='main-header'>🌐 النظام الشامل لمعرفة أجهزة الشبكة</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>أهلاً بك في نظامك الأمني.. اضغط على أي قسم للدخول فوراً</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📱 أجهزة الشبكة والآيبيات"):
            navigate_to('ips')
            st.rerun()
            
        if st.button("🔐 بيانات ورمز الشبكة"):
            navigate_to('wifi')
            st.rerun()

    with col2:
        if st.button("🌍 نشاط المواقع اللحظي"):
            navigate_to('web')
            st.rerun()
            
        if st.button("📊 إحصائيات الاستخدام"):
            navigate_to('stats')
            st.rerun()

# --- واجهة الآيبيات ---
elif st.session_state.page == 'ips':
    st.title("📱 قائمة الأجهزة المتصلة")
    data = pd.DataFrame({
        "الجهاز": ["Xiaomi Pad 7", "Samsung S24 Ultra", "Gaming PC", "Brother's Xbox"],
        "IP Address": ["192.168.1.15", "192.168.1.20", "192.168.1.10", "192.168.1.50"],
        "الحالة": ["نشط ✅", "خامل 💤", "نشط ✅", "نشط ✅"]
    })
    st.table(data)
    if st.button("🔙 العودة للقائمة"): navigate_to('main'); st.rerun()

# --- واجهة بيانات الشبكة ---
elif st.session_state.page == 'wifi':
    st.title("🔐 معلومات الشبكة والوصول")
    st.info("**اسم الشبكة:** Abdullah_FIBER_5G")
    st.info("**نوع التشفير:** WPA3 (الأكثر أماناً)")
    if st.button("إظهار الرمز السري 🔑"):
        st.success("الرمز هو: **Abdullah_2026_Secure**")
    if st.button("🔙 العودة للقائمة"): navigate_to('main'); st.rerun()

# --- واجهة المواقع ---
elif st.session_state.page == 'web':
    st.title("🌍 سجل المواقع النشطة")
    web_data = pd.DataFrame({
        "الجهاز": ["192.168.1.10", "192.168.1.15", "192.168.1.20"],
        "الموقع المفتوح الآن": ["github.com", "google.com.sa", "youtube.com"],
        "النشاط": ["تطوير أكواد", "بحث", "بث 4K"]
    })
    st.table(web_data)
    if st.button("🔙 العودة للقائمة"): navigate_to('main'); st.rerun()

# --- واجهة الإحصائيات ---
elif st.session_state.page == 'stats':
    st.title("📊 ملخص الاستهلاك")
    st.bar_chart({"البيانات المستهلكة (GB)": [5.2, 8.4, 20.1, 12.5]})
    st.write("الأكثر استهلاكاً للشبكة اليوم: **Gaming PC**")
    if st.button("🔙 العودة للقائمة"): navigate_to('main'); st.rerun()

# --- الحقوق الثابتة ---
st.markdown("""
    <div class="footer">
        هذا التطبيق مصمم بواسطة أخوك عبد الله ✍️ | 2026
    </div>
    """, unsafe_allow_html=True)
