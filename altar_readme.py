# -*- coding: utf-8 -*-
"""
========================================================================================
ALTAR KAPSAMLI ÇEVRİMDISI SİSTEM, ARAYÜZ & ÖZELLİK KULLANIM KILAVUZU (altar_readme.py)
========================================================================================
* Bütün uygulamayı, her çalışma sekmesini, 5-katmanlı siber güvenlik kalkanlarını,
  yerel/bulut yapay zeka motorlarını, NASA uzay telemetri laboratuvarını,
  CNC simülatörünü, IDE'yi, multimedya araçlarını ve sinematik animasyonları
  19 AYRI KATEGORİDE GÖRSEL DESTEKLİ OLARAK TANITIR.
* Her kategori için projedeki gerçek arayüz tasarımlarını, buton yerleşimlerini,
  HUD panellerini ve sinematik bileşenleri gösteren 1200x680 yüksek çözünürlüklü
  görseller ile desteklenmiştir.
* '🔍 Görseli Büyüt' butonuyla her arayüz tasarımı tam ekranda piksel kalitesinde
  incelenebilir.
* %100 yerel ve çevrimdışı (internetsiz) çalışır.
* Gerçek tam ekran (Kiosk Mode), F11 tam ekran değiştirme ve ESC kısayolu içerir.
========================================================================================
"""

from __future__ import annotations

import os
import sys
import ctypes
import tkinter as tk
from typing import Any, Dict, Optional
import customtkinter as ctk

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

# Windows Yüksek DPI Desteği
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

if getattr(sys, "frozen", False):
    _ANA_DIZIN = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    if not os.path.isdir(os.path.join(_ANA_DIZIN, "assets", "readme_gorseller")):
        _ANA_DIZIN = os.path.dirname(sys.executable)
else:
    _ANA_DIZIN = os.path.dirname(os.path.abspath(__file__))
GORSELLER_DIZINI = os.path.join(_ANA_DIZIN, "assets", "readme_gorseller")


# ======================================================================================
# 19 AYRI KATEGORİ - GÖRSEL DESTEKLİ KILAVUZ VERİ TABANI
# ======================================================================================
README_KATEGORILERI: Dict[str, Dict[str, Any]] = {
    "genel": {
        "baslik": "🏠 Genel Mimari, Üst Panel & Dashboard",
        "ikon": "🏠",
        "gorsel": "01_genel_mimari.png",
        "gorsel_aciklamasi": "Altar Ana Yönetim Dashboard'u: Üst telemetri kontrol çubuğu, AI Durum butonu, Model/Motor/Profil seçicileri, sol ve sağda yer alan 📑 Sekmeler Gezgini butonları, şeffaf siber cam arayüz ve 60 FPS sinematik nöral arka plan.",
        "icerik": """
========================================================================================
                   🚀 ALTAR ÇEVRİMDISI YASAL SİSTEM & MÜHENDİSLİK PLATFORMU
========================================================================================

Altar; yapay zeka iletişimi, profesyonel yazılım geliştirme (IDE), 5-katmanlı siber güvenlik,
tersine mühendislik, endüstriyel CNC simülasyonu ve NASA mikroçekim yarışma laboratuvarını tek
çatı altında birleştiren yüksek performanslı, %100 çevrimdışı çalışabilen hibrit bir sistemdir.

📌 1. ÜST PANEL VE KONTROL ELEMANLARI (GÖRSELDE GÖRÜLDÜĞÜ GİBİ):
  1. '🔴 Yapay Zeka: Kapalı' / '🟢 Yapay Zeka: Açık' Butonu:
     • AI motorunu tek tıkla açıp kapatır. Kapalıyken yerel Ollama modeli VRAM'den tamamen
       boşaltılır (keep_alive=0) ve dizüstü bilgisayarlarda pil tüketimi %70 azalır.
  2. 'Motor' Seçim Menüsü:
     • Yerel (Ollama): İnternetsiz, tamamen kendi bilgisayarınızın GPU/RAM gücüyle çalışır.
     • Bulut (API)   : Google Gemini 2.5/3.0 modelleriyle yüksek hızda akıl yürütme sağlar.
  3. 'Model' Seçim Menüsü:
     • Bilgisayarınızdaki yerel modelleri (jaahas/qwen3.5-uncensored:9b, deepseek-r1, llama3) listeler.
  4. 'Profil' Seçim Menüsü:
     • Hedefinize uygun uzmanlık modunu (Sohbet, Yazılım, Siber Güvenlik, CNC vb.) belirler.
  5. 🌐 Ağ Radarı & 🛡️ EDR Kalkan Butonları:
     • Anlık sistem bağlantı radarına ve 5-katmanlı antivirüs telemetrisine hızlı erişim sağlar.
  6. Canlı Telemetri Göstergesi:
     • CPU %, RAM MB, VRAM ve Ping gecikmesini 3 saniyede bir milisaniye hassasiyetinde günceller.

📌 2. SOL VE SAĞ '📑 SEKME GEZGİNİ' BUTONLARI:
  • Sekmeler çubuğunun hem solunda (x=14) hem de en sağında (relx=1.0) yer alan iki adet
    '📑 Sekmeler' butonu bulunur.
  • Tıklandığında açık olan tüm harici modülleri (Video, Canva, IDE, EDR, Ses, Kamera) ve
    10 ana sekmeyi cam navigatör penceresinde listeler; tek tıkla arayüze geçiş yaptırır.

📌 3. ŞEFFAF SİBER CAM VE 60 FPS SİNEMATİK ARKA PLAN:
  • Tüm paneller yarı-saydam siber cam (glassmorphism) stiliyle tasarlanmıştır.
  • Arkasında her sekmeye özel olarak atanmış 60 FPS prosedürel parçacık animasyonu akar.
  • CPU yükü diferansiyel optimizasyon ile <%1 seviyesinde tutulur.

📌 4. DONANIM KİLİT MOTORU (Ctrl + Tab) VE KOMPAKT IZGARA:
  • 'Ctrl + Tab' kısayoluyla klavye ve fare girişlerini anında kilitleyebilir veya kilidi açabilirsiniz.
  • 0.35s debouncing filtresi ve iki tonlu sesli bildirim (winsound) ile güvenli çalışma sağlar.
  • 13+ yardımcı araç 2 sütunlu kompakt bir ızgarada toplanarak geniş çalışma alanı kazandırılmıştır.
"""
    },
    "sohbet": {
        "baslik": "💬 Yapay Zeka Sohbet & Kodlama Motoru",
        "ikon": "💬",
        "gorsel": "02_sohbet_ai.png",
        "gorsel_aciklamasi": "Yapay Zeka Sohbet Arayüzü: AI yanıt balonları, sözdizimi renklendirilmiş kod blokları, çoklu model köprüsü, ekli multimedya araçları (Resim, Belge, Ses, Ekranı Sor), Oturumlar (Sessions) butonu ve API modeli altındaki README butonu.",
        "icerik": """
========================================================================================
                   💬 YAPAY ZEKA SOHBET & HİBRİT KODLAMA MOTORU
========================================================================================

📌 1. YEREL MODEL MOTORU (OLLAMA):
  • Bilgisayarınızın ekran kartı (VRAM) veya işlemcisi üzerinde %100 gizli ve internetsiz çalışır.
  • Hiçbir veri dışarı sızmaz, üçüncü taraf sunuculara log veya telemetri gönderilmez.
  • Desteklenen modeller: jaahas/qwen3.5-uncensored:9b, deepseek-r1, llama3, mistral, llava.

📌 2. BULUT MOTORU (GOOGLE GEMINI API):
  • API anahtarınız doğrudan yerel '.env' dosyasından okunur; bellek içi oturumda saklanır.
  • Yüksek bağlam penceresi (1M+ token) ve ultra hızlı analitik akıl yürütme sağlar.

📌 3. HIZLI KOMUTLAR VE AJAN ETİKETLERİ:
  • /otonom <görev>    : 6-Katmanlı Otonom Planlama Ajanını devreye sokar (Rerank + Zincirleme).
  • SEARCH:::<sorgu>   : Web'de salt-okunur arama yapar ve özetler.
  • READ:::<url>       : Belirtilen web sayfasını temiz metin olarak kazır ve analiz eder.
  • NASA_SEARCH:::<s>  : NASA NTRS bilimsel veri tabanında arama yapar.
  • MEMORY_SEARCH:::<s>: Önceki sohbet ve oturum kayıtları içinde anlamsal vektör araması yapar.
  • REPO_CLONE:::<url> : Açık kaynak GitHub deposunu salt-okunur belleğe klonlar ve çözümler.

📌 4. SOHBET OTURUMLARI (SESSIONS) & README ERİŞİMİ:
  • Sol alttaki '💬 Oturumlar' butonuyla tüm eski sohbet geçmişlerinizi görüntüleyebilir,
    oturum adını değiştirebilir veya silebilirsiniz (.altar_hafiza/sohbet_oturumlari).
  • API modelinin altında bulunan '📖 README' butonuna tıklandığında bu görsel kılavuz
    doğrudan tam ekranda açılır.

📌 5. ÇOKLU MEDYA GİRDİLERİ (GÖRSEL, SES, BELGE, EKRAN KIRPMA):
  • 📎 Resim Ekle  : PNG/JPG formatındaki görselleri multimodal (Vision) analiz için ekler.
  • 📄 Belge Ekle  : PDF, Word, Altar ve TXT belgelerini ayıklar ve AI'a özetletir.
  • 🎤 Sesli Yazdır : Konuşmanızı metne dönüştürerek anında komut satırına yazar.
  • ✂️ Ekranı Sor  : Ekrandan fare ile dilediğiniz bölgeyi kırpıp doğrudan AI'a soru olarak sorar.

📌 4. ASENKRON MESAJ KUYRUĞU (FIFO) & AKILLI OTO-KAYDIRMA:
  • Model yanıt üretirken yeni bir mesaj yazdığınızda arayüz donmaz; ileti sıraya alınır (⏳ Kuyruk: X mesaj beklemede). Model yanıtı bitirince sıradaki ileti otomatik işlenir.
  • '📜 Oto Kaydır' anahtarı ile yeni yanıtlarda sayfanın otomatik aşağı kaymasını açabilir veya geçmişi okurken konumu sabitleyebilirsiniz.
  • 'OpenRouter API Anahtarı' penceresiyle sk-or-v1-... anahtarınızı canlı test edebilir (/api/v1/auth/key), bakiye sorgulayabilir ve GPT-4o, Claude 3.5, DeepSeek modellerini tek tıkla kullanabilirsiniz.
"""
    },
    "sekmeler_gezgini": {
        "baslik": "🗂️ Sekmeler & Açık Özellikler Gezgini",
        "ikon": "🗂️",
        "gorsel": "03_sekmeler_gezgini.png",
        "gorsel_aciklamasi": "Altar Sekmeler & Özellikler Gezgini Modal Navigatörü: Canlı arama kutusu, çalışan tüm harici modül pencereleri (Video, Canva, IDE, EDR, vb.) ve 10 temel çalışma sekmesi grid'i.",
        "icerik": """
========================================================================================
                   🗂️ ALTAR SEKME VE ÖZELLİK GEZGİNİ NAVİGATÖRÜ
========================================================================================

Altar arayüzündeki Sohbet sekmesinin hem solunda hem de sağında bulunan '📑 Sekmeler'
butonlarına tıklandığında açılan kapsamlı navigasyon modalıdır.

📌 1. CANLI ARAMA VE FİLTRELEME:
  • Klavyeden aramak istediğiniz özelliğin veya sekmenin adını (örn: 'video', 'oyun', 'cnc')
    yazmaya başladığınız an liste canlı olarak daralır ve filtrelenir.
  • ESC tuşuna basıldığında modal anında kapanır.

📌 2. ÇALIŞAN HARİCİ PENCERELERİ TAKİP ETME & ÖNE GETİRME:
  • Altar üzerinden açılan tüm bağımsız pencereleri (Sinematik Video Oynatıcı, Altar Belge &
    Canva Sunum, Ses Kaydedici, Ekran Video Kaydedici, Kamera, Ağ Radarı, Karantina Kasası,
    Ollama Kurucu, README) gerçek zamanlı takip eder.
  • 'Geçiş Yap' butonuna tıklandığında ilgili pencere görev çubuğu veya diğer pencerelerin
    arkasında kalmış olsa dahi Windows API (SetForegroundWindow) ile doğrudan en öne getirilir.

📌 3. 10 TEMEL ÇALIŞMA SEKMESİNE ANINDA ERİŞİM:
  • Altar içindeki 10 ana çalışma sekmesine tek tıkla geçiş sağlar:
    1. 💬 Yapay Zeka Sohbet & Kodlama Motoru
    2. 🎮 Python Siber & Retro Oyun Merkezi
    3. 🎵 Müzik & Sinematik Animasyon Sahnesi
    4. 🐍 Python IDE, Editör & Canlı Terminal
    5. 📁 Dosya Gezgini & Kriptografik Kasa
    6. 📊 Kazınan Veri, Analiz & Turbo Modem
    7. 📐 CNC G-Code 2D/3D Simülatör (Haas V34)
    8. 🔬 Tersine Mühendislik & Hex Laboratuvarı
    9. 🦠 5-Katmanlı Antivirüs & EDR Kalkanı
    10. 🚀 NASA Mikroçekim & Uzay Telemetri Laboratuvarı
"""
    },
    "oyun": {
        "baslik": "🎮 Python Siber Oyun: Galaktik Savunma",
        "ikon": "🎮",
        "gorsel": "04_siber_oyunlar.png",
        "gorsel_aciklamasi": "Altar Galaktik Savunma (Nebula Interceptor): 60 FPS donanım hızlandırmalı uzay savaşı simülasyonu, akıcı gemi kontrolleri, dinamik lazer mermileri, kalkan ve EMP bomba barı.",
        "icerik": """
========================================================================================
             🎮 PYTHON SİBER OYUN: GALAKTİK SAVUNMA (NEBULA INTERCEPTOR - 60 FPS)
========================================================================================

Altar projesinde tamamen yerli olarak Python ve Tkinter parçacık fiziği ile geliştirilmiş,
akıcı 60 FPS donanım hızlandırmalı arcade uzay savaşı oyunudur (%100 internetsiz çalışır).

📌 1. OYUN DİNAMİKLERİ VE MEKANİKLER:
  • Akıcı 60 FPS Fizik Motoru: Uzay geminiz ve düşman kruvazörleri milisaniye hassasiyetinde hareket eder.
  • Kalkan ve Can Barı: Düşman mermileri veya gemi çarpmalarında kalkanınız darbeyi emer.
  • EMP Süper Bombası: Ekranda sıkıştığınızda 'B' tuşuna basarak tüm düşmanları tek seferde yok edin.
  • Dinamik Sektör & Seviye Artışı: Düşman dalgalarını temizledikçe sektör seviyesi ve skor katlayıcı artar.
  • Lazer Güçlendirmesi: Yok edilen elit gemilerden düşen güç çekirdekleriyle ikili/üçlü lazer atışı açılır.

📌 2. KONTROLLER:
  • Sol / Sağ Ok (← / →) veya A / D : Gemiyi sağa ve sola yönlendirir.
  • Boşluk (Space)                  : Çift plazma lazer mermisi ateşler.
  • B Tuşu                          : EMP Süper Bombasını patlatır.
  • P veya Boşluk                   : Oyunu duraklatır ve devam ettirir.

📌 3. TAM EKRAN OYNAMA MODU (KIOSK):
  • '⛶ Tam Ekran Oyna' butonuna tıklayarak oyunu tüm monitörü kaplayan çerçevesiz
    kiosk modunda odaklanmış olarak oynayabilirsiniz. ESC veya F11 ile pencereye dönülür.
"""
    },
    "muzik": {
        "baslik": "🎵 Müzik & Sinematik Ses Merkezi (YouTube & Arka Plan)",
        "ikon": "🎵",
        "gorsel": "05_muzik_sinematik.png",
        "gorsel_aciklamasi": "Müzik & Sinematik Animasyon Sahnesi: YouTube MP3 indirici paneli, kesintisiz arka plan çalar, 3 sinematik tema (Doğa Şelale, Mavi Plazma, Matrix) ve frekans ekolayzır barları.",
        "icerik": """
========================================================================================
                   🎵 MÜZİK & SİNEMATİK SES MERKEZİ (YOUTUBE & ARKA PLAN)
========================================================================================

Altar Müzik Merkezi; çalışma, kodlama ve araştırma yaparken dikkatinizi dağıtmadan
arka planda müzik dinlemenizi sağlayan gelişmiş bir ses ve görselleştirici motorudur.

📌 1. YOUTUBE VE YOUTUBE MUSIC ENTEGRASYONU:
  • YouTube veya YouTube Music bağlantısını (URL) veya şarkı adını arama kutusuna yazıp
    '📥 Sesi İndir (MP3)' butonuna tıklayın.
  • Sistem yt-dlp ve yerel ffmpeg motorunu kullanarak videodan en yüksek kaliteli sesi
    (192 kbps MP3) çeker ve yerel kütüphanenize otomatik ekler.

📌 2. KESİNTİSİZ ARKA PLAN SESİ (BACKGROUND PLAYBACK):
  • Müzik çalmaya başladığında Altar içerisinde başka sekmelere (Sohbet, IDE, Kasa, CNC)
    geçseniz dahi müzik arka planda kesintisiz çalmaya devam eder.
  • pygame.mixer altyapısı sayesinde işlemciyi yormaz (CPU yükü <%0.8).

📌 3. 3 TEMALI SİNEMATİK ANİMASYON SAHNESİ:
  • Müzik çalarken arka planda 3 farklı temada 60 FPS sinematik animasyon akar:
    1. 🌊 Doğa & Şelale: Işıltılı su damlaları, biolüminesans orman parçacıkları.
    2. 🔥 Kozmik Mavi Plazma: Müzik frekansına duyarlı plazma dalga halkaları.
    3. ⚡ Cyberpunk Matrix Spektrumu: Müziğin ritmine göre dans eden ses çubukları.

📌 4. TAM EKRAN SİNEMATİK GÖRSELLEŞTİRİCİ:
  • '🗖 Tam Ekran' butonuna basarak monitörünüzü ambient bir ses ve ışık sahnesine dönüştürebilirsiniz.
"""
    },
    "video": {
        "baslik": "🎬 Altar Sinematik MP4 Oynatıcı (Borderless Tam Ekran)",
        "ikon": "🎬",
        "gorsel": "06_sinematik_video.png",
        "gorsel_aciklamasi": "Altar Sinematik MP4 Video Oynatıcı: Çerçevesiz (borderless) tam ekran sahnesi, 60 FPS sinematik intro, akıllı gizlenen neon HUD kontrolleri ve klavye kısayolları paneli.",
        "icerik": """
========================================================================================
                   🎬 ALTAR SİNEMATİK MP4 VİDEO OYNATICI
========================================================================================

Altar'da açılan tüm MP4 videoları sinematik bir parçacık animasyonuyla başlar ve doğrudan
çerçevesiz (borderless) tam ekranda açılır.

📌 1. ÖZELLİKLER VE TEKNİK AVANTAJLAR:
  • Tıklama Gerektirmeyen Otomatik Odak: Windows API (SetForegroundWindow) ile görev
    çubuğu arkasında kalmaz; doğrudan en önde ve odaklanmış olarak başlar.
  • Donanım Hızlandırmalı Oynatım: OpenCV (cv2) + FFmpeg + Pygame senkronizasyonu ile
    akıcı 60 FPS görüntü ve ses aktarımı.
  • Akıllı Gizlenen HUD Kontrol Çubuğu: Fare hareket etmediğinde kontroller 2.5 saniye
    sonra otomatik kaybolarak sinematik bir izleme alanı sunar.

📌 2. KLAVYE KISAYOLLARI:
  • Boşluk (Space)  : Oynat / Duraklat
  • Sol / Sağ Ok    : 5 Saniye Geri / İleri Sar
  • Yukarı / Aşağı  : Ses Düzeyini Artır / Azalt
  • F11 veya Çift Tık: Tam Ekran / Pencere Modu Geçişi
  • ESC veya Q      : Oynatıcıdan Çıkış
"""
    },
    "word": {
        "baslik": "📝 Altar Belge & Canva Sunum Stüdyosu",
        "ikon": "📝",
        "gorsel": "07_canva_ve_belge.png",
        "gorsel_aciklamasi": "Altar Belge & Canva Sunum Stüdyosu: Sol slayt listesi, 16:9 geniş ekran slayt tuvali, neon kartlar, mimari şablonlar, PDF/PNG dışa aktarma butonları ve .altar kripto kelime işlemcisi.",
        "icerik": """
========================================================================================
                   📝 ALTAR BELGE & CANVA SUNUM STÜDYOSU
========================================================================================

Sol alt menüdeki '📝 Altar Belge' butonuna tıklandığında açılan, profesyonel belge ve
16:9 slayt hazırlama stüdyosudur.

📌 1. CANVA TARZI PROFESYONEL 16:9 SLAYT STÜDYOSU:
  • 16:9 4K Geniş Ekran Tuval: Modern kurumsal ve siber sunumlar hazırlayın.
  • Hazır Mimari Şablonlar:
    1. 🚀 Başlık & Giriş Slaytı (Title & Hero)
    2. 📊 2 Sütunlu Karşılaştırma & Analiz Kartları
    3. 📐 Teknik Mimari & Sistem Akış Diyagramı
    4. 📈 Metrikler & KPI Göstergeleri
    5. 🛡️ Siber Güvenlik & Tehdit Matrisi
  • Zengin Bileşenler: Neon kartlar, başlıklar, açıklama kutuları ve resim ekleme.
  • Tam Ekran Sunum Modu (F5): Slaytlarınızı tam ekranda klavye oklarıyla sunun.

📌 2. ÇOK SAYFALI PDF VE ULTRA-HD PNG DIŞA AKTARMA:
  • '📄 PDF Olarak Aktar'  : Tüm slaytları tek bir çok sayfalı PDF dokümanı yapar.
  • '🖼️ PNG Olarak Aktar' : Aktif slaytı 1920x1080 yüksek çözünürlüklü PNG olarak kaydeder.
  • '💾 Sunumu Kaydet'     : Sunumu .altarsunumu formatında yerel olarak saklar.

📌 3. .ALTAR ŞİFRELİ KELİME İŞLEMCİSİ (WORD PROGRAMI):
  • SHA-256 imzalı zengin metin düzenleme (Kalın, İtalik, Renkler, Fontlar, Tablolar).
  • Not defteri entegreli; tam ekran açılır ve doğrudan çalışmaya hazır gelir.
"""
    },
    "ollama_kurucu": {
        "baslik": "⚡ Otomatik Ollama & Model Kurucusu (UAC & Firewall)",
        "ikon": "⚡",
        "gorsel": "08_ollama_kurucu.png",
        "gorsel_aciklamasi": "Otomatik Ollama & Model Kurucu Sihirbazı: UAC yönetici yükseltmesi, https://ollama.com/download otomatik indirme, Windows Güvenlik Duvarı port kuralı ve qwen3.5 & llava model çekme ilerlemesi.",
        "icerik": """
========================================================================================
                   ⚡ OTOMATİK OLLAMA VE SİBER MODEL KURUCU SİHİRBAZI
========================================================================================

Altar projesini ve ileride oluşturulacak bağımsız EXE programını kullanıcılar için
sıfır teknik bilgiyle, tek tıklamayla kurulabilir hale getiren otomatik sihirbazdır.

📌 SİSTEMİN 4 ADIMLI ÇALIŞMA MİMARİSİ:
  1. Otomatik UAC Yönetici Yükseltmesi:
     • Program açıldığında Windows Yönetici yetkisi kontrol edilir.
     • Kullanıcı sadece tek bir standart Windows 'Evet' (UAC) onayına bastığında tüm
       yetkileri otomatik devralır.
  2. https://ollama.com/download Otomatik İndirme:
     • Ollama sistemde kurulu değilse resmi Windows kurulum paketi arka planda indirilir
       ve sessiz modda (/SILENT) kurulur.
  3. Windows Defender Güvenlik Duvarı Kuralı:
     • Ollama'nın yerel haberleşmesi için Windows Defender Güvenlik Duvarı'na otomatik
       izin kuralı tanımlanır (shell=False / güvenli parametre ayrıştırma).
  4. localhost:11434 API Servisini Başlatma & Model Çekme:
     • 'ollama serve' arka planda bağımsız servis olarak başlatılır ve port yanıt verene
       kadar doğrulanır.
     • 'jaahas/qwen3.5-uncensored:9b' (Birincil akıl yürütme modeli)
     • 'llava:latest' (Görsel ve resim anlama modeli)
     • Modeller otomatik olarak Ollama API'si üzerinden indirilip SHA-256 ile doğrulanır.
"""
    },
    "guvenlik": {
        "baslik": "🛡️ Siber Güvenlik, Ağ IPS & Canlı Ağ Radarı",
        "ikon": "🛡️",
        "gorsel": "09_guvenlik_ve_radar.png",
        "gorsel_aciklamasi": "Siber Güvenlik & Ağ Radarı Arayüzü: Canlı aktif TCP/UDP bağlantı radarı tablosu (Uygulama, PID, Protokol, Durum, Yerel/Uzak IP), Ağ IPS Kalkanı ve Honeypot tuzak sayaçları.",
        "icerik": """
========================================================================================
                   🛡️ SİBER GÜVENLİK, AĞ IPS KALKANI & AĞ RADARI
========================================================================================

Altar, sisteminizi dış tehditlere ve yetkisiz dinlemelere karşı proaktif koruyan
çok katmanlı güvenlik kalkanlarına sahiptir (%100 salt-okunur ve güvenli mimari).

📌 1. CANLI AĞ BAĞLANTI RADARI (SALT-OKUNUR):
  • Üst bardaki '🌐 Ağ Radarı' butonuna tıklayarak açılır.
  • Bilgisayarınızdaki tüm aktif dinleyen portları, bağlı yabancı IP adreslerini ve
    işlem kimliklerini (PID) salt-okunur olarak listeler.
  • Hiçbir veriyi değiştirmez, zararlı yazılımların gizli bağlantılarını anında yakalar.

📌 2. AĞ IPS VE DEFENDER ENTEGRASYONU:
  • 500+ bilinen saldırı imzasıyla ağ paketlerini inceler.
  • SYN Flood, Port Tarama ve şüpheli ARP saldırılarını tespit eder.
  • Şüpheli IP adreslerini Windows Güvenlik Duvarı'nda otomatik izole etme desteği sunar.

📌 3. HONEYPOT TUZAKLARI (YEM PORTLAR):
  • Sistemde 21 (FTP), 23 (Telnet), 2222 (SSH) gibi sahte tuzak portlar dinler.
  • Yerel ağdan bu portlara izinsiz bağlanan saldırganları anında tespit edip kilitler.
"""
    },
    "ide": {
        "baslik": "🐍 Python IDE, Editör & Canlı Terminal",
        "ikon": "🐍",
        "gorsel": "10_python_ide.png",
        "gorsel_aciklamasi": "Altar Python IDE & Canlı Terminal: Sekmeli kod editörü, satır numaraları, F5 canlı terminal çıktısı, AST güvenlik denetleyicisi, Pip Paket Yöneticisi ve Hazır Mimari Şablon seçici.",
        "icerik": """
========================================================================================
                   🐍 PYTHON IDE, CANLI TERMİNAL & KOD EDİTÖRÜ
========================================================================================

PyCharm veya VS Code açmadan (~2.65 GB RAM tasarrufuyla) eksiksiz Python geliştirme ortamı:

📌 1. KOD YAZMA VE SÖZDİZİMİ DENETİMİ:
  • 'Python IDE & Editör' sekmesine geçin.
  • Sözdizimi renklendirmesi (Syntax Highlighting) ve otomatik girintileme desteklenir.
  • AST Denetleyicisi: Kodunuzu çalıştırmadan önce arka planda Abstract Syntax Tree ile
    tehlikeli sistem çağrıları (`shell=True`, `rmdir /s`, şüpheli socket) için denetler.

📌 2. ÇALIŞTIRMA VE HATA AYIKLAMA (F5):
  • F5 tuşuna veya '▶ Kodu Çalıştır' butonuna basarak kodu alt taraftaki canlı terminalde çalıştırın.
  • Çıktılar, hatalar (Traceback) ve çalışma süresi milisaniye hassasiyetinde terminale basılır.
  • Kod kilitlenirse '⏹ Süreci Durdur' butonuyla güvenli şekilde sonlandırılabilir.
  • '🤖 Hatayı AI'a Sor' butonuyla terminaldeki hatayı tek tıkla çözüme kavuşturabilirsiniz.

📌 3. PİP PAKET YÖNETİCİSİ:
  • '📦 Pip Yöneticisi' butonuyla bilgisayarınızda yüklü Python paketlerini listeleyebilir,
    yeni kütüphaneler kurabilir veya güncelleyebilirsiniz (CWE-88 Flag Injection korumalı).

📌 4. HAZIR KOD ŞABLONLARI:
  • '📋 Kod Şablonları' butonuna tıklayarak veri analizi, makine öğrenmesi, soket programlama,
    Tkinter arayüz ve kriptografi şablonlarını tek tıkla editöre aktarabilirsiniz.
"""
    },
    "kasa": {
        "baslik": "📁 Dosya Gezgini & Kriptografik Kasa",
        "ikon": "📁",
        "gorsel": "11_dosya_gezgini_kasa.png",
        "gorsel_aciklamasi": "Dosya Gezgini & Kriptografik Kasa: Yerel sürücüler (C:, D:, E:), dosya listesi, sağda SHA-256 doğrulama önizlemesi ve altta PBKDF2 + AES-256 şifreli (.altar_lock) kasa kilitleme paneli.",
        "icerik": """
========================================================================================
                   📁 DOSYA GEZGİNİ & KRİPTOGRAFİK GÜVENLİ KASA
========================================================================================

📌 1. GELİŞMİŞ YEREL DİZİN GEZGİNİ:
  • 'Dosya Gezgini & Kasa' sekmesi altında tüm yerel sürücülerinizi (C:, D:, E: vb.) tarayın.
  • Dosya boyutları, uzantıları ve son değiştirilme tarihleri anında listelenir.
  • Dosya arama kutusuyla disklerinizdeki belgeleri hızla bulun.

📌 2. ÇİFT KATMANLI KRİPTO KASA (AES-256):
  • İstediğiniz hassas dosyayı veya klasörü kendi belirleyeceğiniz şifre ile kilitleyin.
  • Şifrelenen dosyalar '.altar_lock' formatına dönüştürülür ve şifre bilinmeden açılamaz.
  • Çözme (Decrypt) işlemi doğrudan RAM içinde yapılır; diskte geçici iz bırakılmaz.
  • SHA-256 Bütünlük Denetimi: Dosyanın değiştirilip değiştirilmediğini doğrular.

📌 3. SİSTEM DOSYASI KORUMASI:
  • C:\\Windows, Program Files ve projenin kendi kök dizini güvenlik amacıyla kilitlenemez;
    işletim sisteminin zarar görmesi %100 engellenir.
"""
    },
    "analiz": {
        "baslik": "📊 Kazınan Veri, Analiz & Ağ Yönetimi",
        "ikon": "📊",
        "gorsel": "12_veri_kazima_modem.png",
        "gorsel_aciklamasi": "Kazınan Veri & Turbo Modem QoS Paneli: Sol panelde NASA NTRS ve web kazıma SSD arşivi; sağ panelde modem gecikme/bant genişliği monitörü ve port süreç dondurma yöneticisi.",
        "icerik": """
========================================================================================
                   📊 KAZINAN VERİ, ANALİZ & TURBO MODEM / PORT MERKEZİ
========================================================================================

📌 1. WEB VERİ KAZIMA VE SSD ARŞİVİ:
  • 'Kazınan Veri & Analiz Merkezi' sekmesinde NASA NTRS veya açık web kaynaklarından
    kazınan tablolar, metinler ve JSON verileri filtrelenir ve analiz edilir.
  • Veriler doğrudan SSD'ye arşivlenebilir veya AI Sohbet ekranına aktarılabilir.

📌 2. TURBO MODEM HOTSPOT & QOS:
  • Alt panelin sol bölümünde yerel modem ağ parametrelerini, bağlantı gecikmesini (Ping),
    paket kaybını ve bant genişliği kalitesini (QoS) denetler.

📌 3. PORT & UYGULAMA YÖNETİCİSİ:
  • Alt panelin sağ bölümünde çalışan yerel servislerin portlarını güvenle listeler.
  • Şüpheli portları izole etmenize ve ağ trafiğini optimize etmenize olanak tanır.
"""
    },
    "cnc": {
        "baslik": "📐 CNC G-Code 2D/3D Simülatör (Haas V34)",
        "ikon": "📐",
        "gorsel": "13_cnc_simulator.png",
        "gorsel_aciklamasi": "Haas V34 Endüstriyel CNC Simülatörü: Haas kumanda paneli, G-Code program editörü, 2D izometrik takım yolu, PyQt6 OpenGL 3D katı model işleme ve mengene çarpışma koruması.",
        "icerik": """
========================================================================================
                   📐 ENDÜSTRİYEL CNC G-CODE 2D & 3D SİMÜLATÖR (HAAS V34)
========================================================================================

📌 1. 2D İZOMETRİK KATI MODEL VE TAKIM YOLU:
  • 'CNC G-Code 2D Simülatör' sekmesi Altar içine gömülüdür.
  • Kütük X/Y/Z boyutlandırma, mengene sıkıştırma payı ve naylon kleransı hesaplanır.
  • ATC Takım Kütüphanesi: T1 (Kaba Freze), T2 (Pah Kırıcı), T3 (Küre Freze).

📌 2. PYQT6 OPENGL 3D KATI MODEL MOTORU (SWANSOFT):
  • '🚀 3D Katı Model Aç' butonuna basıldığında bağımsız süreçte tam ekran açılır.
  • G00, G01, G02, G03 dairesel enterpolasyon, mengene çarpışma (crash) denetimi,
    iş mili devri ve soğutma sıvısı simülasyonunu tam ekran ve akıcı olarak sunar.
  • F11 tuşuyla tam ekran açılıp kapatılabilir; ESC ile çıkış yapılabilir.
"""
    },
    "tersine": {
        "baslik": "🔬 Tersine Mühendislik, Hex Lab & DPI",
        "ikon": "🔬",
        "gorsel": "14_tersine_muhendislik.png",
        "gorsel_aciklamasi": "Tersine Mühendislik & Hex Laboratuvarı: 16'lık hex matrisi ve ASCII dökümü, RAM içi Python bytecode decompiler, Shannon Entropi radar grafiği ve PE/ELF başlık çözücü.",
        "icerik": """
========================================================================================
                   🔬 TERSİNE MÜHENDİSLİK, HEX LABORATUVARI & DERİN PAKET (DPI)
========================================================================================

📌 1. SALT-OKUNUR STATİK ANALİZ VE BYTECODE:
  • 'Tersine Mühendislik' sekmesinden herhangi bir .pyc, .exe, .bin veya .dll dosyası seçin.
  • Python Bytecode Decompile, Disassembly (Opcode analizi) ve PE/ELF başlık yapısı çözülür.
  • Dosya asla çalıştırılmaz; %100 güvenli RAM içi statik inceleme yapılır.

📌 2. HEX DÖKÜMÜ VE ENTROPİ RADARI:
  • 16'lık (Hex) döküm, ASCII eşlemesi ve gömülü metin dizileri (Strings) taranır.
  • Shannon Entropi Hesaplayıcısı: Dosyanın sıkıştırılmış, şifrelenmiş veya paketlenmiş
    (Packer: UPX vb.) olup olmadığını tespit eder.

📌 3. DERİN PAKET ANALİZİ (DPI & DESYNC):
  • Alt panelde yerel ağ paketlerini inceleyen ve TLS/SNI uyumluluğunu test eden
    DPI analizörü yer alır.
"""
    },
    "edr": {
        "baslik": "🦠 5-Katmanlı Antivirüs & EDR Kalkanı",
        "ikon": "🦠",
        "gorsel": "15_edr_antivirus.png",
        "gorsel_aciklamasi": "5-Katmanlı Antivirüs & EDR Kalkanı: Statik imza taraması, Shannon entropi radarı, AST kod analizörü, fidye honeypot tuzağı, canlı telemetri ve AES-GCM Karantina Kasası.",
        "icerik": """
========================================================================================
                   🦠 5-KATMANLI GELİŞMİŞ ANTİVİRÜS & EDR KALKANI
========================================================================================

Altar EDR, sisteminizde sessizce çalışan ve sıfır-gün tehditlerine karşı koruyan 5 katmana sahiptir:

📌 1. KATMANLAR:
  1. Statik SHA-256 İmza ve Bilinen Tehdit Veritabanı Taraması.
  2. Shannon Entropi Radarı (Şifrelenmiş fidye yazılımlarını çalışmadan yakalar).
  3. AST & Kod Analizörü (Zararlı Python ve komut dosyası davranışlarını engeller).
  4. Fidye Tuzağı (Honeypot / Canary Dosya Koruması - Dizin manipülasyonunu anında kilitler).
  5. İndirilenler & Otomatik Karantina Kalkanı.

📌 2. 6 İLERİ DÜZEY GÜVENLİK VE ANTİVİRÜS CEPHANELİĞİ (altar_gelismis_guvenlik.py):
  1. 🧠 AI Tehdit Açıklayıcısı  : Dosyayı çalıştırmadan PE başlığı, entropi ve 15+ API ile analiz eder; AI Türkçe rapor üretir.
  2. 🌲 Süreç Ağacı Radarı      : Ebeveyn-çocuk ilişkisini listeler, gizli LOLBin süreçlerini yakalar, dondurma/sonlandırma sunar.
  3. 🔑 Autoruns Kalkanı        : Windows Registry ve Startup başlangıç kalıcılık mekanizmalarını derinlemesine tarar.
  4. 🔌 USB Flaş Koruyucu       : Flaş bellekleri algılar, kısayol virüslerini listeler ve tek tıkla autorun aşısı uygular.
  5. 🌐 C2 Sızıntı Avcısı       : Dış ağ bağlantılarını bilinen C2 portları (4444, 1337 vb.) ile eşleştirir.
  6. 🔒 Bütünlük Kalkanı (FIM)  : Windows hosts dosyasını izler, zararlı DNS yönlendirmelerini engeller ve orijinal şablonu geri yükler.

📌 3. PERFORMANS ETKİSİ:
  • Cihazınızı yormayan diferansiyel tarama mantığıyla çalışır.
  • RAM tüketimi minimaldir (<45 MB); oyun veya ağır mühendislik yazılımlarını yavaşlatmaz.
"""
    },
    "nasa": {
        "baslik": "🚀 NASA Mikroçekim & Uzay Telemetri Laboratuvarı",
        "ikon": "🚀",
        "gorsel": "16_nasa_mikrocekim.png",
        "gorsel_aciklamasi": "NASA Mikroçekim Laboratuvarı: 0G/1G küresel soğuk alev (cool flame) fiziği, damlacık çapı lineer d²-yasası yanma grafiği, akustik veri seslendirme (sonification) ve osiloskop dalgası.",
        "icerik": """
========================================================================================
                   🚀 NASA MİKROÇEKİM & UZAY TELEMETRİ YARIŞMA MERKEZİ
========================================================================================

'🚀 Simülasyonlar' veya 'Radar & Alev' butonlarıyla açılan NASA yarışma ve araştırma merkezi:

📌 1. CANLI 0G/1G DAMLACIK & d²-YASASI SİMÜLATÖRÜ:
  • BASS, ACME ve Saffire uzay görevi yakıtları (n-Heptan, Metan, Etanol, LH2).
  • Yerçekimsiz ortamda damlacık çapının karesinin zamanla lineer küçülmesini
    (d² = d0² - K*t) ve mikroçekimde oluşan küresel soğuk alev (Cool Flame) fiziğini canlandırır.

📌 2. AKUSTİK VERİ SESLENDİRME (SONIFICATION) & OSİLOSKOP:
  • CSV veya telemetri sayısal verilerini doğrudan işitilebilir ses frekanslarına dönüştürür.
  • Gözle kaçabilecek mikro yerçekimi telemetri anomalilerini kulakla duymanızı sağlar.
  • Diske dosya yazmaz; tamamen RAM içinde dalga sentezleyerek çalar.
"""
    },
    "multimedya": {
        "baslik": "🎬 Multimedya: Ekran Video, Ses & Kamera",
        "ikon": "🎬",
        "gorsel": "17_multimedya_studyosu.png",
        "gorsel_aciklamasi": "Multimedya Stüdyosu: 60 FPS ekran video kaydedici paneli, stüdyo ses kaydedici (mikrofon dalga formu ve dB ölçer) ve web kamerası stüdyosu (tek tıkla AI Vision köprüsü).",
        "icerik": """
========================================================================================
                   🎬 MULTİMEDYA: EKRAN VİDEO, SES & KAMERA STÜDYOSU
========================================================================================

Sol alt menü çubuğunda yer alan donanım multimedya araçları:

📌 1. 🎬 EKRAN VİDEO KAYDEDİCİ & 🔴 HIZLI VİDEO:
  • Ekranınızdaki çalışmaları, kodlama seanslarını veya simülasyonları sıfır kasma ile kaydeder.
  • Mikrofon sesini videoya eşzamanlı olarak gömer.

📌 2. 🎙️ SES KAYDEDİCİ & 🔴 HIZLI KAYIT:
  • Mikrofonunuzdan yüksek kaliteli stüdyo ses kaydı (.wav) alır.
  • Ses seviyesi ölçer ve dalga formu görselleştirmesi sunar.

📌 3. 📷 KAMERA & 🔴 HIZLI KAMERA:
  • Web kameranızı açarak anlık fotoğraf çeker veya video kaydeder.
  • Çekilen fotoğrafları tek tıkla AI Sohbet ekranına görsel analiz (Vision) için aktarabilirsiniz.
"""
    },
    "animasyonlar": {
        "baslik": "✨ 10 Prosedürel Sinematik Arka Plan Animasyonu",
        "ikon": "✨",
        "gorsel": "18_sinematik_animasyonlar.png",
        "gorsel_aciklamasi": "10 Prosedürel Sinematik Arka Plan Animasyonu: Nöral AI Ağı, Kripto Kasa, Synthwave Grid, Doğa Şelalesi, Matrix Kodu, Veri Galaksisi Radarı, CNC Lazer, Enerji Kalkanı, Ayrıştırıcı ve EDR Taraması.",
        "icerik": """
========================================================================================
                   ✨ 10 PROSEDÜREL SİNEMATİK ARKA PLAN ANİMASYONU
========================================================================================

Altar'ın tüm sekmelerinde arayüz şeffaf yapılmış olup, her sekmenin arkasında o özelliğin
ruhuna özel 60 FPS prosedürel bir sinematik animasyon çalışır:

📌 10 SEKMEYE ÖZEL ANİMASYON KATALOĞU:
  1. Nöral AI Ağı         (💬 Sohbet)     : Sinaptik nöron düğümleri, nabız atan veri darbeleri.
  2. Kripto Kasa          (📁 Dosya Gezgini): Kayan hex sütunları, kilit/kasa poligon halkaları.
  3. Synthwave Neon Grid  (🎮 Oyun)       : Neon retro ızgara, dağ silueti, günbatımı ufuk çizgisi.
  4. Doğa Şelalesi        (🎵 Müzik)      : Biolüminesans su damlaları, ambient orman parçacıkları.
  5. Matrix Dijital Yağmur(🔬 Tersine Müh.): Yukarıdan aşağıya akan siber yeşil kod harfleri.
  6. Veri Galaksisi Radarı(📊 Analiz & Modem): Dönen yıldız diski, radar tarama ışını, pulsar darbeleri.
  7. CNC Lazer Takım Yolu (📐 CNC Simülatör): G-Code takım yolu koordinatları, lazer kıvılcımları.
  8. Kuantum Enerji Kalkanı(🛡️ Siber Güvenlik): Altıgen siber kalkan petekleri ve enerji dalgaları.
  9. Ayrıştırıcı Dalga    (🎬 Multimedya)  : Ses/video sinematik dalga formu ve sinüs frekansları.
  10. EDR Tehdit Taraması (🦠 Antivirüs)   : Dairesel radar sweep, tehdit hedef tespit halkaları.

⚡ PERFORMANS:
  • Diferansiyel kuyruk ile hesaplanır; CPU kullanımı <%1 seviyesindedir.
"""
    },
    "performans": {
        "baslik": "⚡ En Yüksek Performans & Donanım Rehberi",
        "ikon": "⚡",
        "gorsel": "19_performans_rehberi.png",
        "gorsel_aciklamasi": "Donanım & Maksimum Performans Rehberi: NVIDIA CUDA VRAM yönetimi, keep_alive=0 RAM boşaltma, profil seçimi ve Ctrl+K Hızlı Komut Paleti şeması.",
        "icerik": """
========================================================================================
                   ⚡ EN YÜKSEK PERFORMANS & DONANIM OPTİMİZASYON REHBERİ
========================================================================================

Altar'dan maksimum FPS, en düşük gecikme ve sıfır donma performansı almak için altın kurallar:

📌 1. EKRAN KARTINIZI (GPU) DEVREYE ALIN:
  • NVIDIA ekran kartınız varsa Ollama'nın CUDA desteğini kullandığından emin olun.
  • Model parametresi num_ctx=2048 olarak ayarlanmıştır; bu sayede 6-8 GB VRAM kartlarda dahi
    VRAM taşması yaşanmaz ve token üretim hızı 45+ token/sn seviyesine çıkar.

📌 2. RAM VE PİL TASARRUFU (KEEP_ALIVE=0):
  • Sohbet etmediğiniz zamanlarda üst menüdeki '🟢 Yapay Zeka: Açık' butonunu '🔴 Kapalı' konuma getirin.
  • Bu işlem modelin belleğini anında boşaltır, dizüstü bilgisayarlarda pil ömrünü 3 katına çıkarır.

📌 3. KISA VE NET SORULAR & DOĞRU PROFİL:
  • Günlük iletişim için 'Profil: Sohbet' seçeneğini kullanın.
  • Kodlama için 'Profil: Yazılım' seçeneğini belirleyin; bu modda model gereksiz sohbet cümlelerini
    atlayarak doğrudan temiz kod blokları üretir ve süreyi %60 kısaltır.

📌 4. HIZLI KOMUT PALETİ (CTRL+K):
  • Klavyeden 'Ctrl+K' tuşlarına basarak tüm sekmelere, araçlara ve radar pencerelerine fareye
    dokunmadan saniyeler içinde erişebilirsiniz.
"""
    }
}


# ======================================================================================
# GÖRSELİ TAM EKRAN BÜYÜTÜCÜ MODAL PENCERESİ (LIGHTBOX)
# ======================================================================================
class AltarGorselBuyutucuModal(ctk.CTkToplevel):
    """Kılavuzdaki arayüz görsellerini tam ekranda ve ultra-HD netlikte inceleme penceresi."""
    def __init__(self, parent, gorsel_yolu: str, baslik: str = "Arayüz Görseli"):
        super().__init__(parent)
        self.title(f"🔍 {baslik} - Ultra HD Görsel İnceleme")
        self.configure(fg_color="#030712")
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)

        self.bind("<Escape>", lambda _: self.destroy())
        self.bind("<F11>", lambda _: self.destroy())

        # Üst Kapatma Çubuğu
        ust = ctk.CTkFrame(self, fg_color="#081020", height=42, corner_radius=0)
        ust.pack(side="top", fill="x")
        ust.pack_propagate(False)

        ctk.CTkLabel(
            ust, text=f"🔍 {baslik} (Piksel Kalitesinde İnceleme)",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color="#00FFCC"
        ).pack(side="left", padx=16)

        ctk.CTkButton(
            ust, text="✕ Kapat (ESC)", width=90, height=28,
            fg_color="#DC2626", hover_color="#991B1B",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.destroy
        ).pack(side="right", padx=12, pady=7)

        # Görsel Alanı
        if PIL_AVAILABLE and os.path.isfile(gorsel_yolu):
            try:
                screen_w = max(800, self.winfo_screenwidth() - 40)
                screen_h = max(600, self.winfo_screenheight() - 70)
                pil_img = Image.open(gorsel_yolu)
                img_w, img_h = pil_img.size
                ratio = min(screen_w / img_w, screen_h / img_h)
                nw, nh = int(img_w * ratio), int(img_h * ratio)
                self.ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(nw, nh))

                lbl = ctk.CTkLabel(self, image=self.ctk_img, text="")
                lbl.pack(expand=True, fill="both", padx=10, pady=10)
            except Exception as e:
                ctk.CTkLabel(self, text=f"Görsel yüklenemedi: {e}", text_color="#EF4444").pack(expand=True)
        else:
            ctk.CTkLabel(self, text="Görsel dosyası bulunamadı.", text_color="#EF4444").pack(expand=True)


# ======================================================================================
# ANA README VE KILAVUZ PENCERESİ
# ======================================================================================
class AltarReadmeMerkeziPenceresi(ctk.CTkToplevel):
    """
    Altar'ın tüm sekmelerini, güvenlik kalkanlarını, AI motorlarını ve araçlarını
    19 ayrı kategoride GÖRSELLERLE DESTEKLEYEREK internetsiz ve tam ekran tanıtan
    kapsamlı README & Rehber Penceresi.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.title("📖 Altar - Kapsamlı Çevrimdışı Sistem & Özellik Kılavuzu (README)")
        self.configure(fg_color="#050A14")
        self.geometry("1400x880")

        self._tam_ekran_mi = True
        self.bind("<F11>", self._tam_ekran_degistir)
        self.bind("<Escape>", self._tam_ekrandan_cik)

        # Doğrudan tam ekran başlat
        self.update_idletasks()
        self.after(20, self._tam_ekran_yap)

        self._aktif_kategori_anahtari = "genel"
        self._ctk_resim_onbellegi: Dict[str, Any] = {}
        self._arayuz_kur()

    def _tam_ekran_yap(self):
        try:
            if self.winfo_exists():
                self.attributes("-fullscreen", True)
                self._tam_ekran_mi = True
                self.lift()
                self.attributes("-topmost", True)
                self.attributes("-topmost", False)
                self.focus_force()
                if sys.platform == "win32":
                    try:
                        hwnd = self.winfo_id()
                        user32 = ctypes.windll.user32
                        parent = user32.GetParent(hwnd)
                        target = parent if parent else hwnd
                        user32.ShowWindow(target, 5)
                        user32.BringWindowToTop(target)
                        user32.SetForegroundWindow(target)
                    except Exception:
                        pass
        except Exception:
            pass

    def _tam_ekran_degistir(self, event=None):
        try:
            self._tam_ekran_mi = not getattr(self, "_tam_ekran_mi", False)
            self.attributes("-fullscreen", self._tam_ekran_mi)
            if hasattr(self, "btn_fullscreen"):
                self.btn_fullscreen.configure(text="🗗" if self._tam_ekran_mi else "🗖")
        except Exception:
            pass

    def _tam_ekrandan_cik(self, event=None):
        try:
            if getattr(self, "_tam_ekran_mi", False):
                self._tam_ekran_mi = False
                self.attributes("-fullscreen", False)
                if hasattr(self, "btn_fullscreen"):
                    self.btn_fullscreen.configure(text="🗖")
        except Exception:
            pass

    def _arayuz_kur(self):
        # 1. ÜST BAŞLIK VE KONTROL BARI
        ust_bar = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=8, border_width=1, border_color="#1E293B")
        ust_bar.pack(side="top", fill="x", padx=12, pady=(10, 6))

        # Sağ Yönetim Butonları
        self.btn_kapat = ctk.CTkButton(
            ust_bar, text="✕ Kapat", width=75, height=28,
            fg_color="#dc2626", hover_color="#991b1b",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.destroy
        )
        self.btn_kapat.pack(side="right", padx=(4, 8), pady=8)

        self.btn_fullscreen = ctk.CTkButton(
            ust_bar, text="🗗 Tam Ekran (F11)", width=120, height=28,
            fg_color="#1E293B", hover_color="#334155",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._tam_ekran_degistir
        )
        self.btn_fullscreen.pack(side="right", padx=(4, 2), pady=8)

        # Sol Başlık
        baslik_kutu = ctk.CTkFrame(ust_bar, fg_color="transparent")
        baslik_kutu.pack(side="left", padx=12, pady=6)

        ctk.CTkLabel(
            baslik_kutu,
            text="📖 ALTAR SİSTEM & ÖZELLİK KULLANIM KILAVUZU (GÖRSEL DESTEKLİ README)",
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
            text_color="#00FFCC"
        ).pack(anchor="w")

        ctk.CTkLabel(
            baslik_kutu,
            text="🔒 %100 Çevrimdışı (İnternetsiz) • 19 Farklı Kategori • Gerçek Arayüz Görselleri & En İyi Performans Rehberi",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#94A3B8"
        ).pack(anchor="w")

        # 2. ORTA GÖVDE (SOL KATEGORİ MENÜSÜ + SAĞ GÖRSEL DESTEKLİ OKUMA ALANI)
        govde = ctk.CTkFrame(self, fg_color="transparent")
        govde.pack(side="top", fill="both", expand=True, padx=12, pady=(0, 10))

        # SOL KATEGORİ MENÜSÜ (Scrollable)
        sol_panel = ctk.CTkScrollableFrame(
            govde, width=310, fg_color="#0B1320",
            corner_radius=8, border_width=1, border_color="#1E293B"
        )
        sol_panel.pack(side="left", fill="y", padx=(0, 8), pady=2)

        ctk.CTkLabel(
            sol_panel, text="📌 19 REHBER KATEGORİSİ",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#38BDF8"
        ).pack(anchor="w", padx=6, pady=(4, 8))

        self.kategori_butonlari = {}
        for anahtar, veri in README_KATEGORILERI.items():
            btn = ctk.CTkButton(
                sol_panel,
                text=veri["baslik"],
                anchor="w",
                height=34,
                fg_color="#1E293B" if anahtar != "genel" else "#0284C7",
                hover_color="#0369A1",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda k=anahtar: self._kategori_sec(k)
            )
            btn.pack(fill="x", padx=4, pady=2)
            self.kategori_butonlari[anahtar] = btn

        # SAĞ PANEL (Görsel Gösterimi + Metin İçeriği)
        sag_panel = ctk.CTkFrame(govde, fg_color="#081020", corner_radius=8, border_width=1, border_color="#1E293B")
        sag_panel.pack(side="right", fill="both", expand=True, padx=(0, 0), pady=2)

        # Üst Başlık Kartı
        self.lbl_kategori_baslik = ctk.CTkLabel(
            sag_panel, text="🏠 Genel Mimari, Üst Panel & Dashboard",
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
            text_color="#00FFCC", anchor="w"
        )
        self.lbl_kategori_baslik.pack(fill="x", padx=16, pady=(10, 4))

        # Sağ İçerik Kaydırma Alanı (Görsel + Açıklama)
        self.scroll_sag = ctk.CTkScrollableFrame(sag_panel, fg_color="#050A14", corner_radius=6)
        self.scroll_sag.pack(fill="both", expand=True, padx=8, pady=8)

        # GÖRSEL KART BÖLÜMÜ
        self.frame_gorsel_kutu = ctk.CTkFrame(self.scroll_sag, fg_color="#0A1428", corner_radius=6, border_width=1, border_color="#0284C7")
        self.frame_gorsel_kutu.pack(fill="x", padx=6, pady=(4, 10))

        # Görsel Üst Barı
        ust_gorsel_bar = ctk.CTkFrame(self.frame_gorsel_kutu, fg_color="#0D1E36", height=32, corner_radius=0)
        ust_gorsel_bar.pack(fill="x")
        ust_gorsel_bar.pack_propagate(False)

        ctk.CTkLabel(
            ust_gorsel_bar, text="🖼️ ARAYÜZ VE GÖRSEL TASARIM ÖNİZLEMESİ (DOĞRULANMIŞ TASARIM)",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color="#38BDF8"
        ).pack(side="left", padx=10)

        self.btn_buyut = ctk.CTkButton(
            ust_gorsel_bar, text="🔍 Görseli Tam Ekran Büyüt", width=160, height=24,
            fg_color="#0284C7", hover_color="#0369A1",
            font=ctk.CTkFont(size=10, weight="bold"),
            command=self._aktif_gorseli_buyut
        )
        self.btn_buyut.pack(side="right", padx=8, pady=4)

        # Görsel Label'ı
        self.lbl_gorsel = ctk.CTkLabel(self.frame_gorsel_kutu, text="", corner_radius=4)
        self.lbl_gorsel.pack(padx=8, pady=8)

        # Görsel Altyazı Kartı
        self.lbl_gorsel_altyazi = ctk.CTkLabel(
            self.frame_gorsel_kutu, text="",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#CBD5E1", justify="left", wraplength=940
        )
        self.lbl_gorsel_altyazi.pack(fill="x", padx=12, pady=(0, 8))

        # METİNSEL AÇIKLAMA BÖLÜMÜ (Zengin Metin Kutusu)
        self.txt_icerik = ctk.CTkTextbox(
            self.scroll_sag,
            height=380,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word",
            fg_color="#060C18",
            text_color="#E2E8F0"
        )
        self.txt_icerik.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        # İlk kategoriyi yükle
        self._kategori_sec("genel")

    def _kategori_sec(self, kategori_anahtari: str):
        self._aktif_kategori_anahtari = kategori_anahtari
        for k, btn in self.kategori_butonlari.items():
            btn.configure(fg_color="#0284C7" if k == kategori_anahtari else "#1E293B")

        veri = README_KATEGORILERI.get(kategori_anahtari, README_KATEGORILERI["genel"])
        self.lbl_kategori_baslik.configure(text=veri["baslik"])

        # Görseli Yükle ve Önizle
        gorsel_dosya = veri.get("gorsel", "")
        gorsel_tam_yol = os.path.join(GORSELLER_DIZINI, gorsel_dosya) if gorsel_dosya else ""

        if PIL_AVAILABLE and gorsel_tam_yol and os.path.isfile(gorsel_tam_yol):
            try:
                if gorsel_dosya not in self._ctk_resim_onbellegi:
                    pil_img = Image.open(gorsel_tam_yol)
                    # 16:9 oranında ölçekle (920x520)
                    nw, nh = 920, 520
                    self._ctk_resim_onbellegi[gorsel_dosya] = (
                        ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(nw, nh)),
                        gorsel_tam_yol
                    )
                ctk_img, _ = self._ctk_resim_onbellegi[gorsel_dosya]
                self.lbl_gorsel.configure(image=ctk_img, text="")
                self.frame_gorsel_kutu.pack(fill="x", padx=6, pady=(4, 10))
                self.btn_buyut.configure(state="normal")
            except Exception as e:
                self.lbl_gorsel.configure(image=None, text=f"[Görsel Yüklenemedi: {e}]", text_color="#EF4444")
        else:
            self.lbl_gorsel.configure(image=None, text="[Görsel Dosyası Bulunamadı]", text_color="#EF4444")

        # Görsel Altyazısını Güncelle
        self.lbl_gorsel_altyazi.configure(text=veri.get("gorsel_aciklamasi", ""))

        # Metin Alanını Güncelle
        self.txt_icerik.configure(state="normal")
        self.txt_icerik.delete("1.0", "end")
        self.txt_icerik.insert("end", veri["icerik"].strip() + "\n\n")
        self.txt_icerik.configure(state="disabled")

        # Scroll pozisyonunu en üste al
        self.scroll_sag._parent_canvas.yview_moveto(0.0)

    def _aktif_gorseli_buyut(self):
        """Aktif kategorinin görselini tam ekran modalda açar."""
        veri = README_KATEGORILERI.get(self._aktif_kategori_anahtari, README_KATEGORILERI["genel"])
        gorsel_dosya = veri.get("gorsel", "")
        gorsel_tam_yol = os.path.join(GORSELLER_DIZINI, gorsel_dosya)
        if os.path.isfile(gorsel_tam_yol):
            AltarGorselBuyutucuModal(self, gorsel_tam_yol, baslik=veri["baslik"])


def readme_merkezi_ac(parent=None):
    """README merkezini tam ekran olarak açar ve ön plana getirir."""
    try:
        win = AltarReadmeMerkeziPenceresi(parent)
        return win
    except Exception as e:
        print(f"[!] README açılırken hata: {e}")
        return None
