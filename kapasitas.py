"""Data tabel PKJI dan fungsi perhitungan kapasitas jalan perkotaan.

Modul ini murni perhitungan (tanpa tampilan) sehingga mudah diuji.
Nilai tabel harus dicocokkan dengan dokumen PKJI yang dipakai dosen.
"""
import numpy as np
import pandas as pd

# ============================================================
# SEL 2 - DATA TABEL PKJI (JALAN PERKOTAAN)
# Catatan: cocokkan nilai di bawah dengan dokumen PKJI yang
# dipakai dosen Anda. Jika ada selisih, cukup ubah angkanya di sini.
# ============================================================

# Tipe jalan: jumlah lajur total, dan kapasitas dasar C0 (smp/jam)
# 2/2 TT  -> C0 total dua arah | 4/2 TT dan 4/2 T -> C0 per lajur
TIPE_JALAN = {
    "2/2 TT": {"nama": "Dua-lajur tak-terbagi",   "lajur": 2, "C0": 2900, "C0_basis": "total"},
    "4/2 TT": {"nama": "Empat-lajur tak-terbagi", "lajur": 4, "C0": 1500, "C0_basis": "per lajur"},
    "4/2 T":  {"nama": "Empat-lajur terbagi",     "lajur": 4, "C0": 1650, "C0_basis": "per lajur"},
}

# FC_LJ : (lebar efektif, faktor)
# 2/2 TT -> lebar total dua arah | 4 lajur -> lebar per lajur
FC_LJ_TABEL = {
    "2/2 TT": [(5, 0.56), (6, 0.87), (7, 1.00), (8, 1.14), (9, 1.25), (10, 1.29), (11, 1.34)],
    "4/2 TT": [(3.00, 0.91), (3.25, 0.95), (3.50, 1.00), (3.75, 1.05), (4.00, 1.09)],
    "4/2 T":  [(3.00, 0.92), (3.25, 0.96), (3.50, 1.00), (3.75, 1.04), (4.00, 1.08)],
}

# FC_PA : (persen arah terbesar, faktor). 4/2 T tidak terpengaruh (=1,00)
FC_PA_TABEL = {
    "2/2 TT": [(50, 1.00), (55, 0.97),  (60, 0.94), (65, 0.91),  (70, 0.88)],
    "4/2 TT": [(50, 1.00), (55, 0.975), (60, 0.95), (65, 0.925), (70, 0.90)],
}

# FC_HS : kolom = lebar bahu/jarak kereb-penghalang [<=0,5 ; 1,0 ; 1,5 ; >=2,0] m
KELAS_HS = ["Sangat rendah", "Rendah", "Sedang", "Tinggi", "Sangat tinggi"]
LEBAR_HS_KOLOM = [0.5, 1.0, 1.5, 2.0]

FC_HS_TABEL = {
    # Jalan BERBAHU
    ("bahu", "T"): {
        "Sangat rendah": [0.96, 0.98, 1.01, 1.03],
        "Rendah":        [0.94, 0.97, 1.00, 1.02],
        "Sedang":        [0.92, 0.95, 0.98, 1.00],
        "Tinggi":        [0.88, 0.92, 0.95, 0.98],
        "Sangat tinggi": [0.84, 0.88, 0.92, 0.96],
    },
    ("bahu", "TT"): {
        "Sangat rendah": [0.94, 0.96, 0.99, 1.01],
        "Rendah":        [0.92, 0.94, 0.97, 1.00],
        "Sedang":        [0.89, 0.92, 0.95, 0.98],
        "Tinggi":        [0.82, 0.86, 0.90, 0.95],
        "Sangat tinggi": [0.73, 0.79, 0.85, 0.91],
    },
    # Jalan BERKERB
    ("kereb", "T"): {
        "Sangat rendah": [0.95, 0.97, 0.99, 1.01],
        "Rendah":        [0.94, 0.96, 0.98, 1.00],
        "Sedang":        [0.91, 0.93, 0.95, 0.98],
        "Tinggi":        [0.86, 0.89, 0.92, 0.95],
        "Sangat tinggi": [0.81, 0.85, 0.88, 0.92],
    },
    ("kereb", "TT"): {
        "Sangat rendah": [0.93, 0.95, 0.97, 0.99],
        "Rendah":        [0.90, 0.92, 0.95, 0.97],
        "Sedang":        [0.86, 0.88, 0.91, 0.94],
        "Tinggi":        [0.78, 0.81, 0.84, 0.88],
        "Sangat tinggi": [0.68, 0.72, 0.77, 0.82],
    },
}

# FC_UK : batas atas jumlah penduduk (juta jiwa) -> faktor
FC_UK_TABEL = [(0.1, 0.86), (0.5, 0.90), (1.0, 0.94), (3.0, 1.00), (float("inf"), 1.04)]
UKURAN_KOTA_OPSI = {
    "< 0,1 juta jiwa": 0.05,
    "0,1 - 0,5 juta jiwa": 0.3,
    "0,5 - 1,0 juta jiwa": 0.75,
    "1,0 - 3,0 juta jiwa": 2.0,
    "> 3,0 juta jiwa": 4.0,
}

# EMP (ekivalensi mobil penumpang): KB = kendaraan berat, SM = sepeda motor
# Batas arus total (kend/jam, dua arah) untuk berpindah ke emp "arus tinggi"
EMP_BATAS_ARUS = {"2/2 TT": 1800, "4/2 TT": 3700, "4/2 T": 3600}



# ============================================================
# SEL 3 - FUNGSI PERHITUNGAN
# ============================================================

def _interp(x, tabel):
    xs = [t[0] for t in tabel]
    ys = [t[1] for t in tabel]
    return float(np.interp(x, xs, ys))


def fc_lebar(tipe, lebar_total):
    """FC_LJ. Untuk 4 lajur, tabel memakai lebar PER LAJUR."""
    lebar_pakai = lebar_total if tipe == "2/2 TT" else lebar_total / TIPE_JALAN[tipe]["lajur"]
    return _interp(lebar_pakai, FC_LJ_TABEL[tipe]), lebar_pakai


def fc_pemisahan(tipe, split):
    """FC_PA. split = persen arus pada arah terbesar (50-100)."""
    if tipe == "4/2 T":
        return 1.0
    split = max(split, 100 - split)  # pastikan >= 50
    return _interp(split, FC_PA_TABEL[tipe])


def fc_hambatan_samping(tipe, jenis, kelas, lebar_hs):
    """FC_HS. jenis = 'bahu' atau 'kereb'. lebar_hs = lebar bahu efektif / jarak kereb-penghalang (m)."""
    grup = "T" if tipe == "4/2 T" else "TT"
    nilai = FC_HS_TABEL[(jenis, grup)][kelas]
    return float(np.interp(lebar_hs, LEBAR_HS_KOLOM, nilai))


def fc_ukuran_kota(juta_penduduk):
    for batas, nilai in FC_UK_TABEL:
        if juta_penduduk < batas:
            return nilai
    return FC_UK_TABEL[-1][1]


def kelas_hambatan_samping(frekuensi_berbobot):
    """Opsional: kelas hambatan samping dari frekuensi berbobot kejadian per 200 m per jam."""
    if frekuensi_berbobot < 100:   return "Sangat rendah"
    if frekuensi_berbobot < 300:   return "Rendah"
    if frekuensi_berbobot < 500:   return "Sedang"
    if frekuensi_berbobot < 900:   return "Tinggi"
    return "Sangat tinggi"


def nilai_emp(tipe, arus_total_kend, lebar_total):
    """Mengembalikan (emp_KB, emp_SM)."""
    tinggi = arus_total_kend >= EMP_BATAS_ARUS[tipe]
    if tipe == "2/2 TT":
        emp_kb = 1.2 if tinggi else 1.3
        if lebar_total <= 6:
            emp_sm = 0.35 if tinggi else 0.50
        else:
            emp_sm = 0.25 if tinggi else 0.40
    else:  # 4/2 TT dan 4/2 T
        emp_kb = 1.2 if tinggi else 1.3
        emp_sm = 0.25 if tinggi else 0.40
    return emp_kb, emp_sm


def tingkat_pelayanan(dj):
    """Tingkat pelayanan (LOS) berdasarkan derajat kejenuhan."""
    batas = [(0.20, "A"), (0.44, "B"), (0.74, "C"), (0.84, "D"), (1.00, "E")]
    for b, los in batas:
        if dj <= b:
            return los
    return "F"


def hitung_kapasitas(tipe, lebar_total, split, jenis_hs, kelas_hs, lebar_hs,
                     ukuran_kota_juta, kr, kb, sm):
    """Menghitung C, Q, dan DJ. Mengembalikan dictionary hasil."""
    # ---- Validasi input ----
    if tipe not in TIPE_JALAN:
        raise ValueError("Tipe jalan tidak dikenal.")
    if lebar_total <= 0:
        raise ValueError("Lebar jalur harus lebih dari 0.")
    if not (50 <= max(split, 100 - split) <= 100) or not (0 <= split <= 100):
        raise ValueError("Pemisahan arah harus antara 0 dan 100 (%).")
    if lebar_hs < 0:
        raise ValueError("Lebar bahu / jarak kereb tidak boleh negatif.")
    if min(kr, kb, sm) < 0:
        raise ValueError("Volume kendaraan tidak boleh negatif.")
    if kelas_hs not in KELAS_HS:
        raise ValueError("Kelas hambatan samping tidak valid.")

    peringatan = []

    # ---- Faktor penyesuaian ----
    info = TIPE_JALAN[tipe]
    c0_total = info["C0"] if info["C0_basis"] == "total" else info["C0"] * info["lajur"]
    fc_lj, lebar_pakai = fc_lebar(tipe, lebar_total)
    fc_pa = fc_pemisahan(tipe, split)
    fc_hs = fc_hambatan_samping(tipe, jenis_hs, kelas_hs, lebar_hs)
    fc_uk = fc_ukuran_kota(ukuran_kota_juta)

    rentang = [t[0] for t in FC_LJ_TABEL[tipe]]
    if lebar_pakai < rentang[0] or lebar_pakai > rentang[-1]:
        peringatan.append(f"Lebar efektif {lebar_pakai:.2f} m di luar rentang tabel "
                          f"({rentang[0]}-{rentang[-1]} m); nilai FC_LJ dibatasi pada ujung tabel.")
    if max(split, 100 - split) > 70 and tipe != "4/2 T":
        peringatan.append("Pemisahan arah > 70:30 di luar rentang tabel; FC_PA dibatasi pada 0,70 tabel.")

    # ---- Kapasitas ----
    kapasitas = c0_total * fc_lj * fc_pa * fc_hs * fc_uk

    # ---- Arus lalu lintas (smp/jam) ----
    arus_total = kr + kb + sm
    emp_kb, emp_sm = nilai_emp(tipe, arus_total, lebar_total)
    q = kr * 1.0 + kb * emp_kb + sm * emp_sm

    dj = q / kapasitas
    status = "MEMENUHI (DJ <= 0,85)" if dj <= 0.85 else "TIDAK MEMENUHI (DJ > 0,85)"

    # ---- Tabel rincian ----
    rincian = pd.DataFrame([
        ["Kapasitas dasar C0 (total)", "smp/jam", c0_total],
        ["Faktor lebar jalur FC_LJ", "-", fc_lj],
        ["Faktor pemisahan arah FC_PA", "-", fc_pa],
        ["Faktor hambatan samping FC_HS", "-", fc_hs],
        ["Faktor ukuran kota FC_UK", "-", fc_uk],
        ["KAPASITAS C", "smp/jam", kapasitas],
        ["emp Kendaraan Berat (KB)", "-", emp_kb],
        ["emp Sepeda Motor (SM)", "-", emp_sm],
        ["Arus total Q", "smp/jam", q],
        ["DERAJAT KEJENUHAN DJ = Q/C", "-", dj],
        ["Tingkat pelayanan (LOS)", "-", tingkat_pelayanan(dj)],
    ], columns=["Parameter", "Satuan", "Nilai"])

    return {
        "tipe": tipe, "C0": c0_total, "FC_LJ": fc_lj, "FC_PA": fc_pa, "FC_HS": fc_hs,
        "FC_UK": fc_uk, "C": kapasitas, "emp_KB": emp_kb, "emp_SM": emp_sm,
        "Q": q, "DJ": dj, "LOS": tingkat_pelayanan(dj), "status": status,
        "peringatan": peringatan, "rincian": rincian,
    }



# ============================================================
# HITUNG BANYAK RUAS SEKALIGUS (CSV / EXCEL)
# ============================================================
KOLOM_BATCH = ["nama_ruas", "tipe", "lebar_total", "split", "jenis_hs", "kelas_hs",
               "lebar_hs", "ukuran_kota_juta", "KR", "KB", "SM"]


def hitung_batch(df):
    """Menghitung banyak ruas. Baris yang salah tidak menghentikan baris lain."""
    baris = []
    for _, r in df.iterrows():
        try:
            if r[KOLOM_BATCH].isna().any():
                raise ValueError("ada kolom yang kosong")
            h = hitung_kapasitas(str(r["tipe"]).strip(), float(r["lebar_total"]), float(r["split"]),
                                 str(r["jenis_hs"]).strip(), str(r["kelas_hs"]).strip(),
                                 float(r["lebar_hs"]), float(r["ukuran_kota_juta"]),
                                 float(r["KR"]), float(r["KB"]), float(r["SM"]))
            baris.append({"Ruas": r["nama_ruas"], "Tipe": r["tipe"],
                          "C (smp/jam)": round(h["C"]), "Q (smp/jam)": round(h["Q"]),
                          "DJ": round(h["DJ"], 3), "LOS": h["LOS"],
                          "Status": "Memenuhi" if h["DJ"] <= 0.85 else "Tidak memenuhi"})
        except Exception as e:
            baris.append({"Ruas": r.get("nama_ruas", "?"), "Tipe": r.get("tipe", "?"),
                          "C (smp/jam)": None, "Q (smp/jam)": None, "DJ": None,
                          "LOS": None, "Status": f"Galat: {e}"})
    return pd.DataFrame(baris)
