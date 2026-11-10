"""Kalkulator Kapasitas Jalan Perkotaan (PKJI) - aplikasi web Streamlit.

Jalankan di komputer sendiri:  streamlit run app.py
"""
import io

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from kapasitas import (
    KELAS_HS,
    KOLOM_BATCH,
    TIPE_JALAN,
    UKURAN_KOTA_OPSI,
    hitung_batch,
    hitung_kapasitas,
    kelas_hambatan_samping,
)

# ---- UBAH IDENTITAS ANDA DI SINI ----
IDENTITAS = "Dwi Galang Ardianto | 2420503072 | Program Studi Teknik Sipil"

st.set_page_config(page_title="Kalkulator Kapasitas Jalan", page_icon="🛣️", layout="wide")


# ------------------------------------------------------------
# Fungsi bantu tampilan
# ------------------------------------------------------------
def format_rincian(df):
    """Ubah kolom Nilai menjadi teks rapi (tabel berisi angka dan huruf LOS)."""
    out = df.copy()

    def fmt(r):
        v = r["Nilai"]
        if isinstance(v, str):
            return v
        return f"{v:,.0f}" if r["Satuan"] == "smp/jam" else f"{v:.3f}"

    out["Nilai"] = out.apply(fmt, axis=1)
    return out


def buat_grafik(h, param):
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))

    batang = ax[0].bar(["Arus Q", "Kapasitas C"], [h["Q"], h["C"]], color=["#e07b39", "#2c7fb8"])
    ax[0].axhline(0.85 * h["C"], color="red", linestyle="--", label="Batas 0,85 x C")
    for b in batang:
        ax[0].text(b.get_x() + b.get_width() / 2, b.get_height(), f"{b.get_height():,.0f}",
                   ha="center", va="bottom", fontsize=9)
    ax[0].set_ylabel("smp/jam")
    ax[0].set_title(f"Arus vs Kapasitas (DJ = {h['DJ']:.2f})")
    ax[0].legend()

    kapasitas_kelas = []
    for k in KELAS_HS:
        p = dict(param)
        p["kelas_hs"] = k
        kapasitas_kelas.append(hitung_kapasitas(**p)["C"])
    ax[1].plot(KELAS_HS, kapasitas_kelas, marker="o", color="#2c7fb8")
    ax[1].axhline(h["Q"] / 0.85, color="red", linestyle="--", label="C minimum agar DJ = 0,85")
    ax[1].set_title("Pengaruh kelas hambatan samping terhadap C")
    ax[1].set_ylabel("Kapasitas C (smp/jam)")
    ax[1].tick_params(axis="x", rotation=25)
    ax[1].legend()
    ax[1].grid(alpha=0.3)

    fig.tight_layout()
    return fig


def buat_excel(param, h):
    """Hasil perhitungan satu ruas -> berkas Excel (bytes)."""
    df_input = pd.DataFrame(list(param.items()), columns=["Input", "Nilai"])
    df_input["Nilai"] = df_input["Nilai"].astype(str)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        df_input.to_excel(xw, sheet_name="Input", index=False)
        h["rincian"].astype({"Nilai": object}).to_excel(xw, sheet_name="Hasil", index=False)
    return buf.getvalue()


MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# ------------------------------------------------------------
# Judul
# ------------------------------------------------------------
st.title("Kalkulator Kapasitas Jalan Perkotaan")
st.caption(f"Mata Kuliah Aplikasi Komputer | Acuan: PKJI | {IDENTITAS}")

tab1, tab2, tab3 = st.tabs(["Kalkulator", "Banyak ruas (CSV/Excel)", "Dasar teori"])

# ------------------------------------------------------------
# TAB 1 - Kalkulator satu ruas
# ------------------------------------------------------------
with tab1:
    with st.expander("Bantuan: tentukan kelas hambatan samping"):
        st.write("Masukkan frekuensi kejadian berbobot per 200 m per jam (dari survei hambatan samping).")
        fb = st.number_input("Frekuensi berbobot", min_value=0.0, value=250.0, step=10.0, key="fb")
        st.info(f"Kelas hambatan samping: **{kelas_hambatan_samping(fb)}**")

    with st.form("form_hitung"):
        kiri, kanan = st.columns(2)

        with kiri:
            st.subheader("Data geometrik dan lingkungan")
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
            st.caption("Untuk jalan 4 lajur, lebar jalur total dibagi jumlah lajur secara otomatis.")

        kirim = st.form_submit_button("HITUNG", type="primary")

    if kirim:
        param = dict(tipe=tipe, lebar_total=lebar, split=split, jenis_hs=jenis, kelas_hs=kelas,
                     lebar_hs=lebar_hs, ukuran_kota_juta=UKURAN_KOTA_OPSI[kota],
                     kr=kr, kb=kb, sm=sm)
        try:
            st.session_state["hasil"] = {"param": param, "hasil": hitung_kapasitas(**param)}
        except ValueError as e:
            st.session_state.pop("hasil", None)
            st.error(f"Input tidak valid: {e}")

    if "hasil" in st.session_state:
        param = st.session_state["hasil"]["param"]
        h = st.session_state["hasil"]["hasil"]

        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Kapasitas C", f"{h['C']:,.0f} smp/jam")
        m2.metric("Arus Q", f"{h['Q']:,.0f} smp/jam")
        m3.metric("Derajat kejenuhan DJ", f"{h['DJ']:.3f}")
        m4.metric("Tingkat pelayanan", h["LOS"])

        if h["DJ"] <= 0.85:
            st.success(h["status"])
        else:
            st.error(h["status"])
        for p in h["peringatan"]:
            st.warning(p)

        st.subheader("Rincian perhitungan")
        st.dataframe(format_rincian(h["rincian"]), hide_index=True)

        fig = buat_grafik(h, param)
        st.pyplot(fig)
        plt.close(fig)

        st.download_button("Unduh hasil (Excel)", data=buat_excel(param, h),
                           file_name="hasil_kapasitas_jalan.xlsx", mime=MIME_XLSX)

# ------------------------------------------------------------
# TAB 2 - Banyak ruas sekaligus
# ------------------------------------------------------------
with tab2:
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

    berkas = st.file_uploader("Unggah file data ruas", type=["csv", "xlsx"])
    if berkas is not None:
        try:
            if berkas.name.lower().endswith("xlsx"):
                data = pd.read_excel(berkas)
            else:
                data = pd.read_csv(berkas)
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
                buf = io.BytesIO()
                hasil_batch.to_excel(buf, index=False, engine="openpyxl")
                st.download_button("Unduh hasil (Excel)", data=buf.getvalue(),
                                   file_name="hasil_banyak_ruas.xlsx", mime=MIME_XLSX)
    else:
        st.write("Contoh hasil dari data template:")
        st.dataframe(hitung_batch(contoh), hide_index=True)

# ------------------------------------------------------------
# TAB 3 - Dasar teori
# ------------------------------------------------------------
with tab3:
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
    st.write("Kinerja jalan dinilai dari derajat kejenuhan:")
    st.latex(r"DJ = \dfrac{Q}{C}")
    st.write("Jalan dinilai memenuhi bila **DJ ≤ 0,85**.")

    st.subheader("Cakupan dan keterbatasan")
    st.markdown(
        "- Mencakup jalan perkotaan tipe 2/2 TT, 4/2 TT, dan 4/2 T.\n"
        "- Jalan luar kota, jalan bebas hambatan, 6/2 T, dan jalan satu arah belum tercakup.\n"
        "- Nilai tabel pada `kapasitas.py` perlu dicocokkan dengan edisi PKJI yang dipakai.\n"
        "- Hasil aplikasi ini untuk keperluan pembelajaran, bukan pengganti analisis perencanaan resmi."
    )
    st.caption("Sumber: Pedoman Kapasitas Jalan Indonesia (PKJI), Kementerian Pekerjaan Umum.")
