#!/usr/bin/env python3
"""Add the Arabic Board of Directors report sheet to Alfaihaa_Inventory_Audit_Full_Data.xlsx.
Mirrors the 'تقرير المجلس' tab already added to the dashboard artifact — same KPIs,
same per-branch table, same top-8 overstock/slow-moving/savings lists, same 7 recommendations."""
import json
from pathlib import Path
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

HERE = Path(__file__).parent
AUDIT = json.loads((HERE / "alfaihaa_inventory_audit.json").read_text(encoding="utf-8"))
XLSX = HERE / "Alfaihaa_Inventory_Audit_Full_Data.xlsx"
wb = load_workbook(XLSX)

FONT = "Arial"
HEAD_FILL = PatternFill("solid", fgColor="0F6E5C")
HEAD_FONT = Font(name=FONT, size=10, bold=True, color="FFFFFF")
TITLE_FONT = Font(name=FONT, size=16, bold=True, color="0F6E5C")
SUB_FONT = Font(name=FONT, size=10, color="425953")
SECTION_FONT = Font(name=FONT, size=12, bold=True, color="0F6E5C")
NOTE_FONT = Font(name=FONT, size=9, italic=True, color="748D86")
BODY_FONT = Font(name=FONT, size=10.5)
LABEL_FONT = Font(name=FONT, size=9.5, bold=True, color="425953")
VAL_FONT = Font(name=FONT, size=13, bold=True, color="0F6E5C")
VAL_WARN_FONT = Font(name=FONT, size=13, bold=True, color="A8660A")
VAL_CRIT_FONT = Font(name=FONT, size=13, bold=True, color="B3372C")
FOOT_FONT = Font(name=FONT, size=8.5, color="425953")
DATA_FONT = Font(name=FONT, size=10)
BOLD_DATA_FONT = Font(name=FONT, size=10, bold=True)
KPI_FILL = PatternFill("solid", fgColor="F2F6F4")
TOTAL_FILL = PatternFill("solid", fgColor="EEF2F0")
THIN = Side(style="thin", color="D8E0DD")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

RTL = Alignment(horizontal="right", vertical="center", wrap_text=True, readingOrder=2)
RTL_TOP = Alignment(horizontal="right", vertical="top", wrap_text=True, readingOrder=2)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True, readingOrder=2)

MONEY0 = '#,##0;(#,##0);"-"'
MONEY2 = '#,##0.00;(#,##0.00);"-"'
QTY0 = '#,##0;(#,##0);"-"'
PCT1 = '0.0%;(0.0%);"-"'
DATE = 'yyyy-mm-dd'


def fmt0(n):
    if n is None:
        return "—"
    return f"{round(n):,}"


def fmt2(n):
    if n is None:
        return "—"
    return f"{n:,.2f}"


def fmt_sar(n):
    if n is None:
        return "—"
    return f"SAR {fmt0(n)}"


def fmt_pct(n):
    if n is None:
        return "—"
    return f"{n:.1f}%"


kpi = AUDIT["kpi"]
as_of = datetime.fromisoformat(AUDIT["meta"]["as_of"]).strftime("%d %b %Y")

# ---------------------------------------------------------------------------
# Sheet setup
# ---------------------------------------------------------------------------
SHEET_NAME = "تقرير مجلس الإدارة"
if SHEET_NAME in wb.sheetnames:
    del wb[SHEET_NAME]
ws: Worksheet = wb.create_sheet(SHEET_NAME, index=1)
ws.sheet_view.showGridLines = False
ws.sheet_view.rightToLeft = True
ws.column_dimensions["A"].width = 2
for col, w in zip("BCDEFG", [30, 20, 20, 20, 20, 20]):
    ws.column_dimensions[col].width = w

row = 2
ws.cell(row=row, column=2, value="تقرير مجلس الإدارة — أداء المخازن").font = TITLE_FONT
ws.cell(row=row, column=2).alignment = RTL
ws.merge_cells(f"B{row}:G{row}")
row += 1
ws.cell(row=row, column=2,
        value="ملخص تنفيذي وتحليل للأداء بالأرقام والمؤشرات، مع مقترحات عملية — معدّ آليًا من بيانات نظام Cure+ (EXSYS) عبر الفروع الأربعة "
              "(الرياض، بريدة 1، بريدة 2، رفحاء).").font = SUB_FONT
ws.cell(row=row, column=2).alignment = RTL_TOP
ws.merge_cells(f"B{row}:G{row}")
ws.row_dimensions[row].height = 30
row += 1
ws.cell(row=row, column=2, value=f"كما في {as_of}  ·  تقرير Al Faihaa Group — AI Reporting HUB").font = NOTE_FONT
ws.cell(row=row, column=2).alignment = RTL
ws.merge_cells(f"B{row}:G{row}")
row += 2

# ---------------------------------------------------------------------------
# Executive summary
# ---------------------------------------------------------------------------
ws.cell(row=row, column=2, value="الملخص التنفيذي").font = SECTION_FONT
ws.cell(row=row, column=2).alignment = RTL
ws.merge_cells(f"B{row}:G{row}")
row += 1

summary_paras = [
    f"يبلغ إجمالي قيمة المخزون في الفروع الأربعة (الرياض، بريدة 1، بريدة 2، رفحاء) اعتبارًا من {as_of} نحو "
    f"{fmt_sar(kpi['total_inventory_value'])}، موزّعة على {fmt0(kpi['sku_count'])} بند صنف/فرع.",

    f"من هذا الإجمالي: يمثل فائض المخزون (Overstock) ما قيمته {fmt_sar(kpi['overstock_value'])} "
    f"(نحو {fmt_pct(kpi['overstock_pct_of_value'])} من إجمالي القيمة) عبر {fmt0(kpi['overstock_sku_count'])} صنفًا تتجاوز مستويات إعادة "
    f"الطلب المعتمدة؛ وتبلغ قيمة الأصناف بطيئة الحركة / الراكدة {fmt_sar(kpi['slow_moving_value'])} عبر "
    f"{fmt0(kpi['slow_moving_sku_count'])} صنفًا لم يُسجَّل لها أي صرف خلال 90 يومًا فأكثر.",

    f"كما رصد التحليل {fmt0(kpi['past_expiry_on_hand_count'])} صنفًا منتهي الصلاحية ما زال متوفرًا على الرفوف بقيمة "
    f"{fmt_sar(kpi['past_expiry_value'])}، إضافة إلى {fmt0(kpi['expiry_risk_sku_count'])} صنفًا قريب الانتهاء بقيمة "
    f"{fmt_sar(kpi['expiry_risk_value'])}. وعلى صعيد الاستلامات، رصد التحليل {fmt0(kpi['receiving_flag_count'])} إشارة تحقّق على "
    f"استلامات خرجت عن الوسيط التاريخي لتكلفة الصنف، مقابل فرص توفير محتملة تقدَّر بـ {fmt_sar(kpi['price_gap_savings_identified'])} "
    f"ناتجة عن فروقات أسعار نفس الصنف بين الموردين.",
]
for p in summary_paras:
    c = ws.cell(row=row, column=2, value=p)
    c.font = BODY_FONT
    c.alignment = RTL_TOP
    ws.merge_cells(f"B{row}:G{row}")
    ws.row_dimensions[row].height = 46
    row += 1
row += 1

# ---------------------------------------------------------------------------
# KPI cards (as a 6-row table)
# ---------------------------------------------------------------------------
ws.cell(row=row, column=2, value="المؤشرات الرئيسية").font = SECTION_FONT
ws.cell(row=row, column=2).alignment = RTL
ws.merge_cells(f"B{row}:G{row}")
row += 1

kpi_defs = [
    ("إجمالي قيمة المخزون", fmt_sar(kpi["total_inventory_value"]), f"{fmt0(kpi['sku_count'])} بند صنف/فرع", VAL_FONT),
    ("فائض المخزون (Overstock)", fmt_sar(kpi["overstock_value"]),
     f"{fmt0(kpi['overstock_sku_count'])} صنف · {fmt_pct(kpi['overstock_pct_of_value'])} من القيمة", VAL_WARN_FONT),
    ("بطيء الحركة / راكد", fmt_sar(kpi["slow_moving_value"]),
     f"{fmt0(kpi['slow_moving_sku_count'])} صنف بلا صرف 90 يومًا فأكثر", VAL_WARN_FONT),
    ("مخاطر انتهاء الصلاحية", fmt_sar((kpi.get("expiry_risk_value") or 0) + (kpi.get("past_expiry_value") or 0)),
     f"{fmt0(kpi['past_expiry_on_hand_count'])} منتهٍ (SAR {fmt0(kpi['past_expiry_value'])}) · {fmt0(kpi['expiry_risk_sku_count'])} قريب الانتهاء",
     VAL_CRIT_FONT if kpi["past_expiry_on_hand_count"] > 0 else VAL_FONT),
    ("إشارات تحقّق الاستلام", fmt0(kpi["receiving_flag_count"]), "استلامات خارجة عن الوسيط التاريخي للصنف", VAL_FONT),
    ("فرص توفير الأسعار", fmt_sar(kpi["price_gap_savings_identified"]), "من تحليل فجوات أسعار الموردين", VAL_FONT),
]
kpi_start = row
for label, value, foot, val_font in kpi_defs:
    for col in range(2, 8):
        ws.cell(row=row, column=col).fill = KPI_FILL
        ws.cell(row=row, column=col).border = BORDER
    c = ws.cell(row=row, column=2, value=label); c.font = LABEL_FONT; c.alignment = RTL
    c = ws.cell(row=row, column=4, value=value); c.font = val_font; c.alignment = RTL
    ws.merge_cells(f"D{row}:E{row}")
    c = ws.cell(row=row, column=6, value=foot); c.font = FOOT_FONT; c.alignment = RTL_TOP
    ws.merge_cells(f"F{row}:G{row}")
    ws.row_dimensions[row].height = 30
    row += 1
row += 1

# ---------------------------------------------------------------------------
# Branch table
# ---------------------------------------------------------------------------
ws.cell(row=row, column=2, value="القيمة والمخاطر حسب الفرع").font = SECTION_FONT
ws.cell(row=row, column=2).alignment = RTL
ws.merge_cells(f"B{row}:G{row}")
row += 1

branches = ["Riyadh", "Buraydah 1", "Buraydah 2", "Rafha"]
branch_ar = {"Riyadh": "الرياض", "Buraydah 1": "بريدة 1", "Buraydah 2": "بريدة 2", "Rafha": "رفحاء"}
evb = AUDIT.get("expiry_value_by_branch", {"near_expiry": [], "past_expiry": []})
near_by_branch = {r["branch"]: r for r in evb.get("near_expiry", [])}
past_by_branch = {r["branch"]: r for r in evb.get("past_expiry", [])}

branch_stats = []
for b in branches:
    val_rows = [r for r in AUDIT["valuation_by_store"] if r["branch"] == b]
    val = sum(r["total_value"] for r in val_rows)
    skus = sum(r["sku_count"] for r in val_rows)
    ov = [r for r in AUDIT["overstock"] if r["branch"] == b]
    sm = [r for r in AUDIT["slow_moving"] if r["branch"] == b]
    near = near_by_branch.get(b, {"value": 0, "count": 0})
    past = past_by_branch.get(b, {"value": 0, "count": 0})
    branch_stats.append({
        "branch_ar": branch_ar[b], "val": val, "skus": skus,
        "ov_val": sum(r["on_hand_cost"] or 0 for r in ov), "ov_count": len(ov),
        "sm_val": sum(r["on_hand_cost"] or 0 for r in sm), "sm_count": len(sm),
        "exp_val": (near.get("value") or 0) + (past.get("value") or 0),
        "exp_count": (near.get("count") or 0) + (past.get("count") or 0),
    })
totals = {
    "branch_ar": "الإجمالي",
    "val": sum(b["val"] for b in branch_stats), "skus": sum(b["skus"] for b in branch_stats),
    "ov_val": sum(b["ov_val"] for b in branch_stats), "ov_count": sum(b["ov_count"] for b in branch_stats),
    "sm_val": sum(b["sm_val"] for b in branch_stats), "sm_count": sum(b["sm_count"] for b in branch_stats),
    "exp_val": sum(b["exp_val"] for b in branch_stats), "exp_count": sum(b["exp_count"] for b in branch_stats),
}

headers = ["الفرع", "القيمة الإجمالية (SAR)", "عدد الأصناف", "فائض المخزون (SAR)", "عدد أصناف الفائض",
           "بطيء الحركة (SAR)", "عدد الأصناف الراكدة", "مخاطر الصلاحية (SAR)", "عدد أصناف المخاطر"]
# Use columns B..J (9 cols) for this wider table
for col, w in zip("BCDEFGHIJ", [16, 18, 12, 16, 14, 16, 14, 16, 14]):
    ws.column_dimensions[col].width = w
header_row = row
for j, h in enumerate(headers, start=2):
    c = ws.cell(row=header_row, column=j, value=h)
    c.font = HEAD_FONT
    c.fill = HEAD_FILL
    c.alignment = CENTER
    c.border = BORDER
ws.row_dimensions[header_row].height = 30
row += 1

for b in branch_stats + [totals]:
    is_total = b is totals
    fnt = BOLD_DATA_FONT if is_total else DATA_FONT
    vals = [b["branch_ar"], b["val"], b["skus"], b["ov_val"], b["ov_count"], b["sm_val"], b["sm_count"], b["exp_val"], b["exp_count"]]
    fmts = [None, MONEY0, QTY0, MONEY0, QTY0, MONEY0, QTY0, MONEY0, QTY0]
    for j, (v, f) in enumerate(zip(vals, fmts), start=2):
        c = ws.cell(row=row, column=j, value=v)
        c.font = fnt
        c.border = BORDER
        c.alignment = RTL if j == 2 else Alignment(horizontal="center", vertical="center")
        if f:
            c.number_format = f
        if is_total:
            c.fill = TOTAL_FILL
    row += 1
row += 1


def write_data_table(ws, row, title, headers, records, keys, formats, widths, name_col_idx=1):
    ws.cell(row=row, column=2, value=title).font = SECTION_FONT
    ws.cell(row=row, column=2).alignment = RTL
    ws.merge_cells(f"B{row}:G{row}")
    row += 1
    header_row = row
    cols = list("BCDEFGHIJK")[:len(headers)]
    for col, w in zip(cols, widths):
        ws.column_dimensions[col].width = max(ws.column_dimensions[col].width or 0, w)
    for j, h in enumerate(headers, start=2):
        c = ws.cell(row=header_row, column=j, value=h)
        c.font = HEAD_FONT
        c.fill = HEAD_FILL
        c.alignment = CENTER
        c.border = BORDER
    row += 1
    for rec in records:
        for j, (k, fmt) in enumerate(zip(keys, formats), start=2):
            v = rec.get(k)
            c = ws.cell(row=row, column=j, value=v)
            c.font = DATA_FONT
            c.border = BORDER
            if fmt:
                c.number_format = fmt
            idx0 = j - 2
            c.alignment = RTL if idx0 == name_col_idx else Alignment(horizontal="center", vertical="center", wrap_text=True)
        row += 1
    return row + 1


# ---------------------------------------------------------------------------
# Top overstock (8)
# ---------------------------------------------------------------------------
top_overstock = sorted(AUDIT["overstock"], key=lambda r: -(r["on_hand_cost"] or 0))[:8]
for r in top_overstock:
    r["branch_ar"] = branch_ar.get(r["branch"], r["branch"])
row = write_data_table(
    ws, row, "أعلى الأصناف فائضًا في المخزون (Overstock)",
    ["الفرع", "الكود", "الصنف", "الكمية", "القيمة (SAR)", "أيام التغطية"],
    top_overstock, ["branch_ar", "product", "product_name", "on_hand", "on_hand_cost", "days_of_cover"],
    [None, None, None, QTY0, MONEY0, QTY0], [14, 12, 34, 10, 14, 12], name_col_idx=2,
)

# ---------------------------------------------------------------------------
# Top slow-moving (8)
# ---------------------------------------------------------------------------
top_slow = sorted(AUDIT["slow_moving"], key=lambda r: -(r["on_hand_cost"] or 0))[:8]
for r in top_slow:
    r["branch_ar"] = branch_ar.get(r["branch"], r["branch"])
row = write_data_table(
    ws, row, "أعلى الأصناف بطيئة الحركة / الراكدة",
    ["الفرع", "الكود", "الصنف", "القيمة (SAR)", "آخر صرف"],
    top_slow, ["branch_ar", "product", "product_name", "on_hand_cost", "last_out_date"],
    [None, None, None, MONEY0, None], [14, 12, 34, 14, 16], name_col_idx=2,
)

# ---------------------------------------------------------------------------
# Top savings opportunities (8)
# ---------------------------------------------------------------------------
GAP_PCT_FMT = '0.0"%"'
top_savings = sorted(AUDIT["supplier_savings_opportunities"], key=lambda r: -(r["gap_pct"] or 0))[:8]
row = write_data_table(
    ws, row, "أعلى فرص توفير الأسعار بين الموردين",
    ["الكود", "الصنف", "الأرخص", "أقل سعر", "الأغلى", "أعلى سعر", "الفجوة %"],
    top_savings, ["product", "product_name", "cheapest_supplier", "cheapest_price", "priciest_supplier", "priciest_price", "gap_pct"],
    [None, None, None, MONEY2, None, MONEY2, GAP_PCT_FMT], [12, 30, 26, 12, 26, 12, 10], name_col_idx=1,
)

row += 1

# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------
ws.cell(row=row, column=2, value="التوصيات المقترحة").font = SECTION_FONT
ws.cell(row=row, column=2).alignment = RTL
ws.merge_cells(f"B{row}:G{row}")
row += 1

riyadh_ov = next(b for b in branch_stats if b["branch_ar"] == "الرياض")
riyadh_ov_pct = round(riyadh_ov["ov_val"] / kpi["overstock_value"] * 100) if kpi["overstock_value"] else 0

recs = [
    f"مراجعة سياسات إعادة الطلب لمخزن الرياض الرئيسي، الذي يتركز فيه أعلى فائض بقيمة {fmt_sar(riyadh_ov['ov_val'])} عبر "
    f"{fmt0(riyadh_ov['ov_count'])} صنفًا (نحو {riyadh_ov_pct}% من إجمالي قيمة الفائض)، ومنها صنف PROLUTEX 25MG بقيمة SAR 51,197 "
    f"وتغطية تقارب 565 يومًا — يُقترح خفض حدود الحد الأقصى للطلب (Max Qty) أو تحويل الفائض إلى الفروع الأخرى بدلاً من شراء كميات جديدة.",

    f"تقييم الأصناف الراكدة (بلا صرف لـ 90 يومًا فأكثر)، والبالغة قيمتها {fmt_sar(kpi['slow_moving_value'])} عبر "
    f"{fmt0(kpi['slow_moving_sku_count'])} صنفًا؛ أبرزها جهاز HP Color Laser Jet في رفحاء بقيمة SAR 9,684 (لم يُصرف منذ يونيو 2025) "
    f"وآلة الترقيم (Numbering machine) المكررة بين بريدة 1 وبريدة 2 بقيمة إجمالية تفوق SAR 27,500 — يُقترح تحويلها بين الفروع أو "
    f"استبعادها من المخزون النشط، خصوصًا الأصول المعمّرة منها.",

    f"صرف أو إتلاف الأصناف منتهية الصلاحية الموجودة فعليًا على الرفوف ({fmt0(kpi['past_expiry_on_hand_count'])} صنفًا بقيمة "
    f"{fmt_sar(kpi['past_expiry_value'])}، معظمها في الرياض) وفق الإجراء النظامي المعتمد، مع إعطاء أولوية صرف (FEFO) للـ "
    f"{fmt0(kpi['expiry_risk_sku_count'])} صنفًا القريبة من الانتهاء بقيمة {fmt_sar(kpi['expiry_risk_value'])} قبل فوات الأوان.",

    f"توحيد التعاقد مع مورد واحد للأصناف ذات فجوة الأسعار الكبيرة بين الموردين، أبرزها OXYGEN-REGULATOR (فجوة 67.6% بين SAR 110 "
    f"وSAR 339.5) وفحص OCCULT BLOOD TEST (فجوة 62%) — بإجمالي فرصة توفير مقدّرة {fmt_sar(kpi['price_gap_savings_identified'])}، "
    f"قابلة للارتفاع بتوسيع نطاق المقارنة السعرية بين الموردين.",

    f"مراجعة الـ {fmt0(kpi['receiving_flag_count'])} إشارة تحقّق على استلامات خرجت عن الوسيط التاريخي لتكلفة الصنف، للتأكد من دقة "
    f"التسعير عند الاستلام وعدم تكرار أخطاء الإدخال أو فروقات الوحدة/العملة.",

    "اعتماد مراجعة دورية (شهرية أو ربع سنوية) لمؤشرات الفائض والركود على مستوى كل فرع على حدة، بدلاً من الاكتفاء بمراجعة مركزية "
    "سنوية، مع إيلاء اهتمام خاص لفرعي بريدة 2 ورفحاء اللذين يظهران نسب فائض وركود مرتفعة نسبيًا مقارنة بحجم مخزونهما الإجمالي.",

    "اعتماد هذا التقرير كأداة متابعة شهرية لمجلس الإدارة، مع تحديثه آليًا من بيانات نظام Cure+ (EXSYS) لضمان اتخاذ القرار استنادًا "
    "إلى أحدث الأرقام الفعلية بدلاً من تقارير يدوية متأخرة.",
]
for i, r in enumerate(recs, start=1):
    c = ws.cell(row=row, column=2, value=f"{i}. {r}")
    c.font = BODY_FONT
    c.alignment = RTL_TOP
    ws.merge_cells(f"B{row}:K{row}")
    ws.row_dimensions[row].height = 58
    row += 1

row += 1
ws.cell(row=row, column=2,
        value="مصدر البيانات: نظام Cure+ (وصول للقراءة فقط) — وحدة إدارة المخازن EXSYS · تقرير آلي، غير مخصص للتوزيع الخارجي دون مراجعة.").font = NOTE_FONT
ws.cell(row=row, column=2).alignment = RTL
ws.merge_cells(f"B{row}:K{row}")

wb.save(XLSX)
print("Board of Directors (Arabic) sheet added:", SHEET_NAME)
for s in wb.sheetnames:
    print(" -", s, wb[s].sheet_view.rightToLeft, wb[s].dimensions)
