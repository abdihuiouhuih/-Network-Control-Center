import streamlit as st
import random

# --- إعدادات الصفحة ---
st.set_page_config(page_title="منصة الإنجاز الذكي 2026", layout="wide", initial_sidebar_state="collapsed")

# --- تنسيق CSS احترافي ---
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #adbac7; }
    div.stButton > button {
        width: 100%; border-radius: 12px; height: 3.8em;
        background-color: #238636; color: white; font-weight: bold; border: none; transition: 0.3s;
    }
    div.stButton > button:hover { background-color: #2ea043; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(46,160,67,0.4); }
    .card {
        padding: 25px; border-radius: 20px; background-color: #1c2128;
        border: 1px solid #444c56; text-align: center; margin-bottom: 20px;
        min-height: 240px; transition: 0.3s;
    }
    .card:hover { border-color: #539bf5; }
    .footer-text { position: fixed; bottom: 10px; left: 15px; color: #539bf5; font-size: 14px; font-weight: bold; }
    .advice-box { padding: 15px; border-right: 5px solid #539bf5; background-color: #22272e; border-radius: 5px; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# إدارة التنقل
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

# دالة لتفريغ المحادثة الحالية مع تحديث الرسالة الترحيبية المطلوبة
def reset_ai_messages():
    st.session_state.ai_messages = [
        {"role": "assistant", "content": "مرحباً بك! أنا الذكاء الاصطناعي الخاص بمنصة التطوير الذاتي الشامل. كيف يمكنني خدمتك اليوم؟"}
    ]

# تخزين محادثات الذكاء الاصطناعي في الذاكرة المؤقتة (Session State) فقط بدون أي قواعد بيانات
if 'ai_messages' not in st.session_state:
    reset_ai_messages()

def navigate_to(page):
    st.session_state.current_page = page

st.markdown('<div class="footer-text">حقوق التطوير محفوظة لـ عبد الله © 2026</div>', unsafe_allow_html=True)

# --- 1. الشاشة الرئيسية (4 خيارات الآن) ---
if st.session_state.current_page == 'home':
    st.markdown("<h1 style='text-align: center; color: #ffffff;'>🚀 منصة التطوير الذاتي الشاملة</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #768390;'>نظام ذكي تفاعلي لتحسين جودة حياتك اليومية ومساعدتك في كل استفساراتك</p>", unsafe_allow_html=True)
    
    st.write("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card"><h2>🏋️ التحدي الرياضي</h2><p>حساب سعرات متطور ونظام نصائح بدنية متغيرة</p></div>', unsafe_allow_html=True)
        if st.button("دخول التحدي الرياضي", key="btn_fit"): 
            navigate_to('fitness')
            st.rerun()

        st.markdown('<div class="card"><h2>🚫 تحدي العادات</h2><p>استراتيجيات نفسية وعملية لترك العادات السلبية</p></div>', unsafe_allow_html=True)
        if st.button("دخول تحدي العادات", key="btn_habits"): 
            navigate_to('habits')
            st.rerun()

    with col2:
        st.markdown('<div class="card"><h2>📚 التحدي الدراسي</h2><p>خطط ذكية ونصائح تخصصية لـ 12 مساراً أكاديمياً</p></div>', unsafe_allow_html=True)
        if st.button("دخول التحدي الدراسي", key="btn_study"): 
            navigate_to('study')
            st.rerun()

        st.markdown('<div class="card"><h2>🤖 الذكاء الاصطناعي الخاص بـ المنصة الشاملة للتطوير الذاتي</h2><p>مساعد ذكي يرد على كافة استفساراتك ويشرح لك محتويات وأقسام الموقع فوراً</p></div>', unsafe_allow_html=True)
        if st.button("دخول الذكاء الاصطناعي", key="btn_ai"): 
            navigate_to('ai_chat')
            st.rerun()

# --- 2. صفحة التحدي الرياضي ---
elif st.session_state.current_page == 'fitness':
    st.title("🏋️ التحدي الرياضي الذكي")
    if st.button("⬅️ العودة للرئيسية", key="back_fit"): 
        navigate_to('home')
        st.rerun()
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("🔢 بيانات الجسم")
        weight = st.number_input("الوزن (كجم):", 30.0, 250.0, 75.0)
        height = st.number_input("الطول (سم):", 100.0, 250.0, 175.0)
        age = st.number_input("العمر:", 10, 90, 22)
    with c2:
        st.subheader("⚡ مستوى النشاط")
        activity = st.radio("نشاطك الأسبوعي:", 
                            ["خامل جداً", "تمارين خفيفة (1-2 يوم)", "نشاط متوسط (3-4 أيام)", "نشاط مكثف (5-6 أيام)", "محترف/بطل رياضي"])
        goal = st.selectbox("هدفك الحالي:", ["تنشيف (خسارة دهون)", "تضخيم (بناء عضل)", "لياقة عامة"])

    if st.button("📊 توليد التقرير البدني والنصائح"):
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        acts = {"خامل جداً": 1.2, "تمارين خفيفة (1-2 يوم)": 1.375, "نشاط متوسط (3-4 أيام)": 1.55, "نشاط مكثف (5-6 أيام)": 1.725, "محترف/بطل رياضي": 1.9}
        tdee = bmr * acts[activity]
        
        st.success(f"سعرات المحافظة: {int(tdee)} سعرة. احتياجك لهدفك: {int(tdee-500 if 'خسارة' in goal else tdee+400 if 'بناء' in goal else tdee)} سعرة.")
        
        st.markdown("### 💡 نصائح رياضية متنوعة لك:")
        fitness_advices = [
            "✅ **قاعدة الـ 10%:** لا تزد شدة تمارينك أكثر من 10% أسبوعياً لتجنب الإصابات.",
            "💧 **الترطيب:** اشرب 500 مل من الماء قبل التمرين بـ 30 دقيقة لتحسين الأداء.",
            "😴 **الاستشفاء:** العضلات تبنى أثناء النوم وليس أثناء التمرين، حافظ على 8 ساعات نوم.",
            "🍎 **التغذية:** ركز على البروتين (1.6 جم لكل كجم من وزنك) لدعم البناء العضلي.",
            "⏱️ **الراحة:** لا تتجاوز 90 ثانية راحة بين الجلسات إذا كان هدفك رفع اللياقة.",
            "🧘 **الإطالة:** خصص 10 دقائق بعد التمرين للإطالات لتقليل آلام العضلات."
        ]
        selected_advices = random.sample(fitness_advices, 3)
        for adv in selected_advices:
            st.markdown(f"<div class='advice-box'>{adv}</div>", unsafe_allow_html=True)

# --- 3. صفحة تحدي العادات ---
elif st.session_state.current_page == 'habits':
    st.title("🚫 مختبر تغيير العادات")
    if st.button("⬅️ العودة للرئيسية", key="back_habits"): 
        navigate_to('home')
        st.rerun()
    
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        habit_name = st.text_input("ما هي العادة التي تود كسرها؟ (مثلاً: التدخين، السهر، السكريات)")
        severity = st.select_slider("مدى صعوبة العادة بالنسبة لك:", options=["سهلة", "متوسطة", "صعبة", "إدمان"])
    with col_h2:
        trigger = st.selectbox("ما هو المحفز الرئيسي لهذه العادة؟", ["الملل", "التوتر", "أصدقاء السوء", "الفراغ", "الوقت (مثلاً قبل النوم)"])

    if st.button("🚀 تحليل العادة ووضع خطة"):
        st.markdown(f"### 🛡️ خطة التخلص من {habit_name}:")
        
        habit_tips = {
            "الملل": "استبدل العادة بنشاط حركي سريع (10 ضغط) أو تعلم مهارة يدوية تشغل يدك.",
            "التوتر": "جرب تقنية التنفس 4-7-8 عند الشعور بالرغبة في ممارسة العادة.",
            "أصدقاء السوء": "غير بيئتك فوراً؛ العادات معدية كالأنفلونزا، اختر من يشبه طموحك.",
            "الفراغ": "جدول يومك بالدقيقة؛ العقل الفارغ هو مختبر للشيطان والعادات السيئة.",
            "الوقت": "غير روتينك في هذا الوقت تحديداً، إذا كانت العادة قبل النوم، ابدأ بالقراءة بعيداً عن السرير."
        }
        
        st.info(f"📍 **نصيحة للمحفز ({trigger}):** {habit_tips[trigger]}")
        
        st.markdown("#### 🧠 استراتيجيات نفسية متنوعة:")
        general_habits = [
            "✨ **قاعدة الـ 5 ثوانٍ:** عندما تأتيك الرغبة، عد تنازلياً 5-4-3-2-1 ثم تحرك فوراً لفعل شيء آخر.",
            "🔗 **ربط العادات:** اربط عادة حسنة جديدة بمكان أو زمان العادة السيئة لتعويض الفراغ العصبي.",
            "📉 **التدرج:** إذا كانت العادة صعبة، لا تتركها فجأة، بل قلل تكرارها بنسبة 20% أسبوعياً.",
            "📝 **التدوين:** اكتب شعورك 'المقرف' بعد ممارسة العادة السيئة واقرأه عندما تشتاق إليها."
        ]
        for h_adv in random.sample(general_habits, 2):
            st.markdown(f"<div class='advice-box'>{h_adv}</div>", unsafe_allow_html=True)

# --- 4. صفحة التحدي الدراسي ---
elif st.session_state.current_page == 'study':
    st.title("📚 مركز التميز الأكاديمي")
    if st.button("⬅️ العودة للرئيسية", key="back_study"): 
        navigate_to('home')
        st.rerun()
    
    major = st.selectbox("اختر تخصصك بدقة:", 
                         ["هندسة الشبكات", "الأمن السيبراني", "الذكاء الاصطناعي", "علوم الحاسب", 
                          "الطب", "الهندسة الميكانيكية", "إدارة الأعمال", "المحاسبة", "القانون", "التمريض", "الهندسة الكهربائية"])
    
    study_data = {
        "هندسة الشبكات": ["تخصص في محاكاة GNS3 و EVEng.", "احصل على شهادة CCNA قبل التخرج.", "افهم OSI Model كأنه اسمك."],
        "الأمن السيبراني": ["تعلم أساسيات Linux (Kali/Parrot).", "مارس تحديات CTF (Capture The Flag) أسبوعياً.", "شهادة Security+ هي بوابتك الأولى."],
        "الذكاء الاصطناعي": ["أتقن الرياضيات (Linear Algebra).", "تعلم مكتبات Pandas و Scikit-learn.", "ابنِ مشاريع تنبؤية بسيطة ببيانات حقيقية."],
        "علوم الحاسب": ["ركز على هياكل البيانات (Data Structures).", "حل مشكلات البرمجة في LeetCode.", "افهم كيف تعمل الذاكرة (Memory Management)."],
        "الطب": ["استخدم Anki للحفظ طويل الأمد.", "اربط المعلومة النظرية بالحالة السريرية.", "ركز على مراجعة علم الأمراض (Pathology) باستمرار."],
        "الهندسة الميكانيكية": ["أتقن برامج الـ CAD مثل SolidWorks.", "افهم الديناميكا الحرارية بعمق تطبيق عملي.", "تابع مشاريع التصنيع الحديثة والـ 3D Printing."],
        "إدارة الأعمال": ["تعلم مهارات تحليل البيانات بـ Excel و Power BI.", "اقرأ في القيادة وعلم النفس المؤسسي.", "افهم استراتيجيات التسويق الرقمي."],
        "المحاسبة": ["افهم الـ IFRS (المعايير الدولية).", "تدرب على برامج مثل SAP أو Oracle.", "دقة الأرقام أهم من سرعتك في الحل."],
        "القانون": ["درب نفسك على الصياغة القانونية الرصينة.", "تابع أحكام المحاكم العليا لفهم روح القانون.", "مارس المحاكم الصورية (Moot Court)."],
        "التمريض": ["الجانب الإنساني والعناية بالمرضى يوازي العلم الطبي.", "أتقن مهارات الطوارئ والإنعاش (BLS).", "الدقة في قياس المؤشرات الحيوية تنقذ الأرواح."],
        "الهندسة الكهربائية": ["ركز على أنظمة الطاقة المتجددة والتحكم.", "أتقن MATLAB للمحاكاة.", "افهم الدوائر المتكاملة والأنظمة المدمجة."]
    }

    st.success(f"📌 **خطة التميز لتخصص {major}:**")
    for tip in study_data[major]:
        st.write(f"- {tip}")
    
    st.markdown("---")
    st.subheader("💡 نصائح دراسية عامة (تتغير عند كل دخول):")
    general_study = [
        "🍅 **تقنية البومودورو:** ادرس 25 دقيقة وارتح 5 دقائق لزيادة التركيز.",
        "🎧 **بيئة الدراسة:** جرب الضوضاء البيضاء (White Noise) لعزل المشتتات.",
        "🖍️ **الخرائط الذهنية:** حول المعلومات المعقدة لرسومات بصرية يسهل تذكرها.",
        "👨‍🏫 **تقنية فينمان:** اشرح ما درسته لشخص خيالي؛ إذا لم تستطع، فأنت لم تفهم بعد."
    ]
    for gs in random.sample(general_study, 2):
        st.markdown(f"<div class='advice-box'>{gs}</div>", unsafe_allow_html=True)

# --- 5. صفحة الذكاء الاصطناعي الخاص بالمنصة ---
elif st.session_state.current_page == 'ai_chat':
    st.title("🤖 الذكاء الاصطناعي الخاص بـ المنصة الشاملة للتطوير الذاتي")
    st.markdown("اسألني عن أي شيء في الموقع، وسأقوم بشرحه لك أو مساعدتك في استخدامه فوراً!")
    
    # صف أزرار للتحكم (العودة + زر مسح الرسائل)
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("⬅️ العودة للرئيسية", key="back_ai"): 
            navigate_to('home')
            st.rerun()
    with col_btn2:
        if st.button("🗑️ مسح جميع الرسائل وبدء محادثة جديدة", key="clear_ai"):
            reset_ai_messages()
            st.rerun()
    
    st.write("---")
    
    # عرض سجل المحادثة من الذاكرة المؤقتة فقط (Streamlit Session)
    for message in st.session_state.ai_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    # استقبال إدخال المستخدم
    if user_query := st.chat_input("اكتب استفسارك هنا (مثلاً: كيف أستفيد من التحدي الرياضي؟ أو اشرح لي صفحة العادات):"):
        # إضافة رسالة المستخدم للذاكرة المؤقتة فقط
        st.session_state.ai_messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)
            
        # توليد رد ذكي مبني على محتوى الموقع
        query_lower = user_query.lower()
        if "رياضي" in query_lower or "رياضة" in query_lower or "سعرات" in query_lower:
            ai_reply = "🏋️ **التحدي الرياضي:** يتيح لك حساب السعرات الحرارية اليومية بدقة (BMR و TDEE) بناءً على وزنك، طولك، عمرك، ونشاطك البدني، ويعطيك أهدافاً واضحة لتنشيف الدهون أو تضخيم العضلات مع نصائح احترافية متغيرة."
        elif "عادات" in query_lower or "عادة" in query_lower or "سلبية" in query_lower:
            ai_reply = "🚫 **تحدي العادات:** مختبر متكامل يساعدك على تفكيك العادات السيئة عبر تحديد المحفزات (مثل الملل أو التوتر) وتزويدك باستراتيجيات علمية ونفسية مثل قاعدة الـ 5 ثوانٍ وتقنيات التدريج."
        elif "دراسي" in query_lower or "تخصص" in query_lower or "دراسة" in query_lower:
            ai_reply = "📚 **التحدي الدراسي (مركز التميز الأكاديمي):** يوفر خطط عمل احترافية ونصحية مخصصة لـ 12 تخصصاً أكاديمياً مختلفاً (مثل الأمن السيبراني، الذكاء الاصطناعي، الطب، الهندسة، وغيرها) لمساعدتك على التفوق."
        elif "من هي" in query_lower or "من أنت" in query_lower or "موقع" in query_lower:
            ai_reply = "هذه **المنصة الشاملة للتطوير الذاتي** المطورة بواسطة عبد الله © 2026، وهي مصممة خصيصاً لمساعدتك على الارتقاء بحياتك صحياً، نفسياً، وأكاديمياً بكل سهولة."
        else:
            ai_reply = f"أهلاً بك! لقد فهمت استفسارك حول ({user_query}). في منصتنا الشاملة، يمكنك الانتقال لأي قسم (التحدي الرياضي، تحدي العادات، أو التحدي الدراسي) من الشاشة الرئيسية، وكل قسم يقدم أدوات تفاعلية مخصصة. هل تود مني أن أشرح لك تفاصيل أي قسم بشكل أعمق؟"
            
        st.session_state.ai_messages.append({"role": "assistant", "content": ai_reply})
        with st.chat_message("assistant"):
            st.markdown(ai_reply)
