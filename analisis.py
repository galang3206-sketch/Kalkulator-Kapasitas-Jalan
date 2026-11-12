"""Analisis lanjutan di atas perhitungan kapasitas dasar (tanpa tampilan).

- skenario_perbaikan : bandingkan beberapa usulan perbaikan jalan
- lebar_minimum      : lebar jalur terkecil agar DJ memenuhi batas
- proyeksi           : DJ dari tahun ke tahun bila lalu lintas tumbuh
- jam_puncak         : jam puncak dan PHF dari data survei per 15 menit
- langkah_perhitungan: rumus dengan angka yang sudah disubstitusi (LaTeX)
"""
import numpy as np
import pandas as pd

from kapasitas import FC_LJ_TABEL, KELAS_HS, TIPE_JALAN, hitung_kapasitas

BATAS_DJ = 0.85


# ------------------------------------------------------------
# Format angka untuk LaTeX (koma desimal Indonesia)
# ------------------------------------------------------------
def _angka(x, nd=3):
    return f"{x:.{nd}f}".replace(".", "{,}")


def _bil(x):
    """Bilangan bulat tampil tanpa desimal, selain itu 2 desimal."""
    x = float(x)
    return str(int(x)) if x.is_integer() else _angka(x, 2)


def _koma(x):
    return f"{x:g}".replace(".", ",")


# ------------------------------------------------------------
# Langkah perhitungan
# ------------------------------------------------------------
def langkah_perhitungan(param, h):
    """Daftar (judul, rumus LaTeX) berisi substitusi angka untuk C, Q, dan DJ."""
    c = (r"C = C_0 \times FC_{LJ} \times FC_{PA} \times FC_{HS} \times FC_{UK}"
         + f" = {_angka(h['C0'], 0)} \\times {_angka(h['FC_LJ'])} \\times {_angka(h['FC_PA'])}"
         + f" \\times {_angka(h['FC_HS'])} \\times {_angka(h['FC_UK'])}"
         + f" = {_angka(h['C'], 0)}\\ \\text{{smp/jam}}")
    q = (r"Q = KR \times 1{,}0 + KB \times emp_{KB} + SM \times emp_{SM}"
         + f" = {_bil(param['kr'])} \\times 1{{,}}0 + {_bil(param['kb'])} \\times {_angka(h['emp_KB'], 2)}"
         + f" + {_bil(param['sm'])} \\times {_angka(h['emp_SM'], 2)}"
         + f" = {_angka(h['Q'], 0)}\\ \\text{{smp/jam}}")
    dj = (r"DJ = \dfrac{Q}{C}" + f" = \\dfrac{{{_angka(h['Q'], 0)}}}{{{_angka(h['C'], 0)}}}"
          + f" = {_angka(h['DJ'])}")
    return [("1. Kapasitas jalan", c), ("2. Arus lalu lintas", q), ("3. Derajat kejenuhan", dj)]


# ------------------------------------------------------------
# Skenario perbaikan
# ------------------------------------------------------------
def skenario_perbaikan(param):
    """Bandingkan kondisi eksisting dengan beberapa usulan perbaikan."""
    lajur = TIPE_JALAN[param["tipe"]]["lajur"]
    idx = KELAS_HS.index(param["kelas_hs"])
    kelas_turun = KELAS_HS[max(idx - 1, 0)]
    w, hs = param["lebar_total"], param["lebar_hs"]

    daftar = [
        ("Kondisi eksisting", {}),
        (f"Perlebar jalur +{_koma(0.5 * lajur)} m", {"lebar_total": w + 0.5 * lajur}),
        (f"Perlebar jalur +{_koma(1.0 * lajur)} m", {"lebar_total": w + 1.0 * lajur}),
        ("Perlebar bahu / jarak kereb +0,5 m", {"lebar_hs": hs + 0.5}),
    ]
    if idx >= 1:
        daftar.append((f"Hambatan samping turun ke '{kelas_turun}'", {"kelas_hs": kelas_turun}))
    if idx >= 2:
        daftar.append(("Hambatan samping 'Sangat rendah'", {"kelas_hs": KELAS_HS[0]}))
    daftar.append((
        "Kombinasi: lebar +" + _koma(0.5 * lajur) + " m, bahu +0,5 m, HS turun satu kelas",
        {"lebar_total": w + 0.5 * lajur, "lebar_hs": hs + 0.5, "kelas_hs": kelas_turun},
    ))

    baris = []
    for nama, ubah in daftar:
        p = dict(param)
        p.update(ubah)
        h = hitung_kapasitas(**p)
        baris.append({
            "Skenario": nama,
            "Lebar (m)": p["lebar_total"],
            "Kelas HS": p["kelas_hs"],
            "C (smp/jam)": h["C"],
            "Q (smp/jam)": h["Q"],
            "DJ": h["DJ"],
            "LOS": h["LOS"],
            "Status": "Memenuhi" if h["DJ"] <= BATAS_DJ else "Tidak memenuhi",
            "Catatan": "Di luar rentang tabel PKJI" if h["peringatan"] else "",
        })
    return pd.DataFrame(baris)


def rentang_lebar(tipe):
    """Rentang lebar jalur TOTAL (m) yang tercakup tabel FC_LJ untuk tipe jalan ini."""
    faktor = 1 if tipe == "2/2 TT" else TIPE_JALAN[tipe]["lajur"]
    tabel = FC_LJ_TABEL[tipe]
    return tabel[0][0] * faktor, tabel[-1][0] * faktor


def lebar_minimum(param, target=BATAS_DJ):
    """Lebar jalur total terkecil (m) yang membuat DJ <= target, atau None.

    Dicari hanya di dalam rentang lebar pada tabel FC_LJ, supaya hasilnya
    tidak bergantung pada nilai yang diperpanjang di luar tabel.
    """
    awal, akhir = rentang_lebar(param["tipe"])
    for w in np.arange(awal, akhir + 1e-9, 0.05):
        p = dict(param)
        p["lebar_total"] = round(float(w), 2)
        if hitung_kapasitas(**p)["DJ"] <= target:
            return p["lebar_total"]
    return None


# ------------------------------------------------------------
# Proyeksi pertumbuhan lalu lintas
# ------------------------------------------------------------
def proyeksi(param, tumbuh_persen, tahun=20):
    """DJ tiap tahun bila semua volume tumbuh geometrik: Qn = Q0 x (1 + i)^n.

    Mengembalikan (tabel, tahun_jenuh). tahun_jenuh adalah tahun ke-n pertama
    saat DJ melewati batas, atau None bila tidak terlewati dalam rentang tahun.
    """
    baris = []
    for n in range(int(tahun) + 1):
        f = (1 + tumbuh_persen / 100.0) ** n
        p = dict(param)
        p.update(kr=param["kr"] * f, kb=param["kb"] * f, sm=param["sm"] * f)
        h = hitung_kapasitas(**p)
        baris.append({"Tahun ke-": n, "Q (smp/jam)": h["Q"], "C (smp/jam)": h["C"],
                      "DJ": h["DJ"], "LOS": h["LOS"]})
    df = pd.DataFrame(baris)
    lewat = df[df["DJ"] > BATAS_DJ]
    tahun_jenuh = int(lewat.iloc[0]["Tahun ke-"]) if len(lewat) else None
    return df, tahun_jenuh


# ------------------------------------------------------------
# Survei per 15 menit -> jam puncak dan PHF
# ------------------------------------------------------------
KOLOM_SURVEI = ["waktu", "KR", "KB", "SM"]


def contoh_survei():
    """Contoh data survei 06:00-09:00 (12 interval 15 menit) untuk template."""
    kr = [90, 110, 140, 165, 175, 160, 140, 125, 110, 100, 95, 90]
    kb = [12, 14, 18, 20, 22, 19, 17, 15, 14, 12, 12, 11]
    sm = [260, 340, 450, 540, 560, 510, 430, 380, 330, 300, 280, 270]
    waktu = [f"{6 + (i * 15) // 60:02d}:{(i * 15) % 60:02d}" for i in range(12)]
    return pd.DataFrame({"waktu": waktu, "KR": kr, "KB": kb, "SM": sm})


def jam_puncak(df):
    """Cari 4 interval 15 menit berurutan dengan volume total terbesar.

    Data harus berurutan menurut waktu. PHF = V_jam / (4 x V_15_maks).
    """
    kurang = [k for k in KOLOM_SURVEI if k not in df.columns]
    if kurang:
        raise ValueError("Kolom belum lengkap: " + ", ".join(kurang))
    d = df[KOLOM_SURVEI].copy().reset_index(drop=True)
    kend = ["KR", "KB", "SM"]
    for k in kend:
        d[k] = pd.to_numeric(d[k], errors="coerce")
    if d[kend].isna().any().any():
        raise ValueError("KR, KB, dan SM harus berupa angka dan tidak boleh kosong.")
    if (d[kend] < 0).any().any():
        raise ValueError("Volume tidak boleh negatif.")
    if len(d) < 4:
        raise ValueError("Minimal 4 baris (1 jam) data per 15 menit.")

    d["waktu"] = d["waktu"].astype(str)
    d["Total"] = d[kend].sum(axis=1)
    if d["Total"].max() <= 0:
        raise ValueError("Semua volume bernilai nol.")

    jendela = d["Total"].rolling(4).sum()
    akhir = int(jendela.idxmax())
    awal = akhir - 3
    v_jam = float(jendela.iloc[akhir])
    v15 = float(d["Total"].max())
    d["Jam puncak"] = False
    d.loc[awal:akhir, "Jam puncak"] = True

    return {
        "tabel": d,
        "waktu_awal": d.loc[awal, "waktu"],
        "KR": float(d.loc[awal:akhir, "KR"].sum()),
        "KB": float(d.loc[awal:akhir, "KB"].sum()),
        "SM": float(d.loc[awal:akhir, "SM"].sum()),
        "total": v_jam,
        "v15_maks": v15,
        "PHF": v_jam / (4 * v15),
    }
