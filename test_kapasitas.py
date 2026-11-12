"""Uji otomatis perhitungan. Jalankan:  python test_kapasitas.py   (atau: pytest)

Berguna sebagai bukti validasi di laporan: hasil program dibandingkan dengan hitungan manual.
"""
import pandas as pd

from analisis import (
    jam_puncak,
    contoh_survei,
    lebar_minimum,
    proyeksi,
    skenario_perbaikan,
)
from kapasitas import hitung_batch, hitung_kapasitas

KASUS = dict(tipe="2/2 TT", lebar_total=7, split=50, jenis_hs="bahu", kelas_hs="Sedang",
             lebar_hs=1.0, ukuran_kota_juta=2.0, kr=600, kb=80, sm=1200)


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


def test_skenario_tidak_memperburuk():
    df = skenario_perbaikan(KASUS)
    eksisting = df.iloc[0]["DJ"]
    assert (df["DJ"] <= eksisting + 1e-9).all()


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


def test_jam_puncak():
    res = jam_puncak(contoh_survei())
    assert res["waktu_awal"] == "06:30"
    assert abs(res["total"] - (640 + 79 + 2060)) < 1e-9
    assert 0 < res["PHF"] <= 1


def test_batch_baris_salah_tidak_menghentikan_yang_lain():
    df = pd.DataFrame([
        ["A", "2/2 TT", 7, 50, "bahu", "Sedang", 1.0, 0.3, 600, 80, 1200],
        ["B", "9/9 X", 7, 50, "bahu", "Sedang", 1.0, 0.3, 600, 80, 1200],
    ], columns=["nama_ruas", "tipe", "lebar_total", "split", "jenis_hs", "kelas_hs",
                "lebar_hs", "ukuran_kota_juta", "KR", "KB", "SM"])
    hasil = hitung_batch(df)
    assert hasil.loc[0, "Status"] in ("Memenuhi", "Tidak memenuhi")
    assert hasil.loc[1, "Status"].startswith("Galat")


if __name__ == "__main__":
    for nama, fungsi in sorted(globals().items()):
        if nama.startswith("test_"):
            fungsi()
            print("LULUS:", nama)
    print("Semua uji lulus.")
