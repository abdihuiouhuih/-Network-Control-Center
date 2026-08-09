import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

# =========================================================
# CONFIGURATION
# =========================================================

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "sales_app.db"
UPLOAD_DIR = APP_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="SalesFlow | إدارة المبيعات والمخزون",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# CUSTOM STYLE
# =========================================================

st.markdown(
    """
    <style>

    .main {
        background: #f8fafc;
    }

    .block-container {
        padding-top: 1.5rem;
        max-width: 1450px;
    }

    [data-testid="stSidebar"] {
        background: #0f172a;
    }

    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }

    .app-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 5px;
    }

    .app-subtitle {
        color: #64748b;
        margin-bottom: 25px;
    }

    .kpi {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(15, 23, 42, 0.05);
        min-height: 125px;
    }

    .kpi-label {
        color: #64748b;
        font-size: 0.9rem;
    }

    .kpi-value {
        color: #0f172a;
        font-size: 1.8rem;
        font-weight: 800;
        margin-top: 7px;
    }

    .small {
        color: #64748b;
        font-size: 0.82rem;
    }

    .section {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 18px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# DATABASE
# =========================================================


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():

    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript(
        """

        CREATE TABLE IF NOT EXISTS reps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            area TEXT,
            rep_id INTEGER,
            active INTEGER DEFAULT 1,
            FOREIGN KEY(rep_id) REFERENCES reps(id)
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            min_stock INTEGER DEFAULT 0,
            dormant_days INTEGER DEFAULT 30,
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS rep_stock (
            rep_id INTEGER,
            product_id INTEGER,
            qty REAL DEFAULT 0,

            PRIMARY KEY(rep_id, product_id),

            FOREIGN KEY(rep_id)
                REFERENCES reps(id),

            FOREIGN KEY(product_id)
                REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rep_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            visit_date TEXT NOT NULL,
            notes TEXT,
            image_path TEXT,

            FOREIGN KEY(rep_id)
                REFERENCES reps(id),

            FOREIGN KEY(customer_id)
                REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS visit_stock (
            visit_id INTEGER,
            product_id INTEGER,
            qty REAL DEFAULT 0,

            PRIMARY KEY(visit_id, product_id),

            FOREIGN KEY(visit_id)
                REFERENCES visits(id),

            FOREIGN KEY(product_id)
                REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rep_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            invoice_no TEXT,
            image_path TEXT,

            FOREIGN KEY(rep_id)
                REFERENCES reps(id),

            FOREIGN KEY(customer_id)
                REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS order_items (
            order_id INTEGER,
            product_id INTEGER,
            qty REAL DEFAULT 0,

            PRIMARY KEY(order_id, product_id),

            FOREIGN KEY(order_id)
                REFERENCES orders(id),

            FOREIGN KEY(product_id)
                REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rep_id INTEGER,
            month TEXT NOT NULL,
            target_sales REAL DEFAULT 0,
            target_collection REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rep_id INTEGER,
            customer_id INTEGER,
            collection_date TEXT,
            amount REAL DEFAULT 0,
            reference TEXT
        );

        """
    )

    # -----------------------------------------------------
    # Demo data
    # -----------------------------------------------------

    if cursor.execute("SELECT COUNT(*) FROM reps").fetchone()[0] == 0:

        cursor.execute(
            """
            INSERT INTO reps(name, phone)
            VALUES (?, ?)
            """,
            ("مندوب تجريبي", "0500000000"),
        )

    if cursor.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:

        rep_id = cursor.execute(
            "SELECT id FROM reps LIMIT 1"
        ).fetchone()[0]

        cursor.executemany(
            """
            INSERT INTO customers(name, area, rep_id)
            VALUES (?, ?, ?)
            """,
            [
                ("عميل الرياض 01", "الرياض", rep_id),
                ("عميل الطائف 01", "الطائف", rep_id),
                ("عميل جدة 01", "جدة", rep_id),
            ],
        )

    if cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:

        cursor.executemany(
            """
            INSERT INTO products
            (sku, name, category, min_stock, dormant_days)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("SKU-001", "صنف تجريبي 1", "مشروبات", 10, 30),
                ("SKU-002", "صنف تجريبي 2", "أغذية", 5, 21),
                ("SKU-003", "صنف تجريبي 3", "عناية", 8, 30),
                ("SKU-004", "صنف تجريبي 4", "منزلية", 5, 45),
            ],
        )

    conn.commit()
    conn.close()


init_db()

# =========================================================
# DATABASE HELPERS
# =========================================================


def query(sql, params=()):

    conn = get_db()

    df = pd.read_sql_query(
        sql,
        conn,
        params=params,
    )

    conn.close()

    return df


def execute(sql, params=()):

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(sql, params)

    conn.commit()

    last_id = cursor.lastrowid

    conn.close()

    return last_id


def save_upload(uploaded_file, prefix):

    if uploaded_file is None:
        return None

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    safe_name = (
        uploaded_file.name
        .replace("/", "_")
        .replace("\\", "_")
    )

    path = (
        UPLOAD_DIR
        / f"{prefix}_{timestamp}_{safe_name}"
    )

    path.write_bytes(
        uploaded_file.getbuffer()
    )

    return str(path)


def format_number(value):

    try:
        return f"{float(value):,.0f}"

    except Exception:
        return "0"


def kpi(label, value, note=""):

    st.markdown(
        f"""
        <div class="kpi">

            <div class="kpi-label">
                {label}
            </div>

            <div class="kpi-value">
                {value}
            </div>

            <div class="small">
                {note}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown(
    """
    <h1 style="color:white;">
    📦 SalesFlow
    </h1>
    """,
    unsafe_allow_html=True,
)

st.sidebar.caption(
    "نظام إدارة المبيعات والمخزون"
)

role = st.sidebar.selectbox(
    "نوع المستخدم",
    [
        "مندوب مبيعات",
        "الإدارة",
    ],
)

reps = query(
    """
    SELECT *
    FROM reps
    WHERE active = 1
    ORDER BY name
    """
)

if len(reps):

    selected_rep = st.sidebar.selectbox(
        "المندوب",
        reps["name"].tolist(),
    )

    rep_id = int(
        reps.loc[
            reps["name"] == selected_rep,
            "id",
        ].iloc[0]
    )

else:

    rep_id = 1


# =========================================================
# NAVIGATION
# =========================================================

if role == "مندوب مبيعات":

    pages = [

        "🏠 لوحة المندوب",

        "👥 العملاء والزيارات",

        "🧾 تسجيل أوردر",

        "📦 مخزون المندوب",

        "💰 التحصيل",

        "📊 تقارير المندوب",

    ]

else:

    pages = [

        "🏢 لوحة الإدارة",

        "👥 العملاء والمندوبون",

        "📦 الأصناف والمخزون",

        "🎯 التارجت والتحصيل",

        "⚠️ الأصناف الراكدة",

        "📥 التقارير والتصدير",

    ]


page = st.sidebar.radio(
    "التنقل",
    pages,
)


st.sidebar.divider()

st.sidebar.caption(
    "SalesFlow v1.0"
)

# =========================================================
# REP DASHBOARD
# =========================================================

if page == "🏠 لوحة المندوب":

    st.markdown(
        '<div class="app-title">مرحباً بك 👋</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="app-subtitle">'
        "ملخص أدائك ومخزونك اليومي"
        "</div>",
        unsafe_allow_html=True,
    )

    today = date.today().isoformat()

    month = date.today().strftime("%Y-%m")

    sales = query(
        """
        SELECT
            COALESCE(SUM(oi.qty), 0) AS qty

        FROM orders o

        JOIN order_items oi
            ON o.id = oi.order_id

        WHERE o.rep_id = ?

        AND substr(
            o.order_date,
            1,
            7
        ) = ?
        """,
        (rep_id, month),
    )

    visits = query(
        """
        SELECT COUNT(*) AS count
        FROM visits
        WHERE rep_id = ?
        AND visit_date = ?
        """,
        (rep_id, today),
    )

    collections = query(
        """
        SELECT
            COALESCE(SUM(amount), 0) AS amount

        FROM collections

        WHERE rep_id = ?

        AND substr(
            collection_date,
            1,
            7
        ) = ?
        """,
        (rep_id, month),
    )

    target = query(
        """
        SELECT
            COALESCE(
                SUM(target_sales),
                0
            ) AS target

        FROM targets

        WHERE rep_id = ?

        AND month = ?
        """,
        (rep_id, month),
    )

    sales_value = float(
        sales.iloc[0]["qty"]
    )

    collection_value = float(
        collections.iloc[0]["amount"]
    )

    target_value = float(
        target.iloc[0]["target"]
    )

    achievement = (
        sales_value / target_value * 100
        if target_value
        else 0
    )

    cols = st.columns(4)

    with cols[0]:

        kpi(
            "زيارات اليوم",
            format_number(
                visits.iloc[0]["count"]
            ),
            "زيارة مسجلة",
        )

    with cols[1]:

        kpi(
            "Sell-in هذا الشهر",
            format_number(
                sales_value
            ),
            "كمية الأوردرات",
        )

    with cols[2]:

        kpi(
            "التحصيل",
            f"{collection_value:,.0f}",
            "خلال الشهر",
        )

    with cols[3]:

        kpi(
            "تحقيق التارجت",
            f"{achievement:.1f}%",
            f"الهدف {target_value:,.0f}",
        )

    st.markdown("### 📈 مستوى تحقيق التارجت")

    if target_value:

        st.progress(
            min(
                achievement / 100,
                1,
            )
        )

    else:

        st.info(
            "لم يتم تحديد تارجت لهذا الشهر."
        )

    # -----------------------------------------------------
    # Rep stock
    # -----------------------------------------------------

    inventory = query(
        """
        SELECT

            p.sku,

            p.name,

            COALESCE(
                rs.qty,
                0
            ) AS qty,

            p.min_stock

        FROM products p

        LEFT JOIN rep_stock rs

            ON p.id = rs.product_id

            AND rs.rep_id = ?

        WHERE p.active = 1

        ORDER BY qty ASC
        """,
        (rep_id,),
    )

    st.markdown(
        "### 📦 حالة مخزون المندوب"
    )

    if len(inventory):

        inventory["الحالة"] = inventory.apply(

            lambda row:

            "🔴 نفد"

            if row.qty <= 0

            else (

                "🟠 منخفض"

                if row.qty <= row.min_stock

                else "🟢 متوفر"

            ),

            axis=1,
        )

        st.dataframe(
            inventory[
                [
                    "sku",
                    "name",
                    "qty",
                    "min_stock",
                    "الحالة",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# CUSTOMER VISITS
# =========================================================

elif page == "👥 العملاء والزيارات":

    st.markdown(
        "## 👥 زيارة العميل وحصر المخزون"
    )

    customers = query(
        """
        SELECT *

        FROM customers

        WHERE active = 1

        AND rep_id = ?

        ORDER BY name
        """,
        (rep_id,),
    )

    products = query(
        """
        SELECT *

        FROM products

        WHERE active = 1

        ORDER BY name
        """
    )

    if not len(customers):

        st.warning(
            "لا يوجد عملاء مرتبطون بهذا المندوب."
        )

    else:

        customer_name = st.selectbox(
            "العميل",
            customers["name"].tolist(),
        )

        customer_id = int(
            customers.loc[
                customers["name"]
                == customer_name,
                "id",
            ].iloc[0]
        )

        visit_date = st.date_input(
            "تاريخ الزيارة",
            date.today(),
        )

        notes = st.text_area(
            "ملاحظات الزيارة"
        )

        image = st.file_uploader(
            "📷 صورة المخزون أو الفاتورة",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp",
            ],
        )

        st.markdown(
            "### 📦 حصر رصيد الأصناف لدى العميل"
        )

        stock_input = {}

        for _, product in products.iterrows():

            stock_input[int(product.id)] = (
                st.number_input(
                    f"{product.name} — {product.sku}",
                    min_value=0.0,
                    step=1.0,
                    value=0.0,
                    key=f"visit_{product.id}",
                )
            )

        if st.button(
            "💾 حفظ الزيارة وحصر المخزون",
            type="primary",
            use_container_width=True,
        ):

            image_path = save_upload(
                image,
                "visit",
            )

            visit_id = execute(
                """
                INSERT INTO visits
                (
                    rep_id,
                    customer_id,
                    visit_date,
                    notes,
                    image_path
                )

                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    rep_id,
                    customer_id,
                    visit_date.isoformat(),
                    notes,
                    image_path,
                ),
            )

            for product_id, qty in stock_input.items():

                execute(
                    """
                    INSERT INTO visit_stock
                    (
                        visit_id,
                        product_id,
                        qty
                    )

                    VALUES (?, ?, ?)
                    """,
                    (
                        visit_id,
                        product_id,
                        qty,
                    ),
                )

            st.success(
                "تم حفظ الزيارة وحصر المخزون بنجاح."
            )

        # -------------------------------------------------
        # Sell-out
        # -------------------------------------------------

        st.markdown(
            "### 📉 Sell-out بين الزيارات"
        )

        sell_out = query(
            """
            WITH visits_data AS (

                SELECT

                    v.id,

                    v.customer_id,

                    v.visit_date,

                    vs.product_id,

                    vs.qty,

                    LAG(vs.qty)

                    OVER (

                        PARTITION BY
                            v.customer_id,
                            vs.product_id

                        ORDER BY
                            v.visit_date,
                            v.id

                    ) AS previous_qty

                FROM visits v

                JOIN visit_stock vs

                    ON v.id =
                    vs.visit_id

                WHERE v.rep_id = ?

            )

            SELECT

                c.name AS العميل,

                p.name AS الصنف,

                v.visit_date AS تاريخ_الزيارة,

                COALESCE(
                    v.previous_qty,
                    0
                ) AS الرصيد_السابق,

                v.qty AS الرصيد_الحالي,

                CASE

                    WHEN v.previous_qty IS NULL
                    THEN 0

                    WHEN v.previous_qty - v.qty < 0
                    THEN 0

                    ELSE
                        v.previous_qty - v.qty

                END AS sell_out

            FROM visits_data v

            JOIN customers c
                ON c.id = v.customer_id

            JOIN products p
                ON p.id = v.product_id

            ORDER BY
                v.visit_date DESC
            """,
            (rep_id,),
        )

        st.dataframe(
            sell_out,
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# ORDER ENTRY
# =========================================================

elif page == "🧾 تسجيل أوردر":

    st.markdown(
        "## 🧾 تسجيل Sell-in / أوردر"
    )

    customers = query(
        """
        SELECT *

        FROM customers

        WHERE active = 1

        AND rep_id = ?

        ORDER BY name
        """,
        (rep_id,),
    )

    products = query(
        """
        SELECT *

        FROM products

        WHERE active = 1

        ORDER BY name
        """
    )

    if len(customers) and len(products):

        customer_name = st.selectbox(
            "العميل",
            customers["name"].tolist(),
        )

        customer_id = int(
            customers.loc[
                customers["name"]
                == customer_name,
                "id",
            ].iloc[0]
        )

        invoice_number = st.text_input(
            "رقم الفاتورة / الأوردر"
        )

        invoice_image = st.file_uploader(
            "📷 صورة الفاتورة",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp",
            ],
        )

        st.markdown(
            "### 🛒 أصناف الأوردر"
        )

        order_items = {}

        for _, product in products.iterrows():

            stock = query(
                """
                SELECT
                    COALESCE(qty, 0) AS qty

                FROM rep_stock

                WHERE rep_id = ?

                AND product_id = ?
                """,
                (
                    rep_id,
                    int(product.id),
                ),
            )

            available = (
                float(stock.iloc[0]["qty"])
                if len(stock)
                else 0
            )

            order_items[
                int(product.id)
            ] = st.number_input(
                f"{product.name} — المتاح: {available:g}",
                min_value=0.0,
                max_value=max(
                    available,
                    0,
                ),
                step=1.0,
                key=f"order_{product.id}",
            )

        if st.button(
            "✅ اعتماد الأوردر",
            type="primary",
            use_container_width=True,
        ):

            selected_items = {
                pid: qty

                for pid, qty
                in order_items.items()

                if qty > 0
            }

            if not selected_items:

                st.error(
                    "اختر صنفاً واحداً على الأقل."
                )

            else:

                insufficient = []

                for product_id, qty in selected_items.items():

                    stock = query(
                        """
                        SELECT
                            COALESCE(qty, 0) AS qty

                        FROM rep_stock

                        WHERE rep_id = ?

                        AND product_id = ?
                        """,
                        (
                            rep_id,
                            product_id,
                        ),
                    )

                    available = (
                        float(
                            stock.iloc[0]["qty"]
                        )
                        if len(stock)
                        else 0
                    )

                    product_name = products.loc[
                        products["id"]
                        == product_id,
                        "name",
                    ].iloc[0]

                    if qty > available:

                        insufficient.append(
                            f"{product_name}: "
                            f"المطلوب {qty:g} "
                            f"والمتاح {available:g}"
                        )

                if insufficient:

                    st.error(
                        "لا يمكن اعتماد الأوردر:\n\n"
                        + "\n".join(
                            insufficient
                        )
                    )

                else:

                    image_path = save_upload(
                        invoice_image,
                        "invoice",
                    )

                    order_id = execute(
                        """
                        INSERT INTO orders
                        (
                            rep_id,
                            customer_id,
                            order_date,
                            invoice_no,
                            image_path
                        )

                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            rep_id,
                            customer_id,
                            date.today().isoformat(),
                            invoice_number,
                            image_path,
                        ),
                    )

                    for product_id, qty in selected_items.items():

                        execute(
                            """
                            INSERT INTO order_items
                            (
                                order_id,
                                product_id,
                                qty
                            )

                            VALUES (?, ?, ?)
                            """,
                            (
                                order_id,
                                product_id,
                                qty,
                            ),
                        )

                        execute(
                            """
                            INSERT INTO rep_stock
                            (
                                rep_id,
                                product_id,
                                qty
                            )

                            VALUES (?, ?, ?)

                            ON CONFLICT
                            (
                                rep_id,
                                product_id
                            )

                            DO UPDATE SET
                                qty = qty - ?
                            """,
                            (
                                rep_id,
                                product_id,
                                qty,
                                qty,
                            ),
                        )

                    st.success(
                        "تم اعتماد الأوردر وخصم الكمية من مخزون المندوب."
                    )


# =========================================================
# REP INVENTORY
# =========================================================

elif page == "📦 مخزون المندوب":

    st.markdown(
        "## 📦 مخزون المندوب"
    )

    products = query(
        """
        SELECT *

        FROM products

        WHERE active = 1

        ORDER BY name
        """
    )

    data = []

    for _, product in products.iterrows():

        stock = query(
            """
            SELECT
                COALESCE(qty, 0) AS qty

            FROM rep_stock

            WHERE rep_id = ?

            AND product_id = ?
            """,
            (
                rep_id,
                int(product.id),
            ),
        )

        qty = (
            float(stock.iloc[0]["qty"])
            if len(stock)
            else 0
        )

        data.append(
            [
                product.sku,
                product.name,
                product.category,
                qty,
                product.min_stock,
            ]
        )

    inventory = pd.DataFrame(
        data,
        columns=[
            "SKU",
            "الصنف",
            "التصنيف",
            "الرصيد",
            "حد إعادة الطلب",
        ],
    )

    inventory["الحالة"] = inventory.apply(

        lambda row:

        "🔴 نفد"

        if row["الرصيد"] <= 0

        else (

            "🟠 منخفض"

            if row["الرصيد"]
            <= row["حد إعادة الطلب"]

            else "🟢 جيد"
        ),

        axis=1,
    )

    st.dataframe(
        inventory,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        "### 🔄 إضافة مخزون"
    )

    product_name = st.selectbox(
        "الصنف",
        products["name"].tolist(),
    )

    product_id = int(
        products.loc[
            products["name"]
            == product_name,
            "id",
        ].iloc[0]
    )

    quantity = st.number_input(
        "الكمية المضافة",
        min_value=0.0,
        step=1.0,
    )

    if st.button(
        "إضافة للمخزون",
        type="primary",
    ):

        execute(
            """
            INSERT INTO rep_stock
            (
                rep_id,
                product_id,
                qty
            )

            VALUES (?, ?, ?)

            ON CONFLICT
            (
                rep_id,
                product_id
            )

            DO UPDATE SET
                qty = qty + ?
            """,
            (
                rep_id,
                product_id,
                quantity,
                quantity,
            ),
        )

        st.success(
            "تم تحديث مخزون المندوب."
        )


# =========================================================
# COLLECTIONS
# =========================================================

elif page == "💰 التحصيل":

    st.markdown(
        "## 💰 تسجيل التحصيل"
    )

    customers = query(
        """
        SELECT *

        FROM customers

        WHERE active = 1

        AND rep_id = ?

        ORDER BY name
        """,
        (rep_id,),
    )

    if len(customers):

        customer_name = st.selectbox(
            "العميل",
            customers["name"].tolist(),
        )

        customer_id = int(
            customers.loc[
                customers["name"]
                == customer_name,
                "id",
            ].iloc[0]
        )

        amount = st.number_input(
            "قيمة التحصيل",
            min_value=0.0,
            step=100.0,
        )

        reference = st.text_input(
            "مرجع / رقم إيصال"
        )

        if st.button(
            "💾 حفظ التحصيل",
            type="primary",
        ):

            execute(
                """
                INSERT INTO collections
                (
                    rep_id,
                    customer_id,
                    collection_date,
                    amount,
                    reference
                )

                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    rep_id,
                    customer_id,
                    date.today().isoformat(),
                    amount,
                    reference,
                ),
            )

            st.success(
                "تم تسجيل التحصيل بنجاح."
            )

    st.markdown(
        "### آخر عمليات التحصيل"
    )

    collection_data = query(
        """
        SELECT

            c.name AS العميل,

            col.collection_date AS التاريخ,

            col.amount AS المبلغ,

            col.reference AS المرجع

        FROM collections col

        JOIN customers c
            ON c.id = col.customer_id

        WHERE col.rep_id = ?

        ORDER BY col.id DESC

        LIMIT 50
        """,
        (rep_id,),
    )

    st.dataframe(
        collection_data,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# REP REPORTS
# =========================================================

elif page == "📊 تقارير المندوب":

    st.markdown(
        "## 📊 تقارير المندوب"
    )

    selected_date = st.date_input(
        "التاريخ",
        date.today(),
    )

    selected_date = selected_date.isoformat()

    report = query(
        """
        SELECT

            o.order_date AS التاريخ,

            c.name AS العميل,

            o.invoice_no AS الفاتورة,

            SUM(oi.qty) AS الكمية

        FROM orders o

        JOIN customers c
            ON c.id = o.customer_id

        JOIN order_items oi
            ON oi.order_id = o.id

        WHERE o.rep_id = ?

        AND o.order_date = ?

        GROUP BY o.id

        ORDER BY o.order_date DESC
        """,
        (
            rep_id,
            selected_date,
        ),
    )

    st.dataframe(
        report,
        use_container_width=True,
        hide_index=True,
    )

    if len(report):

        csv_data = report.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "⬇️ تصدير التقرير",
            csv_data,
            file_name=f"rep_report_{selected_date}.csv",
            mime="text/csv",
        )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

elif page == "🏢 لوحة الإدارة":

    st.markdown(
        "## 🏢 لوحة الإدارة"
    )

    st.markdown(
        '<div class="app-subtitle">'
        "رؤية موحدة للمبيعات والمخزون والزيارات والتحصيل"
        "</div>",
        unsafe_allow_html=True,
    )

    today = date.today().isoformat()

    month = date.today().strftime(
        "%Y-%m"
    )

    reps_count = query(
        """
        SELECT COUNT(*) AS count

        FROM reps

        WHERE active = 1
        """
    )

    customers_count = query(
        """
        SELECT COUNT(*) AS count

        FROM customers

        WHERE active = 1
        """
    )

    visits_count = query(
        """
        SELECT COUNT(*) AS count

        FROM visits

        WHERE visit_date = ?
        """,
        (today,),
    )

    sales_count = query(
        """
        SELECT
            COALESCE(SUM(oi.qty), 0) AS qty

        FROM orders o

        JOIN order_items oi
            ON oi.order_id = o.id

        WHERE substr(
            o.order_date,
            1,
            7
        ) = ?
        """,
        (month,),
    )

    cols = st.columns(4)

    with cols[0]:

        kpi(
            "المندوبون النشطون",
            format_number(
                reps_count.iloc[0]["count"]
            ),
        )

    with cols[1]:

        kpi(
            "العملاء",
            format_number(
                customers_count.iloc[0]["count"]
            ),
        )

    with cols[2]:

        kpi(
            "زيارات اليوم",
            format_number(
                visits_count.iloc[0]["count"]
            ),
        )

    with cols[3]:

        kpi(
            "Sell-in الشهري",
            format_number(
                sales_count.iloc[0]["qty"]
            ),
        )

    st.markdown(
        "### 📊 أداء المندوبين"
    )

    performance = query(
        """
        SELECT

            r.name AS المندوب,

            COALESCE(
                SUM(oi.qty),
                0
            ) AS sell_in,

            COALESCE(

                (
                    SELECT SUM(amount)

                    FROM collections cc

                    WHERE cc.rep_id = r.id

                    AND substr(
                        cc.collection_date,
                        1,
                        7
                    ) = ?

                ),

                0

            ) AS التحصيل

        FROM reps r

        LEFT JOIN orders o
            ON o.rep_id = r.id

            AND substr(
                o.order_date,
                1,
                7
            ) = ?

        LEFT JOIN order_items oi
            ON oi.order_id = o.id

        WHERE r.active = 1

        GROUP BY r.id

        ORDER BY sell_in DESC
        """,
        (
            month,
            month,
        ),
    )

    st.dataframe(
        performance,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# CUSTOMERS AND REPS
# =========================================================

elif page == "👥 العملاء والمندوبون":

    st.markdown(
        "## 👥 العملاء والمندوبون"
    )

    tab_reps, tab_customers = st.tabs(
        [
            "المندوبون",
            "العملاء",
        ]
    )

    # -----------------------------------------------------
    # Reps
    # -----------------------------------------------------

    with tab_reps:

        reps_data = query(
            """
            SELECT
                id,
                name,
                phone,
                active

            FROM reps

            ORDER BY name
            """
        )

        st.dataframe(
            reps_data,
            use_container_width=True,
            hide_index=True,
        )

        with st.form("add_rep"):

            name = st.text_input(
                "اسم المندوب"
            )

            phone = st.text_input(
                "رقم الجوال"
            )

            submitted = st.form_submit_button(
                "إضافة مندوب"
            )

            if submitted:

                if name.strip():

                    execute(
                        """
                        INSERT INTO reps
                        (
                            name,
                            phone
                        )

                        VALUES (?, ?)
                        """,
                        (
                            name,
                            phone,
                        ),
                    )

                    st.success(
                        "تمت إضافة المندوب."
                    )

    # -----------------------------------------------------
    # Customers
    # -----------------------------------------------------

    with tab_customers:

        customers_data = query(
            """
            SELECT

                c.id,

                c.name AS العميل,

                c.area AS المنطقة,

                r.name AS المندوب

            FROM customers c

            LEFT JOIN reps r
                ON r.id = c.rep_id

            ORDER BY c.name
            """
        )

        st.dataframe(
            customers_data,
            use_container_width=True,
            hide_index=True,
        )

        with st.form(
            "add_customer"
        ):

            name = st.text_input(
                "اسم العميل"
            )

            area = st.text_input(
                "المنطقة"
            )

            reps_list = query(
                """
                SELECT *

                FROM reps

                WHERE active = 1

                ORDER BY name
                """
            )

            if len(reps_list):

                rep_name = st.selectbox(
                    "المندوب",
                    reps_list["name"].tolist(),
                )

                submitted = st.form_submit_button(
                    "إضافة عميل"
                )

                if submitted:

                    rep_id_new = int(
                        reps_list.loc[
                            reps_list["name"]
                            == rep_name,
                            "id",
                        ].iloc[0]
                    )

                    execute(
                        """
                        INSERT INTO customers
                        (
                            name,
                            area,
                            rep_id
                        )

                        VALUES (?, ?, ?)
                        """,
                        (
                            name,
                            area,
                            rep_id_new,
                        ),
                    )

                    st.success(
                        "تمت إضافة العميل."
                    )


# =========================================================
# PRODUCTS AND INVENTORY
# =========================================================

elif page == "📦 الأصناف والمخزون":

    st.markdown(
        "## 📦 الأصناف والمخزون"
    )

    products = query(
        """
        SELECT *

        FROM products

        WHERE active = 1

        ORDER BY name
        """
    )

    st.dataframe(
        products,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        "### ➕ إضافة صنف"
    )

    with st.form(
        "add_product"
    ):

        sku = st.text_input(
            "SKU"
        )

        name = st.text_input(
            "اسم الصنف"
        )

        category = st.text_input(
            "التصنيف"
        )

        min_stock = st.number_input(
            "الحد الأدنى للمخزون",
            min_value=0,
            step=1,
        )

        dormant_days = st.number_input(
            "عدد أيام الركود",
            min_value=1,
            value=30,
            step=1,
        )

        submitted = st.form_submit_button(
            "إضافة الصنف"
        )

        if submitted:

            try:

                execute(
                    """
                    INSERT INTO products
                    (
                        sku,
                        name,
                        category,
                        min_stock,
                        dormant_days
                    )

                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        sku,
                        name,
                        category,
                        min_stock,
                        dormant_days,
                    ),
                )

                st.success(
                    "تمت إضافة الصنف."
                )

            except Exception:

                st.error(
                    "تعذر إضافة الصنف. "
                    "تأكد من أن SKU غير مكرر."
                )

    st.markdown(
        "### 📊 مخزون جميع المندوبين"
    )

    all_stock = query(
        """
        SELECT

            r.name AS المندوب,

            p.sku,

            p.name AS الصنف,

            COALESCE(
                rs.qty,
                0
            ) AS الرصيد

        FROM reps r

        CROSS JOIN products p

        LEFT JOIN rep_stock rs

            ON rs.rep_id = r.id

            AND rs.product_id = p.id

        WHERE r.active = 1

        AND p.active = 1

        ORDER BY
            r.name,
            p.name
        """
    )

    st.dataframe(
        all_stock,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# TARGETS
# =========================================================

elif page == "🎯 التارجت والتحصيل":

    st.markdown(
        "## 🎯 التارجت والتحصيل"
    )

    reps_list = query(
        """
        SELECT *

        FROM reps

        WHERE active = 1

        ORDER BY name
        """
    )

    if len(reps_list):

        with st.form(
            "target_form"
        ):

            rep_name = st.selectbox(
                "المندوب",
                reps_list["name"].tolist(),
            )

            selected_rep_id = int(
                reps_list.loc[
                    reps_list["name"]
                    == rep_name,
                    "id",
                ].iloc[0]
            )

            month = st.text_input(
                "الشهر YYYY-MM",
                value=date.today().strftime(
                    "%Y-%m"
                ),
            )

            sales_target = st.number_input(
                "تارجت المبيعات",
                min_value=0.0,
                step=100.0,
            )

            collection_target = st.number_input(
                "تارجت التحصيل",
                min_value=0.0,
                step=100.0,
            )

            submitted = st.form_submit_button(
                "💾 حفظ التارجت"
            )

            if submitted:

                execute(
                    """
                    INSERT INTO targets
                    (
                        rep_id,
                        month,
                        target_sales,
                        target_collection
                    )

                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        selected_rep_id,
                        month,
                        sales_target,
                        collection_target,
                    ),
                )

                st.success(
                    "تم حفظ التارجت."
                )

    targets = query(
        """
        SELECT

            r.name AS المندوب,

            t.month AS الشهر,

            t.target_sales AS تارجت_المبيعات,

            t.target_collection AS تارجت_التحصيل

        FROM targets t

        JOIN reps r
            ON r.id = t.rep_id

        ORDER BY
            t.month DESC,
            r.name
        """
    )

    st.dataframe(
        targets,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# DORMANT PRODUCTS
# =========================================================

elif page == "⚠️ الأصناف الراكدة":

    st.markdown(
        "## ⚠️ الأصناف الراكدة لدى العملاء"
    )

    dormant_days = st.number_input(
        "اعتبر الصنف راكداً بعد عدد أيام",
        min_value=1,
        value=30,
        step=1,
    )

    cutoff = (
        date.today()
        - timedelta(
            days=int(
                dormant_days
            )
        )
    ).isoformat()

    dormant = query(
        """
        WITH latest AS (

            SELECT

                v.customer_id,

                vs.product_id,

                MAX(
                    v.visit_date
                ) AS latest_visit

            FROM visits v

            JOIN visit_stock vs

                ON vs.visit_id = v.id

            GROUP BY
                v.customer_id,
                vs.product_id
        )

        SELECT

            c.name AS العميل,

            p.name AS الصنف,

            latest.latest_visit
                AS آخر_زيارة,

            CAST(

                julianday(?)
                - julianday(
                    latest.latest_visit
                )

                AS INTEGER

            ) AS أيام_منذ_الزيارة

        FROM latest

        JOIN customers c
            ON c.id = latest.customer_id

        JOIN products p
            ON p.id = latest.product_id

        WHERE latest.latest_visit <= ?

        ORDER BY
            أيام_منذ_الزيارة DESC
        """,
        (
            date.today().isoformat(),
            cutoff,
        ),
    )

    if len(dormant):

        st.error(
            f"تم العثور على {len(dormant)} "
            "حالة تحتاج متابعة."
        )

    else:

        st.success(
            "لا توجد أصناف راكدة حسب المدة المحددة."
        )

    st.dataframe(
        dormant,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# ADMIN REPORTS
# =========================================================

elif page == "📥 التقارير والتصدير":

    st.markdown(
        "## 📥 التقارير اليومية والتصدير"
    )

    report_date = st.date_input(
        "تاريخ التقرير",
        date.today(),
    ).isoformat()

    # -----------------------------------------------------
    # Visits
    # -----------------------------------------------------

    visits_report = query(
        """
        SELECT

            v.visit_date AS التاريخ,

            r.name AS المندوب,

            c.name AS العميل,

            v.notes AS الملاحظات

        FROM visits v

        JOIN reps r
            ON r.id = v.rep_id

        JOIN customers c
            ON c.id = v.customer_id

        WHERE v.visit_date = ?

        ORDER BY v.id DESC
        """,
        (report_date,),
    )

    # -----------------------------------------------------
    # Orders
    # -----------------------------------------------------

    orders_report = query(
        """
        SELECT

            o.order_date AS التاريخ,

            r.name AS المندوب,

            c.name AS العميل,

            o.invoice_no AS الفاتورة,

            SUM(
                oi.qty
            ) AS الكمية

        FROM orders o

        JOIN reps r
            ON r.id = o.rep_id

        JOIN customers c
            ON c.id = o.customer_id

        JOIN order_items oi
            ON oi.order_id = o.id

        WHERE o.order_date = ?

        GROUP BY o.id

        ORDER BY o.id DESC
        """,
        (report_date,),
    )

    # -----------------------------------------------------
    # Collections
    # -----------------------------------------------------

    collections_report = query(
        """
        SELECT

            col.collection_date AS التاريخ,

            r.name AS المندوب,

            c.name AS العميل,

            col.amount AS المبلغ,

            col.reference AS المرجع

        FROM collections col

        JOIN reps r
            ON r.id = col.rep_id

        JOIN customers c
            ON c.id = col.customer_id

        WHERE col.collection_date = ?

        ORDER BY col.id DESC
        """,
        (report_date,),
    )

    st.markdown(
        "### 👥 الزيارات"
    )

    st.dataframe(
        visits_report,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        "### 🧾 الأوردرات"
    )

    st.dataframe(
        orders_report,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        "### 💰 التحصيل"
    )

    st.dataframe(
        collections_report,
        use_container_width=True,
        hide_index=True,
    )

    # -----------------------------------------------------
    # Downloads
    # -----------------------------------------------------

    st.markdown(
        "### ⬇️ تحميل التقارير"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.download_button(
            "⬇️ تقرير الزيارات",
            visits_report.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name=f"visits_{report_date}.csv",
            mime="text/csv",
        )

    with col2:

        st.download_button(
            "⬇️ تقرير الأوردرات",
            orders_report.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name=f"orders_{report_date}.csv",
            mime="text/csv",
        )

    with col3:

        st.download_button(
            "⬇️ تقرير التحصيل",
            collections_report.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name=f"collections_{report_date}.csv",
            mime="text/csv",
        )


# =========================================================
# FOOTER
# =========================================================

st.sidebar.markdown("---")

st.sidebar.caption(
    "SalesFlow • Sales & Inventory Management"
)

st.sidebar.caption(
    datetime.now().strftime(
        "%Y-%m-%d %H:%M"
    )
)
