"""Uji otomatis perhitungan. Jalankan:  python test_kapasitas.py   (atau: pytest)

Berguna sebagai bukti validasi di laporan: hasil program dibandingkan dengan hitungan manual.
"""
import io

import pandas as pd

import ui
from analisis import (
    CONTOH_KASUS,
    DEFAULT_INPUT,
    NAMA_KUSTOM,
    baris_daftar,
    contoh_survei,
    daftar_dari_csv,
    daftar_ke_csv,
    input_dari_param,
    interpretasi,
    jam_puncak,
    lebar_minimum,
    proyeksi,
    simpan_ke_daftar,
    skenario_perbaikan,
    ubah_skenario,
)
from kapasitas import UKURAN_KOTA_OPSI, hitung_batch, hitung_kapasitas

KASUS = dict(tipe="2/2 TT", lebar_total=7, split=50, jenis_hs="bahu", kelas_hs="Sedang",
             lebar_hs=1.0, ukuran_kota_juta=2.0, kr=600, kb=80, sm=1200)


# ---------- perhitungan inti ----------
def test_hitungan_manual():
    # C = 2900 x 1,00 x 1,00 x 0,92 x 1,00 = 2668 ; Q = 600 + 80x1,2 + 1200x0,25 = 996
    h = hitung_kapasitas(**KASUS)
    assert abs(h["C"] - 2668) < 0.01
    assert abs(h["Q"] - 996) < 0.01
    assert abs(h["DJ"] - 996 / 2668) < 1e-9


def test_input_salah_ditolak():
    for salah in (dict(lebar_total=-5), dict(split=120), dict(kr=-1), dict(kelas_hs="Tidak ada")):
        try:
            hitung_kapasitas(**{**KASUS, **salah})
        except ValueError:
            continue
        raise AssertionError(f"input salah tidak terdeteksi: {salah}")


def test_batch_baris_salah_tidak_menghentikan_yang_lain():
    df = pd.DataFrame([
        ["A", "2/2 TT", 7, 50, "bahu", "Sedang", 1.0, 0.3, 600, 80, 1200],
        ["B", "9/9 X", 7, 50, "bahu", "Sedang", 1.0, 0.3, 600, 80, 1200],
    ], columns=["nama_ruas", "tipe", "lebar_total", "split", "jenis_hs", "kelas_hs",
                "lebar_hs", "ukuran_kota_juta", "KR", "KB", "SM"])
    hasil = hitung_batch(df)
    assert hasil.loc[0, "Status"] in ("Memenuhi", "Tidak memenuhi")
    assert hasil.loc[1, "Status"].startswith("Galat")


# ---------- skenario, lebar minimum, proyeksi ----------
def test_skenario_tidak_memperburuk():
    df = skenario_perbaikan(KASUS)
    assert (df["DJ"] <= df.iloc[0]["DJ"] + 1e-9).all()


def test_skenario_kustom():
    kustom = ubah_skenario(KASUS, d_lebar=1.0, d_bahu=0.5, kelas_hs="Rendah", d_volume_persen=-10)
    df = skenario_perbaikan(KASUS, kustom)
    assert df.iloc[-1]["Skenario"] == NAMA_KUSTOM
    assert df.iloc[-1]["DJ"] < df.iloc[0]["DJ"]
    # tanpa perubahan apa pun, skenario kustom sama dengan kondisi eksisting
    tanpa = skenario_perbaikan(KASUS, ubah_skenario(KASUS))
    assert abs(tanpa.iloc[-1]["DJ"] - tanpa.iloc[0]["DJ"]) < 1e-9


def test_lebar_minimum_memenuhi_batas():
    berat = {**KASUS, "kr": 1500, "kb": 200, "sm": 3000}
    w = lebar_minimum(berat)
    assert w is not None
    assert hitung_kapasitas(**{**berat, "lebar_total": w})["DJ"] <= 0.85
    assert hitung_kapasitas(**{**berat, "lebar_total": w - 0.1})["DJ"] > 0.85


def test_proyeksi():
    df, tahun = proyeksi(KASUS, 5, 30)
    assert df["DJ"].is_monotonic_increasing
    assert tahun is not None
    assert df.loc[df["Tahun ke-"] == tahun, "DJ"].iloc[0] > 0.85
    assert df.loc[df["Tahun ke-"] == tahun - 1, "DJ"].iloc[0] <= 0.85
    _, tidak_jenuh = proyeksi(KASUS, 0, 10)
    assert tidak_jenuh is None


def test_proyeksi_laju_per_jenis_sama_dengan_laju_tunggal():
    a, ta = proyeksi(KASUS, 4, 15)
    b, tb = proyeksi(KASUS, {"kr": 4, "kb": 4, "sm": 4}, 15)
    assert ta == tb and (a["DJ"] - b["DJ"]).abs().max() < 1e-12
    cepat, _ = proyeksi(KASUS, {"kr": 4, "kb": 4, "sm": 12}, 15)
    assert cepat["DJ"].iloc[-1] > a["DJ"].iloc[-1]


# ---------- jam puncak ----------
def test_jam_puncak():
    res = jam_puncak(contoh_survei())
    assert res["waktu_awal"] == "06:30"
    assert abs(res["total"] - (640 + 79 + 2060)) < 1e-9
    assert 0 < res["PHF"] <= 1


# ---------- contoh kasus, interpretasi, daftar ruas ----------
def test_contoh_kasus_valid_dan_bervariasi():
    los = []
    for c in CONTOH_KASUS.values():
        h = hitung_kapasitas(**c["param"])
        assert h["C"] > 0 and not h["peringatan"]
        los.append(h["DJ"] <= 0.85)
    assert True in los and False in los  # ada yang memenuhi dan ada yang tidak


def test_input_dari_param_float_dan_opsi_valid():
    for c in list(CONTOH_KASUS.values()) + [{"nama": "x", "param": KASUS}]:
        nilai = input_dari_param(c["nama"], c["param"])
        assert nilai["in_kota"] in UKURAN_KOTA_OPSI
        for k in ("in_lebar", "in_split", "in_lebar_hs", "in_kr", "in_kb", "in_sm"):
            assert isinstance(nilai[k], float)
    assert set(DEFAULT_INPUT) == set(input_dari_param("x", KASUS))


def test_interpretasi_menyebut_status():
    ok = interpretasi(KASUS, hitung_kapasitas(**KASUS))
    assert any("masih dapat bertambah" in k for k in ok)
    berat = {**KASUS, "kr": 3000, "kb": 400, "sm": 6000}
    tidak = interpretasi(berat, hitung_kapasitas(**berat))
    assert any("kapasitas perlu naik" in k for k in tidak)


def test_daftar_simpan_ekspor_impor():
    p = CONTOH_KASUS["Arteri padat (4/2 T)"]["param"]
    daftar = simpan_ke_daftar([], baris_daftar("A", p))
    daftar = simpan_ke_daftar(daftar, baris_daftar("B", p))
    daftar = simpan_ke_daftar(daftar, baris_daftar("A", p))  # nama sama: diganti, bukan ganda
    assert [r["Ruas"] for r in daftar] == ["B", "A"]
    kembali, gagal = daftar_dari_csv(pd.read_csv(io.BytesIO(daftar_ke_csv(daftar))))
    assert gagal == 0 and [r["Ruas"] for r in kembali] == ["B", "A"]
    assert abs(kembali[0]["DJ"] - daftar[0]["DJ"]) < 1e-9
    rusak, gagal = daftar_dari_csv(pd.DataFrame({"Ruas": ["x"], "param": ["{bukan json"]}))
    assert rusak == [] and gagal == 1


# ---------- komponen tampilan ----------
def test_html_komponen_satu_baris_dan_berisi_angka():
    h = hitung_kapasitas(**KASUS)
    for html in (ui.kartu_hasil(h), ui.lencana_status(h["DJ"]), ui.meter_dj(h["DJ"]), ui.batang_faktor(h),
                 ui.css(), ui.hero("Judul", "Sub", ["a"])):
        assert "\n" not in html  # satu baris agar Markdown tidak menganggapnya blok kode
    assert "0,373" in ui.kartu_hasil(h)
    assert "MEMENUHI" in ui.lencana_status(0.5) and "TIDAK MEMENUHI" in ui.lencana_status(1.2)


if __name__ == "__main__":
    for nama, fungsi in sorted(globals().items()):
        if nama.startswith("test_"):
            fungsi()
            print("LULUS:", nama)
    print("Semua uji lulus.")
