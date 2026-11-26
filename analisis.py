"""Analisis lanjutan di atas perhitungan kapasitas dasar (tanpa tampilan).

- skenario_perbaikan : bandingkan usulan perbaikan (termasuk skenario buatan sendiri)
- lebar_minimum      : lebar jalur terkecil agar DJ memenuhi batas
- proyeksi           : DJ dari tahun ke tahun bila lalu lintas tumbuh
- jam_puncak         : jam puncak dan PHF dari data survei per 15 menit
- langkah_perhitungan: rumus dengan angka yang sudah disubstitusi (LaTeX)
- interpretasi       : kalimat penjelasan hasil dalam bahasa Indonesia
- daftar ruas        : baris perbandingan, ekspor/impor CSV
- CONTOH_KASUS       : data contoh yang bisa dimuat satu klik
"""
import json

import numpy as np
import pandas as pd

from kapasitas import (
    FC_LJ_TABEL,
    KELAS_HS,
    TIPE_JALAN,
    UKURAN_KOTA_OPSI,
    hitung_kapasitas,
)

BATAS_DJ = 0.85
NAMA_KUSTOM = "Skenario Anda"


# ------------------------------------------------------------
# Format angka (koma desimal Indonesia)
# ------------------------------------------------------------
def _angka(x, nd=3):
    return f"{x:.{nd}f}".replace(".", "{,}")


def _bil(x):
    """Bilangan bulat tampil tanpa desimal, selain itu 2 desimal."""
    x = float(x)
    return str(int(x)) if x.is_integer() else _angka(x, 2)


def _koma(x):
    return f"{x:g}".replace(".", ",")


def _idf(x, nd=3):
    """Angka biasa dengan koma desimal (untuk kalimat, bukan LaTeX)."""
    return f"{x:.{nd}f}".replace(".", ",")


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
# Interpretasi hasil
# ------------------------------------------------------------
DESKRIPSI_LOS = {
    "A": "arus bebas, pengemudi hampir tidak terpengaruh kendaraan lain",
    "B": "arus stabil, mulai terasa pengaruh kendaraan lain",
    "C": "arus stabil, kecepatan mulai dibatasi oleh lalu lintas",
    "D": "mendekati arus tidak stabil, kecepatan menurun dan peka terhadap gangguan",
    "E": "arus tidak stabil, volume mendekati kapasitas",
    "F": "arus terhambat, antrean dan tundaan panjang",
}


def interpretasi(param, h):
    """Beberapa kalimat penjelasan hasil: kondisi, faktor pembatas, dan langkah berikutnya."""
    ok = h["DJ"] <= BATAS_DJ
    kalimat = [f"DJ = {_idf(h['DJ'])} termasuk tingkat pelayanan {h['LOS']} "
               f"({DESKRIPSI_LOS[h['LOS']]})."]

    # Faktor yang bisa diperbaiki pengelola jalan: lebar jalur dan hambatan samping
    bisa = {"lebar jalur (FC_LJ)": h["FC_LJ"], "hambatan samping (FC_HS)": h["FC_HS"]}
    nama_f = min(bisa, key=bisa.get)
    if bisa[nama_f] < 0.98:
        kalimat.append(f"Faktor yang paling mengurangi kapasitas dan masih bisa diperbaiki adalah "
                       f"{nama_f} = {_idf(bisa[nama_f])}.")

    if KELAS_HS.index(param["kelas_hs"]) >= 1:
        p = dict(param)
        p["kelas_hs"] = KELAS_HS[0]
        naik = hitung_kapasitas(**p)["C"] / h["C"] - 1
        if naik >= 0.02:
            kalimat.append(f"Bila hambatan samping dapat ditekan ke 'Sangat rendah' (penertiban parkir "
                           f"dan pedagang kaki lima), kapasitas naik sekitar {naik * 100:.0f}%.")

    if h["Q"] > 0:
        if ok:
            cadangan = (BATAS_DJ * h["C"] / h["Q"] - 1) * 100
            kalimat.append(f"Arus masih dapat bertambah sekitar {cadangan:.0f}% sebelum DJ mencapai "
                           f"{_idf(BATAS_DJ, 2)}.")
        else:
            naik_c = (h["Q"] / BATAS_DJ / h["C"] - 1) * 100
            turun_q = (1 - BATAS_DJ * h["C"] / h["Q"]) * 100
            kalimat.append(f"Agar DJ ≤ {_idf(BATAS_DJ, 2)}, kapasitas perlu naik sekitar {naik_c:.0f}% "
                           f"atau arus turun sekitar {turun_q:.0f}%. Lihat tab Skenario perbaikan.")
    return kalimat


# ------------------------------------------------------------
# Skenario perbaikan
# ------------------------------------------------------------
def ubah_skenario(param, d_lebar=0.0, d_bahu=0.0, kelas_hs=None, d_volume_persen=0.0):
    """Susun perubahan parameter untuk skenario buatan sendiri."""
    f = 1 + d_volume_persen / 100.0
    return {
        "lebar_total": param["lebar_total"] + d_lebar,
        "lebar_hs": param["lebar_hs"] + d_bahu,
        "kelas_hs": kelas_hs or param["kelas_hs"],
        "kr": param["kr"] * f, "kb": param["kb"] * f, "sm": param["sm"] * f,
    }


def skenario_perbaikan(param, kustom=None):
    """Bandingkan kondisi eksisting dengan beberapa usulan perbaikan.

    kustom: dict perubahan dari ubah_skenario(); ditambahkan sebagai baris NAMA_KUSTOM.
    """
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
    if kustom is not None:
        daftar.append((NAMA_KUSTOM, kustom))

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
    """DJ tiap tahun bila volume tumbuh geometrik: Qn = Q0 x (1 + i)^n.

    tumbuh_persen boleh berupa satu angka (semua jenis kendaraan sama) atau dict
    {"kr": ..., "kb": ..., "sm": ...} bila laju pertumbuhan tiap jenis berbeda.
    Mengembalikan (tabel, tahun_jenuh). tahun_jenuh adalah tahun ke-n pertama
    saat DJ melewati batas, atau None bila tidak terlewati dalam rentang tahun.
    """
    if isinstance(tumbuh_persen, dict):
        laju = {k: float(tumbuh_persen[k]) for k in ("kr", "kb", "sm")}
    else:
        laju = {k: float(tumbuh_persen) for k in ("kr", "kb", "sm")}

    baris = []
    for n in range(int(tahun) + 1):
        p = dict(param)
        for k in ("kr", "kb", "sm"):
            p[k] = param[k] * (1 + laju[k] / 100.0) ** n
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


# ------------------------------------------------------------
# Data masukan: contoh kasus dan pemetaan ke widget
# ------------------------------------------------------------
KUNCI_PARAM = ["tipe", "lebar_total", "split", "jenis_hs", "kelas_hs", "lebar_hs",
               "ukuran_kota_juta", "kr", "kb", "sm"]

CONTOH_KASUS = {
    "Kolektor lancar (2/2 TT)": {
        "nama": "Jl. Kolektor Contoh",
        "param": dict(tipe="2/2 TT", lebar_total=7.0, split=50.0, jenis_hs="bahu", kelas_hs="Rendah",
                      lebar_hs=1.5, ukuran_kota_juta=0.3, kr=350.0, kb=40.0, sm=700.0),
    },
    "Arteri padat (4/2 T)": {
        "nama": "Jl. Arteri Contoh",
        "param": dict(tipe="4/2 T", lebar_total=14.0, split=50.0, jenis_hs="kereb", kelas_hs="Tinggi",
                      lebar_hs=1.0, ukuran_kota_juta=2.0, kr=2800.0, kb=380.0, sm=5200.0),
    },
    "Jalan pasar jenuh (2/2 TT)": {
        "nama": "Jl. Pasar Contoh",
        "param": dict(tipe="2/2 TT", lebar_total=6.0, split=60.0, jenis_hs="bahu", kelas_hs="Sangat tinggi",
                      lebar_hs=0.5, ukuran_kota_juta=0.3, kr=900.0, kb=120.0, sm=2000.0),
    },
}


def label_kota(juta):
    """Label ukuran kota (kunci UKURAN_KOTA_OPSI) yang paling dekat dengan nilai juta jiwa."""
    return min(UKURAN_KOTA_OPSI, key=lambda k: abs(UKURAN_KOTA_OPSI[k] - float(juta)))


def input_dari_param(nama, param):
    """Pemetaan param -> nilai widget input (semua angka bertipe float)."""
    return {
        "in_nama": str(nama),
        "in_tipe": param["tipe"],
        "in_lebar": float(param["lebar_total"]),
        "in_split": float(param["split"]),
        "in_jenis": param["jenis_hs"],
        "in_lebar_hs": float(param["lebar_hs"]),
        "in_kelas": param["kelas_hs"],
        "in_kota": label_kota(param["ukuran_kota_juta"]),
        "in_kr": float(param["kr"]),
        "in_kb": float(param["kb"]),
        "in_sm": float(param["sm"]),
    }


DEFAULT_INPUT = input_dari_param("Ruas 1", dict(
    tipe="2/2 TT", lebar_total=7.0, split=50.0, jenis_hs="bahu", kelas_hs="Sedang", lebar_hs=1.0,
    ukuran_kota_juta=0.3, kr=600.0, kb=80.0, sm=1200.0))


# ------------------------------------------------------------
# Daftar perbandingan ruas (simpan, ekspor, impor)
# ------------------------------------------------------------
def baris_daftar(nama, param):
    """Hitung satu ruas dan kembalikan baris untuk daftar perbandingan."""
    h = hitung_kapasitas(**param)
    return {
        "Ruas": str(nama), "Tipe": param["tipe"], "Lebar (m)": float(param["lebar_total"]),
        "Kelas HS": param["kelas_hs"], "C (smp/jam)": h["C"], "Q (smp/jam)": h["Q"],
        "DJ": h["DJ"], "LOS": h["LOS"],
        "Status": "Memenuhi" if h["DJ"] <= BATAS_DJ else "Tidak memenuhi",
        "param": json.dumps({k: param[k] for k in KUNCI_PARAM}),
    }


def simpan_ke_daftar(daftar, baris):
    """Tambahkan baris; bila nama ruas sama, baris lama diganti."""
    return [r for r in daftar if r["Ruas"] != baris["Ruas"]] + [baris]


def daftar_ke_csv(daftar):
    return pd.DataFrame(daftar).to_csv(index=False).encode("utf-8")


def daftar_dari_csv(df):
    """Bangun ulang daftar dari CSV hasil ekspor. Hasil dihitung ulang dari parameter.

    Mengembalikan (daftar, jumlah_baris_gagal).
    """
    if "Ruas" not in df.columns or "param" not in df.columns:
        raise ValueError("File bukan hasil ekspor daftar perbandingan (kolom 'Ruas' dan 'param' tidak ada).")
    hasil, gagal = [], 0
    for _, r in df.iterrows():
        try:
            param = json.loads(r["param"])
            if any(k not in param for k in KUNCI_PARAM):
                raise ValueError("parameter tidak lengkap")
            hasil = simpan_ke_daftar(hasil, baris_daftar(r["Ruas"], param))
        except Exception:
            gagal += 1
    return hasil, gagal


def param_dari_batch(r):
    """Ubah satu baris data 'banyak ruas' menjadi dict param."""
    return dict(tipe=str(r["tipe"]).strip(), lebar_total=float(r["lebar_total"]), split=float(r["split"]),
                jenis_hs=str(r["jenis_hs"]).strip(), kelas_hs=str(r["kelas_hs"]).strip(),
                lebar_hs=float(r["lebar_hs"]), ukuran_kota_juta=float(r["ukuran_kota_juta"]),
                kr=float(r["KR"]), kb=float(r["KB"]), sm=float(r["SM"]))
