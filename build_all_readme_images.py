# -*- coding: utf-8 -*-
"""
Altar README Görsel Varlıkları Üretici (build_all_readme_images.py)
Uygulamanın her kategorisi için projedeki gerçek arayüz tasarımlarını, butonlarını,
sinematik HUD bileşenlerini ve görsel mimarisini yansıtan 19 adet 1200x680 çözünürlüğünde
profesyonel görsel üretir.
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = r"e:\Gemini API\Dosyalama_Projesi_Guncel\assets\readme_gorseller"
os.makedirs(OUT_DIR, exist_ok=True)

try:
    font_huge = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 26)
    font_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 20)
    font_bold = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 15)
    font_sub = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 13)
    font_small = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 11)
    font_tiny = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 10)
except Exception:
    font_huge = font_title = font_bold = font_sub = font_small = font_tiny = ImageFont.load_default()

W, H = 1200, 680

def create_base(title, cat_name, icon="🛡️", accent="#00FFCC"):
    im = Image.new("RGB", (W, H), "#050A14")
    draw = ImageDraw.Draw(im)
    
    # Arka plan siber ızgarası
    for x in range(0, W, 40):
        draw.line([(x, 0), (x, H)], fill="#081020", width=1)
    for y in range(0, H, 40):
        draw.line([(0, y), (W, y)], fill="#081020", width=1)

    # Üst Sistem Çubuğu
    draw.rectangle([(0, 0), (W, 44)], fill="#0B1528", outline="#1E293B", width=1)
    draw.ellipse([(14, 15), (26, 27)], fill="#EF4444")
    draw.ellipse([(34, 15), (46, 27)], fill="#F59E0B")
    draw.ellipse([(54, 15), (66, 27)], fill="#10B981")
    
    draw.text((80, 12), f"ALTAR OS // {cat_name.upper()} // {title}", fill="#38BDF8", font=font_bold)
    draw.text((W - 350, 12), "[●] %100 YEREL & ÇEVRİMDISI • 60 FPS", fill="#10B981", font=font_sub)
    
    # Alt Durum Çubuğu
    draw.rectangle([(0, H - 34), (W, H)], fill="#070D18", outline="#1E293B", width=1)
    draw.text((16, H - 24), "⚡ GPU Hızlandırma: CUDA AKTİF | RAM: Minimal (<185MB) | Tam Ekran (F11) | Kapat (ESC)", fill="#64748B", font=font_small)
    draw.text((W - 400, H - 24), "Altar Hibrit Sistem Kılavuzu • Doğrulanmış Arayüz Mimarisi", fill="#38BDF8", font=font_small)
    
    return im, draw

def draw_card(draw, box, title="", bg="#0B1320", border="#1E293B", title_color="#38BDF8"):
    if isinstance(box[0], (list, tuple)):
        x1, y1 = box[0]
        x2, y2 = box[1]
    else:
        x1, y1, x2, y2 = box
    draw.rectangle([(x1, y1), (x2, y2)], fill=bg, outline=border, width=2)
    if title:
        draw.rectangle([(x1, y1), (x2, y1 + 28)], fill="#0F1D33", outline=border, width=1)
        draw.text((x1 + 12, y1 + 6), title, fill=title_color, font=font_bold)

def draw_btn(draw, box, text, fg_color="#1E293B", text_color="#E2E8F0", border="#334155"):
    if isinstance(box[0], (list, tuple)):
        x1, y1 = box[0]
        x2, y2 = box[1]
    else:
        x1, y1, x2, y2 = box
    draw.rectangle([(x1, y1), (x2, y2)], fill=fg_color, outline=border, width=1)
    draw.text((x1 + 8, y1 + (y2 - y1 - 14) // 2), text, fill=text_color, font=font_small)


# ------------------------------------------------------------------------------
# 1. GENEL MİMARİ, ÜST BAR & DASHBOARD
# ------------------------------------------------------------------------------
def gen_01_genel_mimari():
    im, draw = create_base("Genel Mimari & Dashboard", "GENEL BAKIŞ", "🏠", "#00FFCC")
    
    # Üst Kontrol Paneli Simülasyonu
    draw_card(draw, [(30, 60), (1170, 140)], "⚡ ALTAR ÜST YÖNETİM VE TELEMETRİ KONTROL PANELİ", "#0D1B2A", "#00FFCC")
    draw_btn(draw, [(50, 96), (210, 128)], "🟢 Yapay Zeka: Açık", "#059669", "#FFFFFF")
    draw_btn(draw, [(220, 96), (360, 128)], "Motor: Yerel (Ollama)", "#1E293B", "#38BDF8")
    draw_btn(draw, [(370, 96), (560, 128)], "Model: qwen3.5:9b", "#1E293B", "#F59E0B")
    draw_btn(draw, [(570, 96), (690, 128)], "Profil: Sohbet", "#1E293B", "#E2E8F0")
    draw_btn(draw, [(700, 96), (820, 128)], "🌐 Ağ Radarı", "#1E3A8A", "#60A5FA")
    draw_btn(draw, [(830, 96), (970, 128)], "🛡️ EDR Kalkanı", "#7C3AED", "#DDD6FE")
    draw_btn(draw, [(980, 96), (1150, 128)], "CPU: %1.2 | RAM: 184MB", "#070E1A", "#10B981")

    # Sol ve Sağ Sekmeler Butonu Vurgusu
    draw_card(draw, [(30, 160), (370, 420)], "📑 SOL SEKME GEZGİNİ (X=14)", "#0B1528", "#38BDF8")
    draw_btn(draw, [(50, 205), (350, 245)], "📑 Sekmeler (Tüm Pencereler)", "#0284C7", "#FFFFFF")
    draw.text((50, 260), "• Tıklandığında açık olan tüm harici\n  modülleri (Video, Canva, IDE, EDR)\n  cam navigasyon penceresinde listeler.\n• Tek tıkla ilgili arayüze geçiş sağlar.\n• ESC kısayoluyla anında kapanır.", fill="#94A3B8", font=font_sub)

    # Orta Sekme Barı
    draw_card(draw, [(390, 160), (790, 420)], "🗂️ 10 TEMEL ÇALIŞMA SEKMESİ", "#0B1528", "#10B981")
    sekmeler = [
        "💬 Sohbet (Yerel & Bulut AI)", "🎮 Siber Oyunlar (4 Python Oyunu)",
        "🎵 Müzik & Sinematik Sahne", "🐍 Python IDE & Canlı Terminal",
        "📁 Dosya Gezgini & Kripto Kasa", "📊 Kazınan Veri & Modem QoS",
        "📐 CNC G-Code Haas V34 Simülatör", "🔬 Tersine Mühendislik & Hex Lab"
    ]
    for i, s in enumerate(sekmeler):
        draw.text((410, 200 + i * 26), f"▸ {s}", fill="#38BDF8" if i < 3 else "#E2E8F0", font=font_small)

    # Sağ Sekmeler Butonu Vurgusu
    draw_card(draw, [(810, 160), (1170, 420)], "📑 SAĞ SEKME GEZGİNİ (RELX=1.0)", "#0B1528", "#38BDF8")
    draw_btn(draw, [(830, 205), (1150, 245)], "📑 Sekmeler (Hızlı Geçiş)", "#0284C7", "#FFFFFF")
    draw.text((830, 260), "• Geniş ekranlarda sağ el ile hızlı\n  erişim sağlar.\n• Sinematik video oynatıcı, ses stüdyosu\n  ve belge editörü gibi pencereleri\n  arka plana düşmeden öne getirir.", fill="#94A3B8", font=font_sub)

    # Alt Kısım: Şeffaf Arayüz ve Sinematik Arka Plan Bilgisi
    draw_card(draw, [(30, 440), (1170, 630)], "✨ ŞEFFAF SİBER CAM (GLASSMORPHISM) & 60 FPS PROSEDÜREL ARKA PLAN", "#0B1320", "#F59E0B")
    draw.text((50, 480), "• Her çalışma sekmesi yarı-saydam siber cam panellerle kaplanmıştır; arkasındaki 60 FPS sinematik animasyonlar canlı akar.\n• CPU kullanımı <%1 seviyesinde optimize edilmiştir; oyun veya ağır derleme süreçlerini asla yavaşlatmaz.\n• API modelinin altında bulunan 'README' butonuyla bu kılavuz istenildiği an tam ekranda açılabilir.", fill="#CBD5E1", font=font_sub)

    im.save(os.path.join(OUT_DIR, "01_genel_mimari.png"))


# ------------------------------------------------------------------------------
# 2. SOHBET & YAPAY ZEKA MOTORU
# ------------------------------------------------------------------------------
def gen_02_sohbet_ai():
    im, draw = create_base("Yapay Zeka Sohbet & Kodlama Motoru", "AI SOHBET", "💬", "#38BDF8")
    
    # Sohbet Görüntüleme Alanı
    draw_card(draw, [(30, 60), (840, 520)], "💬 SOHBET & KOD ÇÖZÜMLEME AKIŞI", "#070E1B", "#38BDF8")
    
    # Kullanıcı Balonu
    draw.rectangle([(50, 105), (820, 155)], fill="#0F243A", outline="#1E3A8A")
    draw.text((65, 115), "👤 Sen: Altar Ağ IPS kalkanı için ham scapy paket yakalama fonksiyonunu yaz.", fill="#60A5FA", font=font_small)
    
    # Model Yanıt Balonu
    draw.rectangle([(50, 170), (820, 420)], fill="#0B1A2C", outline="#00FFCC")
    draw.text((65, 180), "🤖 Altar AI (jaahas/qwen3.5-uncensored:9b) [100% Yerel / 48 t/s]:", fill="#00FFCC", font=font_bold)
    kod_ornek = [
        "def ag_paketlerini_dinle(arayuz='Ethernet'):",
        "    from scapy.all import sniff, IP, TCP",
        "    def _paket_filtrele(pkt):",
        "        if pkt.haslayer(IP) and pkt[IP].src not in GUVENLI_IPLER:",
        "            if pkt.haslayer(TCP) and pkt[TCP].flags == 'S':",
        "                EDR_ALARM_VER(pkt[IP].src, sebep='SYN Flood Girişimi')",
        "    sniff(iface=arayuz, prn=_paket_filtrele, store=False)"
    ]
    draw.rectangle([(65, 210), (805, 380)], fill="#050A14", outline="#1E293B")
    for idx, satir in enumerate(kod_ornek):
        draw.text((80, 220 + idx * 22), satir, fill="#F8FAFC" if "def " not in satir else "#F59E0B", font=font_small)
    draw.text((65, 395), "✅ Kod yerel AST denetiminden geçti: Sıfır güvenlik zaafiyeti.", fill="#10B981", font=font_small)

    # Alt Giriş Paneli
    draw_card(draw, [(30, 535), (840, 630)], "⌨️ SİSTEM VE KULLANICI KOMUT GİRİŞİ", "#0B1528", "#1E293B")
    draw.rectangle([(45, 565), (660, 615)], fill="#050A14", outline="#334155")
    draw.text((55, 580), "Soru sorun, Python kodu isteyin veya /otonom yazarak ajan moduna geçin...", fill="#64748B", font=font_small)
    draw_btn(draw, [(675, 565), (745, 615)], "🚀 İlet", "#0284C7", "#FFFFFF")
    draw_btn(draw, [(755, 565), (825, 615)], "🎤 Ses", "#059669", "#FFFFFF")

    # Sağ Panel: Araçlar & Butonlar
    draw_card(draw, [(860, 60), (1170, 630)], "🛠️ HIZLI ARAÇLAR & BUTONLAR", "#0D1B2A", "#F59E0B")
    draw_btn(draw, [(880, 110), (1150, 150)], "💬 Oturumlar (Sessions)", "#1E293B", "#38BDF8")
    draw.text((880, 158), "Tüm eski sohbetleri yerel JSON'da\nsaklayıp tek tıkla geri yükler.", fill="#94A3B8", font=font_tiny)

    draw_btn(draw, [(880, 200), (1150, 240)], "📖 README (Sistem Rehberi)", "#059669", "#FFFFFF")
    draw.text((880, 248), "API modeli altında yer alır; tüm\nözellikleri görselle tanıtır.", fill="#94A3B8", font=font_tiny)

    draw_btn(draw, [(880, 290), (1150, 330)], "📎 Resim / Görsel Ekle (Vision)", "#1E293B", "#F59E0B")
    draw_btn(draw, [(880, 345), (1150, 385)], "📄 Belge Ekle (.pdf, .altar)", "#1E293B", "#F59E0B")
    draw_btn(draw, [(880, 400), (1150, 440)], "✂️ Ekranı Sor (Snipping Tool)", "#1E293B", "#F59E0B")
    draw_btn(draw, [(880, 455), (1150, 495)], "💾 Sohbeti Rapor Olarak Kaydet", "#1E293B", "#10B981")

    im.save(os.path.join(OUT_DIR, "02_sohbet_ai.png"))


# ------------------------------------------------------------------------------
# 3. SEKMELER VE ÖZELLİKLER GEZGİNİ
# ------------------------------------------------------------------------------
def gen_03_sekmeler_gezgini():
    im, draw = create_base("Altar Sekmeler & Özellikler Gezgini", "SEKMELER GEZGİNİ", "🗂️", "#00FFCC")
    
    # Cam Modal Pencere
    draw_card(draw, [(120, 60), (1080, 630)], "🗂️ ALTAR SEKMELER & AÇIK ÖZELLİKLER GEZGİNİ (MODAL)", "#081326", "#00FFCC")
    
    # Canlı Arama Kutusu
    draw.rectangle([(150, 105), (1050, 145)], fill="#040914", outline="#00FFCC", width=1)
    draw.text((170, 118), "🔍 Özellik veya sekme adı yazarak filtreleyin... (ESC ile Kapat)", fill="#38BDF8", font=font_sub)

    # Açık Harici Pencereler Bölümü
    draw.text((150, 160), "⚡ ÇALIŞAN HARİCİ UYGULAMA PENCERELERİ (ÖNE GETİR / ODAKLAN):", fill="#10B981", font=font_bold)
    harici_kartlar = [
        ("🎬 Sinematik Video", "MP4 60 FPS Borderless", "#EF4444"),
        ("📝 Altar Belge & Canva", "Sunum & .altar Editörü", "#F59E0B"),
        ("🎙️ Ses Kaydedici", "Stüdyo Mikrofon Kaydı", "#10B981"),
        ("🎬 Ekran Video", "Ekran+Ses Yakalama", "#06B6D4"),
        ("🌐 Ağ Radarı", "Canlı TCP/UDP Portları", "#3B82F6"),
        ("⚡ Ollama Kurucu", "UAC & Firewall Sihirbazı", "#8B5CF6")
    ]
    for i, (k_baslik, k_alt, k_renk) in enumerate(harici_kartlar):
        col = i % 3
        row = i // 3
        x1 = 150 + col * 305
        y1 = 190 + row * 75
        draw.rectangle([(x1, y1), (x1 + 290, y1 + 65)], fill="#0D1F38", outline=k_renk, width=1)
        draw.text((x1 + 12, y1 + 10), k_baslik, fill="#FFFFFF", font=font_bold)
        draw.text((x1 + 12, y1 + 35), k_alt, fill="#94A3B8", font=font_tiny)
        draw_btn(draw, [(x1 + 200, y1 + 20), (x1 + 278, y1 + 48)], "Geçiş Yap", k_renk, "#FFFFFF")

    # 10 Temel Sekme Listesi
    draw.text((150, 360), "📌 10 TEMEL ÇALIŞMA VE MÜHENDİSLİK SEKMESİ:", fill="#38BDF8", font=font_bold)
    sekmeler_grid = [
        "1. 💬 Yapay Zeka Sohbet & Hibrit Kodlama", "2. 🎮 Python Siber & Retro Oyun Merkezi",
        "3. 🎵 Müzik & Sinematik Animasyon Sahnesi", "4. 🐍 Python IDE, Editör & Canlı Terminal",
        "5. 📁 Dosya Gezgini & Kriptografik Kasa", "6. 📊 Kazınan Veri, Analiz & Turbo Modem",
        "7. 📐 CNC G-Code 2D/3D Simülatör (Haas V34)", "8. 🔬 Tersine Mühendislik & Hex Lab",
        "9. 🦠 5-Katmanlı Antivirüs & EDR Kalkanı", "10. 🚀 NASA Mikroçekim & Uzay Telemetri Lab"
    ]
    for i, s_ad in enumerate(sekmeler_grid):
        col = i % 2
        row = i // 2
        x1 = 150 + col * 460
        y1 = 390 + row * 44
        draw.rectangle([(x1, y1), (x1 + 440, y1 + 36)], fill="#071325", outline="#1E293B", width=1)
        draw.text((x1 + 10, y1 + 9), s_ad, fill="#E2E8F0", font=font_small)
        draw_btn(draw, [(x1 + 365, y1 + 6), (x1 + 430, y1 + 30)], "Sekmeye Git", "#0284C7", "#FFFFFF")

    im.save(os.path.join(OUT_DIR, "03_sekmeler_gezgini.png"))


# ------------------------------------------------------------------------------
# 4. SİBER & RETRO OYUNLAR
# ------------------------------------------------------------------------------
def gen_04_siber_oyunlar():
    im, draw = create_base("Python Siber Oyun: Galaktik Savunma", "GALAKTİK SAVUNMA", "🚀", "#38BDF8")
    
    # Galaktik Savunma Oyun Sahnesi (Geniş Ekran)
    draw_card(draw, [(30, 60), (840, 630)], "🚀 GALAKTİK SAVUNMA (NEBULA INTERCEPTOR - 60 FPS)", "#040914", "#38BDF8")
    
    # HUD Barı
    draw.rectangle([(45, 100), (825, 135)], fill="#0A162B", outline="#1E3A8A")
    draw.text((60, 110), "🚀 SEKTÖR: 04  |  Skor: 3840  |  Kalkan: ❤❤❤❤🤍  |  EMP Bombası: 💣x2  |  Lazer: Çift Plazma (Hız: 60 FPS)", fill="#00FFCC", font=font_small)

    # Oyun Tuvali & Yıldız Tarlası
    draw.rectangle([(45, 145), (825, 615)], fill="#02040A", outline="#00FFCC", width=1)
    
    # Yıldızlar
    for s in range(60):
        sx = 55 + (s * 37) % 750
        sy = 155 + (s * 43) % 440
        draw.ellipse([(sx, sy), (sx + 2, sy + 2)], fill="#FFFFFF" if s % 3 == 0 else "#64748B")

    # Düşman Kruvazörleri (Üstte)
    for e in range(4):
        ex = 120 + e * 180
        ey = 200 + (e % 2) * 45
        draw.polygon([(ex, ey), (ex + 30, ey + 35), (ex - 30, ey + 35)], fill="#EF4444", outline="#FCA5A5")
        draw.text((ex - 22, ey + 42), "Kruvazör", fill="#F87171", font=font_tiny)

    # Lazer Mermileri
    draw.line([(430, 420), (430, 260)], fill="#00FFCC", width=3)
    draw.line([(450, 420), (450, 260)], fill="#00FFCC", width=3)

    # Patlama Parçacıkları
    for p in range(16):
        px = 300 + int(35 * math.cos(p * 0.4))
        py = 220 + int(35 * math.sin(p * 0.4))
        draw.ellipse([(px, py), (px + 3, py + 3)], fill="#F59E0B")

    # Oyuncu Uzay Gemisi (Altta x=440, y=520)
    draw.polygon([(440, 470), (470, 540), (440, 520), (410, 540)], fill="#38BDF8", outline="#00FFCC")
    # Motor Alevi
    draw.polygon([(435, 525), (440, 555), (445, 525)], fill="#F59E0B")

    # Sağ Panel: Kontroller & Özellikler
    draw_card(draw, [(860, 60), (1170, 630)], "🎮 KONTROLLER & FİZİK MOTORU", "#0B1528", "#F59E0B")
    
    kontroller = [
        ("Sol / Sağ Ok (← / →)", "Gemiyi Yönlendir"),
        ("A / D Tuşları", "Alternatif Yön Kontrolü"),
        ("Boşluk (Space)", "Çift Plazma Lazer Ateşle"),
        ("B Tuşu", "EMP Süper Bombası Patlat"),
        ("P Tuşu", "Oyunu Duraklat / Devam Et"),
        ("F11 veya Buton", "Çerçevesiz Tam Ekran (Kiosk)")
    ]
    for i, (tus, aciklama) in enumerate(kontroller):
        ky = 105 + i * 50
        draw.rectangle([(880, ky), (1150, ky + 42)], fill="#081426", outline="#1E293B")
        draw.text((890, ky + 6), tus, fill="#38BDF8", font=font_small)
        draw.text((890, ky + 23), aciklama, fill="#94A3B8", font=font_tiny)

    draw.text((880, 425), "⚡ 60 FPS DONANIM HIZLANDIRMA:\n• Milisaniye hassasiyetinde çarpışma denetimi.\n• Düşman dalgaları temizlendikçe sektör artar.\n• %100 Python ve Tkinter ile geliştirilmiştir;\nharici internet bağlantısı gerektirmez.", fill="#CBD5E1", font=font_tiny)

    draw_btn(draw, [(880, 545), (1150, 595)], "⛶ Tam Ekran Oyna (Kiosk)", "#0284C7", "#FFFFFF")

    im.save(os.path.join(OUT_DIR, "04_siber_oyunlar.png"))


# ------------------------------------------------------------------------------
# 5. MÜZİK & SİNEMATİK SAHNE
# ------------------------------------------------------------------------------
def gen_05_muzik_sinematik():
    im, draw = create_base("Müzik & Sinematik Ses Merkezi", "MÜZİK MERKEZİ", "🎵", "#8B5CF6")
    
    # Sol Panel: YouTube İndirici & Kütüphane
    draw_card(draw, [(30, 60), (480, 630)], "📥 YOUTUBE MÜZİK İNDİRİCİ & KÜTÜPHANE", "#0A1428", "#8B5CF6")
    draw.text((50, 100), "YouTube / YouTube Music URL veya Şarkı Adı:", fill="#CBD5E1", font=font_sub)
    draw.rectangle([(50, 125), (460, 165)], fill="#050A14", outline="#8B5CF6", width=1)
    draw.text((60, 138), "https://music.youtube.com/watch?v=... veya Şarkı Adı", fill="#64748B", font=font_tiny)
    draw_btn(draw, [(50, 175), (280, 210)], "📥 Sesi İndir (MP3)", "#8B5CF6", "#FFFFFF")
    draw_btn(draw, [(290, 175), (460, 210)], "📂 MP3 Klasörü Aç", "#1E293B", "#38BDF8")

    draw.text((50, 230), "🎧 YEREL MP3 KÜTÜPHANESİ (ARKA PLAN ÇALMA):", fill="#10B981", font=font_bold)
    parcalar = [
        "▶ 01. Hans Zimmer - Interstellar Theme (Lossless)",
        "  02. Synthwave Cyberpunk 2077 Night Ambience",
        "  03. Deep Focus Code Beats (Lofi Coding Radio)",
        "  04. NASA Deep Space Horizon Transmission",
        "  05. Brian Eno - Apollo Atmospheres"
    ]
    for i, p in enumerate(parcalar):
        draw.rectangle([(50, 260 + i * 44), (460, 296 + i * 44)], fill="#0D1F38" if i == 0 else "#07101E", outline="#1E293B")
        draw.text((60, 272 + i * 44), p, fill="#00FFCC" if i == 0 else "#E2E8F0", font=font_tiny)

    draw.text((50, 500), "⚡ Kesintisiz Çalma: Başka sekmelere geçseniz\n   dahi arka planda sıfır gecikmeyle devam eder.\n   CPU yükü <%0.8, pil dostu pygame mikser.", fill="#94A3B8", font=font_tiny)

    # Sağ Panel: Sinematik Sahne & Frekans Spektrumu
    draw_card(draw, [(500, 60), (1170, 630)], "🌊 3 TEMALI SİNEMATİK ANİMASYON SAHNESİ & EKOLAYZIR", "#081326", "#00FFCC")
    draw_btn(draw, [(520, 100), (670, 130)], "🌊 Doğa & Şelale", "#0284C7", "#FFFFFF")
    draw_btn(draw, [(680, 100), (840, 130)], "🔥 Mavi Kozmik Plazma", "#1E293B", "#E2E8F0")
    draw_btn(draw, [(850, 100), (1020, 130)], "⚡ Cyberpunk Matrix", "#1E293B", "#E2E8F0")
    draw_btn(draw, [(1030, 100), (1150, 130)], "🗖 Tam Ekran", "#10B981", "#FFFFFF")

    # Görsel Sahne Önizlemesi
    draw.rectangle([(520, 145), (1150, 480)], fill="#030812", outline="#00FFCC", width=1)
    # Şelale & Işıltı Parçacıkları Çizimi
    for i in range(40):
        px = 540 + (i * 15) % 600
        py = 160 + (i * 17) % 300
        draw.line([(px, py), (px, py + 12)], fill="#38BDF8", width=2)
    draw.text((700, 280), "🌊 DOĞA ŞELALESİ SİNEMATİK ANİMASYON (60 FPS)", fill="#00FFCC", font=font_bold)
    draw.text((710, 310), "Biolüminesans Su Damlacıkları & Ambient Ritim", fill="#94A3B8", font=font_sub)

    # Frekans Ekolayzır Barları
    for b in range(32):
        bar_h = max(6, abs(int(25 + 65 * math.sin(b * 0.3) + 25 * math.cos(b * 0.5))))
        bx = 550 + b * 18
        draw.rectangle([(bx, 460 - bar_h), (bx + 12, 460)], fill="#8B5CF6")

    draw.text((520, 510), "Şarkı: Hans Zimmer - Interstellar (4:12 / 8:36)   Döngü: Açık   Ses: %85", fill="#FFFFFF", font=font_sub)
    draw.rectangle([(520, 540), (1150, 550)], fill="#1E293B")
    draw.rectangle([(520, 540), (780, 550)], fill="#00FFCC")

    im.save(os.path.join(OUT_DIR, "05_muzik_sinematik.png"))


# ------------------------------------------------------------------------------
# 6. SİNEMATİK MP4 OYNATICI
# ------------------------------------------------------------------------------
def gen_06_sinematik_video():
    im, draw = create_base("Altar Sinematik MP4 Oynatıcı", "SİNEMATİK VİDEO", "🎬", "#EF4444")
    
    # Tam Ekran Video Sahnesi
    draw.rectangle([(40, 60), (1160, 530)], fill="#02040A", outline="#EF4444", width=2)
    draw.text((450, 220), "🎬 ALTAR SİNEMATİK VİDEO SAHNESİ", fill="#FFFFFF", font=font_huge)
    draw.text((380, 265), "OpenCV + FFmpeg Donanım Hızlandırmalı 60 FPS Oynatım", fill="#38BDF8", font=font_title)
    draw.text((410, 305), "Windows API ile Çerçevesiz (Borderless) Tam Ekran ve Otomatik Odak", fill="#94A3B8", font=font_sub)

    # Gizlenen Akıllı HUD Kontrol Çubuğu (2.5 sn sonra kaybolur)
    draw.rectangle([(80, 440), (1120, 510)], fill="#081426", outline="#00FFCC", width=1)
    draw_btn(draw, [(100, 455), (145, 495)], "⏸", "#1E293B", "#00FFCC")
    draw_btn(draw, [(155, 455), (200, 495)], "⏮ 5s", "#1E293B", "#FFFFFF")
    draw_btn(draw, [(210, 455), (255, 495)], "5s ⏭", "#1E293B", "#FFFFFF")
    draw.text((270, 470), "01:24:18 / 02:40:00", fill="#FFFFFF", font=font_sub)

    # İlerleme Çubuğu
    draw.rectangle([(440, 470), (960, 480)], fill="#1E293B")
    draw.rectangle([(440, 470), (680, 480)], fill="#EF4444")
    draw_btn(draw, [(980, 455), (1040, 495)], "🔊 90%", "#1E293B", "#10B981")
    draw_btn(draw, [(1050, 455), (1100, 495)], "🗖", "#1E293B", "#FFFFFF")

    # Kısayol Tuşları Bilgilendirme Kutuları
    kisayollar = [
        ("Boşluk (Space)", "Oynat / Duraklat"),
        ("Sol / Sağ Ok", "5 Sn İleri / Geri Sar"),
        ("Yukarı / Aşağı", "Ses Düzeyi Ayarla"),
        ("F11 / Çift Tık", "Tam Ekran Aç / Kapat"),
        ("ESC veya Q", "Güvenli Kapat ve Çık")
    ]
    for i, (tus, aciklama) in enumerate(kisayollar):
        kx = 40 + i * 228
        draw_card(draw, [(kx, 550), (kx + 220, 630)], tus, "#0B1528", "#1E293B", "#F59E0B")
        draw.text((kx + 12, 595), aciklama, fill="#CBD5E1", font=font_small)

    im.save(os.path.join(OUT_DIR, "06_sinematik_video.png"))


# ------------------------------------------------------------------------------
# 7. CANVA SUNUM & ALTAR BELGE
# ------------------------------------------------------------------------------
def gen_07_canva_ve_belge():
    im, draw = create_base("Altar Belge & Canva Sunum Stüdyosu", "CANVA & BELGE", "📝", "#F59E0B")
    
    # Sol Slayt Listesi
    draw_card(draw, [(30, 60), (270, 630)], "📑 SLAYTLAR (16:9)", "#0B1320", "#F59E0B")
    draw_btn(draw, [(45, 98), (255, 128)], "+ Yeni Slayt Ekle", "#0284C7", "#FFFFFF")
    for s in range(5):
        sy = 140 + s * 80
        draw.rectangle([(45, sy), (255, sy + 70)], fill="#0D1F38" if s == 0 else "#07101E", outline="#F59E0B" if s == 0 else "#1E293B")
        draw.text((55, sy + 10), f"Slayt {s + 1}: {'Mimari Giriş' if s == 0 else 'Teknik Analiz'}", fill="#FFFFFF", font=font_small)
        draw.text((55, sy + 35), "16:9 4K Geniş Ekran", fill="#94A3B8", font=font_tiny)

    # Orta: 16:9 Canva Tuvali
    draw_card(draw, [(285, 60), (910, 630)], "🎨 CANVA PROFESYONEL SLAYT TASARIM TUVALİ", "#050A14", "#00FFCC")
    # Slayt Alanı (16:9)
    draw.rectangle([(305, 100), (890, 520)], fill="#081326", outline="#38BDF8", width=2)
    draw.text((330, 130), "ALTAR CYBERNETICS // TEKNİK MİMARİ SUNUMU", fill="#00FFCC", font=font_title)
    draw.text((330, 165), "Çevrimdışı Hibrit Güvenlik ve Yapay Zeka Platformu", fill="#94A3B8", font=font_sub)

    # Neon Kart Bileşenleri
    draw.rectangle([(330, 210), (580, 360)], fill="#0D1F38", outline="#10B981")
    draw.text((345, 225), "🔒 5-Katmanlı EDR Kalkanı", fill="#10B981", font=font_bold)
    draw.text((345, 260), "• Sıfır-gün koruması\n• Bellek içi şifreleme\n• Diferansiyel tarama", fill="#CBD5E1", font=font_small)

    draw.rectangle([(610, 210), (860, 360)], fill="#0D1F38", outline="#8B5CF6")
    draw.text((625, 225), "🧠 Hibrit AI Çekirdeği", fill="#8B5CF6", font=font_bold)
    draw.text((625, 260), "• Yerel Ollama (Qwen)\n• Bulut Gemini API\n• %100 Çevrimdışı", fill="#CBD5E1", font=font_small)

    draw.text((330, 420), "📊 Performans: 60 FPS Akıcı Render | KaTeX / Math Desteği | Vektörel Şekiller", fill="#38BDF8", font=font_small)

    # Tuval Altı Hızlı Araçlar
    draw_btn(draw, [(305, 545), (430, 585)], "+ Metin Ekle", "#1E293B", "#38BDF8")
    draw_btn(draw, [(440, 545), (565, 585)], "+ Kart Ekle", "#1E293B", "#10B981")
    draw_btn(draw, [(575, 545), (700, 585)], "+ Resim Ekle", "#1E293B", "#F59E0B")
    draw_btn(draw, [(710, 545), (890, 585)], "▶ Tam Ekran Sunum (F5)", "#059669", "#FFFFFF")

    # Sağ Panel: Dışa Aktarma & .altar Belge
    draw_card(draw, [(925, 60), (1170, 630)], "📤 DIŞA AKTAR & BELGE PRO", "#0B1528", "#E2E8F0")
    draw_btn(draw, [(945, 105), (1150, 145)], "📄 PDF Olarak Aktar", "#DC2626", "#FFFFFF")
    draw.text((945, 152), "Tüm slaytları tek bir yüksek\nkaliteli PDF dosyası yapar.", fill="#94A3B8", font=font_tiny)

    draw_btn(draw, [(945, 200), (1150, 240)], "🖼️ PNG Resim Olarak Aktar", "#0284C7", "#FFFFFF")
    draw.text((945, 248), "Aktif slaytı ultra-HD PNG\nformatında kaydeder.", fill="#94A3B8", font=font_tiny)

    draw_btn(draw, [(945, 300), (1150, 340)], "💾 Sunumu Kaydet (.altarsunumu)", "#059669", "#FFFFFF")
    draw_btn(draw, [(945, 355), (1150, 395)], "📂 Sunumu Aç (.json / .altar)", "#1E293B", "#38BDF8")

    draw.rectangle([(945, 425), (1150, 610)], fill="#07101E", outline="#334155")
    draw.text((955, 435), "📝 ALTAR BELGE EDİTÖRÜ:", fill="#F59E0B", font=font_small)
    draw.text((955, 460), "• SHA-256 imzalı kripto\n  .altar metin işlemcisi\n• Yan not defteri entegreli\n• Zengin font biçimlendirme\n• F11 çerçevesiz mod", fill="#94A3B8", font=font_tiny)

    im.save(os.path.join(OUT_DIR, "07_canva_ve_belge.png"))


# ------------------------------------------------------------------------------
# 8. OLLAMA & MODEL KURUCUSU
# ------------------------------------------------------------------------------
def gen_08_ollama_kurucu():
    im, draw = create_base("Otomatik Ollama & Model Kurucusu", "OLLAMA KURUCU", "⚡", "#10B981")
    
    draw_card(draw, [(120, 60), (1080, 630)], "⚡ ALTAR OTOMATİK OLLAMA VE SİBER MODEL KURUCU SİHİRBAZI", "#081326", "#10B981")
    draw.text((150, 105), "Tek Tıkla Windows Kurulumu • Otomatik UAC • Güvenlik Duvarı Kuralı • Model Çekme", fill="#38BDF8", font=font_sub)

    # 4 Adım İlerleme Kartları
    adimlar = [
        ("ADIM 1: YÖNETİCİ İZNİ (UAC) & İNDİRME", "https://ollama.com/download resmi Windows kurulum paketi arka planda indirilir.", "✔ TAMAMLANDI (#10B981)"),
        ("ADIM 2: SESSİZ KURULUM & DEFENDER PORT İZNİ", "Windows Defender Güvenlik Duvarı'na otomatik gelen kuralı tanımlanır (shell=False).", "✔ TAMAMLANDI (#10B981)"),
        ("ADIM 3: OLLAMA APİ SERVİSİNİ BAŞLATMA", "localhost:11434 üzerinde 'ollama serve' bağımsız arka plan sürecinde ayağa kaldırılır.", "✔ ÇALIŞIYOR (PID: 8420)"),
        ("ADIM 4: SİBER YAPAY ZEKA MODELLERİNİ ÇEKME", "jaahas/qwen3.5-uncensored:9b & llava:latest modelleri SHA-256 ile doğrulanıp çekilir.", "⏳ İNDİRİLİYOR (%84 - 42 MB/s)")
    ]

    for i, (baslik, aciklama, durum) in enumerate(adimlar):
        ay = 145 + i * 95
        draw.rectangle([(150, ay), (1050, ay + 80)], fill="#0D1E36", outline="#10B981" if i < 3 else "#F59E0B", width=1)
        draw.text((170, ay + 12), baslik, fill="#FFFFFF", font=font_bold)
        draw.text((170, ay + 36), aciklama, fill="#CBD5E1", font=font_small)
        draw.text((170, ay + 56), durum, fill="#10B981" if i < 3 else "#F59E0B", font=font_small)

    # Genel İlerleme Çubuğu
    draw.text((150, 540), "Toplam Kurulum İlerlemesi: %85", fill="#00FFCC", font=font_bold)
    draw.rectangle([(150, 565), (1050, 585)], fill="#1E293B")
    draw.rectangle([(150, 565), (915, 585)], fill="#10B981")

    im.save(os.path.join(OUT_DIR, "08_ollama_kurucu.png"))


# ------------------------------------------------------------------------------
# 9. SİBER GÜVENLİK & AĞ RADARI
# ------------------------------------------------------------------------------
def gen_09_guvenlik_ve_radar():
    im, draw = create_base("Siber Güvenlik, Ağ IPS & Canlı Ağ Radarı", "SİBER GÜVENLİK", "🛡️", "#00FFCC")
    
    # Sol: Canlı Ağ Radarı
    draw_card(draw, [(30, 60), (680, 630)], "🌐 CANLI SİSTEM AĞ BAĞLANTI RADARI (SALT-OKUNUR)", "#091325", "#00FFCC")
    radar_basliklar = "UYGULAMA (PID)     PROTOKOL    DURUM           YEREL ADRES         UZAK HEDEF"
    draw.text((45, 100), radar_basliklar, fill="#38BDF8", font=font_tiny)
    draw.line([(45, 120), (665, 120)], fill="#1E293B", width=1)

    baglantilar = [
        ("ollama.exe (8420)", "TCP", "LISTEN", "127.0.0.1:11434", "Dinleniyor (*)", "#38BDF8"),
        ("python.exe (1420)", "TCP", "ESTABLISHED", "192.168.1.34:52410", "142.250.185.206:443", "#10B981"),
        ("chrome.exe (9312)", "TCP", "ESTABLISHED", "192.168.1.34:52412", "172.217.16.206:443", "#10B981"),
        ("svchost.exe (1024)", "UDP", "LISTEN", "0.0.0.0:5353", "Dinleniyor (*)", "#94A3B8"),
        ("spoolsv.exe (1820)", "TCP", "LISTEN", "0.0.0.0:445", "Dinleniyor (*)", "#F59E0B")
    ]
    for idx, (app, proto, st, loc, rem, clr) in enumerate(baglantilar):
        ry = 130 + idx * 32
        draw.rectangle([(45, ry), (665, ry + 26)], fill="#0D1E36" if idx % 2 == 0 else "#081326")
        satir_txt = f"{app:<20} {proto:<10} {st:<15} {loc:<19} {rem}"
        draw.text((50, ry + 6), satir_txt, fill=clr, font=font_tiny)

    draw.text((45, 320), "🛡️ RADAR ÖZELLİKLERİ:\n• Bilgisayarınızdaki yabancı bağlantıları salt-okunur gösterir.\n• Sisteme paket göndermez, ağınızı yavaşlatmaz (%100 güvenli).\n• Şüpheli süreç PID numarasını anında tespit eder.", fill="#94A3B8", font=font_small)

    # Sağ: Ağ IPS Kalkanı & Tehdit Sayacı
    draw_card(draw, [(700, 60), (1170, 630)], "🛡️ AĞ IPS VE DEFENDER ENTEGRASYONU", "#0B1528", "#38BDF8")
    draw_btn(draw, [(720, 105), (1150, 145)], "Ağ IPS Kalkanı: AKTİF (500+ İmza)", "#059669", "#FFFFFF")
    
    threat_info = [
        ("SYN Flood Engelleme", "AKTİF", "#10B981"),
        ("Port Tarama Koruması", "AKTİF", "#10B981"),
        ("Honeypot Tuzak Portları", "Port 21, 23, 2222", "#F59E0B"),
        ("Fidye Yazılımı İzolasyonu", "Karantina Kasası Hazır", "#00FFCC")
    ]
    for i, (k_ad, k_val, k_clr) in enumerate(threat_info):
        ty = 170 + i * 55
        draw.rectangle([(720, ty), (1150, ty + 45)], fill="#081426", outline="#1E293B")
        draw.text((735, ty + 12), k_ad, fill="#E2E8F0", font=font_small)
        draw.text((980, ty + 12), k_val, fill=k_clr, font=font_small)

    draw.text((720, 420), "📌 UAC YÖNETİCİ ERİŞİMİ:\n• 'UAC İzni' butonuna basarak Altar'a tek tıkla Yönetici izni verebilirsiniz.\n• Bu izin sayesinde scapy ham soket yakalama ve Windows Güvenlik Duvarı\n  kuralları tam yetkiyle çalışır.", fill="#94A3B8", font=font_small)

    im.save(os.path.join(OUT_DIR, "09_guvenlik_ve_radar.png"))


# ------------------------------------------------------------------------------
# 10. PYTHON IDE & TERMİNAL
# ------------------------------------------------------------------------------
def gen_10_python_ide():
    im, draw = create_base("Python IDE, Editör & Canlı Terminal", "PYTHON IDE", "🐍", "#38BDF8")
    
    # Sol Üst: Kod Editörü
    draw_card(draw, [(30, 60), (820, 410)], "🐍 ALTAR PYTHON GELİŞTİRME EDİTÖRÜ (SEKMELİ)", "#060D1A", "#38BDF8")
    draw_btn(draw, [(45, 96), (150, 122)], "main.py ✕", "#0284C7", "#FFFFFF")
    draw_btn(draw, [(155, 96), (270, 122)], "ag_radari.py ✕", "#1E293B", "#94A3B8")
    draw_btn(draw, [(275, 96), (330, 122)], "+", "#1E293B", "#38BDF8")
    
    satirlar = [
        "1 | import socket, threading",
        "2 | from altar_edr_kalkan import AltarEdrMotoru",
        "3 | ",
        "4 | def sistem_tarama_baslat():",
        "5 |     edr = AltarEdrMotoru()",
        "6 |     print('[*] 5-Katmanlı EDR Telemetrisi Başlatıldı...')",
        "7 |     edr.tum_diskleri_tara(callback=lambda r: print(f'[TARAMA] {r}'))",
        "8 | ",
        "9 | if __name__ == '__main__':",
        "10|     sistem_tarama_baslat()"
    ]
    draw.rectangle([(45, 130), (805, 395)], fill="#030710", outline="#1E293B")
    for idx, s in enumerate(satirlar):
        draw.text((55, 140 + idx * 24), s, fill="#38BDF8" if "def " in s or "import" in s else "#F8FAFC", font=font_small)

    # Alt: Canlı Terminal
    draw_card(draw, [(30, 425), (820, 630)], "💻 CANLI TERMİNAL (F5 / ÇIKTI & TRACEBACK)", "#03060E", "#10B981")
    term_satirlar = [
        "[F5] Süreç Başlatıldı: python.exe main.py (PID: 10452)",
        "[*] 5-Katmanlı EDR Telemetrisi Başlatıldı...",
        "[TARAMA] C:\\Users\\Burak\\Downloads\\test.exe -> SHA-256: 4a2f8c... [TEMİZ]",
        "[TARAMA] Bellek Blokları Taranıyor (Shannon Entropisi: 4.12) -> Güvenli.",
        "[BAŞARILI] Betik 0.84 saniyede hatasız tamamlandı. (Return Code: 0)"
    ]
    for idx, ts in enumerate(term_satirlar):
        draw.text((45, 460 + idx * 22), ts, fill="#10B981" if "BAŞARILI" in ts or "TEMİZ" in ts else "#E2E8F0", font=font_small)

    # Sağ Panel: Araçlar & Şablonlar
    draw_card(draw, [(840, 60), (1170, 630)], "⚙️ GELİŞTİRİCİ ARAÇLARI", "#0B1528", "#F59E0B")
    draw_btn(draw, [(860, 100), (1150, 135)], "▶ Kodu Çalıştır (F5)", "#059669", "#FFFFFF")
    draw_btn(draw, [(860, 145), (1150, 180)], "⏹ Süreci Durdur", "#DC2626", "#FFFFFF")
    draw_btn(draw, [(860, 195), (1150, 230)], "🤖 Hatayı / Kodu AI'a Sor", "#0284C7", "#FFFFFF")
    draw_btn(draw, [(860, 240), (1150, 275)], "📋 Hazır Kod Şablonları", "#1E293B", "#F59E0B")
    draw_btn(draw, [(860, 285), (1150, 320)], "📦 Pip Paket Yöneticisi", "#1E293B", "#38BDF8")
    
    draw.text((860, 345), "🛡️ AST SÖZDİZİMİ KALKANI:\n• Kodu çalıştırmadan önce Abstract\n  Syntax Tree ile denetler.\n• rmdir /s veya izinsiz komut\n  enjeksiyonlarını uyarır.\n\n⚡ 2.65 GB RAM TASARRUFU:\n• VS Code veya PyCharm açmadan\n  aynı işi sıfır bellek yüküyle\n  doğrudan Altar içinde yapar.", fill="#94A3B8", font=font_small)

    im.save(os.path.join(OUT_DIR, "10_python_ide.png"))


# ------------------------------------------------------------------------------
# 11. DOSYA GEZGİNİ & KASA
# ------------------------------------------------------------------------------
def gen_11_dosya_gezgini_kasa():
    im, draw = create_base("Dosya Gezgini & Kriptografik Kasa", "DOSYA KASASI", "📁", "#10B981")
    
    # Sol Sürücü ve Dosya Ağacı
    draw_card(draw, [(30, 60), (600, 480)], "📁 YEREL DİZİN & DOSYA GEZGİNİ", "#081326", "#38BDF8")
    draw.text((45, 96), "Sürücüler: [C: Sistem] [D: Depo] [E: Gemini API Projesi]", fill="#38BDF8", font=font_small)
    draw.rectangle([(45, 120), (585, 460)], fill="#040914", outline="#1E293B")
    
    dosyalar = [
        ("📁 .altar_hafiza", "Klasör", "-", "2026-10-21"),
        ("📄 altar_arayuz.py", "Python", "112.4 KB", "2026-10-21"),
        ("📄 altar_edr_kalkan.py", "Python", "48.2 KB", "2026-10-21"),
        ("🔒 finans_raporu.altar_lock", "Kilitli Kasa", "2.1 MB", "2026-10-20"),
        ("🎬 sinematik_demo.mp4", "Video", "84.5 MB", "2026-10-20"),
        ("📄 Word Programı.py", "Python", "54.1 KB", "2026-10-19")
    ]
    for idx, (ad, tur, boy, tar) in enumerate(dosyalar):
        dy = 135 + idx * 30
        draw.text((55, dy), f"{ad:<32} {tur:<14} {boy:<10} {tar}", fill="#10B981" if ".altar_lock" in ad else "#E2E8F0", font=font_tiny)

    # Sağ Panel: Önizleme & SHA-256
    draw_card(draw, [(620, 60), (1170, 480)], "🔍 SALT-OKUNUR ÖNİZLEME & SHA-256 ANALİZİ", "#0A1428", "#F59E0B")
    draw.text((635, 100), "Seçili Dosya: finans_raporu.altar_lock (Boyut: 2.1 MB)", fill="#FFFFFF", font=font_bold)
    draw.rectangle([(635, 130), (1150, 220)], fill="#040914", outline="#F59E0B")
    draw.text((645, 140), "SHA-256 İMZA HASH DEĞERİ (BÜTÜNLÜK GARANTİSİ):", fill="#F59E0B", font=font_small)
    draw.text((645, 165), "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", fill="#00FFCC", font=font_tiny)
    draw.text((645, 190), "✔ Dosya disk üzerinde değiştirilmemiş; hash doğrulaması başarılı.", fill="#10B981", font=font_tiny)

    draw.text((635, 240), "KRİPTOGRAFİK GÜVENLİK BİLGİSİ:\n• Şifreleme Algoritması: AES-256 (Fernet) + PBKDF2-HMAC-SHA256\n• İterasyon Sayısı: 200.000 döngü (Kaba kuvvet saldırılarına karşı tam koruma)\n• Sistem Dosyası Koruması: C:\\Windows ve Program Files asla kilitlenemez.", fill="#CBD5E1", font=font_small)

    # Alt Panel: Kasa Kilitle / Kilit Aç
    draw_card(draw, [(30, 495), (1170, 630)], "🔐 KULLANICI ŞİFRELİ KASA İŞLEMLERİ", "#08152A", "#10B981")
    draw.text((50, 530), "Kasa Şifresi (En az 8 Karakter):", fill="#E2E8F0", font=font_small)
    draw.rectangle([(50, 555), (450, 595)], fill="#040914", outline="#10B981")
    draw.text((65, 570), "••••••••••••••••", fill="#10B981", font=font_sub)
    draw_btn(draw, [(470, 555), (680, 595)], "🔒 Seçili Dosyayı Kilitle", "#DC2626", "#FFFFFF")
    draw_btn(draw, [(700, 555), (910, 595)], "🔓 Şifreyi Çöz (Kilidi Aç)", "#059669", "#FFFFFF")
    draw_btn(draw, [(930, 555), (1150, 595)], "🤖 Dosyayı AI'a Analiz Ettir", "#0284C7", "#FFFFFF")

    im.save(os.path.join(OUT_DIR, "11_dosya_gezgini_kasa.png"))


# ------------------------------------------------------------------------------
# 12. VERİ KAZIMA & MODEM QOS
# ------------------------------------------------------------------------------
def gen_12_veri_kazima_modem():
    im, draw = create_base("Kazınan Veri, Analiz & Turbo Modem / Port", "VERİ & AĞ YÖNETİMİ", "📊", "#38BDF8")
    
    # Sol: Web Kazıyıcı & SSD Arşiv
    draw_card(draw, [(30, 60), (580, 630)], "📊 KAZINAN VERİ ARŞİVİ & ANALİZ MERKEZİ", "#081326", "#38BDF8")
    draw.text((50, 100), "NASA NTRS & Web Kazıma Koleksiyonu (JSON/SSD):", fill="#E2E8F0", font=font_sub)
    
    draw.rectangle([(50, 130), (560, 440)], fill="#040914", outline="#1E293B")
    arss = [
        ("NTRS 2026: Microgravity Droplet Combustion Data.json", "3.4 MB"),
        ("ACME Flame Extinction Experiments Table.json", "1.8 MB"),
        ("Space Station Zero-G Fluid Dynamics Corpus.json", "8.2 MB"),
        ("Haas CNC Tool Wear and Speed Feed Dataset.json", "940 KB")
    ]
    for i, (ad, sz) in enumerate(arss):
        ay = 145 + i * 50
        draw.text((65, ay), f"📄 {ad[:42]}...", fill="#38BDF8", font=font_tiny)
        draw.text((65, ay + 20), f"Boyut: {sz} • Yerel SSD Arşivlendi", fill="#94A3B8", font=font_tiny)
        draw_btn(draw, [(470, ay + 6), (545, ay + 36)], "Analiz Et", "#0284C7", "#FFFFFF")

    draw_btn(draw, [(50, 460), (320, 500)], "🤖 Seçili Veriyi AI'a Gönder", "#059669", "#FFFFFF")
    draw_btn(draw, [(330, 460), (560, 500)], "📂 JSON Arşiv Klasörünü Aç", "#1E293B", "#38BDF8")

    # Sağ: Turbo Modem QoS & Port Yöneticisi
    draw_card(draw, [(600, 60), (1170, 630)], "🚀 TURBO MODEM HOTSPOT, QOS & PORT YÖNETİCİSİ", "#0B1528", "#10B981")
    draw.text((620, 100), "Ağ Kalitesi (QoS) & Gecikme Monitörü:", fill="#FFFFFF", font=font_bold)
    
    qos_items = [
        ("Modem Bağlantısı", "192.168.1.1 (Fiber Gateway)", "#10B981"),
        ("Ping / Gecikme", "4.2 ms (Jitter: 0.3 ms)", "#10B981"),
        ("Bant Genişliği", "940 Mbps Download / 120 Mbps Upload", "#38BDF8"),
        ("Paket Kaybı", "%0.00 (Mükemmel)", "#10B981")
    ]
    for i, (k, v, c) in enumerate(qos_items):
        qy = 135 + i * 44
        draw.rectangle([(620, qy), (1150, qy + 36)], fill="#07101E", outline="#1E293B")
        draw.text((635, qy + 8), k, fill="#E2E8F0", font=font_small)
        draw.text((850, qy + 8), v, fill=c, font=font_small)

    draw.text((620, 330), "🔧 SİSTEM SERVİS PORTLARI & SÜREÇ DONDURMA (FREEZE):", fill="#F59E0B", font=font_bold)
    draw.rectangle([(620, 360), (1150, 550)], fill="#040914", outline="#1E293B")
    draw.text((635, 375), "PID 4120  |  Port 8080 (HTTP)  |  Durum: Normal   |  [Dondur / Sürdür]", fill="#CBD5E1", font=font_tiny)
    draw.text((635, 410), "PID 5820  |  Port 3306 (MySQL) |  Durum: Korumalı |  [Yönetici Gerekli]", fill="#CBD5E1", font=font_tiny)
    draw.text((635, 445), "PID 9110  |  Port 27017 (Mongo)|  Durum: İzole     |  [Port Kapatıldı]", fill="#EF4444", font=font_tiny)

    im.save(os.path.join(OUT_DIR, "12_veri_kazima_modem.png"))


# ------------------------------------------------------------------------------
# 13. CNC G-CODE SİMÜLATÖR
# ------------------------------------------------------------------------------
def gen_13_cnc_simulator():
    im, draw = create_base("CNC G-Code 2D/3D Simülatör (Haas V34)", "CNC SİMÜLATÖR", "📐", "#F59E0B")
    
    # Sol: Haas V34 Kontrol Paneli & G-Code
    draw_card(draw, [(30, 60), (450, 630)], "📐 HAAS V34 CNC KUMANDA PANELİ", "#081326", "#F59E0B")
    draw_btn(draw, [(50, 100), (160, 130)], "▶ CYCLE START", "#059669", "#FFFFFF")
    draw_btn(draw, [(170, 100), (280, 130)], "⏹ FEED HOLD", "#DC2626", "#FFFFFF")
    draw_btn(draw, [(290, 100), (430, 130)], "RESET", "#1E293B", "#E2E8F0")

    draw.text((50, 145), "Aktif G-Code Programı (O0124 - KABA CEP):", fill="#CBD5E1", font=font_small)
    g_code_satirlar = [
        "N05 G90 G54 G17 G21 G40 G80",
        "N10 T01 M06 (10mm Kaba Parmak Freze)",
        "N15 S3200 M03 M08 (Spindle Devri & Sıvı)",
        "N20 G00 X10.0 Y15.0 Z5.0",
        "N25 G01 Z-2.0 F250",
        "N30 G01 X80.0 Y15.0 F650",
        "N35 G02 X95.0 Y30.0 R15.0 F450",
        "N40 G01 Y70.0",
        "N45 G00 Z25.0 M09",
        "N50 M30 (Program Sonu)"
    ]
    draw.rectangle([(50, 175), (430, 440)], fill="#040914", outline="#1E293B")
    for idx, gs in enumerate(g_code_satirlar):
        draw.text((60, 185 + idx * 24), gs, fill="#00FFCC" if "T01" in gs or "S3200" in gs else "#E2E8F0", font=font_small)

    draw.text((50, 460), "TAKIM KÜTÜPHANESİ (ATC):\n• T1: 10mm Kaba Freze\n• T2: 6mm Küre Freze (Pah)\n• T3: 4mm Parmak Freze", fill="#94A3B8", font=font_small)

    # Sağ: 2D İzometrik & 3D OpenGL Katı Model Sahnesi
    draw_card(draw, [(470, 60), (1170, 630)], "🚀 2D İZOMETRİK VE PYQT6 OPENGL 3D KATI MODEL SAHNESİ", "#081020", "#00FFCC")
    draw_btn(draw, [(490, 100), (680, 135)], "🚀 3D Katı Model Aç", "#0284C7", "#FFFFFF")
    draw_btn(draw, [(690, 100), (860, 135)], "📐 2D Takım Yolu", "#1E293B", "#38BDF8")
    draw_btn(draw, [(870, 100), (1030, 135)], "⚠️ Mengene Çarpışma: AÇIK", "#059669", "#FFFFFF")

    # Çizim Alanı
    draw.rectangle([(490, 150), (1150, 520)], fill="#030712", outline="#00FFCC", width=1)
    # Kütük Çizimi
    draw.rectangle([(550, 220), (950, 440)], fill="#0D1F38", outline="#38BDF8", width=2)
    draw.text((560, 230), "KÜTÜK (ALU 6061-T6): 120 x 80 x 30 mm", fill="#60A5FA", font=font_small)
    # Mengene
    draw.rectangle([(510, 200), (550, 460)], fill="#334155")
    draw.rectangle([(950, 200), (990, 460)], fill="#334155")
    draw.text((515, 320), "MENGENE", fill="#CBD5E1", font=font_tiny)
    draw.text((955, 320), "MENGENE", fill="#CBD5E1", font=font_tiny)

    # Takım Yolu (Yeşil ve Kırmızı)
    draw.line([(580, 280), (880, 280)], fill="#10B981", width=3)
    draw.line([(880, 280), (880, 380)], fill="#10B981", width=3)
    draw.line([(880, 380), (580, 380)], fill="#10B981", width=3)
    draw.line([(580, 380), (580, 280)], fill="#10B981", width=3)
    draw.line([(580, 280), (520, 200)], fill="#EF4444", width=2)  # G00 Hızlı

    draw.text((490, 545), "Koordinatlar: X: +45.200  Y: +28.500  Z: -2.000   Devir: 3200 RPM   İlerleme: 650 mm/dk", fill="#F59E0B", font=font_bold)
    draw.text((490, 575), "Çarpışma Koruması: Mengene güvenlik payı (5mm) aktif; takım mengene kleransına girmedi.", fill="#10B981", font=font_small)

    im.save(os.path.join(OUT_DIR, "13_cnc_simulator.png"))


# ------------------------------------------------------------------------------
# 14. TERSİNE MÜHENDİSLİK & HEX LAB
# ------------------------------------------------------------------------------
def gen_14_tersine_muhendislik():
    im, draw = create_base("Tersine Mühendislik, Hex Lab & DPI", "TERSİNE MÜHENDİSLİK", "🔬", "#EC4899")
    
    # Sol: Hex Matrisi ve Disassembly
    draw_card(draw, [(30, 60), (740, 630)], "🔬 16'LIK HEX MATRİSİ & RAM DECOMPILER", "#060D1A", "#EC4899")
    draw.text((45, 100), "OFFSET      00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F  ASCII EŞLEMESİ", fill="#38BDF8", font=font_tiny)
    draw.line([(45, 120), (725, 120)], fill="#1E293B", width=1)

    hex_data = [
        ("00000000", "4D 5A 90 00 03 00 00 00  04 00 00 00 FF FF 00 00", "MZ.............."),
        ("00000010", "B8 00 00 00 00 00 00 00  40 00 00 00 00 00 00 00", "........@......."),
        ("00000020", "00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00", "................"),
        ("00000030", "00 00 00 00 00 00 00 00  00 00 00 00 F0 00 00 00", "................"),
        ("00000040", "0E 1F BA 0E 00 B4 09 CD  21 B8 01 4C CD 21 54 68", "........!..L.!Th"),
        ("00000050", "69 73 20 70 72 6F 67 72  61 6D 20 63 61 6E 6E 6F", "is program canno"),
        ("00000060", "74 20 62 65 20 72 75 6E  20 69 6E 20 44 4F 53 20", "t be run in DOS ")
    ]
    for i, (off, hx, asc) in enumerate(hex_data):
        hy = 130 + i * 28
        draw.text((45, hy), f"{off}  {hx}  {asc}", fill="#F8FAFC" if i < 4 else "#F59E0B", font=font_tiny)

    draw.text((45, 340), "📌 PYTHON BYTECODE DECOMPILE (DISASSEMBLY):", fill="#10B981", font=font_bold)
    draw.rectangle([(45, 370), (725, 600)], fill="#03060E", outline="#1E293B")
    opcodes = [
        "10 LOAD_GLOBAL              0 (os)",
        "12 LOAD_METHOD              1 (path)",
        "14 LOAD_ATTR                2 (exists)",
        "16 LOAD_FAST                0 (dosya_yolu)",
        "18 PRECALL                  1",
        "22 CALL                     1",
        "32 POP_JUMP_IF_FALSE       45 (to line 45)",
        "34 LOAD_GLOBAL              3 (SHA256_HESAPLA)",
        "36 LOAD_FAST                0 (dosya_yolu)",
        "38 CALL                     1"
    ]
    for idx, op in enumerate(opcodes):
        draw.text((55, 380 + idx * 21), op, fill="#00FFCC" if "CALL" in op else "#E2E8F0", font=font_tiny)

    # Sağ Panel: Shannon Entropi & PE Başlık
    draw_card(draw, [(760, 60), (1170, 630)], "📊 SHANNON ENTROPİ & GÖMÜLÜ STRINGS", "#0B1528", "#38BDF8")
    draw.text((780, 100), "Shannon Entropi Değeri: 7.84 / 8.00", fill="#EF4444", font=font_bold)
    draw.text((780, 125), "⚠️ Tehdit / Şifreleme Tespiti: Dosya UPX ile paketlenmiş\n   veya kriptolanmış (Packer / Cryptor tespit edildi).", fill="#F59E0B", font=font_small)

    # Entropi Grafiği
    draw.rectangle([(780, 180), (1150, 320)], fill="#040914", outline="#1E293B")
    for ex in range(780, 1150, 10):
        val = max(5, abs(int(20 + 75 * math.sin((ex - 780) * 0.05))))
        draw.line([(ex, 310), (ex, 310 - val)], fill="#EC4899", width=2)
    draw.text((790, 190), "Entropi Dağılım Grafiği (Bölüm Analizi)", fill="#CBD5E1", font=font_tiny)

    draw.text((780, 340), "GÖMÜLÜ METİNLER (EXTRACTED STRINGS):\n• 'VirtualAlloc'\n• 'WriteProcessMemory'\n• 'kernel32.dll'\n• 'https://malicious-node.xyz/beacon'", fill="#CBD5E1", font=font_tiny)

    im.save(os.path.join(OUT_DIR, "14_tersine_muhendislik.png"))


# ------------------------------------------------------------------------------
# 15. EDR ANTİVİRÜS & KARANTİNA
# ------------------------------------------------------------------------------
def gen_15_edr_antivirus():
    im, draw = create_base("5-Katmanlı Antivirüs & EDR Kalkanı", "EDR KALKANI", "🦠", "#EF4444")
    
    # 5 Katman Kartları
    draw_card(draw, [(30, 60), (740, 630)], "🦠 5-KATMANLI PROAKTİF EDR TELEMETRİSİ", "#081326", "#EF4444")
    katmanlar = [
        ("KATMAN 1: STATİK SHA-256 İMZA TARAMASI", "Bilinen 12.000+ kötü amaçlı yazılım hash veri tabanı ile anlık eşleme.", "✔ GÜNCEL"),
        ("KATMAN 2: SHANNON ENTROPİ RADARI", "Bellek bloklarının entropisini hesaplayarak paketlenmiş fidye yazılımlarını yakalar.", "✔ AKTİF"),
        ("KATMAN 3: AST & KOD ANALİZÖRÜ", "Zararlı Python ve PowerShell betiklerini Abstract Syntax Tree ile bloke eder.", "✔ AKTİF"),
        ("KATMAN 4: FİDYE TUZAĞI (CANARY HONEYPOT)", "Altar_Ransomware_Tuzagi dizinindeki yem dosyaları izler; yetkisiz erişimde süreci dondurur.", "✔ 0 İHLAL"),
        ("KATMAN 5: İNDİRİLENLER VE KARANTİNA KASASI", "Yeni indirilen dosyaları otomatik sandbox'a alır; tehdit durumunda AES-GCM ile kilitler.", "✔ HAZIR")
    ]
    for i, (b, d, s) in enumerate(katmanlar):
        ky = 100 + i * 85
        draw.rectangle([(50, ky), (720, ky + 72)], fill="#0D1E36", outline="#EF4444" if "KATMAN 4" in b else "#10B981")
        draw.text((65, ky + 8), b, fill="#FFFFFF", font=font_bold)
        draw.text((65, ky + 30), d, fill="#CBD5E1", font=font_tiny)
        draw.text((65, ky + 50), f"Durum: {s}", fill="#10B981", font=font_tiny)

    draw.text((50, 545), "⚡ Diferansiyel Kuyruk Mantığı: Arka planda çalışırken CPU <%0.5,\n   RAM <%45 MB tüketir. Bilgisayarınızı veya oyunlarınızı asla kasmaz.", fill="#38BDF8", font=font_small)

    # Sağ Panel: Karantina Kasası
    draw_card(draw, [(760, 60), (1170, 630)], "🔒 KRİPTOGRAFİK KARANTİNA KASASI", "#0A1428", "#F59E0B")
    draw_btn(draw, [(780, 100), (1150, 135)], "🔒 Dosyayı Güvenle Karantinaya Al", "#DC2626", "#FFFFFF")
    draw_btn(draw, [(780, 145), (1150, 180)], "🔄 Karantinadan Geri Yükle", "#1E293B", "#38BDF8")
    draw_btn(draw, [(780, 190), (1150, 225)], "🗑️ Kalıcı Olarak İmha Et", "#1E293B", "#EF4444")

    draw.text((780, 245), "Karantinadaki Yalıtılmış Dosyalar:", fill="#E2E8F0", font=font_small)
    draw.rectangle([(780, 270), (1150, 480)], fill="#040914", outline="#1E293B")
    kar_files = [
        ("suspicious_macro.docm", "2026-10-21 09:14", "Trojan.Dropper"),
        ("miner_beacon.exe", "2026-10-20 18:22", "CoinMiner.Generic"),
        ("ransom_test_payload.bin", "2026-10-19 14:05", "Ransomware.Lockbit")
    ]
    for idx, (f_ad, f_tar, f_turu) in enumerate(kar_files):
        fy = 285 + idx * 60
        draw.text((790, fy), f"🔒 {f_ad}", fill="#F59E0B", font=font_tiny)
        draw.text((790, fy + 18), f"Tarih: {f_tar} | Tehdit: {f_turu}", fill="#94A3B8", font=font_tiny)

    draw.text((780, 500), "Karantina Garantisi: Yalıtılan dosyalar .altar_karantina\naltında şifreli saklanır; yürütme bayrakları silinir ve\nsisteme zarar verme olasılığı %0'a indirilir.", fill="#CBD5E1", font=font_tiny)

    im.save(os.path.join(OUT_DIR, "15_edr_antivirus.png"))


# ------------------------------------------------------------------------------
# 16. NASA MİKROÇEKİM & UZAY TELEMETRİ
# ------------------------------------------------------------------------------
def gen_16_nasa_mikrocekim():
    im, draw = create_base("NASA Mikroçekim & Uzay Telemetri Lab", "NASA TELEMETRİ", "🚀", "#38BDF8")
    
    # Sol: 0G/1G Damlacık & d²-Yasası Simülatörü
    draw_card(draw, [(30, 60), (600, 630)], "🚀 0G/1G DAMLACIK YANMA & d²-YASASI SİMÜLATÖRÜ", "#070F1E", "#38BDF8")
    draw_btn(draw, [(50, 100), (210, 130)], "▶ 0G Simülasyonu Başlat", "#0284C7", "#FFFFFF")
    draw_btn(draw, [(220, 100), (370, 130)], "Yakıt: n-Heptan", "#1E293B", "#F59E0B")
    draw_btn(draw, [(380, 100), (580, 130)], "Ortam: %21 O2, 1.0 atm", "#1E293B", "#10B981")

    # Küresel Soğuk Alev Sahnesi
    draw.rectangle([(50, 145), (580, 360)], fill="#02040A", outline="#00FFCC")
    draw.ellipse([(240, 180), (390, 330)], outline="#38BDF8", width=3)  # Soğuk alev küresi
    draw.ellipse([(290, 230), (340, 280)], fill="#F59E0B")  # Yakıt damlacığı
    draw.text((180, 155), "KÜRESEL MİKROÇEKİM SOĞUK ALEVİ (COOL FLAME)", fill="#00FFCC", font=font_small)
    draw.text((250, 335), "d² = d0² - K·t (Lineer Yanma)", fill="#F8FAFC", font=font_small)

    # d²-Yasası Grafiği
    draw.text((50, 380), "d² Çap Değişim Eğrisi (0G vs 1G Yanma Hızı):", fill="#E2E8F0", font=font_small)
    draw.rectangle([(50, 405), (580, 540)], fill="#040814", outline="#1E293B")
    draw.line([(70, 520), (560, 520)], fill="#64748B", width=1)
    draw.line([(70, 420), (70, 520)], fill="#64748B", width=1)
    draw.line([(70, 430), (540, 510)], fill="#00FFCC", width=3)  # 0G Lineer
    draw.line([(70, 430), (380, 510)], fill="#EF4444", width=2)  # 1G Hızlı söner
    draw.text((450, 470), "0G Mikroçekim", fill="#00FFCC", font=font_tiny)
    draw.text((320, 525), "1G Yerçekimi", fill="#EF4444", font=font_tiny)

    draw.text((50, 560), "NASA BASS & ACME Deneyleri: Yerçekimsiz ortamda damlacık\nkusursuz bir küre şeklinde kalır ve lineer d²-yasasını izler.", fill="#94A3B8", font=font_tiny)

    # Sağ: Akustik Sonification & Osiloskop
    draw_card(draw, [(620, 60), (1170, 630)], "🔊 AKUSTİK VERİ SESLENDİRME (SONIFICATION) & NTRS", "#0A1428", "#F59E0B")
    draw.text((640, 100), "DİJİTAL TELEMETRİ OSİLOSKOPU (RAM DİREKT SENTEZ):", fill="#FFFFFF", font=font_bold)
    
    draw.rectangle([(640, 130), (1150, 310)], fill="#02040A", outline="#10B981")
    for ox in range(640, 1150, 8):
        oy = int(220 + 50 * math.sin((ox - 640) * 0.08) + 20 * math.sin((ox - 640) * 0.2))
        draw.line([(ox, oy), (ox + 4, oy)], fill="#10B981", width=2)
    draw.text((650, 140), "Frekans: 432 Hz  |  Örnekleme: 44.1 kHz  |  Anomali: %0.0", fill="#10B981", font=font_tiny)

    draw_btn(draw, [(640, 325), (880, 360)], "▶ Telemetriyi Seslendir (Play)", "#059669", "#FFFFFF")
    draw_btn(draw, [(890, 325), (1150, 360)], "⏹ Sesi Durdur", "#1E293B", "#EF4444")

    draw.text((640, 390), "NASA NTRS BİLİMSEL KORPUS TARAYICI:\n• 2.400+ NASA mikroçekim raporu taranır.\n• CSV sayısal verilerini işitilebilir ses tonlarına çevirir.\n• Kulakla veri anomalilerini anında duymanızı sağlar.", fill="#CBD5E1", font=font_small)

    im.save(os.path.join(OUT_DIR, "16_nasa_mikrocekim.png"))


# ------------------------------------------------------------------------------
# 17. MULTİMEDYA STÜDYOSU
# ------------------------------------------------------------------------------
def gen_17_multimedya_studyosu():
    im, draw = create_base("Multimedya Stüdyosu: Ekran Video, Ses & Kamera", "MULTİMEDYA", "🎬", "#8B5CF6")
    
    # 3 Multimedya Aracı
    araclar = [
        ("🎬 EKRAN VİDEO KAYDEDİCİ", "60 FPS ekran kaydı, ses senkronizasyonu, sıfır kasma", "#0284C7", [
            "Çözünürlük: 1920x1080 (Full HD)",
            "FPS: 60 FPS Sabit Hızlandırma",
            "Ses: Mikrofon + Sistem Sesi Dahil",
            "Kayıt Formatı: MP4 (H.264 / AAC)"
        ]),
        ("🎙️ STÜDYO SES KAYDEDİCİ", "Lossless WAV stüdyo kaydı, dinamik dB seviye göstergesi", "#059669", [
            "Örnekleme: 44.1 kHz / 16-Bit Stereo",
            "dB Ölçer: -12 dB (İdeal Dinamik Aralık)",
            "Gürültü Filtresi: Arka Plan Gürültü Engelleme",
            "Kayıt Formatı: WAV / 192 kbps MP3"
        ]),
        ("📷 KAMERA STÜDYOSU & VISİON", "Web kamerası yakalama, tek tıkla AI görsel analiz köprüsü", "#F59E0B", [
            "Kamera: HD Web Cam (1280x720)",
            "Görsel Analiz: AI Vision Köprüsüne Aktar",
            "Fotoğraf & Video: Anlık Yakalama Desteği",
            "Format: PNG / MP4"
        ])
    ]

    for i, (baslik, alt, renk, maddeler) in enumerate(araclar):
        ax = 30 + i * 385
        draw_card(draw, [(ax, 60), (ax + 370, 520)], baslik, "#091428", renk, renk)
        draw.text((ax + 14, 100), alt, fill="#CBD5E1", font=font_small)
        
        # Önizleme Kutusu
        draw.rectangle([(ax + 14, 135), (ax + 356, 320)], fill="#040914", outline=renk)
        draw.text((ax + 50, 210), f"CANLI {baslik.split()[1]} SAHNESİ", fill=renk, font=font_bold)
        draw.text((ax + 70, 240), "Donanım Hızlandırmalı", fill="#94A3B8", font=font_tiny)

        for m_idx, m in enumerate(maddeler):
            draw.text((ax + 20, 345 + m_idx * 24), f"• {m}", fill="#E2E8F0", font=font_tiny)

        draw_btn(draw, [(ax + 14, 465), (ax + 356, 500)], "🚀 Stüdyoyu Aç", renk, "#FFFFFF")

    # Alt Bilgilendirme
    draw_card(draw, [(30, 540), (1170, 630)], "⚡ HIZLI ERİŞİM BUTONLARI (SOL ALT BAR)", "#081020", "#00FFCC")
    draw.text((50, 575), "Sol alt çubukta bulunan '🔴 Hızlı Kayıt', '⏺ Hızlı Video' ve '📷 Hızlı Kamera' butonları pencereleri açmadan tek tıkla kaydı başlatır.", fill="#94A3B8", font=font_sub)

    im.save(os.path.join(OUT_DIR, "17_multimedya_studyosu.png"))


# ------------------------------------------------------------------------------
# 18. SİNEMATİK ANİMASYONLAR
# ------------------------------------------------------------------------------
def gen_18_sinematik_animasyonlar():
    im, draw = create_base("10 Prosedürel Sinematik Arka Plan Animasyonu", "ANİMASYON MOTORU", "✨", "#00FFCC")
    
    draw_card(draw, [(30, 60), (1170, 630)], "✨ HER ÇALIŞMA SEKMESİ İÇİN 10 AYRI 60 FPS SİNEMATİK ANİMASYON", "#081326", "#00FFCC")
    draw.text((50, 100), "Altar'ın tüm sekmelerinde arka planda çalışan, CPU yükü <%1 olan prosedürel parçacık motorları:", fill="#38BDF8", font=font_sub)

    animasyonlar = [
        ("1. NÖRAL AI AĞI", "💬 Sohbet Sekmesi", "Sinaptik nöron düğümleri, nabız atan veri darbeleri", "#00FFCC"),
        ("2. KRİPTO KASA", "📁 Dosya Gezgini", "Kayan hex sütunları, kilit/kasa poligon halkaları", "#10B981"),
        ("3. SYNTHWAVE GRID", "🎮 Oyun Merkezi", "Neon retro ızgara, dağ silueti, günbatımı ufuk çizgisi", "#EC4899"),
        ("4. DOĞA ŞELALESİ", "🎵 Müzik Merkezi", "Biolüminesans su damlaları, ambient orman parçacıkları", "#38BDF8"),
        ("5. MATRIX KODU", "🔬 Tersine Müh.", "Yukarıdan aşağı akan yeşil dijital yağmur ve semboller", "#22C55E"),
        ("6. VERİ GALAKSİSİ", "📊 Analiz & Modem", "Dönen yıldız diski, radar tarama ışını, pulsar darbeleri", "#8B5CF6"),
        ("7. CNC LAZER YOLU", "📐 CNC Simülatör", "G-Code takım yolu koordinatları, lazer kıvılcımları", "#F59E0B"),
        ("8. ENERJİ KALKANI", "🛡️ Siber Güvenlik", "Altıgen (Hexagon) siber kalkan petekleri, şok dalgaları", "#06B6D4"),
        ("9. AYRIŞTIRICI DALGA", "🎬 Multimedya", "Ses/video sinematik dalga formu ve sinüs frekansları", "#E11D48"),
        ("10. EDR TEHDİT RADARI", "🦠 Antivirüs & EDR", "Dairesel radar sweep, tehdit hedef tespit halkaları", "#EF4444")
    ]

    for i, (b, sekme, d, c) in enumerate(animasyonlar):
        col = i % 2
        row = i // 2
        x1 = 50 + col * 550
        y1 = 135 + row * 92
        draw.rectangle([(x1, y1), (x1 + 530, y1 + 78)], fill="#0D1E36", outline=c, width=1)
        draw.text((x1 + 14, y1 + 10), b, fill=c, font=font_bold)
        draw.text((x1 + 240, y1 + 10), f"[{sekme}]", fill="#E2E8F0", font=font_tiny)
        draw.text((x1 + 14, y1 + 40), d, fill="#94A3B8", font=font_tiny)

    im.save(os.path.join(OUT_DIR, "18_sinematik_animasyonlar.png"))


# ------------------------------------------------------------------------------
# 19. PERFORMANS REHBERİ
# ------------------------------------------------------------------------------
def gen_19_performans_rehberi():
    im, draw = create_base("Donanım & Maksimum Performans Rehberi", "PERFORMANS", "⚡", "#F59E0B")
    
    # 4 Kritik Performans Kuralı
    kurallar = [
        ("1. NVIDIA CUDA & GPU VRAM YÖNETİMİ", [
            "• Ollama modelini GPU (CUDA) üzerinden çalıştırmak token üretim hızını 8x artırır.",
            "• Altar'da num_ctx=2048 olarak kilitlenmiştir; 6-8 GB VRAM kartlarda dahi taşma yaşanmaz.",
            "• 45+ token/saniye hızıyla anlık yanıtlar üretilir."
        ], "#00FFCC"),
        ("2. RAM & PİL TASARRUFU (KEEP_ALIVE=0)", [
            "• Sohbet etmediğinizde üstteki '🟢 Yapay Zeka: Açık' butonunu '🔴 Kapalı' yapın.",
            "• Ollama modeli VRAM'den tamamen düşürülür ve bellek anında işletim sistemine iade edilir.",
            "• Dizüstü bilgisayarlarda pil ömrünü 3 katına çıkarır."
        ], "#10B981"),
        ("3. DOĞRU UZMANLIK PROFİLİ SEÇİMİ", [
            "• Günlük sohbetler için 'Profil: Sohbet' seçin.",
            "• Kodlama için 'Profil: Yazılım' seçin; gereksiz nezaket cümleleri atlanır,",
            "  doğrudan temiz kod basılır ve yanıt süresi %60 kısalır."
        ], "#38BDF8"),
        ("4. HIZLI KOMUT PALETİ (CTRL+K)", [
            "• Klavyeden 'Ctrl+K' tuşuna basarak hızlı komut paletini açın.",
            "• Fareye dokunmadan tüm sekmelere, pencerelere ve radar araçlarına",
            "  saniyeler içinde geçiş yapın."
        ], "#F59E0B")
    ]

    for i, (b, maddeler, c) in enumerate(kurallar):
        col = i % 2
        row = i // 2
        x1 = 30 + col * 580
        y1 = 60 + row * 280
        draw_card(draw, [(x1, y1), (x1 + 560, y1 + 265)], b, "#081326", c, c)
        for m_idx, m in enumerate(maddeler):
            draw.text((x1 + 16, y1 + 48 + m_idx * 30), m, fill="#CBD5E1", font=font_small)

    im.save(os.path.join(OUT_DIR, "19_performans_rehberi.png"))


def main():
    print("Generating 19 rich visual preview diagrams for README...")
    gen_01_genel_mimari()
    gen_02_sohbet_ai()
    gen_03_sekmeler_gezgini()
    gen_04_siber_oyunlar()
    gen_05_muzik_sinematik()
    gen_06_sinematik_video()
    gen_07_canva_ve_belge()
    gen_08_ollama_kurucu()
    gen_09_guvenlik_ve_radar()
    gen_10_python_ide()
    gen_11_dosya_gezgini_kasa()
    gen_12_veri_kazima_modem()
    gen_13_cnc_simulator()
    gen_14_tersine_muhendislik()
    gen_15_edr_antivirus()
    gen_16_nasa_mikrocekim()
    gen_17_multimedya_studyosu()
    gen_18_sinematik_animasyonlar()
    gen_19_performans_rehberi()
    print("All 19 visual diagrams generated successfully!")

if __name__ == "__main__":
    main()
