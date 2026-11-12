# Kalkulator Kapasitas Jalan Perkotaan (PKJI)

Aplikasi web untuk menghitung kapasitas (C), derajat kejenuhan (DJ), dan tingkat pelayanan (LOS)
jalan perkotaan tipe 2/2 TT, 4/2 TT, dan 4/2 T berdasarkan Pedoman Kapasitas Jalan Indonesia (PKJI).

Dibuat untuk mata kuliah Aplikasi Komputer, Program Studi Teknik Sipil.

## Fitur

| Tab | Isi |
|---|---|
| Kalkulator | Hitung satu ruas, rincian, langkah perhitungan berangka, grafik, unduh laporan PDF dan Excel |
| Skenario perbaikan | Bandingkan pelebaran jalur, pelebaran bahu, dan penurunan hambatan samping; hitung lebar jalur minimum agar DJ ≤ 0,85 |
| Proyeksi lalu lintas | DJ tahun demi tahun dengan pertumbuhan lalu lintas; tahun jalan mulai jenuh |
| Perbandingan ruas | Simpan beberapa ruas, bandingkan DJ-nya dalam satu grafik |
| Survei jam puncak | Unggah data survei per 15 menit, cari jam puncak dan PHF |
| Banyak ruas | Hitung banyak ruas sekaligus dari CSV atau Excel |
| Dasar teori | Rumus yang dipakai, cakupan, dan keterbatasan |

## Isi repositori

| File | Fungsi |
|---|---|
| `app.py` | Tampilan web (Streamlit) |
| `kapasitas.py` | Data tabel PKJI dan rumus kapasitas |
| `analisis.py` | Skenario perbaikan, proyeksi, jam puncak, langkah perhitungan |
| `tampilan.py` | Format angka, grafik, dan laporan PDF |
| `test_kapasitas.py` | Uji otomatis (opsional, bukti validasi) |
| `requirements.txt` | Daftar library |

## Menjalankan di komputer sendiri

```bash
pip install -r requirements.txt
streamlit run app.py
python test_kapasitas.py     # menjalankan uji otomatis
```

## Catatan

- Nilai tabel pada `kapasitas.py` (C0, faktor penyesuaian, emp, batas LOS) harus dicocokkan dengan edisi PKJI yang dipakai.
- Jalan luar kota, bebas hambatan, 6/2 T, dan satu arah belum tercakup.
- Skenario dan proyeksi bersifat indikatif: volume dianggap tumbuh seragam dan kapasitas tetap.
