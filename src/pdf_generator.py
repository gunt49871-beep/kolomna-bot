import io
import os
import logging

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

W, H = A4
LM = 72       # left margin ~25mm
RM = W - 43   # right margin ~15mm

FONT_PATHS = [
    os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu-sans/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]
BOLD_PATHS = [
    os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu-sans/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]

_FONT = "Helvetica"
_FONT_B = "Helvetica-Bold"
_fonts_inited = False


def _init_fonts():
    global _FONT, _FONT_B, _fonts_inited
    if _fonts_inited:
        return
    for p in FONT_PATHS:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont("DJ", p))
                _FONT = "DJ"
                logger.info("PDF font loaded: %s", p)
                break
            except Exception as e:
                logger.warning("Font %s failed: %s", p, e)
    for p in BOLD_PATHS:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont("DJB", p))
                _FONT_B = "DJB"
                break
            except Exception as e:
                logger.warning("Bold font %s failed: %s", p, e)
    _fonts_inited = True


# ── Drawing helpers ─────────────────────────────────────────────────────────

def _t(c, x, y, text, size=11, bold=False):
    c.setFont(_FONT_B if bold else _FONT, size)
    c.drawString(x, y, text)


def _tc(c, y, text, size=14, bold=True):
    c.setFont(_FONT_B if bold else _FONT, size)
    c.drawCentredString(W / 2, y, text)


def _ul(c, y, x1=None, x2=None):
    c.setLineWidth(0.4)
    c.line(x1 or LM, y, x2 or RM, y)


def _new_canvas():
    _init_fonts()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    return c, buf


def _addressee_block(c, y, to_lines, from_label="от"):
    """Draws top-right 'To / From' block, returns updated y."""
    rx = W / 2 + 20
    for line in to_lines:
        _t(c, rx, y, line, 10)
        y -= 14
    y -= 6
    _t(c, rx, y, from_label, 10)
    y -= 14
    _ul(c, y, rx, RM)
    y -= 5
    _t(c, rx, y, "(ФИО полностью)", 8)
    y -= 18
    _ul(c, y, rx, RM)
    y -= 5
    _t(c, rx, y, "(адрес регистрации)", 8)
    y -= 18
    _ul(c, y, rx, RM)
    y -= 5
    _t(c, rx, y, "(контактный телефон)", 8)
    y -= 14
    return y


def _sign_block(c, y):
    """Date + signature line."""
    y -= 20
    _t(c, LM, y, '«___» ____________ 20___ г.', 11)
    _t(c, W / 2 + 20, y, "Подпись:", 11)
    _ul(c, y, W / 2 + 75, RM)
    y -= 5
    _t(c, W / 2 + 75, y, "(подпись / расшифровка)", 8)
    return y


# ── Form generators ──────────────────────────────────────────────────────────

def gen_fz59() -> io.BytesIO:
    """Обращение гражданина по ФЗ-59."""
    c, buf = _new_canvas()
    y = H - 57

    y = _addressee_block(c, y, [
        "Главе городского округа Коломна",
        "Московской области",
        "___________________________",
    ])
    y -= 20

    _tc(c, y, "ОБРАЩЕНИЕ", 14, bold=True)
    y -= 16
    _tc(c, y, "(жалоба / предложение / запрос информации)", 9, bold=False)
    y -= 30

    _t(c, LM, y, "Прошу рассмотреть следующее обращение:", 11)
    y -= 20
    for _ in range(8):
        _ul(c, y)
        y -= 18
    y -= 10

    _t(c, LM, y, "Прошу направить ответ:", 11)
    y -= 18
    _t(c, LM, y, "□  почтой по адресу:", 11)
    _ul(c, y, LM + 130, RM)
    y -= 18
    _t(c, LM, y, "□  на электронный адрес:", 11)
    _ul(c, y, LM + 155, RM)
    y -= 28
    _t(c, LM, y, "Ответ прошу подготовить в срок, установленный ФЗ №59-ФЗ от 02.05.2006 (30 дней).", 9)
    y -= 28

    _sign_block(c, y)
    c.save()
    buf.seek(0)
    return buf


def gen_land_request() -> io.BytesIO:
    """Заявление о предоставлении земельного участка."""
    c, buf = _new_canvas()
    y = H - 57

    y = _addressee_block(c, y, [
        "В Комитет по управлению имуществом",
        "городского округа Коломна",
        "Московской области",
    ])
    y -= 6
    _t(c, W / 2 + 20, y, "Паспорт: серия _______ № ______________", 9)
    y -= 13
    _t(c, W / 2 + 20, y, "выдан: ________________________________", 9)
    y -= 20

    _tc(c, y, "ЗАЯВЛЕНИЕ", 14, bold=True)
    y -= 16
    _tc(c, y, "о предоставлении земельного участка", 11, bold=False)
    y -= 30

    _t(c, LM, y, "Прошу предоставить земельный участок, расположенный по адресу:", 11)
    y -= 18
    _ul(c, y)
    y -= 18
    _t(c, LM, y, "Кадастровый номер (при наличии):", 11)
    _ul(c, y, LM + 200, RM)
    y -= 18
    _t(c, LM, y, "Площадь: _________________ кв.м", 11)
    y -= 18
    _t(c, LM, y, "Цель использования:", 11)
    _ul(c, y, LM + 120, RM)
    y -= 18
    _t(c, LM, y, "Вид права:", 11)
    _t(c, LM + 72, y, "□  аренда     □  безвозмездное пользование     □  собственность", 11)
    y -= 18
    _t(c, LM, y, "Основание предоставления:", 11)
    _ul(c, y, LM + 160, RM)
    y -= 25

    _t(c, LM, y, "Прилагаемые документы:", 11, bold=True)
    y -= 16
    for doc in [
        "□  Копия паспорта (разворот + регистрация)",
        "□  Схема расположения участка на кадастровом плане территории",
        "□  Правоустанавливающие документы на строения (при наличии)",
        "□  Иные документы: _____________________________________________",
    ]:
        _t(c, LM + 10, y, doc, 10)
        y -= 15
    y -= 10

    _sign_block(c, y)
    c.save()
    buf.seek(0)
    return buf


def gen_nto_request() -> io.BytesIO:
    """Заявление на включение в схему НТО."""
    c, buf = _new_canvas()
    y = H - 57

    # Custom addressee block for legal entity
    rx = W / 2 + 20
    for line in ["В Администрацию городского округа Коломна", "(Комитет по экономическому развитию)"]:
        _t(c, rx, y, line, 10)
        y -= 14
    y -= 6
    _t(c, rx, y, "от:", 10)
    y -= 14
    _ul(c, y, rx, RM)
    y -= 5
    _t(c, rx, y, "(наименование ИП / организации)", 8)
    y -= 18
    _ul(c, y, rx, RM)
    y -= 5
    _t(c, rx, y, "(ИНН / ОГРН)", 8)
    y -= 18
    _ul(c, y, rx, RM)
    y -= 5
    _t(c, rx, y, "(адрес, телефон)", 8)
    y -= 20

    _tc(c, y, "ЗАЯВЛЕНИЕ", 14, bold=True)
    y -= 16
    _tc(c, y, "о включении в схему размещения нестационарных торговых объектов", 11, bold=False)
    y -= 30

    _t(c, LM, y, "Прошу включить в схему размещения НТО следующий объект:", 11)
    y -= 20
    _t(c, LM, y, "Тип НТО:", 11)
    _t(c, LM + 58, y, "□  киоск     □  павильон     □  лоток     □  иное: _______________", 11)
    y -= 18
    _t(c, LM, y, "Адрес размещения:", 11)
    _ul(c, y, LM + 115, RM)
    y -= 18
    _t(c, LM, y, "Площадь НТО: _________________ кв.м", 11)
    y -= 18
    _t(c, LM, y, "Вид торговли:", 11)
    _ul(c, y, LM + 85, RM)
    y -= 18
    _t(c, LM, y, "Период размещения: с __________________ по __________________", 11)
    y -= 25

    _t(c, LM, y, "Прилагаемые документы:", 11, bold=True)
    y -= 16
    for doc in [
        "□  Свидетельство о регистрации ИП / ООО (копия)",
        "□  Схема размещения объекта НТО",
        "□  Фотографии места предполагаемого размещения",
        "□  Копия документа на объект НТО (при наличии)",
        "□  Иные документы: _____________________________________________",
    ]:
        _t(c, LM + 10, y, doc, 10)
        y -= 15
    y -= 12

    _t(c, LM, y, "Руководитель / ИП:", 11)
    _ul(c, y, LM + 120, W / 2 + 60)
    _t(c, W / 2 + 65, y, "М.П.", 11)
    _sign_block(c, y)
    c.save()
    buf.seek(0)
    return buf


def gen_resettlement_request() -> io.BytesIO:
    """Заявление о признании жилья аварийным и расселении."""
    c, buf = _new_canvas()
    y = H - 57

    y = _addressee_block(c, y, [
        "В Межведомственную комиссию",
        "Администрации городского округа Коломна",
        "Московской области",
    ])
    y -= 20

    _tc(c, y, "ЗАЯВЛЕНИЕ", 14, bold=True)
    y -= 16
    _tc(c, y, "о признании жилого помещения непригодным для проживания", 11, bold=False)
    y -= 30

    _t(c, LM, y, "Я проживаю по адресу:", 11)
    _ul(c, y, LM + 135, RM)
    y -= 18
    _t(c, LM, y, "Право на жилое помещение:", 11)
    _t(c, LM + 163, y, "□  собственник          □  наниматель", 11)
    y -= 18
    _t(c, LM, y, "Документ на жильё:", 11)
    _ul(c, y, LM + 118, RM)
    y -= 20

    _t(c, LM, y, "Прошу провести обследование и признать жилое помещение непригодным", 11)
    y -= 14
    _t(c, LM, y, "для проживания в связи со следующими техническими неисправностями:", 11)
    y -= 20
    for _ in range(4):
        _ul(c, y)
        y -= 18
    y -= 10

    _t(c, LM, y, "Прошу включить в программу переселения из аварийного жилищного фонда.", 11)
    y -= 18
    _t(c, LM, y, "Количество проживающих: __________ чел.", 11)
    y -= 25

    _t(c, LM, y, "Прилагаемые документы:", 11, bold=True)
    y -= 16
    for doc in [
        "□  Копия паспорта(ов) всех проживающих",
        "□  Документ о праве пользования помещением (свидетельство / договор найма)",
        "□  Технический паспорт помещения",
        "□  Заключение о техническом состоянии конструкций (при наличии)",
        "□  Акты осмотра жилья / фотографии (при наличии)",
        "□  Иные документы: _____________________________________________",
    ]:
        _t(c, LM + 10, y, doc, 10)
        y -= 15
    y -= 10

    _sign_block(c, y)
    c.save()
    buf.seek(0)
    return buf


# ── Public API ───────────────────────────────────────────────────────────────

PDF_TYPES = {
    "fz59": ("Обращение_ФЗ-59", gen_fz59),
    "land": ("Заявление_на_ЗУ", gen_land_request),
    "nto": ("Заявление_на_НТО", gen_nto_request),
    "resettlement": ("Заявление_о_расселении", gen_resettlement_request),
}


def generate_pdf(pdf_type: str) -> tuple[io.BytesIO, str]:
    """Returns (pdf_bytes, filename). Raises KeyError for unknown type."""
    label, func = PDF_TYPES[pdf_type]
    return func(), f"Образец_{label}.pdf"
