#!/usr/bin/env bash
# MediClear – Daldırma Cidar Kalınlığı Hesabı (macOS / Linux başlatıcı)
# Kullanım: Terminalde bu klasöre gelip  ./baslat.sh  yaz (ilk seferde: chmod +x baslat.sh)
cd "$(dirname "$0")" || exit 1
PORT=8501
URL="http://localhost:$PORT"

ac() {  # tarayıcıyı aç
  if command -v open >/dev/null 2>&1; then open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1
  else echo "  Tarayıcıda şu adresi aç: $URL"; fi
}

echo
echo "  MediClear - Daldırma Cidar Kalınlığı Hesabı"
echo "  ============================================"
echo

if curl -s "$URL/_stcore/health" >/dev/null 2>&1; then
  echo "  Program zaten açık; tarayıcıda gösteriliyor."
  ac
  exit 0
fi

# Önceki kurulum bu bilgisayarda çalışıyor mu? (klasör taşınınca bozulur)
if [ -x .venv/bin/python ] && ! .venv/bin/python -c "import streamlit, scipy, plotly, openpyxl" >/dev/null 2>&1; then
  echo "  Önceki kurulum bu bilgisayarda çalışmıyor; yeniden kurulacak."
  rm -rf .venv
fi

if [ ! -x .venv/bin/python ]; then
  PY=""
  for c in python3.12 python3.13 python3.11 python3.14 python3 python; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
      PY="$c"; break
    fi
  done
  if [ -z "$PY" ]; then
    echo "  [HATA] Python 3.11 veya daha yenisi bulunamadı."
    echo "  macOS: https://www.python.org/downloads/ adresinden kur."
    echo "  Linux: paket yöneticisiyle python3 ve python3-venv paketlerini kur."
    echo "  Ayrıntı: KULLANIM.md, '1. Python kurulumu'."
    exit 1
  fi
  echo "  İlk çalıştırma: gerekli paketler kuruluyor (internet gerekir, birkaç dakika sürebilir)..."
  if ! "$PY" -m venv .venv || ! .venv/bin/python -m pip install --disable-pip-version-check -q -r requirements.txt; then
    echo "  [HATA] Paketler kurulamadı. İnternet bağlantını kontrol edip tekrar dene."
    echo "  Linux'ta 'python3-venv' paketi eksik olabilir."
    rm -rf .venv
    exit 1
  fi
  echo "  Kurulum tamamlandı."
fi

echo "  Program açılıyor; tarayıcı birkaç saniye içinde kendiliğinden açılacak."
echo "  Programı kapatmak için bu pencerede Ctrl+C'ye bas."
(
  for _ in $(seq 1 120); do
    if curl -s "$URL/_stcore/health" >/dev/null 2>&1; then ac; break; fi
    sleep 1
  done
) &
exec .venv/bin/python -m streamlit run app.py --server.port "$PORT" --server.address localhost
