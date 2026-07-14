"""
reports.py
----------
IT Saha Ziyaret Takip Uygulaması - Rapor ve Dışa Aktarım Modülü
Excel (.xlsx) ve PDF formatında rapor üretimi.
"""

import io
import pandas as pd
from datetime import datetime

# ---------------------------------------------------------------------------
# Excel Dışa Aktarım
# ---------------------------------------------------------------------------

def export_to_excel(df: pd.DataFrame, title: str = "Ziyaret Raporu") -> bytes:
    """
    Pandas DataFrame'ini biçimlendirilmiş Excel dosyasına (.xlsx) dönüştürür.
    
    Özellikler:
    - Başlık satırı (koyu mavi arka plan, beyaz yazı)
    - Alternatif satır renklendirmesi (zebra banding)
    - Otomatik sütun genişliği ayarı
    - Tüm kenarlıklar

    Args:
        df    : Dışa aktarılacak veri çerçevesi
        title : Rapor başlığı (sayfa adı olarak da kullanılır)
    
    Returns:
        Excel dosyasının byte içeriği (indirme için)
    """
    from openpyxl import Workbook
    from openpyxl.styles import (
        Font, PatternFill, Alignment, Border, Side, GradientFill
    )
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]  # Sayfa adı max 31 karakter

    # --- Renkler ---
    HEADER_BG   = "1E3A5F"    # Koyu lacivert
    HEADER_FG   = "FFFFFF"    # Beyaz
    ROW_ODD     = "EBF2FA"    # Açık mavi-gri
    ROW_EVEN    = "FFFFFF"    # Beyaz
    BORDER_CLR  = "B8C6D6"    # Gri kenarlık

    # Kenarlık stili
    thin = Side(style="thin", color=BORDER_CLR)
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # --- Rapor Başlık Satırı (1. Satır) ---
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(df.columns))
    title_cell = ws.cell(row=1, column=1)
    title_cell.value = f"🔷 {title}  —  Oluşturulma: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    title_cell.font = Font(name="Calibri", bold=True, size=13, color="FFFFFF")
    title_cell.fill = PatternFill("solid", fgColor="0D2137")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    # --- Sütun Başlıkları (2. Satır) ---
    for col_idx, col_name in enumerate(df.columns, start=1):
        cell = ws.cell(row=2, column=col_idx, value=col_name)
        cell.font      = Font(name="Calibri", bold=True, size=11, color=HEADER_FG)
        cell.fill      = PatternFill("solid", fgColor=HEADER_BG)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border    = border
    ws.row_dimensions[2].height = 22

    # --- Veri Satırları ---
    for row_idx, row_data in enumerate(df.itertuples(index=False), start=3):
        bg_color = ROW_ODD if (row_idx % 2 == 1) else ROW_EVEN
        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.fill      = PatternFill("solid", fgColor=bg_color)
            cell.font      = Font(name="Calibri", size=10)
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border    = border
        ws.row_dimensions[row_idx].height = 18

    # --- Otomatik Sütun Genişliği ---
    for col_idx, col_name in enumerate(df.columns, start=1):
        col_letter = get_column_letter(col_idx)
        max_len = max(
            len(str(col_name)),
            *(len(str(v)) for v in df.iloc[:, col_idx - 1].fillna("").astype(str))
        ) if len(df) > 0 else len(str(col_name))
        # Genişliği sınırlandır: min 12, max 50 karakter
        ws.column_dimensions[col_letter].width = min(50, max(12, max_len + 3))

    # --- Pencereyi dondur (başlık satırları sabit kalsın) ---
    ws.freeze_panes = "A3"

    # Belleğe yaz ve byte döndür
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


# ---------------------------------------------------------------------------
# PDF Dışa Aktarım
# ---------------------------------------------------------------------------

def export_to_pdf(df: pd.DataFrame, title: str = "Ziyaret Raporu") -> bytes:
    """
    Pandas DataFrame'ini biçimlendirilmiş PDF dosyasına dönüştürür.
    
    Özellikler:
    - Şirket başlığı ve rapor tarihi
    - Zebra banding'li tablo
    - Türkçe karakter desteği (ReportLab Helvetica latin1)
    - Otomatik sayfa sonu
    - A4 yatay (landscape) veya dikey

    Args:
        df    : Dışa aktarılacak veri çerçevesi
        title : Rapor başlığı

    Returns:
        PDF dosyasının byte içeriği
    """
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    output = io.BytesIO()

    # Sütun sayısına göre yatay/dikey sayfa seç
    page_size = landscape(A4) if len(df.columns) > 5 else A4
    doc = SimpleDocTemplate(
        output,
        pagesize=page_size,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Özel stil tanımları
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=16,
        textColor=colors.HexColor("#1E3A5F"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#666666"),
        spaceAfter=16,
        alignment=TA_CENTER,
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#999999"),
        spaceBefore=10,
        alignment=TA_CENTER,
    )

    story = []

    # Başlık bölümü
    story.append(Paragraph(_safe_text(title), title_style))
    story.append(Paragraph(
        f"Oluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}  |  Toplam Kayıt: {len(df)}",
        subtitle_style,
    ))
    story.append(Spacer(1, 0.3 * cm))

    # Tablo verisi hazırla
    # Sütun başlıkları
    header_row = [_safe_text(col) for col in df.columns]
    data = [header_row]

    for _, row in df.iterrows():
        data.append([_safe_text(str(v) if pd.notna(v) else "") for v in row])

    # Sayfa genişliğine göre sütun genişliklerini orantıla
    available_width = (landscape(A4)[0] if len(df.columns) > 5 else A4[0]) - 3 * cm
    col_width = available_width / len(df.columns)
    col_widths = [col_width] * len(df.columns)

    # Notlar sütunu varsa ona daha fazla alan ver
    for i, col in enumerate(df.columns):
        if "not" in col.lower() or "açıklama" in col.lower() or "konu" in col.lower():
            col_widths[i] = col_width * 2.0
    # Oranı yeniden normalize et
    scale = available_width / sum(col_widths)
    col_widths = [w * scale for w in col_widths]

    tbl = Table(data, colWidths=col_widths, repeatRows=1)

    # Tablo stili
    tbl_style = TableStyle([
        # Başlık satırı
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#1E3A5F")),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0),  9),
        ("ALIGN",        (0, 0), (-1, 0),  "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUND",(0, 1), (-1, -1), [colors.HexColor("#EBF2FA"), colors.white]),
        # Veri satırları
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 8),
        ("ALIGN",        (0, 1), (-1, -1), "LEFT"),
        # Kenarlıklar
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#B8C6D6")),
        ("LINEBELOW",    (0, 0), (-1, 0),  1.5, colors.HexColor("#1E3A5F")),
        # Satır yüksekliği ve padding
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("WORDWRAP",     (0, 0), (-1, -1), True),
    ])

    # Tek çift satır renklendirme (zebra)
    for row_idx in range(1, len(data)):
        bg = colors.HexColor("#EBF2FA") if row_idx % 2 == 0 else colors.white
        tbl_style.add("BACKGROUND", (0, row_idx), (-1, row_idx), bg)

    tbl.setStyle(tbl_style)
    story.append(tbl)
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "IT Saha Ziyaret ve Takip Otomasyonu — Gizlidir",
        footer_style,
    ))

    doc.build(story)
    return output.getvalue()


def _safe_text(text: str) -> str:
    """
    Türkçe karakterleri PDF için Latin-1 uyumlu hale getirir.
    ReportLab'ın standart fontları UTF-8'i tam desteklemez.
    """
    replacements = {
        "ı": "i", "İ": "I",
        "ğ": "g", "Ğ": "G",
        "ü": "u", "Ü": "U",
        "ş": "s", "Ş": "S",
        "ö": "o", "Ö": "O",
        "ç": "c", "Ç": "C",
    }
    for tr_char, latin_char in replacements.items():
        text = text.replace(tr_char, latin_char)
    return text


def build_dataframe(visits: list[dict]) -> pd.DataFrame:
    """
    Ham ziyaret kayıtları listesini, rapora uygun Türkçe sütun başlıklı
    DataFrame'e dönüştürür.
    
    Args:
        visits: database.get_visits() çıktısı

    Returns:
        Biçimlendirilmiş pandas DataFrame
    """
    if not visits:
        return pd.DataFrame()

    df = pd.DataFrame(visits)

    # Gereksiz dahili sütunları çıkar
    drop_cols = ["id", "created_at"]
    df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)

    # Tarih biçimlendirme
    if "visit_date" in df.columns:
        df["visit_date"] = pd.to_datetime(df["visit_date"]).dt.strftime("%d.%m.%Y")

    # Süre biçimlendirme
    if "duration" in df.columns:
        df["duration"] = df["duration"].apply(lambda x: f"{x:.1f} saat" if x else "—")

    # Sütun adlarını Türkçeye çevir
    col_rename = {
        "visit_date":  "Tarih",
        "company":     "Firma",
        "contact":     "İletişim Kişisi",
        "subject":     "Konu",
        "work_notes":  "Yapılan İşlemler",
        "duration":    "Süre",
        "technician":  "Kategori",
        "status":      "Durum",
    }
    df.rename(columns=col_rename, inplace=True)

    return df
