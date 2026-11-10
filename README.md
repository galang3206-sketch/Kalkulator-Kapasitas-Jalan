# Kalkulator Kapasitas Jalan Perkotaan (PKJI)

Aplikasi web untuk menghitung kapasitas (C), derajat kejenuhan (DJ), dan tingkat pelayanan (LOS)
jalan perkotaan tipe 2/2 TT, 4/2 TT, dan 4/2 T berdasarkan Pedoman Kapasitas Jalan Indonesia (PKJI).

Dibuat untuk mata kuliah Aplikasi Komputer, Program Studi Teknik Sipil.

## Isi repositori

| File | Fungsi |
|---|---|
| `app.py` | Tampilan web (Streamlit) |
| `kapasitas.py` | Data tabel PKJI dan fungsi perhitungan |
| `requirements.txt` | Daftar library yang dibutuhkan |

## Menjalankan di komputer sendiri

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Catatan

- Nilai tabel pada `kapasitas.py` harus dicocokkan dengan edisi PKJI yang dipakai.
- Jalan luar kota, bebas hambatan, 6/2 T, dan satu arah belum tercakup.
