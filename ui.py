"""Komponen tampilan berupa HTML/CSS (tanpa Streamlit, jadi mudah diuji).

Semua kartu memakai warna eksplisit sehingga tetap terbaca di tema terang maupun gelap.
Warna: biru #2a78d6 (seri 1), oranye #eb6834 (seri 2), status hijau/merah dengan ikon dan teks.
"""
from html import escape

BIRU = "#2a78d6"
ORANYE = "#eb6834"
BIRU_TUA = "#0f3d7a"

# Rentang DJ untuk meter: (huruf LOS, batas atas, warna latar, warna teks)
SEGMEN_LOS = [
    ("A", 0.20, "#dbe8f8", "#0b0b0b"),
    ("B", 0.44, "#b5d1f2", "#0b0b0b"),
    ("C", 0.74, "#8db8ec", "#0b0b0b"),
    ("D", 0.84, "#5b97e0", "#ffffff"),
    ("E", 1.00, "#2a78d6", "#ffffff"),
    ("F", 1.20, "#1b4f94", "#ffffff"),
]
DJ_MAKS_METER = 1.20


def _id(x, nd=0):
    """Angka berformat Indonesia: titik ribuan, koma desimal."""
    s = f"{x:,.{nd}f}"
    return s.replace(",", "\0").replace(".", ",").replace("\0", ".")


def _satu_baris(html):
    """Hilangkan baris baru dan indentasi agar Markdown tidak menganggapnya blok kode."""
    return " ".join(baris.strip() for baris in html.splitlines() if baris.strip())


def css():
    return _satu_baris("""
<style>
.block-container{padding-top:1.6rem;padding-bottom:2.5rem;max-width:1280px}
.stTabs [data-baseweb="tab-list"]{gap:2px;flex-wrap:wrap}
.stTabs [data-baseweb="tab"]{font-weight:600;padding:8px 14px}
.kj-hero{background:linear-gradient(120deg,#0f3d7a 0%,#2a78d6 100%);color:#fff;border-radius:16px;
 padding:24px 28px;margin:0 0 16px 0}
.kj-hero .t{font-size:1.75rem;font-weight:750;line-height:1.2;margin:0}
.kj-hero .s{font-size:1rem;opacity:.92;margin-top:6px}
.kj-chips{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}
.kj-chip{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.35);color:#fff;
 border-radius:999px;padding:3px 12px;font-size:.8rem}
.kj-sec{font-size:.78rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#52514e;
 margin:4px 0 8px 0}
.kj-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:10px;margin:6px 0 14px 0}
.kj-card{background:#fff;border:1px solid #e1e0d9;border-left:5px solid #2a78d6;border-radius:12px;
 padding:12px 14px;color:#0b0b0b}
.kj-card .l{font-size:.74rem;font-weight:650;letter-spacing:.04em;text-transform:uppercase;color:#52514e}
.kj-card .v{font-size:1.65rem;font-weight:750;line-height:1.25;margin-top:2px}
.kj-card .u{font-size:.8rem;color:#52514e;font-weight:500;margin-left:4px}
.kj-badge{display:flex;align-items:center;gap:10px;border-radius:12px;padding:12px 16px;margin:6px 0 14px 0;
 font-weight:700;font-size:1.02rem;border:1px solid}
.kj-badge.ok{background:#e9f6e9;color:#006300;border-color:#9fd49f}
.kj-badge.no{background:#fbeaea;color:#a82727;border-color:#e5a3a3}
.kj-badge .i{font-size:1.3rem;line-height:1}
.kj-badge .d{font-weight:500;font-size:.88rem;opacity:.95}
.kj-meter{background:#fff;border:1px solid #e1e0d9;border-radius:12px;padding:14px 16px 12px 16px;margin:6px 0 14px 0;color:#0b0b0b}
.kj-meter .h{display:flex;justify-content:space-between;align-items:baseline;font-size:.85rem;color:#52514e;margin-bottom:34px}
.kj-meter .h b{color:#0b0b0b;font-size:1rem}
.kj-track{position:relative;display:flex;height:30px;border-radius:8px;overflow:visible;margin:0 6px}
.kj-track .seg{display:flex;align-items:center;justify-content:center;font-size:.78rem;font-weight:700}
.kj-track .seg:first-child{border-radius:8px 0 0 8px}
.kj-track .seg:last-child{border-radius:0 8px 8px 0}
.kj-mark{position:absolute;top:-8px;height:46px;width:4px;background:#0b0b0b;border-radius:2px;
 box-shadow:0 0 0 2px #fff;transform:translateX(-2px)}
.kj-mark .tag{position:absolute;bottom:100%;left:50%;transform:translateX(-50%);margin-bottom:4px;
 background:#0b0b0b;color:#fff;font-size:.74rem;font-weight:700;padding:2px 8px;border-radius:6px;white-space:nowrap}
.kj-limit{position:absolute;top:-4px;height:38px;border-left:2px dashed #52514e}
.kj-scale{position:relative;height:34px;margin:4px 6px 0 6px;font-size:.72rem;color:#52514e}
.kj-scale .t{position:absolute;top:0;transform:translateX(-50%);white-space:nowrap}
.kj-scale .lim{position:absolute;top:15px;transform:translateX(-50%);white-space:nowrap;font-weight:650;color:#0b0b0b}
.kj-fak{background:#fff;border:1px solid #e1e0d9;border-radius:12px;padding:12px 16px;margin:6px 0 14px 0;color:#0b0b0b}
.kj-fak .r{display:grid;grid-template-columns:minmax(120px,1.3fr) 3fr 56px;align-items:center;gap:10px;padding:4px 0;
 font-size:.86rem}
.kj-fak .bar{position:relative;height:10px;background:#eeede8;border-radius:6px}
.kj-fak .bar i{display:block;height:100%;border-radius:6px;background:#2a78d6}
.kj-fak .bar i.min{background:#eb6834}
.kj-fak .bar .tk{position:absolute;top:-3px;height:16px;border-left:2px solid #52514e}
.kj-fak .n{color:#0b0b0b}
.kj-fak .n em{color:#52514e;font-style:normal}
.kj-fak b{text-align:right;font-variant-numeric:tabular-nums}
.kj-fak .note{font-size:.76rem;color:#52514e;margin-top:6px}
.kj-note{background:#f1f6fd;border:1px solid #cfe0f6;border-radius:12px;padding:12px 16px;margin:6px 0 14px 0;color:#0b0b0b;font-size:.92rem}
.kj-note ul{margin:0;padding-left:18px}
.kj-note li{margin:3px 0}
@media (max-width:520px){.kj-fak .r{grid-template-columns:1fr 56px;grid-template-areas:"n v" "b b";row-gap:4px;padding:6px 0}.kj-fak .r .n{grid-area:n}.kj-fak .r .bar{grid-area:b}.kj-fak .r b{grid-area:v}.kj-hero{padding:18px 18px}.kj-hero .t{font-size:1.4rem}.kj-card .v{font-size:1.4rem}}
.kj-foot{margin-top:28px;padding-top:12px;border-top:1px solid #e1e0d9;font-size:.78rem;color:#52514e;text-align:center}
</style>""")


def hero(judul, subjudul, chips):
    isi = "".join(f'<span class="kj-chip">{escape(c)}</span>' for c in chips if c)
    return _satu_baris(f"""
<div class="kj-hero"><div class="t">{escape(judul)}</div><div class="s">{escape(subjudul)}</div>
<div class="kj-chips">{isi}</div></div>""")


def judul_seksi(teks):
    return f'<div class="kj-sec">{escape(teks)}</div>'


def kartu(label, nilai, satuan="", aksen=BIRU):
    u = f'<span class="u">{escape(satuan)}</span>' if satuan else ""
    return (f'<div class="kj-card" style="border-left-color:{aksen}"><div class="l">{escape(label)}</div>'
            f'<div class="v">{escape(str(nilai))}{u}</div></div>')


def kartu_hasil(h):
    """Empat kartu utama: C, Q, DJ, LOS."""
    ok = h["DJ"] <= 0.85
    aksen_status = "#0ca30c" if ok else "#d03b3b"
    isi = (kartu("Kapasitas C", _id(h["C"]), "smp/jam", BIRU)
           + kartu("Arus Q", _id(h["Q"]), "smp/jam", ORANYE)
           + kartu("Derajat kejenuhan DJ", _id(h["DJ"], 3), "", aksen_status)
           + kartu("Tingkat pelayanan", h["LOS"], "", aksen_status))
    return f'<div class="kj-grid">{isi}</div>'


def lencana_status(dj, batas=0.85):
    ok = dj <= batas
    if ok:
        return _satu_baris(f"""
<div class="kj-badge ok"><span class="i">✔</span><span>MEMENUHI<br><span class="d">DJ {_id(dj, 3)} ≤ {_id(batas, 2)}: arus
masih di bawah batas kapasitas yang disyaratkan</span></span></div>""")
    return _satu_baris(f"""
<div class="kj-badge no"><span class="i">✖</span><span>TIDAK MEMENUHI<br><span class="d">DJ {_id(dj, 3)} &gt; {_id(batas, 2)}:
arus melewati batas kapasitas yang disyaratkan</span></span></div>""")


def meter_dj(dj, batas=0.85):
    """Meter horizontal 0 - 1,20 dengan segmen LOS A-F, penanda DJ, dan garis batas."""
    lebar_prev, segmen = 0.0, []
    for huruf, atas, bg, fg in SEGMEN_LOS:
        persen = (atas - lebar_prev) / DJ_MAKS_METER * 100
        segmen.append(f'<div class="seg" style="width:{persen:.3f}%;background:{bg};color:{fg}">{huruf}</div>')
        lebar_prev = atas
    pos = min(max(dj, 0.0), DJ_MAKS_METER) / DJ_MAKS_METER * 100
    pos_batas = batas / DJ_MAKS_METER * 100
    tanda = "".join(
        f'<span class="t" style="left:{v / DJ_MAKS_METER * 100:.2f}%">{_id(v, 2)}</span>'
        for v in (0.0, 0.2, 0.44, 0.74, 1.0, 1.2))
    return _satu_baris(f"""
<div class="kj-meter"><div class="h"><span>Posisi DJ pada skala tingkat pelayanan (LOS)</span>
<b>DJ = {_id(dj, 3)}</b></div>
<div class="kj-track">{''.join(segmen)}
<div class="kj-limit" style="left:{pos_batas:.2f}%"></div>
<div class="kj-mark" style="left:{pos:.2f}%"><span class="tag">DJ {_id(dj, 3)}</span></div></div>
<div class="kj-scale">{tanda}<span class="lim" style="left:{pos_batas:.2f}%">▲ batas {_id(batas, 2)}</span></div></div>""")


def batang_faktor(h):
    """Batang kecil tiap faktor penyesuaian; faktor terendah yang bisa diperbaiki disorot oranye."""
    baris = [("FC_LJ", "Lebar jalur", h["FC_LJ"], True), ("FC_PA", "Pemisahan arah", h["FC_PA"], False),
             ("FC_HS", "Hambatan samping", h["FC_HS"], True), ("FC_UK", "Ukuran kota", h["FC_UK"], False)]
    bisa = {k: v for k, _, v, b in baris if b}
    terendah = min(bisa, key=bisa.get) if min(bisa.values()) < 0.98 else None
    skala = max(1.1, max(v for _, _, v, _ in baris) * 1.02)
    isi = []
    for kode, nama, v, b in baris:
        kelas = "min" if kode == terendah else ""
        isi.append(
            f'<div class="r"><span class="n">{kode} <em>· {nama}</em></span>'
            f'<div class="bar"><i class="{kelas}" style="width:{v / skala * 100:.2f}%"></i>'
            f'<span class="tk" style="left:{1.0 / skala * 100:.2f}%"></span></div><b>{_id(v, 3)}</b></div>')
    catatan = ('<div class="note">Garis tegak menandai faktor = 1,000 (tanpa pengurangan kapasitas). '
               'Oranye = faktor terendah yang masih bisa diperbaiki.</div>')
    return f'<div class="kj-fak">{"".join(isi)}{catatan}</div>'


def catatan(daftar_kalimat, judul="Interpretasi hasil"):
    butir = "".join(f"<li>{escape(k)}</li>" for k in daftar_kalimat)
    return f'<div class="kj-note"><b>{escape(judul)}</b><ul>{butir}</ul></div>'


def footer(teks):
    return f'<div class="kj-foot">{escape(teks)}</div>'
