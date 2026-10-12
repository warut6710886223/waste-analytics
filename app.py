import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from pathlib import Path

# ==================================================
# 1. ตั้งค่าหน้าเว็บไซต์
# ==================================================
st.set_page_config(
    page_title="Waste Analytics Dashboard",
    page_icon="♻️",
    layout="wide"
)

st.title("♻️ Waste Data Analytics Dashboard")
st.caption(
    "แดชบอร์ดวิเคราะห์ปริมาณขยะและการใช้ประโยชน์ "
    "จำแนกตามเดือน สังกัด และหน่วยงาน"
)

# ==================================================
# 2. อ่านไฟล์ Excel จาก Repository
# ==================================================
DATA_FILE = Path(_file_).parent / "data.xlsx"

if not DATA_FILE.exists():
    st.error(
        "ไม่พบไฟล์ data.xlsx กรุณาอัปโหลดไฟล์นี้ไว้ใน "
        "Repository เดียวกับ app.py"
    )
    st.stop()

try:
    df = pd.read_excel(DATA_FILE)
except Exception as e:
    st.error(f"อ่านไฟล์ Excel ไม่สำเร็จ: {e}")
    st.stop()

# ตรวจสอบชื่อคอลัมน์
df.columns = df.columns.astype(str).str.strip()

required_columns = [
    "ปี",
    "สังกัด",
    "หน่วยงาน",
    "เดือน",
    "คนเฉลี่ย",
    "วันทำงาน",
    "โฟมบรรจุอาหาร (ใบ)",
    "ขยะที่เกิดขึ้น (กก.)",
    "ใช้ประโยชน์ (กก.)",
    "ขยะที่ส่งกำจัด (กก.)",
    "ร้อยละส่งกำจัดลดลง"
]

missing_columns = [
    c for c in required_columns if c not in df.columns
]

if missing_columns:
    st.error(
        "คอลัมน์ในไฟล์ไม่ตรงกับที่ระบบต้องการ: "
        + ", ".join(missing_columns)
    )
    st.stop()

# แปลงคอลัมน์ตัวเลขให้เป็นตัวเลข
numeric_columns = [
    "ปี",
    "คนเฉลี่ย",
    "วันทำงาน",
    "โฟมบรรจุอาหาร (ใบ)",
    "ขยะที่เกิดขึ้น (กก.)",
    "ใช้ประโยชน์ (กก.)",
    "ขยะที่ส่งกำจัด (กก.)",
    "ร้อยละส่งกำจัดลดลง"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# ลบช่องว่างจากข้อความ
for col in ["สังกัด", "หน่วยงาน", "เดือน"]:
    df[col] = df[col].astype("string").str.strip()

df = df.dropna(subset=[
    "ปี", "สังกัด", "หน่วยงาน", "เดือน"
])

month_order = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน",
    "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
    "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]

month_short = {
    "มกราคม": "ม.ค.",
    "กุมภาพันธ์": "ก.พ.",
    "มีนาคม": "มี.ค.",
    "เมษายน": "เม.ย.",
    "พฤษภาคม": "พ.ค.",
    "มิถุนายน": "มิ.ย.",
    "กรกฎาคม": "ก.ค.",
    "สิงหาคม": "ส.ค.",
    "กันยายน": "ก.ย.",
    "ตุลาคม": "ต.ค.",
    "พฤศจิกายน": "พ.ย.",
    "ธันวาคม": "ธ.ค."
}

# ==================================================
# 3. แถบตัวกรองด้านซ้าย
# ==================================================
st.sidebar.header("🔎 ตัวกรองข้อมูล")

years = sorted(df["ปี"].dropna().unique().tolist())
selected_years = st.sidebar.multiselect(
    "เลือกปี พ.ศ.",
    years,
    default=years
)

affiliations = sorted(
    df["สังกัด"].dropna().unique().tolist()
)
selected_affiliations = st.sidebar.multiselect(
    "เลือกสังกัด",
    affiliations,
    default=affiliations
)

agencies = sorted(
    df["หน่วยงาน"].dropna().unique().tolist()
)
selected_agencies = st.sidebar.multiselect(
    "เลือกหน่วยงาน",
    agencies,
    default=agencies
)

months = [m for m in month_order if m in df["เดือน"].unique()]
months += sorted(
    set(df["เดือน"].dropna().tolist()) - set(month_order)
)

selected_months = st.sidebar.multiselect(
    "เลือกเดือน",
    months,
    default=months
)

filtered = df[
    df["ปี"].isin(selected_years)
    & df["สังกัด"].isin(selected_affiliations)
    & df["หน่วยงาน"].isin(selected_agencies)
    & df["เดือน"].isin(selected_months)
].copy()

st.sidebar.caption(
    f"ข้อมูลหลังกรอง {len(filtered):,} รายการ"
)

if filtered.empty:
    st.warning("ไม่พบข้อมูลตามตัวกรอง กรุณาเลือกเงื่อนไขใหม่")
    st.stop()

# ==================================================
# 4. KPI ภาพรวม
# ==================================================
generated = filtered["ขยะที่เกิดขึ้น (กก.)"].sum()
reused = filtered["ใช้ประโยชน์ (กก.)"].sum()
disposed = filtered["ขยะที่ส่งกำจัด (กก.)"].sum()

reuse_pct = reused / generated * 100 if generated else 0
dispose_pct = disposed / generated * 100 if generated else 0

st.subheader("📌 ภาพรวมข้อมูลที่เลือก")

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "ขยะที่เกิดขึ้น",
    f"{generated:,.2f} กก."
)

k2.metric(
    "ขยะที่ใช้ประโยชน์",
    f"{reused:,.2f} กก.",
    f"{reuse_pct:.2f}% ของขยะที่เกิดขึ้น"
)

k3.metric(
    "ขยะที่ส่งกำจัด",
    f"{disposed:,.2f} กก.",
    f"{dispose_pct:.2f}% ของขยะที่เกิดขึ้น"
)

k4.metric(
    "จำนวนรายการ",
    f"{len(filtered):,}"
)

st.caption(
    "หมายเหตุ: เปอร์เซ็นต์ใช้ประโยชน์และส่งกำจัดด้านบน "
    "คำนวณจากยอดรวมของแต่ละคอลัมน์หารด้วยยอดขยะที่เกิดขึ้น "
    "ไม่ใช่ค่าจากคอลัมน์ร้อยละส่งกำจัดลดลง"
)

# ==================================================
# 5. ปริมาณขยะรายเดือน
# ==================================================
st.subheader("📈 ปริมาณขยะรายเดือน")

monthly = (
    filtered.groupby("เดือน", as_index=False)
    .agg({
        "ขยะที่เกิดขึ้น (กก.)": "sum",
        "ใช้ประโยชน์ (กก.)": "sum",
        "ขยะที่ส่งกำจัด (กก.)": "sum"
    })
)

monthly["ลำดับเดือน"] = monthly["เดือน"].map(
    {m: i for i, m in enumerate(month_order)}
)
monthly = monthly.sort_values("ลำดับเดือน")
monthly["เดือนย่อ"] = monthly["เดือน"].map(month_short).fillna(
    monthly["เดือน"]
)

monthly_long = monthly.melt(
    id_vars=["เดือน", "เดือนย่อ", "ลำดับเดือน"],
    value_vars=[
        "ขยะที่เกิดขึ้น (กก.)",
        "ใช้ประโยชน์ (กก.)",
        "ขยะที่ส่งกำจัด (กก.)"
    ],
    var_name="ประเภทข้อมูล",
    value_name="ปริมาณ (กก.)"
)

fig_month = px.line(
    monthly_long,
    x="เดือนย่อ",
    y="ปริมาณ (กก.)",
    color="ประเภทข้อมูล",
    markers=True,
    category_orders={
        "เดือนย่อ": [
            month_short.get(m, m) for m in months
        ]
    },
    title="แนวโน้มขยะที่เกิดขึ้น ใช้ประโยชน์ และส่งกำจัด"
)

fig_month.update_layout(
    template="plotly_white",
    xaxis_title="เดือน",
    yaxis_title="ปริมาณ (กก.)",
    legend_title="ประเภทข้อมูล"
)

st.plotly_chart(fig_month, use_container_width=True)

# ==================================================
# 6. เปรียบเทียบสังกัด
# ==================================================
st.subheader("🏢 เปรียบเทียบปริมาณขยะตามสังกัด")

by_affiliation = (
    filtered.groupby("สังกัด", as_index=False)
    .agg({
        "ขยะที่เกิดขึ้น (กก.)": "sum",
        "ใช้ประโยชน์ (กก.)": "sum",
        "ขยะที่ส่งกำจัด (กก.)": "sum"
    })
)

affiliation_long = by_affiliation.melt(
    id_vars="สังกัด",
    var_name="ประเภทข้อมูล",
    value_name="ปริมาณ (กก.)"
)

fig_aff = px.bar(
    affiliation_long,
    x="สังกัด",
    y="ปริมาณ (กก.)",
    color="ประเภทข้อมูล",
    barmode="group",
    title="เปรียบเทียบยอดรวมตามสังกัด"
)

fig_aff.update_layout(template="plotly_white")
st.plotly_chart(fig_aff, use_container_width=True)

# ==================================================
# 7. จัดอันดับหน่วยงาน
# ==================================================
st.subheader("🏆 จัดอันดับหน่วยงาน")

rank_metric = st.selectbox(
    "เลือกตัวชี้วัดสำหรับจัดอันดับ",
    [
        "ขยะที่เกิดขึ้น (กก.)",
        "ใช้ประโยชน์ (กก.)",
        "ขยะที่ส่งกำจัด (กก.)",
        "คนเฉลี่ย",
        "โฟมบรรจุอาหาร (ใบ)"
    ]
)

top_n = st.slider(
    "จำนวนหน่วยงานที่แสดง",
    min_value=5,
    max_value=20,
    value=10
)

ranking = (
    filtered.groupby("หน่วยงาน", as_index=False)[rank_metric]
    .sum()
    .sort_values(rank_metric, ascending=False)
    .head(top_n)
)

fig_rank = px.bar(
    ranking.sort_values(rank_metric),
    x=rank_metric,
    y="หน่วยงาน",
    orientation="h",
    title=f"Top {top_n} หน่วยงานตาม {rank_metric}"
)

fig_rank.update_layout(
    template="plotly_white",
    yaxis_title="หน่วยงาน",
    xaxis_title=rank_metric
)

st.plotly_chart(fig_rank, use_container_width=True)
st.dataframe(ranking, use_container_width=True)

# ==================================================
# 8. เปรียบเทียบการใช้ประโยชน์และการส่งกำจัด
# ==================================================
st.subheader("♻️ การใช้ประโยชน์เทียบกับการส่งกำจัด")

utilization = pd.DataFrame({
    "ประเภท": ["ใช้ประโยชน์", "ส่งกำจัด"],
    "ปริมาณ (กก.)": [reused, disposed]
})

fig_util = px.pie(
    utilization,
    names="ประเภท",
    values="ปริมาณ (กก.)",
    hole=0.55,
    title="สัดส่วนระหว่างการใช้ประโยชน์และการส่งกำจัด"
)

fig_util.update_layout(template="plotly_white")
st.plotly_chart(fig_util, use_container_width=True)

# ==================================================
# 9. วิเคราะห์ร้อยละส่งกำจัดลดลง
# ==================================================
st.subheader("📉 ร้อยละส่งกำจัดลดลงตามข้อมูลต้นทาง")

rate = (
    filtered.groupby("หน่วยงาน", as_index=False)
    ["ร้อยละส่งกำจัดลดลง"]
    .mean()
    .sort_values("ร้อยละส่งกำจัดลดลง", ascending=False)
)

fig_rate = px.bar(
    rate.head(10).sort_values("ร้อยละส่งกำจัดลดลง"),
    x="ร้อยละส่งกำจัดลดลง",
    y="หน่วยงาน",
    orientation="h",
    title="10 หน่วยงานที่มีค่าเฉลี่ยร้อยละส่งกำจัดลดลงสูงสุด"
)

fig_rate.update_layout(template="plotly_white")
st.plotly_chart(fig_rate, use_container_width=True)

st.caption(
    "กราฟนี้แสดงค่าเฉลี่ยของคอลัมน์ต้นทาง "
    "ไม่ได้คำนวณสูตรการลดลงใหม่"
)

# ==================================================
# 10. ตารางข้อมูลที่ผ่านการกรอง
# ==================================================
st.subheader("📋 ตารางข้อมูล")

st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True
)

# ==================================================
# 11. ดาวน์โหลดผลลัพธ์
# ==================================================
output = BytesIO()

with pd.ExcelWriter(output, engine="openpyxl") as writer:
    filtered.to_excel(
        writer,
        sheet_name="FilteredData",
        index=False
    )

    monthly.to_excel(
        writer,
        sheet_name="MonthlySummary",
        index=False
    )

    by_affiliation.to_excel(
        writer,
        sheet_name="AffiliationSummary",
        index=False
    )

    ranking.to_excel(
        writer,
        sheet_name="AgencyRanking",
        index=False
    )

st.download_button(
    "⬇️ ดาวน์โหลดข้อมูลและผลสรุปเป็น Excel",
    data=output.getvalue(),
    file_name="waste_analysis_result.xlsx",
    mime=(
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    )
)

st.divider()
st.caption(
    "Waste Data Analytics Dashboard | "
    "Python • Pandas • Streamlit • Plotly"
)
