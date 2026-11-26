"""Kalkulator Kapasitas Jalan Perkotaan (PKJI) - aplikasi web Streamlit.

Jalankan di komputer sendiri:  streamlit run app.py

Berkas pendukung:
  kapasitas.py  data tabel dan rumus      analisis.py  skenario, proyeksi, jam puncak, daftar ruas
  tampilan.py   grafik dan laporan PDF    ui.py        gaya dan kartu HTML
"""
import io
import json

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import ui
from analisis import (
    BATAS_DJ,
    CONTOH_KASUS,
    DEFAULT_INPUT,
    DESKRIPSI_LOS,
    KOLOM_SURVEI,
    baris_daftar,
    contoh_survei,
    daftar_dari_csv,
    daftar_ke_csv,
    input_dari_param,
    interpretasi,
    jam_puncak,
    langkah_perhitungan,
    lebar_minimum,
    param_dari_batch,
    proyeksi,
    rentang_lebar,
    simpan_ke_daftar,
    skenario_perbaikan,
    ubah_skenario,
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

# ---- Identitas bawaan (bisa juga diubah dari kolom di sidebar) ----
IDENTITAS_BAWAAN = "Dwi Galang | 2420503072 | Program Studi Teknik Sipil"

st.set_page_config(page_title="Kalkulator Kapasitas Jalan", page_icon="🛣️", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(ui.css(), unsafe_allow_html=True)

MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# ------------------------------------------------------------
# Nilai awal widget (harus ada sebelum widget dibuat)
# ------------------------------------------------------------
for _k, _v in DEFAULT_INPUT.items():
    st.session_state.setdefault(_k, _v)
st.session_state.setdefault("fb", 250.0)
st.session_state.setdefault("daftar", [])
st.session_state.setdefault("identitas", IDENTITAS_BAWAAN)
st.session_state.setdefault("skenario_ubah", None)


# ------------------------------------------------------------
# Callback tombol (dijalankan sebelum halaman digambar ulang)
# ------------------------------------------------------------
def terapkan_input(nilai):
    for k, v in nilai.items():
        st.session_state[k] = v


def muat_contoh(nama):
    c = CONTOH_KASUS[nama]
    terapkan_input(input_dari_param(c["nama"], c["param"]))
    st.toast(f"Contoh dimuat: {nama}")


def atur_ulang():
    terapkan_input(DEFAULT_INPUT)
    st.toast("Input dikembalikan ke nilai awal")


def pakai_kelas_hs():
    st.session_state["in_kelas"] = kelas_hambatan_samping(st.session_state["fb"])


def simpan_ruas():
    r = st.session_state.get("hasil")
    if r:
        st.session_state["daftar"] = simpan_ke_daftar(st.session_state["daftar"],
                                                      baris_daftar(r["nama"], r["param"]))
        st.toast(f"'{r['nama']}' disimpan ke daftar perbandingan")


def muat_ruas():
    nama = st.session_state.get("pil_ruas")
    for r in st.session_state["daftar"]:
        if r["Ruas"] == nama:
            terapkan_input(input_dari_param(nama, json.loads(r["param"])))
            st.toast(f"'{nama}' dimuat ke Kalkulator")
            return


def hapus_ruas():
    nama = st.session_state.get("pil_ruas")
    st.session_state["daftar"] = [r for r in st.session_state["daftar"] if r["Ruas"] != nama]
    st.session_state.pop("pil_ruas", None)


def kosongkan_daftar():
    st.session_state["daftar"] = []
    st.session_state.pop("pil_ruas", None)


def gabung_impor(baris):
    daftar = st.session_state["daftar"]
    for r in baris:
        daftar = simpan_ke_daftar(daftar, r)
    st.session_state["daftar"] = daftar
    st.toast(f"{len(baris)} ruas digabungkan ke daftar")


def kirim_survei(kr, kb, sm):
    terapkan_input({"in_kr": float(kr), "in_kb": float(kb), "in_sm": float(sm)})
    st.toast("Volume jam puncak dikirim ke Kalkulator")


def tambah_batch(data):
    n = 0
    daftar = st.session_state["daftar"]
    for _, r in data.iterrows():
        try:
            daftar = simpan_ke_daftar(daftar, baris_daftar(r["nama_ruas"], param_dari_batch(r)))
            n += 1
        except Exception:
            continue
    st.session_state["daftar"] = daftar
    st.toast(f"{n} ruas ditambahkan ke daftar perbandingan")


# ------------------------------------------------------------
# Fungsi bantu dan cache (hasil yang sama tidak dihitung ulang)
# ------------------------------------------------------------
def pj(obj):
    return json.dumps(obj, sort_keys=True)


@st.cache_data(show_spinner=False)
def c_pdf(identitas, nama, param_json):
    param = json.loads(param_json)
    return laporan_pdf(identitas, param, hitung_kapasitas(**param), nama)


@st.cache_data(show_spinner=False)
def c_skenario(param_json, kustom_json):
    return skenario_perbaikan(json.loads(param_json), json.loads(kustom_json) if kustom_json else None)


@st.cache_data(show_spinner=False)
def c_lebar_min(param_json):
    return lebar_minimum(json.loads(param_json))


@st.cache_data(show_spinner=False)
def c_proyeksi(param_json, tumbuh_json, tahun):
    return proyeksi(json.loads(param_json), json.loads(tumbuh_json), tahun)


def tampilkan_grafik(fig):
    st.pyplot(fig)
    plt.close(fig)


def excel_bytes(**lembar):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for nama, df in lembar.items():
            df.to_excel(xw, sheet_name=nama[:31], index=False)
    return buf.getvalue()


def baca_berkas(berkas):
    if berkas.name.lower().endswith("xlsx"):
        return pd.read_excel(berkas)
    return pd.read_csv(berkas)


def seksi(teks):
    st.markdown(ui.judul_seksi(teks), unsafe_allow_html=True)


def belum_hitung():
    st.info("Isi data di tab **Kalkulator** terlebih dahulu. Hasilnya dipakai oleh tab ini.")


# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛣️ Kapasitas Jalan")
    st.text_input("Identitas untuk laporan", key="identitas",
                  help="Nama, NIM, dan program studi. Tampil di header dan laporan PDF.")
    seksi("Contoh kasus")
    st.caption("Muat data contoh dengan satu klik.")
    for _nama in CONTOH_KASUS:
        st.button(_nama, on_click=muat_contoh, args=(_nama,), key=f"contoh_{_nama}")
    st.button("↺ Atur ulang input", on_click=atur_ulang, key="btn_reset")
    seksi("Tingkat pelayanan (LOS)")
    st.markdown(
        "| LOS | DJ |\n|---|---|\n"
        "| A | ≤ 0,20 |\n| B | 0,21 - 0,44 |\n| C | 0,45 - 0,74 |\n"
        "| D | 0,75 - 0,84 |\n| E | 0,85 - 1,00 |\n| F | > 1,00 |"
    )
    st.caption("Batas kinerja yang disyaratkan: DJ ≤ 0,85.")

IDENTITAS = st.session_state["identitas"].strip() or IDENTITAS_BAWAAN

# ------------------------------------------------------------
# Header dan tab
# ------------------------------------------------------------
st.markdown(ui.hero("Kalkulator Kapasitas Jalan Perkotaan",
                    "Hitung kapasitas, derajat kejenuhan, dan tingkat pelayanan, lalu uji skenario "
                    "perbaikan dan proyeksi lalu lintas.",
                    ["Acuan PKJI", "Mata Kuliah Aplikasi Komputer", IDENTITAS]), unsafe_allow_html=True)

(tab_hitung, tab_skenario, tab_proyeksi, tab_banding,
 tab_survei, tab_batch, tab_teori) = st.tabs([
    "🧮 Kalkulator", "🛠️ Skenario perbaikan", "📈 Proyeksi", "🗂️ Perbandingan ruas",
    "⏱️ Jam puncak", "📑 Banyak ruas", "📘 Teori",
])

# ============================================================
# TAB 1 - Kalkulator (hasil langsung, tanpa tombol hitung)
# ============================================================
with tab_hitung:
    with st.expander("Panduan singkat"):
        st.markdown(
            "1. Isi data di kolom kiri (atau klik **contoh kasus** di sidebar). Hasil di kanan **berubah langsung**.\n"
            "2. Buka tab **Skenario perbaikan** dan **Proyeksi** untuk menguji solusi dan umur jalan.\n"
            "3. Klik **Unduh laporan (PDF)**, atau **Simpan ke daftar perbandingan** untuk membandingkan beberapa ruas."
        )

    kiri, kanan = st.columns([4, 6], gap="large")

    with kiri:
        with st.container(border=True):
            seksi("1 · Data geometrik")
            st.text_input("Nama ruas / lokasi", key="in_nama")
            tipe = st.selectbox("Tipe jalan", list(TIPE_JALAN.keys()), key="in_tipe",
                                format_func=lambda k: f"{k} · {TIPE_JALAN[k]['nama']}")
            lebar = st.number_input("Lebar jalur efektif total (m)", min_value=0.1, max_value=40.0,
                                    step=0.25, format="%.2f", key="in_lebar")
            _awal, _akhir = rentang_lebar(tipe)
            st.caption(f"Rentang tabel PKJI untuk {tipe}: {fmt_id(_awal, 1)} - {fmt_id(_akhir, 1)} m "
                       "(lebar total). Di luar rentang, nilai dibatasi pada ujung tabel.")
            split = st.number_input("Arus pada arah terbesar (%)", min_value=50.0, max_value=100.0,
                                    step=5.0, format="%.0f", key="in_split")

        with st.container(border=True):
            seksi("2 · Tepi jalan dan lingkungan")
            jenis = st.radio("Tepi jalan", ["bahu", "kereb"], horizontal=True, key="in_jenis",
                             format_func=lambda k: "Jalan berbahu" if k == "bahu" else "Jalan berkereb")
            lebar_hs = st.number_input("Lebar bahu / jarak kereb ke penghalang (m)", min_value=0.0,
                                       max_value=10.0, step=0.25, format="%.2f", key="in_lebar_hs")
            kelas = st.selectbox("Kelas hambatan samping", KELAS_HS, key="in_kelas")
            with st.expander("Bantu tentukan kelas hambatan samping"):
                st.number_input("Frekuensi berbobot kejadian per 200 m per jam", min_value=0.0,
                                step=10.0, format="%.0f", key="fb")
                st.caption(f"Kelas hasil survei: **{kelas_hambatan_samping(st.session_state['fb'])}**")
                st.button("Pakai kelas ini", on_click=pakai_kelas_hs, key="btn_pakai_hs")
            kota = st.selectbox("Ukuran kota", list(UKURAN_KOTA_OPSI.keys()), key="in_kota")

        with st.container(border=True):
            seksi("3 · Volume lalu lintas (dua arah, jam puncak)")
            kr = st.number_input("Kendaraan ringan, KR (kend/jam)", min_value=0.0, step=10.0,
                                 format="%.0f", key="in_kr")
            kb = st.number_input("Kendaraan berat, KB (kend/jam)", min_value=0.0, step=10.0,
                                 format="%.0f", key="in_kb")
            sm = st.number_input("Sepeda motor, SM (kend/jam)", min_value=0.0, step=10.0,
                                 format="%.0f", key="in_sm")
            st.caption("Tidak punya volume jam puncak? Hitung dari data survei di tab **Jam puncak**.")

    nama = (st.session_state["in_nama"] or "").strip() or "Ruas tanpa nama"
    param = dict(tipe=tipe, lebar_total=float(lebar), split=float(split), jenis_hs=jenis, kelas_hs=kelas,
                 lebar_hs=float(lebar_hs), ukuran_kota_juta=UKURAN_KOTA_OPSI[kota],
                 kr=float(kr), kb=float(kb), sm=float(sm))

    with kanan:
        try:
            h = hitung_kapasitas(**param)
        except ValueError as e:
            st.session_state.pop("hasil", None)
            st.error(f"Input tidak valid: {e}")
        else:
            st.session_state["hasil"] = {"param": param, "hasil": h, "nama": nama}

            seksi(f"Hasil · {nama}")
            st.markdown(ui.kartu_hasil(h), unsafe_allow_html=True)
            st.markdown(ui.lencana_status(h["DJ"]), unsafe_allow_html=True)
            st.markdown(ui.meter_dj(h["DJ"]), unsafe_allow_html=True)
            for p in h["peringatan"]:
                st.warning(p)
            st.markdown(ui.catatan(interpretasi(param, h)), unsafe_allow_html=True)

            seksi("Faktor penyesuaian kapasitas")
            st.markdown(ui.batang_faktor(h), unsafe_allow_html=True)

            with st.expander("Rincian dan langkah perhitungan"):
                st.dataframe(format_rincian(h["rincian"]), hide_index=True)
                for judul, rumus in langkah_perhitungan(param, h):
                    st.markdown(f"**{judul}**")
                    st.latex(rumus)

            with st.container(border=True):
                tampilkan_grafik(buat_grafik(h, param))

            a, b, c = st.columns(3)
            with a:
                st.download_button("⬇ Laporan (PDF)", data=c_pdf(IDENTITAS, nama, pj(param)),
                                   file_name="laporan_kapasitas_jalan.pdf", mime="application/pdf", key="dl_pdf")
            with b:
                _in = pd.DataFrame([(k, str(v)) for k, v in param.items()], columns=["Input", "Nilai"])
                st.download_button("⬇ Hasil (Excel)",
                                   data=excel_bytes(Input=_in, Hasil=h["rincian"].astype({"Nilai": object})),
                                   file_name="hasil_kapasitas_jalan.xlsx", mime=MIME_XLSX, key="dl_hasil_xlsx")
            with c:
                st.button("＋ Simpan ke perbandingan", on_click=simpan_ruas, key="btn_simpan")

# ============================================================
# TAB 2 - Skenario perbaikan
# ============================================================
with tab_skenario:
    st.session_state["skenario_ubah"] = None
    if "hasil" not in st.session_state:
        belum_hitung()
    else:
        param = st.session_state["hasil"]["param"]
        h = st.session_state["hasil"]["hasil"]
        nama = st.session_state["hasil"]["nama"]
        seksi(f"Skenario perbaikan · {nama}")
        st.write("Seberapa besar kinerja jalan membaik bila geometrik diperlebar, hambatan samping "
                 "dikurangi, atau arus diturunkan? Tabel di bawah memuat skenario siap pakai dan skenario buatan Anda.")

        with st.container(border=True):
            seksi("Buat skenario sendiri")
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                d_lebar = st.slider("Tambah lebar jalur (m)", 0.0, 6.0, 0.0, 0.25, key="sk_lebar")
            with s2:
                d_bahu = st.slider("Tambah bahu / jarak kereb (m)", 0.0, 2.0, 0.0, 0.25, key="sk_bahu")
            with s3:
                kelas_sk = st.selectbox("Kelas hambatan samping", ["Tidak diubah"] + KELAS_HS, key="sk_kelas")
            with s4:
                d_vol = st.slider("Perubahan arus (%)", -50, 50, 0, 5, key="sk_vol",
                                  help="Negatif = arus turun (mis. manajemen lalu lintas, jalan alternatif).")
            aktif = d_lebar > 0 or d_bahu > 0 or kelas_sk != "Tidak diubah" or d_vol != 0
            kustom = ubah_skenario(param, d_lebar, d_bahu, None if kelas_sk == "Tidak diubah" else kelas_sk,
                                   d_vol) if aktif else None
            st.session_state["skenario_ubah"] = kustom
            if not aktif:
                st.caption("Geser salah satu pengaturan di atas untuk menambahkan baris 'Skenario Anda'. "
                           "Skenario ini juga dipakai di tab Proyeksi.")

        df_s = c_skenario(pj(param), pj(kustom) if kustom else "")
        tabel_s = format_df(df_s, {"Lebar (m)": 2, "C (smp/jam)": 0, "Q (smp/jam)": 0, "DJ": 3})
        if (tabel_s["Catatan"] == "").all():
            tabel_s = tabel_s.drop(columns=["Catatan"])
        st.dataframe(tabel_s, hide_index=True)
        with st.container(border=True):
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

        seksi("Lebar jalur minimum")
        awal, akhir = rentang_lebar(param["tipe"])
        w = c_lebar_min(pj(param))
        if w is None:
            st.warning(f"Pada rentang lebar tabel PKJI ({fmt_id(awal, 2)} - {fmt_id(akhir, 2)} m), "
                       "DJ ≤ 0,85 tidak tercapai. Pertimbangkan menambah lajur.")
        else:
            x1, x2, x3 = st.columns(3)
            x1.metric("Lebar total minimum agar DJ ≤ 0,85", f"{fmt_id(w, 2)} m")
            x2.metric("Lebar eksisting", f"{fmt_id(param['lebar_total'], 2)} m")
            x3.metric("Selisih", f"{fmt_id(max(w - param['lebar_total'], 0), 2)} m")
            if w <= awal + 1e-9:
                st.caption("Nilai ini berada di batas bawah rentang tabel, jadi jalan sudah memenuhi "
                           "pada lebar terkecil yang tercakup tabel.")
        st.download_button("⬇ Tabel skenario (Excel)", data=excel_bytes(Skenario=df_s),
                           file_name="skenario_perbaikan.xlsx", mime=MIME_XLSX, key="dl_skenario")

# ============================================================
# TAB 3 - Proyeksi lalu lintas
# ============================================================
with tab_proyeksi:
    if "hasil" not in st.session_state:
        belum_hitung()
    else:
        param = st.session_state["hasil"]["param"]
        seksi(f"Proyeksi lalu lintas · {st.session_state['hasil']['nama']}")
        st.write("Volume tumbuh geometrik: Qn = Q0 × (1 + i)ⁿ. Kapasitas dianggap tetap, sehingga terlihat "
                 "kapan jalan mulai jenuh.")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                tumbuh = st.slider("Pertumbuhan lalu lintas per tahun (%)", 0.0, 15.0, 5.0, 0.5, key="pj_tumbuh")
            with c2:
                umur = st.slider("Umur rencana (tahun)", 5, 40, 20, key="pj_umur")
            beda = st.checkbox("Laju pertumbuhan berbeda tiap jenis kendaraan", key="pj_beda")
            laju = tumbuh
            if beda:
                d1, d2, d3 = st.columns(3)
                with d1:
                    g_kr = st.slider("KR (%/tahun)", 0.0, 15.0, 4.0, 0.5, key="pj_kr")
                with d2:
                    g_kb = st.slider("KB (%/tahun)", 0.0, 15.0, 3.0, 0.5, key="pj_kb")
                with d3:
                    g_sm = st.slider("SM (%/tahun)", 0.0, 15.0, 8.0, 0.5, key="pj_sm")
                laju = {"kr": g_kr, "kb": g_kb, "sm": g_sm}

        df_p, tahun_jenuh = c_proyeksi(pj(param), pj(laju), umur)
        kustom = st.session_state.get("skenario_ubah")
        df2 = th2 = None
        if kustom:
            df2, th2 = c_proyeksi(pj({**param, **kustom}), pj(laju), umur)

        akhir = df_p.iloc[-1]
        p1, p2, p3 = st.columns(3)
        p1.metric("DJ saat ini", fmt_id(df_p.iloc[0]["DJ"], 3))
        p2.metric(f"DJ tahun ke-{umur}", fmt_id(akhir["DJ"], 3))
        p3.metric("Mulai jenuh (DJ > 0,85)", "Belum jenuh" if tahun_jenuh is None else f"Tahun ke-{tahun_jenuh}")

        if tahun_jenuh is None:
            st.success(f"Sampai tahun ke-{umur}, DJ tetap ≤ 0,85.")
        elif tahun_jenuh == 0:
            st.error("Pada kondisi sekarang DJ sudah melewati 0,85.")
        else:
            st.warning(f"DJ melewati 0,85 pada tahun ke-{tahun_jenuh}. Perbaikan perlu direncanakan "
                       f"sebelum tahun tersebut.")

        if kustom:
            ket1 = "Belum jenuh" if tahun_jenuh is None else f"tahun ke-{tahun_jenuh}"
            ket2 = "belum jenuh" if th2 is None else f"tahun ke-{th2}"
            if th2 is None and tahun_jenuh is not None:
                st.success(f"Dengan **Skenario Anda** jalan tidak jenuh sampai tahun ke-{umur} (tanpa skenario: {ket1}).")
            elif th2 is not None and tahun_jenuh is not None and th2 > tahun_jenuh:
                st.success(f"Dengan **Skenario Anda**, jalan mulai jenuh pada tahun ke-{th2}, "
                           f"yaitu {th2 - tahun_jenuh} tahun lebih lama.")
            else:
                st.info(f"Dengan **Skenario Anda**: {ket2}; tanpa skenario: {ket1.lower()}.")
        else:
            st.caption("Tip: atur 'Skenario Anda' di tab Skenario perbaikan untuk membandingkan "
                       "umur jalan sebelum dan sesudah perbaikan.")

        with st.container(border=True):
            tampilkan_grafik(grafik_proyeksi(df_p, tahun_jenuh, df2, th2))
        with st.expander("Tabel proyeksi per tahun"):
            st.dataframe(format_df(df_p, {"Q (smp/jam)": 0, "C (smp/jam)": 0, "DJ": 3}), hide_index=True)
        st.download_button("⬇ Tabel proyeksi (Excel)", data=excel_bytes(Proyeksi=df_p),
                           file_name="proyeksi_lalu_lintas.xlsx", mime=MIME_XLSX, key="dl_proyeksi")

# ============================================================
# TAB 4 - Perbandingan ruas
# ============================================================
with tab_banding:
    seksi("Perbandingan beberapa ruas")
    daftar = st.session_state["daftar"]
    if not daftar:
        st.info("Belum ada ruas tersimpan. Isi data di tab Kalkulator, lalu klik **Simpan ke perbandingan**. "
                "Ulangi dengan nama ruas yang berbeda. Anda juga bisa memuat daftar dari file CSV di bawah.")
    else:
        df_d = pd.DataFrame(daftar).drop(columns=["param"])
        st.dataframe(format_df(df_d, {"Lebar (m)": 2, "C (smp/jam)": 0, "Q (smp/jam)": 0, "DJ": 3}),
                     hide_index=True)
        n_tidak = int((df_d["DJ"] > BATAS_DJ).sum())
        st.write(f"**{len(df_d)} ruas** dibandingkan; **{n_tidak}** ruas melewati batas DJ 0,85.")
        with st.container(border=True):
            tampilkan_grafik(grafik_perbandingan(df_d))

        with st.container(border=True):
            seksi("Kelola ruas")
            st.selectbox("Pilih ruas", list(df_d["Ruas"]), key="pil_ruas")
            k1, k2, k3 = st.columns(3)
            with k1:
                st.button("Muat ke Kalkulator", on_click=muat_ruas, key="btn_muat")
            with k2:
                st.button("Hapus ruas ini", on_click=hapus_ruas, key="btn_hapus")
            with k3:
                st.button("Kosongkan daftar", on_click=kosongkan_daftar, key="btn_kosong")

        e1, e2 = st.columns(2)
        with e1:
            st.download_button("⬇ Simpan daftar (CSV)", data=daftar_ke_csv(daftar),
                               file_name="daftar_ruas.csv", mime="text/csv", key="dl_daftar_csv",
                               help="Simpan agar daftar bisa dimuat lagi nanti. Daftar hilang bila halaman dimuat ulang.")
        with e2:
            st.download_button("⬇ Perbandingan (Excel)", data=excel_bytes(Perbandingan=df_d),
                               file_name="perbandingan_ruas.xlsx", mime=MIME_XLSX, key="dl_banding_xlsx")

    with st.container(border=True):
        seksi("Muat daftar dari file")
        st.caption("Pilih file CSV hasil 'Simpan daftar (CSV)'. Hasil dihitung ulang dari parameter di dalam file.")
        berkas_d = st.file_uploader("File daftar ruas (CSV)", type=["csv"], key="impor_daftar")
        if berkas_d is not None:
            try:
                baris_impor, gagal = daftar_dari_csv(pd.read_csv(berkas_d))
            except Exception as e:
                st.error(f"File tidak bisa dibaca: {e}")
            else:
                st.write(f"Terbaca **{len(baris_impor)}** ruas" + (f", {gagal} baris dilewati karena tidak valid." if gagal else "."))
                if baris_impor:
                    st.button("Gabungkan ke daftar", on_click=gabung_impor, args=(baris_impor,), key="btn_gabung")

# ============================================================
# TAB 5 - Jam puncak
# ============================================================
with tab_survei:
    seksi("Jam puncak dan PHF dari data survei")
    st.write("Unggah hasil survei volume per **15 menit** (berurutan menurut waktu). Aplikasi mencari 4 interval "
             "berurutan dengan volume terbesar, lalu menghitung Peak Hour Factor (PHF).")
    st.code(", ".join(KOLOM_SURVEI))
    st.caption("waktu = jam mulai interval (mis. 06:00). KR, KB, SM = jumlah kendaraan pada interval itu (bukan per jam).")
    st.download_button("⬇ Template CSV", data=contoh_survei().to_csv(index=False).encode("utf-8"),
                       file_name="template_survei.csv", mime="text/csv", key="dl_tpl_survei")

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
            with st.container(border=True):
                seksi("Komposisi jam puncak")
                st.dataframe(pd.DataFrame({
                    "Jenis": ["Kendaraan ringan (KR)", "Kendaraan berat (KB)", "Sepeda motor (SM)"],
                    "kend/jam": [fmt_id(res["KR"]), fmt_id(res["KB"]), fmt_id(res["SM"])],
                }), hide_index=True)
                st.button("➜ Pakai volume ini di Kalkulator", on_click=kirim_survei,
                          args=(res["KR"], res["KB"], res["SM"]), key="btn_kirim_survei")
            with st.container(border=True):
                tampilkan_grafik(grafik_jam_puncak(res))
            with st.expander("Tabel data survei"):
                st.dataframe(format_df(res["tabel"], {"KR": 0, "KB": 0, "SM": 0, "Total": 0}), hide_index=True)

# ============================================================
# TAB 6 - Banyak ruas sekaligus
# ============================================================
with tab_batch:
    seksi("Hitung banyak ruas sekaligus")
    st.write("Siapkan file **CSV atau Excel** dengan kolom berikut:")
    st.code(", ".join(KOLOM_BATCH))

    contoh = pd.DataFrame([
        ["Jl. Contoh A", "2/2 TT", 7.0, 50, "bahu", "Sedang", 1.0, 0.3, 600, 80, 1200],
        ["Jl. Contoh B", "4/2 TT", 12.0, 60, "kereb", "Tinggi", 1.0, 0.3, 900, 120, 2000],
        ["Jl. Contoh C", "4/2 T", 14.0, 50, "kereb", "Rendah", 1.5, 0.3, 1500, 300, 3000],
    ], columns=KOLOM_BATCH)

    st.caption("Isian yang valid: tipe = 2/2 TT, 4/2 TT, 4/2 T | jenis_hs = bahu atau kereb | "
               "kelas_hs = " + ", ".join(KELAS_HS) + ". Gunakan titik sebagai pemisah desimal.")
    st.download_button("⬇ Template CSV", data=contoh.to_csv(index=False).encode("utf-8"),
                       file_name="template_banyak_ruas.csv", mime="text/csv", key="dl_tpl_batch")

    berkas = st.file_uploader("Unggah file data ruas", type=["csv", "xlsx"], key="unggah_batch")
    data_b = contoh
    if berkas is not None:
        try:
            data_b = baca_berkas(berkas)
        except Exception as e:
            st.error(f"File tidak bisa dibaca: {e}")
            data_b = None
    else:
        st.caption("Menampilkan contoh dari data template. Unggah file sendiri untuk menggantinya.")

    if data_b is not None:
        kurang = [k for k in KOLOM_BATCH if k not in data_b.columns]
        if kurang:
            st.error("Kolom belum lengkap: " + ", ".join(kurang))
        else:
            hasil_batch = hitung_batch(data_b)
            st.dataframe(hasil_batch, hide_index=True)
            valid = hasil_batch[hasil_batch["DJ"].notna()]
            if len(valid) < len(hasil_batch):
                st.warning(f"{len(hasil_batch) - len(valid)} baris gagal dihitung (lihat kolom Status).")
            if len(valid):
                with st.container(border=True):
                    tampilkan_grafik(grafik_perbandingan(valid))
            b1, b2 = st.columns(2)
            with b1:
                st.download_button("⬇ Hasil (Excel)", data=excel_bytes(Hasil=hasil_batch),
                                   file_name="hasil_banyak_ruas.xlsx", mime=MIME_XLSX, key="dl_batch_xlsx")
            with b2:
                st.button("＋ Tambahkan ke Perbandingan ruas", on_click=tambah_batch, args=(data_b,),
                          key="btn_tambah_batch")

# ============================================================
# TAB 7 - Teori
# ============================================================
with tab_teori:
    seksi("Kapasitas jalan perkotaan")
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

    seksi("Rumus analisis lanjutan")
    st.write("Proyeksi lalu lintas (pertumbuhan geometrik, i = laju per tahun, n = tahun):")
    st.latex(r"Q_n = Q_0 \times (1 + i)^n")
    st.write("Faktor jam puncak dari survei per 15 menit:")
    st.latex(r"PHF = \dfrac{V_{jam\ puncak}}{4 \times V_{15\ maks}}")

    seksi("Tingkat pelayanan (LOS)")
    batas_los = {"A": "≤ 0,20", "B": "0,21 - 0,44", "C": "0,45 - 0,74", "D": "0,75 - 0,84",
                 "E": "0,85 - 1,00", "F": "> 1,00"}
    st.markdown("| LOS | DJ | Kondisi arus |\n|---|---|---|\n" +
                "\n".join(f"| {k} | {batas_los[k]} | {v} |" for k, v in DESKRIPSI_LOS.items()))

    seksi("Cakupan dan keterbatasan")
    st.markdown(
        "- Mencakup jalan perkotaan tipe 2/2 TT, 4/2 TT, dan 4/2 T.\n"
        "- Jalan luar kota, jalan bebas hambatan, 6/2 T, dan jalan satu arah belum tercakup.\n"
        "- Nilai tabel pada `kapasitas.py` (C₀, faktor, emp, batas LOS) perlu dicocokkan dengan edisi PKJI yang dipakai.\n"
        "- Skenario dan proyeksi bersifat indikatif: volume dianggap tumbuh geometrik dan kapasitas tetap.\n"
        "- Hasil aplikasi ini untuk pembelajaran, bukan pengganti analisis perencanaan resmi."
    )
    st.caption("Sumber: Pedoman Kapasitas Jalan Indonesia (PKJI), Kementerian Pekerjaan Umum.")

st.markdown(ui.footer("Kalkulator Kapasitas Jalan Perkotaan · Acuan PKJI · Untuk pembelajaran, bukan pengganti "
                      "analisis perencanaan resmi."), unsafe_allow_html=True)
