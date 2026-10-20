# MediClear – Daldırma Cidar Kalınlığı Hesabı

Spiralli PVC endotrakeal tüp üreten bir daldırma (dip molding) hattında cidar kalınlığını, deney
yapmadan veri sayfası ve literatür değerleriyle tahmin eden bitirme projesi programı.

- **Denklemler (D1–D12):** [cidar_kalinligi_hesabi.md](cidar_kalinligi_hesabi.md)
- **Kullanım kılavuzu:** [KULLANIM.md](KULLANIM.md)

> Sonuçlar modele dayalı tahmindir; kesin değerler devreye almada ölçümle kalibre edilmelidir.

## Çalıştırma

- **Tarayıcıdan:** Streamlit Community Cloud bağlantısı (yayınlandıktan sonra buraya eklenecek).
- **Kendi bilgisayarında:** Windows'ta `baslat.bat`'a çift tıkla; macOS/Linux'ta `./baslat.sh`.
  Ayrıntılar KULLANIM.md'de.

## Yapı

| Klasör | İçerik |
| --- | --- |
| `physics/` | Hesap modülü (arayüzden bağımsız, SI birimleri): D1 ön ısıtma, D2–D4 jel, D5–D8 film, D9–D11 cidar, D12 Monte Carlo, ters tasarım |
| `app.py`, `sayfalar/`, `ui/` | Streamlit arayüzü, grafikler, HTML rapor |
| `tests/` | pytest testleri (`python -m pytest -q`) |
