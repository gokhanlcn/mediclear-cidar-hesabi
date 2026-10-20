import streamlit as st

st.title("MediClear – Daldırma Cidar Kalınlığı Hesabı")

st.markdown(
    "Bu program, spiralli PVC endotrakeal tüpün daldırma (dip molding) ile üretiminde oluşacak "
    "**cidar kalınlığını** deney yapmadan, veri sayfası ve literatür değerleriyle tahmin eder. "
    "Sıcak mandrel plastisole daldırılınca mandrelin ısısıyla bir **jel katmanı** oluşur; mandrel "
    "çekilirken üstüne ince bir **sıvı film** sürüklenir. Toplam kalınlık bu ikisinin toplamıdır."
)

with st.container(border=True):
    st.subheader("Nasıl kullanılır?")
    st.markdown(
        "1. **Verileri gir.** Sol menüden *1. Parametre girişi* sayfasını aç. Elinde veri yoksa "
        "**Örnek değerlerle doldur** düğmesine bas; her değerin yanına bulduğun **kaynağı** yaz.\n"
        "2. **Sayfaları sırayla gez.** Her sayfa bir hesap adımını (D1, D2 …) grafiklerle gösterir. "
        "Grafiklerin altındaki *Bu grafik ne gösteriyor?* kutusu ne göreceğini anlatır.\n"
        "3. **Raporu indir.** Son sayfadan sonuç tablosunu, Excel dosyasını ve tek sayfalık raporu al."
    )

with st.container(border=True):
    st.subheader("Renkler ve işaretler")
    st.markdown(
        "- 🟢 **Tamam** – değer girilmiş ve kaynağı yazılmış.\n"
        "- 🟡 **Kaynak yok** – değer var ama kaynağı boş. Bu değerler ancak **Taslak mod** açıkken "
        "hesaba girer.\n"
        "- 🔴 **Hata** – değer eksik ya da fiziksel olarak anlamsız; yanındaki mesaj ne yapacağını söyler.\n"
        "- **YAKLAŞIK** notu – örnek değerdir, gerçek malzemenin veri sayfasıyla teyit edilmeli."
    )

st.page_link("sayfalar/p1_parametre.py", label="Başla: Parametre girişi", icon="📝")
