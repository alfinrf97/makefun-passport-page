# Passport spread generator — draws an invented passport spread with code.
# Three fictional countries (Kalandra / Veyrland / Aldermere), one shared
# layout engine, per-country config for emblem, portrait, stamps, visas and
# the telling paperwork detail. Deterministic: no clock, no network, the
# only randomness is random.Random(1234) used for desk noise.
# Run: python3 compose.py  -> writes variant-a.png / variant-b.png /
# variant-c.png (1024x1024) next to this file.
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
W = H = 1024

F_SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
F_SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
F_SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
F_SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
F_SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
F_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
F_MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def txt(d, xy, s, f, fill, anchor="la"):
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def wrap(d, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- MRZ (ICAO 9303)
_MRZ_W = (7, 3, 1)


def _mrz_val(ch):
    if ch == "<":
        return 0
    if ch.isdigit():
        return int(ch)
    return ord(ch) - 55


def mrz_check(s):
    total = 0
    for i, ch in enumerate(s):
        total += _mrz_val(ch) * _MRZ_W[i % 3]
    return str(total % 10)


def mrz_lines(cfg):
    def pad(s, n):
        return (s + "<" * n)[:n]

    surname = cfg["surname"].upper().replace(" ", "<")
    given = cfg["given"].upper().replace(" ", "<")
    line1 = pad("P<" + cfg["code"] + surname + "<<" + given, 44)
    doc = pad(cfg["number"], 9)
    dob = cfg["dob_mrz"]
    exp = cfg["exp_mrz"]
    personal = "<" * 14
    line2 = (
        doc + mrz_check(doc)
        + cfg["code"]
        + dob + mrz_check(dob)
        + cfg["sex"]
        + exp + mrz_check(exp)
        + personal + mrz_check(personal)
    )
    comp = mrz_check(line2[0:10] + line2[13:20] + line2[21:28] + line2[28:43])
    line2 = line2 + comp
    assert len(line1) == 44 and len(line2) == 44, (line1, line2)
    return line1, line2


# ---------------------------------------------------------------- guilloche
def guilloche(base, box, ink=(120, 105, 70), alpha=42):
    x0, y0, x1, y1 = box
    ov = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    w, h = x1 - x0, y1 - y0
    for k in range(0, h, 9):
        pts = []
        for x in range(0, w + 1, 8):
            y = k + 2.2 * math.sin((x + k * 3.1) / 26.0)
            pts.append((x, y))
        od.line(pts, fill=ink + (alpha,), width=1)
    for k in range(0, w, 11):
        pts = []
        for y in range(0, h + 1, 8):
            x = k + 2.0 * math.sin((y + k * 2.7) / 24.0)
            pts.append((x, y))
        od.line(pts, fill=ink + (alpha,), width=1)
    base.alpha_composite(ov, (x0, y0))


# ---------------------------------------------------------------- desk + spread
def desk():
    img = Image.new("RGB", (W, H), (38, 41, 47))
    d = ImageDraw.Draw(img)
    rnd = random.Random(1234)
    for _ in range(9000):
        x = rnd.randint(0, W - 1)
        y = rnd.randint(0, H - 1)
        v = rnd.randint(-7, 7)
        d.point((x, y), fill=(38 + v, 41 + v, 47 + v))
    # soft vignette: dark translucent frame
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i in range(36):
        a = int(2.6 * i)
        od.rectangle([i, i, W - 1 - i, H - 1 - i], outline=(0, 0, 0, a))
    img = Image.alpha_composite(img.convert("RGBA"), ov)
    return img


def spread_shadow(img):
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([40, 176, 1000, 876], radius=6, fill=(0, 0, 0, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    img.alpha_composite(sh)


# ---------------------------------------------------------------- emblems
def emblem(d, cx, cy, r, kind, ink):
    # shield outline
    pts = [(cx - r, cy - r * 0.7), (cx + r, cy - r * 0.7),
           (cx + r, cy + r * 0.1),
           (cx, cy + r), (cx - r, cy + r * 0.1)]
    d.polygon(pts, outline=ink, width=3)
    d.line([(cx - r, cy - r * 0.7), (cx + r, cy - r * 0.7)], fill=ink, width=2)
    if kind == "sun_waves":
        d.ellipse([cx - 11, cy - 22, cx + 11, cy], fill=ink)
        for j, yy in enumerate((2, 10, 18)):
            d.arc([cx - 24, cy + yy, cx + 24, cy + yy + 16], 200, 340,
                  fill=ink, width=2)
    elif kind == "mountain_star":
        d.polygon([(cx - 24, cy + 16), (cx - 8, cy - 18), (cx + 2, cy + 2),
                   (cx + 10, cy - 12), (cx + 24, cy + 16)], outline=ink, width=2)
        d.polygon([(cx - 24, cy + 16), (cx + 24, cy + 16),
                   (cx + 24, cy + 22), (cx - 24, cy + 22)], fill=ink)
        d.regular_polygon((cx, cy - 30, 6), 6, 0, fill=ink)
    elif kind == "lighthouse":
        d.polygon([(cx - 7, cy - 24), (cx + 7, cy - 24), (cx + 5, cy + 14),
                   (cx - 5, cy + 14)], fill=ink)
        d.rectangle([cx - 9, cy - 30, cx + 9, cy - 24], fill=ink)
        d.line([(cx - 26, cy - 27), (cx - 10, cy - 27)], fill=ink, width=2)
        d.line([(cx + 10, cy - 27), (cx + 26, cy - 27)], fill=ink, width=2)
        for yy in (18, 24):
            d.arc([cx - 24, cy + yy - 6, cx + 24, cy + yy + 6], 200, 340,
                  fill=ink, width=2)
    # laurel: two small sprigs flanking the shield base
    for sgn in (-1, 1):
        for j in range(3):
            x = cx + sgn * (r + 6)
            y = cy + r * 0.55 + j * 7
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=ink)


# ---------------------------------------------------------------- portrait
def portrait(cfg):
    w, h = 170, 225
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # photo background: soft vertical gradient + faint arcs
    for y in range(h):
        t = y / h
        c = tuple(int(a + (b - a) * t) for a, b in
                  zip(cfg["photo_bg"][0], cfg["photo_bg"][1]))
        d.line([(0, y), (w, y)], fill=c + (255,))
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for k in range(0, h, 12):
        od.arc([-40, k - 30, w + 40, k + 90], 200, 340, fill=(90, 100, 110, 40))
    img.alpha_composite(ov)
    d = ImageDraw.Draw(img)
    skin = cfg["skin"]
    hair = cfg["hair"]
    jacket = cfg["jacket"]
    cx = w // 2
    # shoulders / jacket
    d.polygon([(cx - 78, h), (cx - 62, 168), (cx - 30, 152),
               (cx + 30, 152), (cx + 62, 168), (cx + 78, h)], fill=jacket + (255,))
    d.polygon([(cx - 14, 152), (cx, 176), (cx + 14, 152), (cx + 8, 148),
               (cx - 8, 148)], fill=(235, 232, 225, 255))  # shirt V
    # neck
    d.rectangle([cx - 13, 128, cx + 13, 156], fill=skin + (255,))
    d.polygon([(cx - 13, 128), (cx + 13, 128), (cx + 20, 150),
               (cx - 20, 150)], fill=tuple(int(c * 0.88) for c in skin) + (255,))
    # head
    d.ellipse([cx - 34, 52, cx + 34, 128], fill=skin + (255,))
    # ears
    d.ellipse([cx - 40, 84, cx - 31, 104], fill=skin + (255,))
    d.ellipse([cx + 31, 84, cx + 40, 104], fill=skin + (255,))
    # hair per style
    if cfg["hair_style"] == "curly":
        d.pieslice([cx - 40, 30, cx + 40, 92], 180, 360, fill=hair + (255,))
        for dx in (-34, -20, -6, 8, 22, 34):
            d.ellipse([cx + dx - 9, 66, cx + dx + 9, 84], fill=hair + (255,))
        d.ellipse([cx - 40, 56, cx - 26, 100], fill=hair + (255,))
        d.ellipse([cx + 26, 56, cx + 40, 100], fill=hair + (255,))
    elif cfg["hair_style"] == "short_blond":
        d.pieslice([cx - 36, 40, cx + 36, 92], 180, 360, fill=hair + (255,))
        d.rectangle([cx - 36, 66, cx - 30, 92], fill=hair + (255,))
        d.rectangle([cx + 30, 66, cx + 36, 92], fill=hair + (255,))
        # short beard along the jaw, kept low so it never reads as a smile
        d.arc([cx - 29, 100, cx + 29, 130], 20, 160, fill=hair + (255,),
              width=4)
    elif cfg["hair_style"] == "bun":
        d.pieslice([cx - 36, 38, cx + 36, 90], 180, 360, fill=hair + (255,))
        d.ellipse([cx - 13, 26, cx + 13, 52], fill=hair + (255,))
        d.rectangle([cx - 36, 64, cx - 29, 100], fill=hair + (255,))
        d.rectangle([cx + 29, 64, cx + 36, 100], fill=hair + (255,))
    # face: brows, eyes, nose, mouth — small and soft, like a photo
    dark = (58, 48, 40, 255)
    for sgn in (-1, 1):
        ex = cx + sgn * 15
        d.line([(ex - 7, 81), (ex + 7, 80)], fill=dark, width=1)   # brow
        d.ellipse([ex - 4, 88, ex + 4, 92], fill=dark)             # eye
    d.line([(cx + 1, 94), (cx - 1, 106), (cx + 3, 108)], fill=(120, 85, 65, 220),
           width=2)  # nose
    d.arc([cx - 9, 112, cx + 9, 122], 15, 165, fill=(140, 70, 60, 230), width=2)
    img = img.filter(ImageFilter.GaussianBlur(0.7))
    # laminate glare
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.polygon([(18, 0), (58, 0), (8, h), (-32, h)], fill=(255, 255, 255, 16))
    img.alpha_composite(ov)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=(60, 55, 45, 255), width=2)
    return img


# ---------------------------------------------------------------- stamps & visa
def stamp_layer(text_lines, color, w=180, h=112, date_circle=True):
    """A rubber stamp on its own RGBA layer, ready to rotate."""
    lay = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    ink = color + (205,)
    d.rounded_rectangle([20, 20, 20 + w, 20 + h], radius=10,
                        outline=ink, width=3)
    d.rounded_rectangle([24, 24, 20 + w - 4, 20 + h - 4], radius=8,
                        outline=color + (150,), width=1)
    y = 32
    for i, (s, f, sz) in enumerate(text_lines):
        txt(d, (20 + w / 2, y), s, font(f, sz), ink, anchor="ma")
        y += sz + 4
    if date_circle:
        cx, cy = 20 + w - 34, 20 + h - 30
        d.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], outline=ink, width=2)
        d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=color + (150,),
                  width=1)
        txt(d, (cx, cy - 5), "*", font(F_SANS_B, 14), ink, anchor="ma")
    return lay


def place_stamp(base, lay, x, y, angle):
    rot = lay.rotate(angle, expand=True, resample=Image.BICUBIC)
    base.alpha_composite(rot, (x, y))


def visa_sticker(d, x, y, w, h, cfg, visa):
    d.rectangle([x, y, x + w, y + h], fill=(214, 228, 240),
                outline=(70, 100, 140), width=2)
    d.rectangle([x, y, x + w, y + 30], fill=(58, 92, 138))
    txt(d, (x + 12, y + 6), "VISA", font(F_SANS_B, 17), (255, 255, 255))
    txt(d, (x + w - 12, y + 8), visa["country"].upper(),
        font(F_SANS_B, 14), (255, 255, 255), anchor="ra")
    yy = y + 42
    cols = [("TYPE", visa["type"]), ("ENTRIES", visa["entries"]),
            ("VALID FROM", visa["valid_from"]), ("UNTIL", visa["until"]),
            ("VISA No.", visa["no"])]
    cx = x + 12
    for label, val in cols:
        txt(d, (cx, yy), label, font(F_SANS, 9), (90, 90, 90))
        txt(d, (cx, yy + 12), val, font(F_SANS_B, 13), (20, 30, 50))
        cx += 142 if label not in ("VALID FROM",) else 132
        if cx > x + w - 120:
            cx = x + 12
            yy += 40
    txt(d, (x + 12, y + h - 26), visa["condition"], font(F_SANS, 11),
        (40, 50, 70))
    # sticker serial + faint waves
    txt(d, (x + w - 12, y + h - 26), visa["serial"], font(F_MONO, 10),
        (90, 100, 120), anchor="ra")


# ---------------------------------------------------------------- data page
def data_page(img, px, py, cfg):
    d = ImageDraw.Draw(img, "RGBA")
    ink = cfg["ink"]
    # header
    emblem(d, px + 240, py + 46, 30, cfg["emblem"], ink)
    txt(d, (px + 240, py + 84), cfg["country"].upper(), font(F_SERIF_B, 25),
        ink, anchor="ma")
    txt(d, (px + 240, py + 112), cfg["native"], font(F_SERIF_I, 13),
        (90, 80, 60), anchor="ma")
    txt(d, (px + 240, py + 130), "P A S S P O R T", font(F_SANS_B, 14),
        ink, anchor="ma")
    d.line([(px + 26, py + 154), (px + 454, py + 154)], fill=ink, width=2)
    d.line([(px + 26, py + 158), (px + 454, py + 158)], fill=ink, width=1)
    # type / code / number row
    y = py + 168
    for cx, label, val in ((px + 26, "TYPE", "P"),
                           (px + 110, "CODE", cfg["code"]),
                           (px + 210, "PASSPORT No.", cfg["number"])):
        txt(d, (cx, y), label, font(F_SANS, 9), (110, 100, 85))
        txt(d, (cx, y + 13), val, font(F_SANS_B, 15), (25, 25, 25))
    # photo
    ph = portrait(cfg)
    img.alpha_composite(ph, (px + 26, py + 208))
    txt(d, (px + 26, py + 438), "SIGNATURE OF HOLDER", font(F_SANS, 8),
        (110, 100, 85))
    d.line([(px + 26, py + 468), (px + 196, py + 468)], fill=(70, 65, 55),
           width=1)
    txt(d, (px + 30, py + 446), cfg["signature"], font(F_SERIF_I, 17),
        (40, 40, 55))
    # data fields right of the photo
    fx = px + 216
    fy = py + 206
    fields = [
        ("SURNAME", cfg["surname"].upper()),
        ("GIVEN NAMES", cfg["given"].upper()),
        ("NATIONALITY", cfg["nationality"].upper()),
        ("DATE OF BIRTH", cfg["dob"]),
        ("PLACE OF BIRTH", cfg["pob"].upper()),
        ("SEX", cfg["sex"]),
        ("DATE OF ISSUE", cfg["issued"]),
        ("DATE OF EXPIRY", cfg["expiry"]),
        ("AUTHORITY", cfg["authority"].upper()),
    ]
    for label, val in fields:
        txt(d, (fx, fy), label, font(F_SANS, 9), (110, 100, 85))
        txt(d, (fx, fy + 12), val, font(F_SANS_B, 14), (25, 25, 25))
        fy += 29
    # occupation line under the fields
    txt(d, (fx, fy + 2), "OCCUPATION", font(F_SANS, 9), (110, 100, 85))
    txt(d, (fx, fy + 14), cfg["occupation"].upper(), font(F_SANS_B, 13),
        (25, 25, 25))
    # MRZ
    l1, l2 = mrz_lines(cfg)
    txt(d, (px + 30, py + 560), l1, font(F_MONO, 16), (20, 20, 20))
    txt(d, (px + 30, py + 586), l2, font(F_MONO, 16), (20, 20, 20))
    d.line([(px + 26, py + 548), (px + 454, py + 548)], fill=(150, 140, 120),
           width=1)
    txt(d, (px + 240, py + 626), cfg["mrz_note"], font(F_SANS, 9),
        (120, 110, 95), anchor="ma")


# ---------------------------------------------------------------- visa page
def visa_page(img, px, py, cfg):
    d = ImageDraw.Draw(img, "RGBA")
    ink = cfg["ink"]
    txt(d, (px + 26, py + 26), "VISAS", font(F_SERIF_B, 21), ink)
    txt(d, (px + 454, py + 32), "PAGE 7", font(F_SANS, 10), (110, 100, 85),
        anchor="ra")
    d.line([(px + 26, py + 54), (px + 454, py + 54)], fill=ink, width=2)
    visa_sticker(d, px + 26, py + 66, 428, 168, cfg, cfg["visa"])
    # entry / exit stamps
    for st in cfg["stamps"]:
        lay = stamp_layer(
            [(st["country"], F_SANS_B, 15),
             (st["kind"], F_SANS_B, 13),
             (st["date"], F_SANS, 12),
             (st["port"], F_SANS, 10)],
            st["color"])
        place_stamp(img, lay, px + st["x"], py + st["y"], st["angle"])
    # endorsement box — the telling paperwork detail
    bx, by, bw, bh = px + 26, py + 520, 428, 108
    d.rectangle([bx, by, bx + bw, by + bh], outline=ink, width=2)
    txt(d, (bx + 12, by + 8), "ENDORSEMENT", font(F_SANS_B, 11), ink)
    lines = wrap(d, cfg["endorsement"], font(F_SANS, 12), bw - 140)
    yy = by + 28
    for ln in lines:
        txt(d, (bx + 12, yy), ln, font(F_SANS, 12), (30, 30, 30))
        yy += 17
    # fee stamp overlapping the box's lower-right corner (text keeps clear)
    fee = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fee)
    fd.ellipse([10, 10, 110, 110], outline=(150, 30, 30, 215), width=3)
    fd.ellipse([19, 19, 101, 101], outline=(150, 30, 30, 160), width=1)
    txt(fd, (60, 34), "FEE", font(F_SANS_B, 13), (150, 30, 30, 225),
        anchor="ma")
    txt(fd, (60, 50), "PAID", font(F_SANS_B, 13), (150, 30, 30, 225),
        anchor="ma")
    txt(fd, (60, 68), cfg["fee"], font(F_SANS_B, 11), (150, 30, 30, 225),
        anchor="ma")
    place_stamp(img, fee, px + 352, py + 528, -12)
    txt(d, (px + 240, py + 648), "7", font(F_SANS, 11), (110, 100, 85),
        anchor="ma")


# ---------------------------------------------------------------- countries
BLUE = (26, 58, 138)
RED = (150, 30, 30)
PURPLE = (90, 42, 122)

COUNTRIES = [
    {
        "key": "a",
        "country": "Republic of Kalandra",
        "native": "Republika Kalandra  ·  Kalandran / English",
        "code": "KLD",
        "emblem": "sun_waves",
        "ink": (28, 72, 82),
        "surname": "Voss", "given": "Mara Selin", "sex": "F",
        "dob": "14 JUN 1991", "dob_mrz": "910614",
        "pob": "Port Liora",
        "issued": "12 MAR 2024", "expiry": "11 MAR 2034", "exp_mrz": "340311",
        "number": "K4829173",
        "authority": "Ministry of the Interior",
        "nationality": "Kalandran",
        "occupation": "Marine biologist",
        "signature": "Mara S. Voss",
        "mrz_note": "This passport remains the property of the Republic of Kalandra.",
        "hair_style": "curly", "hair": (42, 32, 24), "skin": (201, 143, 106),
        "jacket": (47, 111, 106),
        "photo_bg": ((206, 215, 221), (168, 180, 190)),
        "visa": {"country": "Taluvia", "type": "VISITOR", "entries": "SINGLE",
                 "valid_from": "01 MAY 2024", "until": "30 MAY 2024",
                 "no": "TV-2024-11847",
                 "condition": "Stay max 30 days. Employment prohibited.",
                 "serial": "TV 11847 24"},
        "stamps": [
            {"country": "TALUVIA", "kind": "ENTRY", "date": "03 MAY 2024",
             "port": "PORT LIORA", "x": 30, "y": 252, "angle": -8,
             "color": BLUE},
            {"country": "TALUVIA", "kind": "EXIT", "date": "18 MAY 2024",
             "port": "PORT LIORA", "x": 252, "y": 264, "angle": 7,
             "color": BLUE},
            {"country": "MERIDIAN ISLES", "kind": "ENTRY",
             "date": "22 NOV 2025", "port": "HARBOUR GATE 2", "x": 140,
             "y": 384, "angle": -4, "color": PURPLE},
        ],
        "endorsement": ("SEAFARER'S ENDORSEMENT — the holder may sign on "
                        "as crew of inter-island vessels. Not valid for air "
                        "transit. Renewal at any harbour office."),
        "fee": "25 KLD",
    },
    {
        "key": "b",
        "country": "Kingdom of Veyrland",
        "native": "Konungsríki Veyrland  ·  Veyrsk / English",
        "code": "VYR",
        "emblem": "mountain_star",
        "ink": (40, 50, 82),
        "surname": "Berg", "given": "Anders Kjell", "sex": "M",
        "dob": "02 OCT 1988", "dob_mrz": "881002",
        "pob": "Hrafnvik",
        "issued": "05 FEB 2024", "expiry": "04 FEB 2034", "exp_mrz": "340204",
        "number": "V7312046",
        "authority": "Royal Passport Office",
        "nationality": "Veyrlander",
        "occupation": "Mountain guide",
        "signature": "Anders K. Berg",
        "mrz_note": "This passport remains the property of the Kingdom of Veyrland.",
        "hair_style": "short_blond", "hair": (200, 168, 106),
        "skin": (224, 181, 150), "jacket": (44, 62, 85),
        "photo_bg": ((212, 216, 220), (175, 182, 190)),
        "visa": {"country": "Ostmark", "type": "TRANSIT", "entries": "SINGLE",
                 "valid_from": "10 JUN 2024", "until": "09 JUL 2024",
                 "no": "OS-2024-55210",
                 "condition": "Transit only. Max stay 72 hours.",
                 "serial": "OS 55210 24"},
        "stamps": [
            {"country": "OSTMARK", "kind": "ENTRY", "date": "14 JUN 2024",
             "port": "SOUTH GATE", "x": 30, "y": 252, "angle": -8,
             "color": BLUE},
            {"country": "OSTMARK", "kind": "EXIT", "date": "28 JUN 2024",
             "port": "SOUTH GATE", "x": 252, "y": 264, "angle": 7,
             "color": BLUE},
            {"country": "DUNMARRA", "kind": "ENTRY", "date": "09 JAN 2025",
             "port": "NORTH PASS", "x": 140, "y": 384, "angle": -4,
             "color": RED},
        ],
        "endorsement": ("SNOW-PASS REQUIRED beyond the Treeline, "
                        "1 NOV – 30 APR. Holders travelling north of "
                        "Hrafnvik must carry a snow-pass. Fee 40 KR."),
        "fee": "40 KR",
    },
    {
        "key": "c",
        "country": "Republic of Aldermere",
        "native": "Poblacht Aldermere  ·  Alders / English",
        "code": "ALD",
        "emblem": "lighthouse",
        "ink": (52, 44, 74),
        "surname": "Wren", "given": "Tamsin Elinor", "sex": "F",
        "dob": "27 SEP 1995", "dob_mrz": "950927",
        "pob": "Greyhaven",
        "issued": "19 JUN 2024", "expiry": "18 JUN 2034", "exp_mrz": "340618",
        "number": "A9035518",
        "authority": "Department of the Interior",
        "nationality": "Aldermerian",
        "occupation": "Lighthouse keeper",
        "signature": "Tamsin E. Wren",
        "mrz_note": "This passport remains the property of the Republic of Aldermere.",
        "hair_style": "bun", "hair": (110, 59, 31), "skin": (217, 165, 131),
        "jacket": (90, 58, 74),
        "photo_bg": ((208, 212, 216), (170, 178, 186)),
        "visa": {"country": "Skerry Isles", "type": "FERRY VISA",
                 "entries": "12 CROSSINGS",
                 "valid_from": "01 AUG 2024", "until": "31 JUL 2025",
                 "no": "SK-2024-09177",
                 "condition": "Ferry crossings only. No air or road entry.",
                 "serial": "SK 09177 24"},
        "stamps": [
            {"country": "SKERRY ISLES", "kind": "ENTRY", "date": "04 AUG 2024",
             "port": "GREYHAVEN", "x": 30, "y": 252, "angle": -8,
             "color": BLUE},
            {"country": "SKERRY ISLES", "kind": "EXIT", "date": "11 AUG 2024",
             "port": "GREYHAVEN", "x": 252, "y": 264, "angle": 7,
             "color": BLUE},
            {"country": "DUNMORE", "kind": "ENTRY", "date": "17 MAR 2025",
             "port": "EAST QUAY", "x": 140, "y": 384, "angle": -4,
             "color": PURPLE},
        ],
        "endorsement": ("FERRY VISA — valid for 12 crossings on the "
                        "Greyhaven–Skerry line only. The visa expires with "
                        "the twelfth crossing; unused crossings do not "
                        "carry over."),
        "fee": "18 ALD",
    },
]


# ---------------------------------------------------------------- render
def render(cfg):
    img = desk()
    spread_shadow(img)
    d = ImageDraw.Draw(img, "RGBA")
    page = (243, 239, 228)
    d.rectangle([32, 162, 512, 862], fill=page + (255,),
                outline=(150, 140, 118), width=2)
    d.rectangle([512, 162, 992, 862], fill=page + (255,),
                outline=(150, 140, 118), width=2)
    # gutter shadow between the pages
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i in range(10):
        od.rectangle([508 + i, 162, 509 + i, 862], fill=(0, 0, 0, 26 - i * 2))
        od.rectangle([512 - i, 162, 513 - i, 862], fill=(0, 0, 0, 26 - i * 2))
    img.alpha_composite(ov)
    guilloche(img, (34, 164, 510, 860))
    guilloche(img, (514, 164, 990, 860))
    data_page(img, 32, 162, cfg)
    visa_page(img, 512, 162, cfg)
    return img.convert("RGB")


def main():
    for cfg in COUNTRIES:
        img = render(cfg)
        out = HERE / ("variant-" + cfg["key"] + ".png")
        img.save(out, optimize=True)
        print(out.name, img.size, out.stat().st_size, "bytes")
        jpg = HERE / ("variant-" + cfg["key"] + ".jpg")
        img.save(jpg, quality=88)
        print(jpg.name, jpg.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
