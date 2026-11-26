"""Komponen tampilan berupa HTML/CSS (tanpa Streamlit, jadi mudah diuji).

Semua kartu memakai warna eksplisit sehingga tetap terbaca di tema terang maupun gelap.
Warna: biru #2a78d6 (seri 1), oranye #eb6834 (seri 2), status hijau/merah dengan ikon dan teks.
Aturan CSS untuk widget bawaan Streamlit sengaja ringan (warna, sudut, bayangan) agar tidak merusak tata letak.
"""
from html import escape

BIRU = "#2a78d6"
ORANYE = "#eb6834"
HIJAU = "#0ca30c"
MERAH = "#d03b3b"

# Rentang DJ untuk meter dan legenda: (huruf LOS, batas atas, warna latar, warna teks, label rentang)
SEGMEN_LOS = [
    ("A", 0.20, "#dbe8f8", "#0b0b0b", "≤ 0,20"),
    ("B", 0.44, "#b5d1f2", "#0b0b0b", "0,21 - 0,44"),
    ("C", 0.74, "#8db8ec", "#0b0b0b", "0,45 - 0,74"),
    ("D", 0.84, "#5b97e0", "#ffffff", "0,75 - 0,84"),
    ("E", 1.00, "#2a78d6", "#ffffff", "0,85 - 1,00"),
    ("F", 1.20, "#1b4f94", "#ffffff", "> 1,00"),
]
DJ_MAKS_METER = 1.20


def _id(x, nd=0):
    """Angka berformat Indonesia: titik ribuan, koma desimal."""
    s = f"{x:,.{nd}f}"
    return s.replace(",", "\0").replace(".", ",").replace("\0", ".")


def _satu_baris(html):
    """Hilangkan baris baru dan indentasi agar Markdown tidak menganggapnya blok kode."""
    return " ".join(baris.strip() for baris in html.splitlines() if baris.strip())


# ------------------------------------------------------------
# CSS
# ------------------------------------------------------------
def css():
    return _satu_baris("""
<style>
.block-container{padding-top:1.1rem;padding-bottom:2.5rem;max-width:1280px}
header[data-testid="stHeader"]{background:transparent}
section[data-testid="stSidebar"]{background:#fff;border-right:1px solid #e1e0d9}
section[data-testid="stSidebar"] .stButton>button{width:100%;justify-content:flex-start;text-align:left}

/* ---- widget bawaan Streamlit: gaya ringan ---- */
.stTabs [data-baseweb="tab-list"]{gap:4px;flex-wrap:wrap;background:#e6ebf2;padding:5px;border-radius:14px;border-bottom:none}
.stTabs [data-baseweb="tab"]{height:auto;padding:8px 14px;border-radius:10px;background:transparent}
.stTabs [data-baseweb="tab"] p{font-weight:600;color:#3d3c39}
.stTabs [data-baseweb="tab"][aria-selected="true"]{background:#fff;box-shadow:0 1px 4px rgba(15,61,122,.22)}
.stTabs [data-baseweb="tab"][aria-selected="true"] p{color:#0f3d7a}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none}
.stButton>button,.stDownloadButton>button{border-radius:10px;font-weight:600;border:1px solid #cdd5e0;transition:all .15s ease}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:#2a78d6;color:#2a78d6;box-shadow:0 2px 10px rgba(42,120,214,.18)}
.stDownloadButton>button{background:#f1f6fd;border-color:#cfe0f6;color:#0f3d7a}
[data-testid="stMetric"]{background:#fff;border:1px solid #e1e0d9;border-radius:12px;padding:10px 14px}
[data-testid="stExpander"] details{border-radius:12px;border:1px solid #e1e0d9;background:#fff}
[data-testid="stDataFrame"]{border:1px solid #e1e0d9;border-radius:12px;overflow:hidden}
[data-testid="stAlert"]{border-radius:12px}

/* ---- header ---- */
.kj-hero{position:relative;overflow:hidden;color:#fff;border-radius:18px;margin:0 0 14px 0;
 background:radial-gradient(circle at 90% 15%,rgba(255,255,255,.22) 0,rgba(255,255,255,0) 36%),
 radial-gradient(circle at 72% 125%,rgba(235,104,52,.38) 0,rgba(235,104,52,0) 46%),
 linear-gradient(120deg,#0b2f63 0%,#1d5fb8 60%,#2a78d6 100%);box-shadow:0 8px 24px rgba(15,61,122,.22)}
.kj-hero-in{display:flex;align-items:center;gap:18px;padding:26px 30px 24px 30px}
.kj-ikon{flex:none;width:60px;height:60px;border-radius:16px;background:rgba(255,255,255,.16);
 border:1px solid rgba(255,255,255,.3);display:flex;align-items:center;justify-content:center;font-size:30px}
.kj-hero .t{font-size:1.75rem;font-weight:780;line-height:1.2;letter-spacing:-.01em}
.kj-hero .s{font-size:1rem;opacity:.92;margin-top:6px;max-width:760px}
.kj-chips{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}
.kj-chip{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.34);color:#fff;
 border-radius:999px;padding:3px 12px;font-size:.8rem}
.kj-road{position:relative;height:16px;background:#14233a}
.kj-road i{position:absolute;left:0;right:0;top:7px;height:3px;
 background:repeating-linear-gradient(90deg,#f6c445 0 26px,transparent 26px 52px)}

/* ---- bilah ringkasan ---- */
.kj-bar{display:flex;flex-wrap:wrap;align-items:center;gap:6px 22px;background:#fff;border:1px solid #e1e0d9;
 border-radius:14px;padding:10px 18px;margin:0 0 14px 0;color:#0b0b0b;box-shadow:0 1px 3px rgba(15,61,122,.06)}
.kj-bar .it{display:flex;flex-direction:column;line-height:1.2;padding-right:22px;border-right:1px solid #e1e0d9}
.kj-bar .it:last-of-type{border-right:none;padding-right:0}
.kj-bar .lb{font-size:.68rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#6b6a66}
.kj-bar b{font-size:1.05rem;font-variant-numeric:tabular-nums}
.kj-bar .u{font-size:.74rem;font-weight:500;color:#52514e;margin-left:3px}
.kj-pill{margin-left:auto;border-radius:999px;padding:5px 14px;font-weight:700;font-size:.85rem;border:1px solid}
.kj-pill.ok{background:#e9f6e9;color:#006300;border-color:#9fd49f}
.kj-pill.no{background:#fbeaea;color:#a82727;border-color:#e5a3a3}

/* ---- judul seksi, kartu, lencana ---- */
.kj-sec{display:flex;align-items:center;gap:8px;font-size:.8rem;font-weight:700;letter-spacing:.05em;
 text-transform:uppercase;color:#3d3c39;margin:2px 0 10px 0}
.kj-sec .no{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;
 background:#2a78d6;color:#fff;font-size:.74rem;letter-spacing:0}
.kj-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:10px;margin:6px 0 14px 0}
.kj-card{background:#fff;border:1px solid #e1e0d9;border-left:5px solid #2a78d6;border-radius:14px;
 padding:12px 14px;color:#0b0b0b;box-shadow:0 1px 3px rgba(15,61,122,.06);transition:transform .15s ease,box-shadow .15s ease}
.kj-card:hover{transform:translateY(-2px);box-shadow:0 8px 18px rgba(15,61,122,.12)}
.kj-card .l{font-size:.72rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#52514e}
.kj-card .v{font-size:1.6rem;font-weight:760;line-height:1.25;margin-top:2px;font-variant-numeric:tabular-nums}
.kj-card .u{font-size:.8rem;color:#52514e;font-weight:500;margin-left:4px}
.kj-card .sub{font-size:.76rem;color:#52514e;margin-top:2px}
.kj-badge{display:flex;align-items:center;gap:12px;border-radius:14px;padding:12px 16px;margin:6px 0 14px 0;
 font-weight:700;font-size:1.02rem;border:1px solid}
.kj-badge.ok{background:#e9f6e9;color:#006300;border-color:#9fd49f}
.kj-badge.no{background:#fbeaea;color:#a82727;border-color:#e5a3a3}
.kj-badge .i{flex:none;display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:50%;
 font-size:1.1rem;line-height:1;background:rgba(255,255,255,.75)}
.kj-badge .d{font-weight:500;font-size:.88rem;opacity:.95}

/* ---- meter DJ ---- */
.kj-meter{background:#fff;border:1px solid #e1e0d9;border-radius:14px;padding:14px 16px 12px 16px;margin:6px 0 14px 0;
 color:#0b0b0b;box-shadow:0 1px 3px rgba(15,61,122,.06)}
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

/* ---- faktor, catatan, panduan, keadaan kosong, legenda ---- */
.kj-fak{background:#fff;border:1px solid #e1e0d9;border-radius:14px;padding:12px 16px;margin:6px 0 14px 0;color:#0b0b0b;
 box-shadow:0 1px 3px rgba(15,61,122,.06)}
.kj-fak .r{display:grid;grid-template-columns:minmax(120px,1.3fr) 3fr 56px;align-items:center;gap:10px;padding:4px 0;font-size:.86rem}
.kj-fak .bar{position:relative;height:10px;background:#eeede8;border-radius:6px}
.kj-fak .bar i{display:block;height:100%;border-radius:6px;background:#2a78d6}
.kj-fak .bar i.min{background:#eb6834}
.kj-fak .bar .tk{position:absolute;top:-3px;height:16px;border-left:2px solid #52514e}
.kj-fak .n{color:#0b0b0b}
.kj-fak .n em{color:#52514e;font-style:normal}
.kj-fak b{text-align:right;font-variant-numeric:tabular-nums}
.kj-fak .note{font-size:.76rem;color:#52514e;margin-top:6px}
.kj-note{background:#f1f6fd;border:1px solid #cfe0f6;border-left:5px solid #2a78d6;border-radius:14px;padding:12px 16px;
 margin:6px 0 14px 0;color:#0b0b0b;font-size:.92rem}
.kj-note ul{margin:6px 0 0 0;padding-left:18px}
.kj-note li{margin:3px 0}
.kj-steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin:4px 0 8px 0}
.kj-step{background:#fff;border:1px solid #e1e0d9;border-radius:14px;padding:12px 14px;color:#0b0b0b;font-size:.9rem}
.kj-step .no{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;
 background:#2a78d6;color:#fff;font-weight:700;font-size:.8rem;margin-bottom:6px}
.kj-step b{display:block;margin-bottom:2px}
.kj-empty{background:#fff;border:1.5px dashed #c3c2b7;border-radius:16px;padding:28px 20px;text-align:center;color:#0b0b0b;margin:6px 0 14px 0}
.kj-empty .ik{font-size:2rem;line-height:1}
.kj-empty b{display:block;margin-top:8px;font-size:1.02rem}
.kj-empty p{margin:4px auto 0 auto;max-width:520px;color:#52514e;font-size:.9rem}
.kj-los{display:flex;flex-direction:column;gap:6px;margin:4px 0 8px 0}
.kj-los .r{display:flex;align-items:center;gap:10px;font-size:.84rem;color:#0b0b0b}
.kj-los .c{flex:none;width:28px;height:24px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.78rem}
.kj-los .g{flex:none;min-width:84px;color:#3d3c39;font-variant-numeric:tabular-nums}
.kj-los .k{color:#52514e}
.kj-foot{margin-top:28px;padding-top:12px;border-top:1px solid #e1e0d9;font-size:.78rem;color:#52514e;text-align:center}

@media (max-width:640px){
.kj-hero-in{padding:20px 18px;gap:12px}.kj-ikon{width:46px;height:46px;font-size:23px;border-radius:12px}
.kj-hero .t{font-size:1.3rem}.kj-card .v{font-size:1.4rem}
.kj-bar .it{padding-right:14px}.kj-pill{margin-left:0}
.kj-fak .r{grid-template-columns:1fr 56px;grid-template-areas:"n v" "b b";row-gap:4px;padding:6px 0}
.kj-fak .r .n{grid-area:n}.kj-fak .r .bar{grid-area:b}.kj-fak .r b{grid-area:v}}
</style>""")


# ------------------------------------------------------------
# Komponen
# ------------------------------------------------------------
def hero(judul, subjudul, chips, ikon="🛣️"):
    isi = "".join(f'<span class="kj-chip">{escape(c)}</span>' for c in chips if c)
    return _satu_baris(f"""
<div class="kj-hero"><div class="kj-hero-in"><div class="kj-ikon">{ikon}</div>
<div><div class="t">{escape(judul)}</div><div class="s">{escape(subjudul)}</div>
<div class="kj-chips">{isi}</div></div></div><div class="kj-road"><i></i></div></div>""")


def judul_seksi(teks, nomor=None):
    no = f'<span class="no">{nomor}</span>' if nomor is not None else ""
    return f'<div class="kj-sec">{no}<span>{escape(teks)}</span></div>'


def kartu(label, nilai, satuan="", aksen=BIRU, sub=""):
    u = f'<span class="u">{escape(satuan)}</span>' if satuan else ""
    s = f'<div class="sub">{escape(sub)}</div>' if sub else ""
    return (f'<div class="kj-card" style="border-left-color:{aksen}"><div class="l">{escape(label)}</div>'
            f'<div class="v">{escape(str(nilai))}{u}</div>{s}</div>')


def grid_kartu(items):
    """items: daftar (label, nilai, satuan, aksen) atau (label, nilai, satuan, aksen, sub)."""
    return f'<div class="kj-grid">{"".join(kartu(*i) for i in items)}</div>'


def kartu_hasil(h):
    """Empat kartu utama: C, Q, DJ, LOS."""
    ok = h["DJ"] <= 0.85
    aksen_status = HIJAU if ok else MERAH
    return grid_kartu([
        ("Kapasitas C", _id(h["C"]), "smp/jam", BIRU),
        ("Arus Q", _id(h["Q"]), "smp/jam", ORANYE),
        ("Derajat kejenuhan DJ", _id(h["DJ"], 3), "", aksen_status),
        ("Tingkat pelayanan", h["LOS"], "", aksen_status),
    ])


def ringkasan_bar(nama, tipe, h):
    """Bilah ringkas ruas aktif; dipasang di atas tab agar terlihat di semua tab."""
    ok = h["DJ"] <= 0.85
    pil = ('<span class="kj-pill ok">✔ Memenuhi</span>' if ok
           else '<span class="kj-pill no">✖ Tidak memenuhi</span>')

    def it(lb, nilai, u=""):
        satuan = f'<span class="u">{u}</span>' if u else ""
        return f'<div class="it"><span class="lb">{lb}</span><b>{nilai}{satuan}</b></div>'

    return _satu_baris(
        '<div class="kj-bar">'
        + it("Ruas aktif", escape(nama)) + it("Tipe", escape(tipe))
        + it("Kapasitas C", _id(h["C"]), "smp/jam") + it("Arus Q", _id(h["Q"]), "smp/jam")
        + it("DJ", _id(h["DJ"], 3)) + it("LOS", h["LOS"]) + pil + "</div>")


def lencana_status(dj, batas=0.85):
    if dj <= batas:
        return _satu_baris(f"""
<div class="kj-badge ok"><span class="i">✔</span><span>MEMENUHI<br><span class="d">DJ {_id(dj, 3)} ≤ {_id(batas, 2)}: arus
masih di bawah batas kapasitas yang disyaratkan</span></span></div>""")
    return _satu_baris(f"""
<div class="kj-badge no"><span class="i">✖</span><span>TIDAK MEMENUHI<br><span class="d">DJ {_id(dj, 3)} &gt; {_id(batas, 2)}:
arus melewati batas kapasitas yang disyaratkan</span></span></div>""")


def meter_dj(dj, batas=0.85):
    """Meter horizontal 0 - 1,20 dengan segmen LOS A-F, penanda DJ, dan garis batas."""
    lebar_prev, segmen = 0.0, []
    for huruf, atas, bg, fg, _ in SEGMEN_LOS:
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


def catatan(daftar_kalimat, judul="💡 Interpretasi hasil"):
    butir = "".join(f"<li>{escape(k)}</li>" for k in daftar_kalimat)
    return f'<div class="kj-note"><b>{escape(judul)}</b><ul>{butir}</ul></div>'


def panduan(langkah):
    """langkah: daftar (judul, keterangan). Kartu bernomor."""
    isi = "".join(f'<div class="kj-step"><span class="no">{i}</span><b>{escape(j)}</b>{escape(k)}</div>'
                  for i, (j, k) in enumerate(langkah, 1))
    return f'<div class="kj-steps">{isi}</div>'


def kosong(ikon, judul, teks):
    """Keadaan kosong: kotak putus-putus dengan ikon dan petunjuk."""
    return (f'<div class="kj-empty"><div class="ik">{ikon}</div><b>{escape(judul)}</b>'
            f'<p>{escape(teks)}</p></div>')


def legenda_los(deskripsi=None):
    """Daftar LOS A-F dengan chip berwarna sama seperti meter. deskripsi: dict huruf -> keterangan."""
    baris = []
    for huruf, _, bg, fg, rentang in SEGMEN_LOS:
        ket = f'<span class="k">{escape(deskripsi[huruf])}</span>' if deskripsi and huruf in deskripsi else ""
        baris.append(f'<div class="r"><span class="c" style="background:{bg};color:{fg}">{huruf}</span>'
                     f'<span class="g">DJ {rentang}</span>{ket}</div>')
    return f'<div class="kj-los">{"".join(baris)}</div>'


def footer(teks):
    return f'<div class="kj-foot">{escape(teks)}</div>'
