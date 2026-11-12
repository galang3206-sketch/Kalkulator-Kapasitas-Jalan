"""Kalkulator Kapasitas Jalan Perkotaan (PKJI) - aplikasi web Streamlit.

Jalankan di komputer sendiri:  streamlit run app.py

Berkas pendukung: kapasitas.py (data dan rumus), analisis.py (skenario, proyeksi,
jam puncak), tampilan.py (grafik, format angka, laporan PDF).
"""
import io

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from analisis import (
    BATAS_DJ,
    KOLOM_SURVEI,
    contoh_survei,
    jam_puncak,
    langkah_perhitungan,
    lebar_minimum,
    proyeksi,
    rentang_lebar,
    skenario_perbaikan,
)
from kapasitas import (
    KELAS_HS,
    KOLOM_BATCH,
    TIPE_JALAN,
    UKURAN_KOTA_OPSI,
    hitung_batch,
    hitung_kapasitas,
    kelas_hambatan_samping,
)
from tampilan import (
    buat_grafik,
    fmt_id,
    format_df,
    format_rincian,
    grafik_jam_puncak,
    grafik_perbandingan,
    grafik_proyeksi,
    grafik_skenario,
    laporan_pdf,
)

# ---- UBAH IDENTITAS ANDA DI SINI ----
IDENTITAS = "Dwi Galang | 2420503072 | Program Studi Teknik Sipil"

st.set_page_config(page_title="Kalkulator Kapasitas Jalan", page_icon="🛣️", layout="wide")

MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# ------------------------------------------------------------
# Fungsi bantu
# ------------------------------------------------------------
def tampilkan_grafik(fig):
    st.pyplot(fig)
    plt.close(fig)


def excel_bytes(**lembar):
    """Beberapa DataFrame -> satu berkas Excel (bytes). Kunci = nama lembar."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for nama, df in lembar.items():
            df.to_excel(xw, sheet_name=nama[:31], index=False)
    return buf.getvalue()


def excel_satu_ruas(param, h):
    df_input = pd.DataFrame(list(param.items()), columns=["Input", "Nilai"])
    df_input["Nilai"] = df_input["Nilai"].astype(str)
    return excel_bytes(Input=df_input, Hasil=h["rincian"].astype({"Nilai": object}))


def baca_berkas(berkas):
    if berkas.name.lower().endswith("xlsx"):
        return pd.read_excel(berkas)
    return pd.read_csv(berkas)


def belum_hitung():
    st.info("Hitung dulu di tab **Kalkulator**. Hasilnya akan dipakai oleh tab ini.")


# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
with st.sidebar:
    st.header("Tentang aplikasi")
    st.write("Menghitung kapasitas, derajat kejenuhan, dan tingkat pelayanan jalan perkotaan "
             "menurut PKJI, lengkap dengan analisis skenario, proyeksi, dan laporan PDF.")
    st.markdown("**Tingkat pelayanan (LOS)**")
    st.markdown(
        "| LOS | DJ |\n|---|---|\n"
        "| A | ≤ 0,20 |\n| B | 0,21 - 0,44 |\n| C | 0,45 - 0,74 |\n"
        "| D | 0,75 - 0,84 |\n| E | 0,85 - 1,00 |\n| F | > 1,00 |"
    )
    st.caption(IDENTITAS)

# ------------------------------------------------------------
# Judul dan tab
# ------------------------------------------------------------
st.title("Kalkulator Kapasitas Jalan Perkotaan")
st.caption(f"Mata Kuliah Aplikasi Komputer | Acuan: PKJI | {IDENTITAS}")

(tab_hitung, tab_skenario, tab_proyeksi, tab_banding,
 tab_survei, tab_batch, tab_teori) = st.tabs([
    "Kalkulator", "Skenario perbaikan", "Proyeksi lalu lintas", "Perbandingan ruas",
    "Survei jam puncak", "Banyak ruas (CSV/Excel)", "Dasar teori",
])

# ============================================================
# TAB 1 - Kalkulator satu ruas
# ============================================================
with tab_hitung:
    with st.expander("Bantuan: tentukan kelas hambatan samping"):
        st.write("Masukkan frekuensi kejadian berbobot per 200 m per jam (dari survei hambatan samping).")
        fb = st.number_input("Frekuensi berbobot", min_value=0.0, value=250.0, step=10.0, key="fb")
        st.info(f"Kelas hambatan samping: **{kelas_hambatan_samping(fb)}**")

    with st.form("form_hitung"):
        kiri, kanan = st.columns(2)

        with kiri:
            st.subheader("Data geometrik dan lingkungan")
            nama = st.text_input("Nama ruas / lokasi", value="Ruas 1")
            tipe = st.selectbox("Tipe jalan", list(TIPE_JALAN.keys()),
                                format_func=lambda k: f"{k} - {TIPE_JALAN[k]['nama']}")
            lebar = st.number_input("Lebar jalur efektif total (m)", min_value=0.1, max_value=40.0,
                                    value=7.0, step=0.25)
            split = st.number_input("Arus pada arah terbesar (%)", min_value=50.0, max_value=100.0,
                                    value=50.0, step=5.0)
            jenis = st.radio("Tepi jalan", ["bahu", "kereb"], horizontal=True,
                             format_func=lambda k: "Jalan berbahu" if k == "bahu" else "Jalan berkereb")
            lebar_hs = st.number_input("Lebar bahu / jarak kereb ke penghalang (m)", min_value=0.0,
                                       max_value=10.0, value=1.0, step=0.25)
            kelas = st.selectbox("Kelas hambatan samping", KELAS_HS, index=2)
            kota = st.selectbox("Ukuran kota", list(UKURAN_KOTA_OPSI.keys()), index=1)

        with kanan:
            st.subheader("Volume lalu lintas (total dua arah, jam puncak)")
            kr = st.number_input("Kendaraan ringan (kend/jam)", min_value=0.0, value=600.0, step=10.0)
            kb = st.number_input("Kendaraan berat (kend/jam)", min_value=0.0, value=80.0, step=10.0)
            sm = st.number_input("Sepeda motor (kend/jam)", min_value=0.0, value=1200.0, step=10.0)
            st.caption("Untuk jalan 4 lajur, lebar jalur total dibagi jumlah lajur secara otomatis. "
                       "Volume jam puncak bisa diperoleh dari tab Survei jam puncak.")

        kirim = st.form_submit_button("HITUNG", type="primary")

    if kirim:
        param = dict(tipe=tipe, lebar_total=lebar, split=split, jenis_hs=jenis, kelas_hs=kelas,
                     lebar_hs=lebar_hs, ukuran_kota_juta=UKURAN_KOTA_OPSI[kota],
                     kr=kr, kb=kb, sm=sm)
        try:
            st.session_state["hasil"] = {"param": param, "hasil": hitung_kapasitas(**param),
                                         "nama": nama.strip() or "Ruas tanpa nama"}
        except ValueError as e:
            st.session_state.pop("hasil", None)
            st.error(f"Input tidak valid: {e}")

    if "hasil" in st.session_state:
        param = st.session_state["hasil"]["param"]
        h = st.session_state["hasil"]["hasil"]
        nama_ruas = st.session_state["hasil"]["nama"]

        st.divider()
        st.subheader(f"Hasil: {nama_ruas}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Kapasitas C", f"{fmt_id(h['C'])} smp/jam")
        m2.metric("Arus Q", f"{fmt_id(h['Q'])} smp/jam")
        m3.metric("Derajat kejenuhan DJ", fmt_id(h["DJ"], 3))
        m4.metric("Tingkat pelayanan", h["LOS"])

        if h["DJ"] <= BATAS_DJ:
            st.success(h["status"])
        else:
            st.error(h["status"])
        for p in h["peringatan"]:
            st.warning(p)

        st.subheader("Rincian perhitungan")
        st.dataframe(format_rincian(h["rincian"]), hide_index=True)

        with st.expander("Lihat langkah perhitungan (rumus dengan angka)"):
            for judul, rumus in langkah_perhitungan(param, h):
                st.markdown(f"**{judul}**")
                st.latex(rumus)

        tampilkan_grafik(buat_grafik(h, param))

        a, b, c = st.columns(3)
        with a:
            st.download_button("Unduh laporan (PDF)", data=laporan_pdf(IDENTITAS, param, h, nama_ruas),
                               file_name="laporan_kapasitas_jalan.pdf", mime="application/pdf")
        with b:
            st.download_button("Unduh hasil (Excel)", data=excel_satu_ruas(param, h),
                               file_name="hasil_kapasitas_jalan.xlsx", mime=MIME_XLSX)
        with c:
            if st.button("Simpan ke daftar perbandingan"):
                baris = {
                    "Ruas": nama_ruas, "Tipe": param["tipe"], "Lebar (m)": param["lebar_total"],
                    "Kelas HS": param["kelas_hs"], "C (smp/jam)": h["C"], "Q (smp/jam)": h["Q"],
                    "DJ": h["DJ"], "LOS": h["LOS"],
                    "Status": "Memenuhi" if h["DJ"] <= BATAS_DJ else "Tidak memenuhi",
                }
                daftar = [r for r in st.session_state.get("daftar", []) if r["Ruas"] != nama_ruas]
                st.session_state["daftar"] = daftar + [baris]
                st.success(f"'{nama_ruas}' disimpan. Lihat di tab Perbandingan ruas.")

# ============================================================
# TAB 2 - Skenario perbaikan
# ============================================================
with tab_skenario:
    if "hasil" not in st.session_state:
        belum_hitung()
    else:
        param = st.session_state["hasil"]["param"]
        h = st.session_state["hasil"]["hasil"]
        st.subheader(f"Skenario perbaikan: {st.session_state['hasil']['nama']}")
        st.write("Seberapa besar kinerja jalan membaik bila geometrik diperlebar atau hambatan samping "
                 "dikurangi? Volume lalu lintas dianggap tetap.")

        df_s = skenario_perbaikan(param)
        tabel_s = format_df(df_s, {"Lebar (m)": 2, "C (smp/jam)": 0, "Q (smp/jam)": 0, "DJ": 3})
        if (tabel_s["Catatan"] == "").all():
            tabel_s = tabel_s.drop(columns=["Catatan"])
        st.dataframe(tabel_s, hide_index=True)
        tampilkan_grafik(grafik_skenario(df_s))

        memenuhi = df_s[(df_s["Skenario"] != "Kondisi eksisting") & (df_s["DJ"] <= BATAS_DJ)]
        if h["DJ"] <= BATAS_DJ:
            st.success("Kondisi eksisting sudah memenuhi (DJ ≤ 0,85). Skenario di atas menunjukkan "
                       "seberapa besar cadangan kapasitas yang bisa diperoleh.")
        elif len(memenuhi):
            st.success(f"Skenario pertama yang membuat DJ ≤ 0,85: **{memenuhi.iloc[0]['Skenario']}** "
                       f"(DJ = {fmt_id(memenuhi.iloc[0]['DJ'], 3)}).")
        else:
            st.warning("Tidak ada skenario di atas yang membuat DJ ≤ 0,85. Pertimbangkan menambah lajur "
                       "atau mengurangi arus lewat manajemen lalu lintas.")

        st.divider()
        st.subheader("Lebar jalur minimum")
        awal, akhir = rentang_lebar(param["tipe"])
        w = lebar_minimum(param)
        if w is None:
            st.warning(f"Pada rentang lebar tabel PKJI ({fmt_id(awal, 2)} - {fmt_id(akhir, 2)} m), "
                       "DJ ≤ 0,85 tidak tercapai. Pertimbangkan menambah lajur.")
        else:
            x1, x2 = st.columns(2)
            x1.metric("Lebar total minimum agar DJ ≤ 0,85", f"{fmt_id(w, 2)} m")
            x2.metric("Lebar eksisting", f"{fmt_id(param['lebar_total'], 2)} m")
            if w <= awal + 1e-9:
                st.caption("Nilai ini sudah berada di batas bawah rentang tabel, jadi jalan sudah memenuhi "
                           "pada lebar terkecil yang tercakup tabel.")
            elif w > param["lebar_total"]:
                st.caption(f"Perlu penambahan lebar sekitar {fmt_id(w - param['lebar_total'], 2)} m.")

        st.download_button("Unduh tabel skenario (Excel)", data=excel_bytes(Skenario=df_s),
                           file_name="skenario_perbaikan.xlsx", mime=MIME_XLSX)

# ============================================================
# TAB 3 - Proyeksi lalu lintas
# ============================================================
with tab_proyeksi:
    if "hasil" not in st.session_state:
        belum_hitung()
    else:
        param = st.session_state["hasil"]["param"]
        st.subheader(f"Proyeksi lalu lintas: {st.session_state['hasil']['nama']}")
        st.write("Volume tumbuh geometrik: Qn = Q0 × (1 + i)ⁿ. Kapasitas dianggap tetap, "
                 "sehingga terlihat kapan jalan mulai jenuh.")
        c1, c2 = st.columns(2)
        with c1:
            tumbuh = st.slider("Pertumbuhan lalu lintas per tahun (%)", 0.0, 15.0, 5.0, 0.5)
        with c2:
            umur = st.slider("Umur rencana (tahun)", 5, 40, 20)

        df_p, tahun_jenuh = proyeksi(param, tumbuh, umur)
        akhir = df_p.iloc[-1]
        p1, p2, p3 = st.columns(3)
        p1.metric("DJ saat ini", fmt_id(df_p.iloc[0]["DJ"], 3))
        p2.metric(f"DJ tahun ke-{umur}", fmt_id(akhir["DJ"], 3))
        p3.metric("Tahun mulai jenuh", "Belum jenuh" if tahun_jenuh is None else f"Tahun ke-{tahun_jenuh}")

        if tahun_jenuh is None:
            st.success(f"Sampai tahun ke-{umur}, DJ tetap ≤ 0,85 dengan pertumbuhan {fmt_id(tumbuh, 1)}% per tahun.")
        elif tahun_jenuh == 0:
            st.error("Pada kondisi sekarang DJ sudah melewati 0,85.")
        else:
            st.warning(f"DJ melewati 0,85 pada tahun ke-{tahun_jenuh}. Perbaikan perlu direncanakan "
                       f"sebelum tahun tersebut.")

        tampilkan_grafik(grafik_proyeksi(df_p, tahun_jenuh))
        with st.expander("Tabel proyeksi per tahun"):
            st.dataframe(format_df(df_p, {"Q (smp/jam)": 0, "C (smp/jam)": 0, "DJ": 3}), hide_index=True)
        st.download_button("Unduh tabel proyeksi (Excel)", data=excel_bytes(Proyeksi=df_p),
                           file_name="proyeksi_lalu_lintas.xlsx", mime=MIME_XLSX)

# ============================================================
# TAB 4 - Perbandingan ruas
# ============================================================
with tab_banding:
    st.subheader("Perbandingan beberapa ruas")
    daftar = st.session_state.get("daftar", [])
    if not daftar:
        st.info("Belum ada ruas tersimpan. Hitung sebuah ruas di tab Kalkulator, lalu klik "
                "**Simpan ke daftar perbandingan**. Ulangi dengan nama ruas yang berbeda.")
    else:
        df_d = pd.DataFrame(daftar)
        st.dataframe(format_df(df_d, {"Lebar (m)": 2, "C (smp/jam)": 0, "Q (smp/jam)": 0, "DJ": 3}),
                     hide_index=True)
        n_tidak = int((df_d["DJ"] > BATAS_DJ).sum())
        st.write(f"**{len(df_d)} ruas** dibandingkan; **{n_tidak}** ruas melewati batas DJ 0,85.")
        tampilkan_grafik(grafik_perbandingan(df_d))
        k1, k2 = st.columns(2)
        with k1:
            st.download_button("Unduh perbandingan (Excel)", data=excel_bytes(Perbandingan=df_d),
                               file_name="perbandingan_ruas.xlsx", mime=MIME_XLSX)
        with k2:
            if st.button("Kosongkan daftar"):
                st.session_state["daftar"] = []
                st.rerun()

# ============================================================
# TAB 5 - Survei jam puncak
# ============================================================
with tab_survei:
    st.subheader("Jam puncak dan PHF dari data survei")
    st.write("Unggah hasil survei volume per **15 menit** (berurutan menurut waktu). Aplikasi mencari "
             "4 interval berurutan dengan volume terbesar, lalu menghitung Peak Hour Factor (PHF).")
    st.code(", ".join(KOLOM_SURVEI))
    st.caption("waktu = jam mulai interval (misal 06:00). KR, KB, SM = jumlah kendaraan pada interval itu "
               "(bukan per jam).")
    st.download_button("Unduh template CSV", data=contoh_survei().to_csv(index=False).encode("utf-8"),
                       file_name="template_survei.csv", mime="text/csv")

    berkas_s = st.file_uploader("Unggah file survei", type=["csv", "xlsx"], key="unggah_survei")
    data_s = contoh_survei()
    if berkas_s is not None:
        try:
            data_s = baca_berkas(berkas_s)
        except Exception as e:
            st.error(f"File tidak bisa dibaca: {e}")
            data_s = None
    else:
        st.caption("Menampilkan contoh data. Unggah file sendiri untuk menggantinya.")

    if data_s is not None:
        try:
            res = jam_puncak(data_s)
        except ValueError as e:
            st.error(str(e))
        else:
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Jam puncak mulai", res["waktu_awal"])
            s2.metric("Volume jam puncak", f"{fmt_id(res['total'])} kend/jam")
            s3.metric("Volume 15 menit maks", f"{fmt_id(res['v15_maks'])} kend")
            s4.metric("PHF", fmt_id(res["PHF"], 2))
            st.caption("PHF = V jam puncak / (4 × V 15 menit maksimum). Makin mendekati 1, arus makin merata.")
            st.markdown("**Komposisi jam puncak** (pakai angka ini sebagai masukan di tab Kalkulator):")
            st.dataframe(pd.DataFrame({
                "Jenis": ["Kendaraan ringan (KR)", "Kendaraan berat (KB)", "Sepeda motor (SM)"],
                "kend/jam": [fmt_id(res["KR"]), fmt_id(res["KB"]), fmt_id(res["SM"])],
            }), hide_index=True)
            tampilkan_grafik(grafik_jam_puncak(res))
            with st.expander("Tabel data survei"):
                st.dataframe(format_df(res["tabel"], {"KR": 0, "KB": 0, "SM": 0, "Total": 0}), hide_index=True)

# ============================================================
# TAB 6 - Banyak ruas sekaligus
# ============================================================
with tab_batch:
    st.write("Hitung banyak ruas jalan sekaligus. Siapkan file **CSV atau Excel** dengan kolom berikut:")
    st.code(", ".join(KOLOM_BATCH))

    contoh = pd.DataFrame([
        ["Jl. Contoh A", "2/2 TT", 7.0, 50, "bahu", "Sedang", 1.0, 0.3, 600, 80, 1200],
        ["Jl. Contoh B", "4/2 TT", 12.0, 60, "kereb", "Tinggi", 1.0, 0.3, 900, 120, 2000],
        ["Jl. Contoh C", "4/2 T", 14.0, 50, "kereb", "Rendah", 1.5, 0.3, 1500, 300, 3000],
    ], columns=KOLOM_BATCH)

    st.caption("Isian yang valid: tipe = 2/2 TT, 4/2 TT, 4/2 T | jenis_hs = bahu atau kereb | "
               "kelas_hs = " + ", ".join(KELAS_HS) + ". Gunakan titik sebagai pemisah desimal.")
    st.download_button("Unduh template CSV", data=contoh.to_csv(index=False).encode("utf-8"),
                       file_name="template_banyak_ruas.csv", mime="text/csv")

    berkas = st.file_uploader("Unggah file data ruas", type=["csv", "xlsx"], key="unggah_batch")
    if berkas is not None:
        try:
            data = baca_berkas(berkas)
        except Exception as e:
            st.error(f"File tidak bisa dibaca: {e}")
        else:
            kurang = [k for k in KOLOM_BATCH if k not in data.columns]
            if kurang:
                st.error("Kolom belum lengkap: " + ", ".join(kurang))
            else:
                hasil_batch = hitung_batch(data)
                st.subheader("Hasil")
                st.dataframe(hasil_batch, hide_index=True)
                st.download_button("Unduh hasil (Excel)", data=excel_bytes(Hasil=hasil_batch),
                                   file_name="hasil_banyak_ruas.xlsx", mime=MIME_XLSX)
    else:
        st.write("Contoh hasil dari data template:")
        st.dataframe(hitung_batch(contoh), hide_index=True)

# ============================================================
# TAB 7 - Dasar teori
# ============================================================
with tab_teori:
    st.subheader("Kapasitas jalan perkotaan")
    st.write("Menurut Pedoman Kapasitas Jalan Indonesia (PKJI), kapasitas dihitung dengan:")
    st.latex(r"C = C_0 \times FC_{LJ} \times FC_{PA} \times FC_{HS} \times FC_{UK}")
    st.markdown(
        "| Simbol | Keterangan |\n|---|---|\n"
        "| C₀ | Kapasitas dasar menurut tipe jalan |\n"
        "| FC_LJ | Faktor penyesuaian lebar jalur lalu lintas |\n"
        "| FC_PA | Faktor penyesuaian pemisahan arah (jalan tak-terbagi) |\n"
        "| FC_HS | Faktor penyesuaian hambatan samping (bahu atau kereb) |\n"
        "| FC_UK | Faktor penyesuaian ukuran kota |"
    )
    st.write("Arus lalu lintas dikonversi ke satuan mobil penumpang (smp):")
    st.latex(r"Q = KR \times 1{,}0 + KB \times emp_{KB} + SM \times emp_{SM}")
    st.write("Kinerja jalan dinilai dari derajat kejenuhan; jalan memenuhi bila **DJ ≤ 0,85**:")
    st.latex(r"DJ = \dfrac{Q}{C}")

    st.subheader("Rumus analisis lanjutan")
    st.write("Proyeksi lalu lintas (pertumbuhan geometrik, i = laju per tahun, n = tahun):")
    st.latex(r"Q_n = Q_0 \times (1 + i)^n")
    st.write("Faktor jam puncak dari survei per 15 menit:")
    st.latex(r"PHF = \dfrac{V_{jam\ puncak}}{4 \times V_{15\ maks}}")

    st.subheader("Cakupan dan keterbatasan")
    st.markdown(
        "- Mencakup jalan perkotaan tipe 2/2 TT, 4/2 TT, dan 4/2 T.\n"
        "- Jalan luar kota, jalan bebas hambatan, 6/2 T, dan jalan satu arah belum tercakup.\n"
        "- Nilai tabel pada `kapasitas.py` perlu dicocokkan dengan edisi PKJI yang dipakai.\n"
        "- Skenario perbaikan dan proyeksi bersifat indikatif: volume dianggap tumbuh seragam dan "
        "kapasitas tetap.\n"
        "- Hasil aplikasi ini untuk keperluan pembelajaran, bukan pengganti analisis perencanaan resmi."
    )
    st.caption("Sumber: Pedoman Kapasitas Jalan Indonesia (PKJI), Kementerian Pekerjaan Umum.")
