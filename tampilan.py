"""Format angka Indonesia, grafik, dan laporan PDF.

Gaya grafik: satu warna aksen (biru), abu-abu untuk konteks, garis batas
putus-putus, nilai dilabeli langsung, dan latar terang agar terbaca di tema
terang maupun gelap Streamlit.
"""
import datetime
import io
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from analisis import BATAS_DJ  # noqa: E402
from kapasitas import KELAS_HS, hitung_kapasitas  # noqa: E402

# ---- Palet (nilai tervalidasi, lihat catatan di akhir berkas) ----
PERMUKAAN = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
REDUP = "#898781"
GRID = "#e1e0d9"
SUMBU = "#c3c2b7"
BIRU = "#2a78d6"      # seri 1
ORANYE = "#eb6834"    # seri 2

plt.rcParams.update({
    "figure.facecolor": PERMUKAAN, "axes.facecolor": PERMUKAAN, "savefig.facecolor": PERMUKAAN,
    "text.color": TINTA, "axes.labelcolor": TINTA_2, "axes.edgecolor": SUMBU,
    "xtick.color": TINTA_2, "ytick.color": TINTA_2, "font.size": 9,
    "axes.titlesize": 10, "axes.titleweight": "bold", "axes.titlelocation": "left",
})


# ------------------------------------------------------------
# Format angka (titik ribuan, koma desimal)
# ------------------------------------------------------------
def fmt_id(v, nd=0):
    s = f"{v:,.{nd}f}"
    return s.replace(",", "\0").replace(".", ",").replace("\0", ".")


def format_df(df, desimal):
    """Salinan df dengan kolom tertentu diubah jadi teks berformat Indonesia.

    desimal: {nama_kolom: jumlah_desimal}. Nilai kosong tetap kosong.
    """
    out = df.copy()
    for kolom, nd in desimal.items():
        if kolom in out.columns:
            out[kolom] = out[kolom].map(lambda v, nd=nd: "" if v != v or v is None else fmt_id(v, nd))
    return out


def format_rincian(df):
    out = df.copy()

    def fmt(r):
        v = r["Nilai"]
        if isinstance(v, str):
            return v
        return fmt_id(v, 0) if r["Satuan"] == "smp/jam" else fmt_id(v, 3)

    out["Nilai"] = out.apply(fmt, axis=1)
    return out


# ------------------------------------------------------------
# Gaya dasar sumbu
# ------------------------------------------------------------
def _gaya(ax, grid="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(SUMBU)
    ax.tick_params(length=0)
    ax.set_axisbelow(True)
    ax.grid(axis=grid, color=GRID, linewidth=0.8)


def _garis_batas(ax, nilai, label, arah="v", **kw):
    """Garis batas putus-putus dengan label langsung."""
    if arah == "v":
        ax.axvline(nilai, color=TINTA_2, linestyle=(0, (4, 3)), linewidth=1.2, zorder=2)
        ax.text(nilai, 1.01, label, transform=ax.get_xaxis_transform(), ha="center",
                va="bottom", fontsize=8, color=TINTA_2, **kw)
    else:
        ax.axhline(nilai, color=TINTA_2, linestyle=(0, (4, 3)), linewidth=1.2, zorder=2)
        ax.text(0.99, nilai, label, transform=ax.get_yaxis_transform(), ha="right",
                va="bottom", fontsize=8, color=TINTA_2, **kw)


def _label_nilai(ax, x, y, teks):
    """Label di ujung batang horizontal; latar permukaan agar garis batas tidak menembus teks."""
    ax.annotate(teks, (x, y), xytext=(6, 0), textcoords="offset points", va="center", ha="left",
                fontsize=8.5, zorder=5, bbox=dict(facecolor=PERMUKAAN, edgecolor="none", pad=1.5))


# ------------------------------------------------------------
# Grafik kalkulator (dua panel)
# ------------------------------------------------------------
def _panel_q_c(ax, h):
    nilai = [h["C"], h["Q"]]
    batang = ax.bar(["Kapasitas C", "Arus Q"], nilai, color=[BIRU, ORANYE], width=0.5, zorder=3)
    for b, v in zip(batang, nilai):
        ax.text(b.get_x() + b.get_width() / 2, v, fmt_id(v), ha="center", va="bottom", fontsize=9)
    batas = BATAS_DJ * h["C"]
    _garis_batas(ax, batas, f"Batas arus 0,85 C = {fmt_id(batas)}", arah="h")
    ax.set_ylim(0, max(nilai) * 1.18)
    ax.set_ylabel("smp/jam")
    ax.set_title(f"Arus dan kapasitas (DJ = {fmt_id(h['DJ'], 3)})")
    _gaya(ax, "y")
    # Legenda di kanan atas: batang Q lebih pendek sehingga tidak menutupi label nilai
    ax.legend(handles=[Patch(color=BIRU, label="Kapasitas C"), Patch(color=ORANYE, label="Arus Q")],
              frameon=False, loc="upper right", fontsize=8, bbox_to_anchor=(1.0, 0.9))


def _panel_hs(ax, h, param):
    kapasitas = []
    for k in KELAS_HS:
        p = dict(param)
        p["kelas_hs"] = k
        kapasitas.append(hitung_kapasitas(**p)["C"])
    x = range(len(KELAS_HS))
    ax.plot(x, kapasitas, color=BIRU, linewidth=2, marker="o", markersize=8,
            markeredgecolor=PERMUKAAN, markeredgewidth=2, zorder=3)
    sekarang = KELAS_HS.index(param["kelas_hs"])
    ax.annotate(f"Kondisi saat ini\n{fmt_id(kapasitas[sekarang])} smp/jam",
                (sekarang, kapasitas[sekarang]), textcoords="offset points", xytext=(0, 14),
                ha="center", fontsize=8, color=TINTA, arrowprops=dict(arrowstyle="-", color=REDUP))
    c_min = h["Q"] / BATAS_DJ
    _garis_batas(ax, c_min, f"C minimum agar DJ = 0,85: {fmt_id(c_min)}", arah="h")
    ax.set_xticks(list(x))
    ax.set_xticklabels(KELAS_HS, rotation=20, ha="right")
    bawah = min(min(kapasitas), c_min)
    atas = max(max(kapasitas), c_min)
    ax.set_ylim(bawah - 0.15 * (atas - bawah + 1), atas + 0.3 * (atas - bawah + 1))
    ax.set_ylabel("Kapasitas C (smp/jam)")
    ax.set_title("Pengaruh hambatan samping terhadap kapasitas")
    _gaya(ax, "y")


def buat_grafik(h, param):
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    _panel_q_c(ax[0], h)
    _panel_hs(ax[1], h, param)
    fig.tight_layout()
    return fig


# ------------------------------------------------------------
# Grafik skenario, proyeksi, perbandingan, jam puncak
# ------------------------------------------------------------
def grafik_skenario(df):
    n = len(df)
    fig, ax = plt.subplots(figsize=(9, 0.55 * n + 1.4))
    nama = ["\n".join(textwrap.wrap(s, 38)) for s in df["Skenario"]]
    y = list(range(n))[::-1]
    warna = [REDUP if s == "Kondisi eksisting" else BIRU for s in df["Skenario"]]
    ax.barh(y, df["DJ"], color=warna, height=0.55, zorder=3)
    for yi, dj, st_ in zip(y, df["DJ"], df["Status"]):
        _label_nilai(ax, dj, yi, f"{fmt_id(dj, 3)} ({st_.lower()})")
    ax.set_yticks(y)
    ax.set_yticklabels(nama)
    _garis_batas(ax, BATAS_DJ, "Batas DJ = 0,85", arah="v")
    ax.set_xlim(0, max(1.0, df["DJ"].max() * 1.45))
    ax.set_xlabel("Derajat kejenuhan (DJ)")
    _gaya(ax, "x")
    ax.legend(handles=[Patch(color=REDUP, label="Kondisi eksisting"), Patch(color=BIRU, label="Skenario perbaikan")],
              frameon=False, loc="lower right", fontsize=8)
    fig.tight_layout()
    return fig


def grafik_proyeksi(df, tahun_jenuh):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(df["Tahun ke-"], df["DJ"], color=BIRU, linewidth=2, zorder=3)
    _garis_batas(ax, BATAS_DJ, "Batas DJ = 0,85", arah="h")
    if tahun_jenuh is not None:
        dj = float(df.loc[df["Tahun ke-"] == tahun_jenuh, "DJ"].iloc[0])
        ax.plot([tahun_jenuh], [dj], marker="o", markersize=9, color=BIRU,
                markeredgecolor=PERMUKAAN, markeredgewidth=2, zorder=4)
        ax.annotate(f"Tahun ke-{tahun_jenuh}: DJ = {fmt_id(dj, 2)}\n(mulai melewati batas)",
                    (tahun_jenuh, dj), textcoords="offset points", xytext=(-14, 26),
                    ha="right", fontsize=8.5, arrowprops=dict(arrowstyle="-", color=REDUP))
    ax.set_xlim(0, df["Tahun ke-"].max())
    ax.set_ylim(0, max(1.0, df["DJ"].max() * 1.1))
    ax.set_xlabel("Tahun ke-")
    ax.set_ylabel("Derajat kejenuhan (DJ)")
    _gaya(ax, "y")
    fig.tight_layout()
    return fig


def grafik_perbandingan(df):
    d = df.sort_values("DJ", ascending=True).reset_index(drop=True)
    n = len(d)
    fig, ax = plt.subplots(figsize=(9, 0.5 * n + 1.4))
    ax.barh(range(n), d["DJ"], color=BIRU, height=0.55, zorder=3)
    for i, (dj, st_) in enumerate(zip(d["DJ"], d["Status"])):
        _label_nilai(ax, dj, i, f"{fmt_id(dj, 3)} ({st_.lower()})")
    ax.set_yticks(range(n))
    ax.set_yticklabels(["\n".join(textwrap.wrap(str(s), 30)) for s in d["Ruas"]])
    _garis_batas(ax, BATAS_DJ, "Batas DJ = 0,85", arah="v")
    ax.set_xlim(0, max(1.0, d["DJ"].max() * 1.45))
    ax.set_xlabel("Derajat kejenuhan (DJ)")
    _gaya(ax, "x")
    fig.tight_layout()
    return fig


def grafik_jam_puncak(res):
    d = res["tabel"]
    fig, ax = plt.subplots(figsize=(9, 4))
    warna = [BIRU if p else REDUP for p in d["Jam puncak"]]
    ax.bar(range(len(d)), d["Total"], color=warna, width=0.6, zorder=3)
    imaks = int(d["Total"].idxmax())
    ax.text(imaks, d["Total"].iloc[imaks], f"{fmt_id(res['v15_maks'])}", ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(range(len(d)))
    ax.set_xticklabels(d["waktu"], rotation=45, ha="right")
    ax.set_ylabel("Volume per 15 menit (kend)")
    ax.set_xlabel("Waktu mulai interval")
    ax.set_ylim(0, d["Total"].max() * 1.15)
    ax.set_title(f"Jam puncak mulai {res['waktu_awal']}: {fmt_id(res['total'])} kend/jam, PHF = {fmt_id(res['PHF'], 2)}")
    _gaya(ax, "y")
    ax.legend(handles=[Patch(color=BIRU, label="Jam puncak (4 interval)"), Patch(color=REDUP, label="Interval lain")],
              frameon=False, loc="upper right", fontsize=8)
    fig.tight_layout()
    return fig


# ------------------------------------------------------------
# Laporan PDF (2 halaman A4)
# ------------------------------------------------------------
_A4 = (8.27, 11.69)


def _tabel(ax, atas, baris, judul_kolom, lebar_kolom, tebal=(), tinggi=0.024):
    """Gambar tabel dengan tepi atas di y=atas (koordinat sumbu); kembalikan tepi bawah."""
    n = len(baris) + 1
    bawah = atas - n * tinggi
    tb = ax.table(cellText=baris, colLabels=judul_kolom, colWidths=lebar_kolom,
                  cellLoc="left", bbox=[0, bawah, 1, n * tinggi])
    tb.auto_set_font_size(False)
    tb.set_fontsize(8.5)
    for (r, c), sel in tb.get_celld().items():
        sel.set_edgecolor(SUMBU)
        sel.set_linewidth(0.6)
        sel.PAD = 0.03
        if r == 0:
            sel.set_facecolor(GRID)
            sel.set_text_props(fontweight="bold", color=TINTA)
        else:
            sel.set_facecolor(PERMUKAAN)
            sel.set_text_props(color=TINTA, fontweight="bold" if (r - 1) in tebal else "normal")
    return bawah


def laporan_pdf(identitas, param, h, nama_ruas=""):
    """Laporan perhitungan satu ruas dalam bentuk PDF (bytes)."""
    buf = io.BytesIO()
    ok = h["DJ"] <= BATAS_DJ
    with PdfPages(buf) as pdf:
        # ---------- Halaman 1: data, hasil, kesimpulan ----------
        fig = plt.figure(figsize=_A4)
        ax = fig.add_axes([0.08, 0.04, 0.84, 0.92])
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

        ax.text(0, 0.995, "LAPORAN PERHITUNGAN KAPASITAS JALAN PERKOTAAN", fontsize=13,
                fontweight="bold", va="top")
        ax.text(0, 0.968, "Acuan: Pedoman Kapasitas Jalan Indonesia (PKJI)", fontsize=9, color=TINTA_2, va="top")
        ax.text(0, 0.950, f"{identitas}", fontsize=9, color=TINTA_2, va="top")
        ax.text(0, 0.932, f"Ruas: {nama_ruas or '-'}   |   Tanggal: {datetime.date.today().strftime('%d-%m-%Y')}",
                fontsize=9, color=TINTA_2, va="top")

        ax.text(0, 0.900, "A. Data masukan", fontsize=10.5, fontweight="bold", va="top")
        masukan = [
            ["Tipe jalan", param["tipe"]],
            ["Lebar jalur efektif total (m)", fmt_id(param["lebar_total"], 2)],
            ["Arus pada arah terbesar (%)", fmt_id(param["split"], 0)],
            ["Tepi jalan", "Berbahu" if param["jenis_hs"] == "bahu" else "Berkereb"],
            ["Lebar bahu / jarak kereb ke penghalang (m)", fmt_id(param["lebar_hs"], 2)],
            ["Kelas hambatan samping", param["kelas_hs"]],
            ["Ukuran kota (juta jiwa, nilai wakil kelas)", fmt_id(param["ukuran_kota_juta"], 2)],
            ["Kendaraan ringan, KR (kend/jam)", fmt_id(param["kr"], 0)],
            ["Kendaraan berat, KB (kend/jam)", fmt_id(param["kb"], 0)],
            ["Sepeda motor, SM (kend/jam)", fmt_id(param["sm"], 0)],
        ]
        y = _tabel(ax, 0.882, masukan, ["Parameter", "Nilai"], [0.7, 0.3])

        ax.text(0, y - 0.022, "B. Hasil perhitungan", fontsize=10.5, fontweight="bold", va="top")
        rincian = format_rincian(h["rincian"])
        baris = rincian.values.tolist()
        tebal = [i for i, r in enumerate(baris) if r[0].startswith(("KAPASITAS", "DERAJAT"))]
        y = _tabel(ax, y - 0.044, baris, ["Parameter", "Satuan", "Nilai"], [0.6, 0.15, 0.25], tebal=tebal)

        ax.text(0, y - 0.022, "C. Kesimpulan", fontsize=10.5, fontweight="bold", va="top")
        simbol = "≤" if ok else ">"
        kesimpulan = (f"Derajat kejenuhan DJ = {fmt_id(h['DJ'], 3)} {simbol} {fmt_id(BATAS_DJ, 2)}, sehingga kinerja "
                      f"ruas jalan {'MEMENUHI' if ok else 'TIDAK MEMENUHI'} syarat (tingkat pelayanan {h['LOS']}).")
        teks = "\n".join(textwrap.wrap(kesimpulan, 100))
        for p in h["peringatan"]:
            teks += "\n\nPeringatan: " + "\n".join(textwrap.wrap(p, 100))
        ax.text(0, y - 0.046, teks, fontsize=9, va="top", linespacing=1.4)

        ax.text(0, 0.0, "Dibuat dengan Kalkulator Kapasitas Jalan Perkotaan. Untuk keperluan pembelajaran; "
                        "nilai tabel perlu dicocokkan dengan edisi PKJI yang berlaku.",
                fontsize=7.5, color=REDUP, va="bottom")
        pdf.savefig(fig)
        plt.close(fig)

        # ---------- Halaman 2: grafik ----------
        fig = plt.figure(figsize=_A4)
        fig.text(0.08, 0.955, "D. Grafik", fontsize=10.5, fontweight="bold", va="top")
        _panel_q_c(fig.add_axes([0.14, 0.62, 0.78, 0.28]), h)
        _panel_hs(fig.add_axes([0.14, 0.17, 0.78, 0.30]), h, param)
        fig.text(0.08, 0.04, "Grafik atas membandingkan arus dan kapasitas; grafik bawah menunjukkan "
                             "sensitivitas kapasitas terhadap kelas hambatan samping.", fontsize=7.5, color=REDUP)
        pdf.savefig(fig)
        plt.close(fig)
    return buf.getvalue()


# Catatan palet: biru #2a78d6 dan oranye #eb6834 adalah slot 1 dan 2 palet kategorikal
# referensi; pasangan ini lolos seluruh pemeriksaan validator pada permukaan #fcfcfb
# (CVD dE 24,7; penglihatan normal dE 33,6; kontras >= 3:1).
