import streamlit as st
import pandas as pd
import socket
from datetime import datetime

# إعدادات الصفحة الاحترافية
st.set_page_config(
    page_title="Security Network Monitor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تصميم مخصص باستخدام CSS لإضفاء لمسة أمنية
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    .status-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #1f2937;
        color: #10b981;
        border-left: 5px solid #10b981;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# القائمة الجانبية بشكل أنيق
with st.sidebar:
    st.image("https://img.icons8.com/fluency/100/000000/shield.png", width=100)
    st.title("لوحة التحكم الأمنية")
    st.markdown("---")
    choice = st.radio(
        "الانتقال السريع:",
        ["🛡️ نظرة عامة", "📱 الأجهزة النشطة", "🌐 سجل التصفح", "🛠️ الأدوات والضبط"],
        index=0
    )
    st.markdown("---")
    st.info("حالة النظام: متصل وجاهز")

# دالة لجلب الوقت الحالي
now = datetime.now().strftime("%H:%M:%S")

# --- 1. صفحة نظرة عامة ---
if "🛡️ نظرة عامة" in choice:
    st.title("🛡️ نظام المراقبة الأمني الذكي")
    
    st.markdown(f"""
    <div class="status-box">
        <h4>مرحباً بك في برنامجك الأمني المتكامل لكشف استخدام الشبكة</h4>
        <p>تم تفعيل نظام المسح التلقائي. يمكنك الآن تتبع الأجهزة المتصلة وتحليل استهلاك البيانات وحماية خصوصيتك.</p>
    </div>
    """, unsafe_allow_html=True)

    # بطاقات البيانات (Metrics)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="الأجهزة النشطة", value="4", delta="1+ جديد")
    with col2:
        st.metric(label="حالة التشفير", value="WPA2/WPA3", delta="آمن")
    with col3:
        st.metric(label="المخاطر المكتشفة", value="0", delta="لا يوجد")
    with col4:
        st.metric(label="آخر فحص", value=now)

    st.subheader("📊 إحصائيات الاستخدام الأخيرة")
    chart_data = pd.DataFrame({
        'الوقت': ['10 AM', '11 AM', '12 PM', '01 PM', '02 PM'],
        'الاستهلاك (MB)': [150, 220, 180, 450, 300]
    })
    st.area_chart(chart_data.set_index('الوقت'))

# --- 2. صفحة الأجهزة ---
elif "📱 الأجهزة النشطة" in choice:
    st.header("🔍 فحص الأجهزة المتصلة بالشبكة")
    st.write("يتم الآن عرض جميع الأجهزة التي تستخدم التردد الحالي:")
    
    devices_data = {
        "نوع الجهاز": ["كمبيوتر مكتبي", "هاتف ذكي (Android)", "جهاز لوحي", "منصة أ
