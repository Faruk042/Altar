import os
import sys
import ctypes

# Windows Yüksek DPI ve Gerçek Tam Ekran (100% Monitör Kiosk) Desteği
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import json
import time
import threading
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import customtkinter as ctk
from PIL import Image
from tkinter import messagebox

# Konsept 3: Yörünge ve Dünya Ufku Renk Paleti
PANEL_COLOR = "#0D1B2A"
BTN_COLOR = "#00A86B"
BTN_HOVER = "#007F50"


class NasaScraperWindow(ctk.CTkToplevel):
    def __init__(self, main_app):
        super().__init__(main_app)
        self.main_app = main_app  # Ana uygulamanın referansını hafızaya alıyoruz
        self.title("Altar Web Veri Kazıyıcı, Kategorizasyon ve Telemetri Köprüsü")

        self.geometry("1050x700")
        self._tam_ekran_mi = True
        self.after(20, self._tam_ekran_yap)
        self.bind("<F11>", self._tam_ekran_degistir)
        self.bind("<Escape>", self._tam_ekrandan_cik)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Hızlı HTTP Bağlantı Havuzu (Session Reuse)
        self._http_session = requests.Session()
        self._http_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Web Kazıma Değişkenleri
        self.taramaya_devam_et = False
        self.bulunan_linkler = set()
        self.son_kategorize_veri = None
        self._kazima_aktif = False

        # --- ARAYÜZ TASARIMI ---
        self.main_frame = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=15, border_width=2,
                                       border_color="#1B263B")
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.96, relheight=0.96)

        # Üst Sağ Kontrol Butonları (Tam Ekran Kapat / Geri Yükle)
        self.btn_kapat = ctk.CTkButton(
            self.main_frame,
            text="✕ Kapat",
            width=75,
            height=28,
            fg_color="#dc2626",
            hover_color="#991b1b",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.on_closing
        )
        self.btn_kapat.place(relx=0.985, rely=0.015, anchor="ne")

        self.btn_tam_ekran = ctk.CTkButton(
            self.main_frame,
            text="🗗 Tam Ekran (F11)",
            width=120,
            height=28,
            fg_color="#1E293B",
            hover_color="#334155",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._tam_ekran_degistir
        )
        self.btn_tam_ekran.place(relx=0.90, rely=0.015, anchor="ne")

        self.lbl_baslik = ctk.CTkLabel(
            self.main_frame,
            text="🌍 YÖRÜNGE & WEB VERİ KAZIMA MERKEZİ",
            font=ctk.CTkFont(family="Consolas", size=24, weight="bold"),
            text_color=BTN_COLOR
        )
        self.lbl_baslik.pack(pady=(15, 5))

        self.lbl_alt_baslik = ctk.CTkLabel(
            self.main_frame,
            text="Herkese açık web sitelerindeki tabloları, belgeleri, başlıkları ve metinleri salt-okunur kazır, kategorize eder ve SSD'ye veya Altar Analiz Merkezine aktarır.",
            font=ctk.CTkFont(size=12), text_color="#778DA9"
        )
        self.lbl_alt_baslik.pack(pady=(0, 15))

        # URL Giriş ve Kontrol Butonları
        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=30, pady=5)

        ctk.CTkLabel(self.input_frame, text="Hedef URL:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)

        self.url_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Örn: https://ntrs.nasa.gov veya herhangi bir açık web sitesi...",
            width=380, fg_color="#1B263B", border_color=BTN_COLOR
        )
        self.url_entry.pack(side="left", padx=8, fill="x", expand=True)

        self.btn_kategorize = ctk.CTkButton(
            self.input_frame, text="🔍 Sayfayı Kategorize Et & Kazı", width=190,
            fg_color="#1f538d", hover_color="#14375e", command=self.baslat_kategorize_kazima
        )
        self.btn_kategorize.pack(side="left", padx=5)

        self.btn_ssd_kaydet = ctk.CTkButton(
            self.input_frame, text="💾 SSD'ye Kaydet (JSON/MD)", width=170,
            fg_color="#6A0dad", hover_color="#4B0082", command=self.ssd_guvenli_kaydet
        )
        self.btn_ssd_kaydet.pack(side="left", padx=5)

        self.btn_aktar = ctk.CTkButton(
            self.input_frame, text="🧠 Altar Analiz Sekmesine Gönder", width=200,
            fg_color="#b85c00", hover_color="#8f4700", command=self.kategorize_veriyi_altara_gonder
        )
        self.btn_aktar.pack(side="left", padx=5)

        self.btn_tara = ctk.CTkButton(
            self.input_frame, text="📡 Canlı İzle", width=110,
            fg_color=BTN_COLOR, hover_color=BTN_HOVER, command=self.toggle_tarama
        )
        self.btn_tara.pack(side="right", padx=5)

        # Log ve Önizleme Ekranı
        self.log_ekrani = ctk.CTkTextbox(
            self.main_frame, fg_color="#050B14", text_color="#00FF88",
            font=ctk.CTkFont(family="Consolas", size=13), corner_radius=8, border_width=1,
            border_color="#333333"
        )
        self.log_ekrani.pack(fill="both", expand=True, padx=30, pady=(10, 15))
        self.log_ekrani.insert(
            "end",
            "[SİSTEM]: Veri Kazıma Köprüsü Çevrimiçi.\n"
            "• Tek seferlik detaylı bilgi/tablo/link ayrıştırması için '🔍 Sayfayı Kategorize Et & Kazı' butonunu kullanın.\n"
            "• Sürekli yeni dosya (.csv, .json, .txt) takibi için '📡 Canlı İzle' butonunu kullanın.\n\n"
        )
        self.log_ekrani.configure(state="disabled")

        self.lbl_status = ctk.CTkLabel(
            self.main_frame, text="Durum: Bekleniyor...",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#778DA9"
        )
        self.lbl_status.pack(side="bottom", pady=8)

        # Arka Plan Görselini pencere açılışını dondurmadan asenkron yükle
        self.bg_image_path = "earth_horizon_bg.jpg"
        self._arka_plani_hazirla()

    def _arka_plani_hazirla(self):
        def _bg_worker():
            try:
                if not os.path.exists(self.bg_image_path):
                    url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1080"
                    response = self._http_session.get(url, timeout=6)
                    if response.status_code == 200:
                        with open(self.bg_image_path, "wb") as f:
                            f.write(response.content)

                if os.path.exists(self.bg_image_path):
                    bg_image = Image.open(self.bg_image_path)
                    ekran_genisligi = self.winfo_screenwidth()
                    ekran_yuksekligi = self.winfo_screenheight()

                    def _uygula():
                        if not self.winfo_exists():
                            return
                        self.bg_photo = ctk.CTkImage(
                            light_image=bg_image, dark_image=bg_image,
                            size=(ekran_genisligi, ekran_yuksekligi)
                        )
                        self.bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
                        self.bg_label.place(relx=0.5, rely=0.5, anchor="center")
                        self.bg_label.lower()

                    self.after(0, _uygula)
            except Exception:
                pass

        threading.Thread(target=_bg_worker, daemon=True).start()

    def log_yaz(self, mesaj):
        def _yaz():
            if not self.winfo_exists():
                return
            self.log_ekrani.configure(state="normal")
            saat = datetime.now().strftime("%H:%M:%S")
            self.log_ekrani.insert("end", f"[{saat}] {mesaj}\n")
            self.log_ekrani.see("end")
            self.log_ekrani.configure(state="disabled")
        self.after(0, _yaz)

    # =========================================================================
    # DERİN WEB KAZIMA VE OTOMATİK KATEGORİZASYON (SALT-OKUNUR)
    # =========================================================================
    def baslat_kategorize_kazima(self):
        if self._kazima_aktif:
            return
        hedef_url = self.url_entry.get().strip()
        if not hedef_url.startswith("http"):
            messagebox.showerror("Hata", "Lütfen geçerli bir 'http://' veya 'https://' URL'si girin.", parent=self)
            return

        self._kazima_aktif = True
        self.lbl_status.configure(text="Durum: Sayfa Kategorize Ediliyor...", text_color="#00AAFF")
        threading.Thread(target=self._kategorize_kazi_islem, args=(hedef_url,), daemon=True).start()

    def _kategorize_kazi_islem(self, url):
        self.log_yaz(f"🔍 '{url}' adresine salt-okunur erişim sağlanıyor...")

        try:
            res = self._http_session.get(url, timeout=12)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')

            # 1. Meta Bilgiler
            sayfa_basligi = soup.title.string.strip() if soup.title and soup.title.string else "Başlık Bulunamadı"
            meta_desc = ""
            meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
            if meta_tag and meta_tag.get("content"):
                meta_desc = meta_tag.get("content").strip()

            # 2. Başlık Hiyerarşisi (H1, H2, H3)
            basliklar = []
            for h in soup.find_all(['h1', 'h2', 'h3']):
                metin = h.get_text(strip=True)
                if metin and len(metin) > 2:
                    basliklar.append(f"[{h.name.upper()}] {metin}")

            # 3. Veri Tabloları (Tables)
            tablolar = []
            for idx, table in enumerate(soup.find_all('table')[:10], 1):
                satirlar = []
                for tr in table.find_all('tr')[:25]:
                    hucreler = [td.get_text(strip=True) for td in tr.find_all(['th', 'td'])]
                    if any(hucreler):
                        satirlar.append(" | ".join(hucreler))
                if satirlar:
                    tablolar.append(f"Tablo #{idx}:\n" + "\n".join(satirlar))

            # 4. Dosya / Veri Seti Bağlantıları ve Önemli Linkler
            veri_dosyalari = []
            veri_seti_seen = set()
            diger_linkler = []
            veri_uzantilari = ('.csv', '.json', '.txt', '.pdf', '.xlsx', '.xls', '.xml', '.zip', '.tar.gz', '.doc', '.docx')

            for a in soup.find_all('a', href=True):
                tam_url = urljoin(url, a['href'])
                etiket = a.get_text(strip=True) or os.path.basename(tam_url)
                temiz_alt = tam_url.lower().split('?')[0]
                if any(temiz_alt.endswith(ext) for ext in veri_uzantilari):
                    if tam_url not in veri_seti_seen:
                        veri_seti_seen.add(tam_url)
                        veri_dosyalari.append(f"{etiket} -> {tam_url}")
                elif tam_url.startswith("http") and len(diger_linkler) < 30:
                    diger_linkler.append(f"{etiket[:50]} -> {tam_url}")

            # 5. Önemli Metin / Makale Paragrafları
            paragraflar = []
            for p in soup.find_all('p'):
                p_metin = p.get_text(strip=True)
                if len(p_metin) > 60:
                    paragraflar.append(p_metin)

            # Kategorize Veri Paketi Oluştur
            self.son_kategorize_veri = {
                "kaynak_url": url,
                "kazima_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sayfa_basligi": sayfa_basligi,
                "meta_aciklama": meta_desc,
                "kategoriler": {
                    "baslik_hiyerarsisi": basliklar[:40],
                    "veri_tablolari": tablolar,
                    "indirilebilir_veri_ve_belgeler": veri_dosyalari,
                    "onemli_paragraflar": paragraflar[:35],
                    "sayfa_baglantilari": diger_linkler
                }
            }

            ozet_metin = self._kategorize_veriyi_metne_dok(self.son_kategorize_veri)
            self.log_yaz("✅ KATEGORİZASYON TAMAMLANDI!\n" + "=" * 60 + "\n" + ozet_metin + "\n" + "=" * 60)
            self.after(0, lambda: self.lbl_status.configure(
                text=f"Durum: '{sayfa_basligi[:40]}' başarıyla kategorize edildi.", text_color=BTN_COLOR
            ))

        except Exception as e:
            self.log_yaz(f"❌ Kazıma hatası: {e}")
            self.after(0, lambda: self.lbl_status.configure(text="Durum: Hata oluştu.", text_color="#FF4444"))
        finally:
            self._kazima_aktif = False

    def _kategorize_veriyi_metne_dok(self, paket: dict) -> str:
        kat = paket["kategoriler"]
        rapor = [
            f"📌 KAYNAK URL: {paket['kaynak_url']}",
            f"🕒 TARİH: {paket['kazima_tarihi']}",
            f"🏷️ SAYFA BAŞLIĞI: {paket['sayfa_basligi']}",
            f"📝 META ÖZET: {paket['meta_aciklama'] or 'Yok'}\n",
            f"--- 📂 1. BAŞLIK HİYERARŞİSİ ({len(kat['baslik_hiyerarsisi'])} Adet) ---"
        ]
        rapor.extend(kat['baslik_hiyerarsisi'][:15] or ["Başlık bulunamadı."])

        rapor.append(f"\n--- 📊 2. ÇIKARILAN VERİ TABLOLARI ({len(kat['veri_tablolari'])} Adet) ---")
        rapor.extend(kat['veri_tablolari'][:5] or ["Tablo bulunamadı."])

        rapor.append(f"\n--- 📥 3. TESPİT EDİLEN BELGE VE VERİ DOSYALARI ({len(kat['indirilebilir_veri_ve_belgeler'])} Adet) ---")
        rapor.extend(kat['indirilebilir_veri_ve_belgeler'][:20] or ["İndirilebilir doğrudan veri dosyası bulunamadı."])

        rapor.append(f"\n--- 📖 4. ÖNEMLİ İÇERİK PARAGRAFLARI ({len(kat['onemli_paragraflar'])} Adet) ---")
        rapor.extend([f"• {p}" for p in kat['onemli_paragraflar'][:12]] or ["Uzun paragraf bulunamadı."])

        return "\n".join(rapor)

    def ssd_guvenli_kaydet(self):
        """Kategorize edilen veriyi SSD'de 'scraped_archive' klasörüne ÜZERİNE YAZMADAN ('x' kipi) JSON ve MD olarak saklar."""
        if not self.son_kategorize_veri:
            messagebox.showwarning("Uyarı", "Önce bir web sayfasını '🔍 Sayfayı Kategorize Et & Kazı' butonuyla taramalısınız.", parent=self)
            return

        veri_kopyasi = self.son_kategorize_veri

        def _kaydet_worker():
            arsiv_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraped_archive")
            os.makedirs(arsiv_klasoru, exist_ok=True)

            domain = urlparse(veri_kopyasi["kaynak_url"]).netloc.replace(":", "_").replace(".", "_") or "web"
            zaman = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_yolu = os.path.join(arsiv_klasoru, f"Kategorize_{domain}_{zaman}.json")
            md_yolu = os.path.join(arsiv_klasoru, f"Kategorize_{domain}_{zaman}.md")

            try:
                with open(json_yolu, "x", encoding="utf-8") as f_json:
                    json.dump(veri_kopyasi, f_json, ensure_ascii=False, indent=2)

                md_icerik = self._kategorize_veriyi_metne_dok(veri_kopyasi)
                with open(md_yolu, "x", encoding="utf-8") as f_md:
                    f_md.write(f"# KATEGORİZE WEB KAZIMA RAPORU\n\n{md_icerik}")

                self.log_yaz(f"💾 SSD'ye Güvenle Kaydedildi:\n  -> {json_yolu}\n  -> {md_yolu}")
                self.after(0, lambda: messagebox.showinfo(
                    "SSD Kaydı Başarılı",
                    f"Kategorize edilen veriler hem JSON hem Markdown formatında SSD'ye kaydedildi:\n\n{json_yolu}",
                    parent=self
                ))
            except Exception as e:
                self.after(0, lambda err=e: messagebox.showerror("Kayıt Hatası", f"SSD'ye yazılırken hata oluştu: {err}", parent=self))

        threading.Thread(target=_kaydet_worker, daemon=True).start()

    def kategorize_veriyi_altara_gonder(self):
        """Kazınan kategorize veriyi doğrudan Altar'ın Analiz Sekmesine ve RAG Hafızasına aktarır."""
        if not self.son_kategorize_veri:
            messagebox.showwarning("Uyarı", "Önce bir sayfayı kazıyıp kategorize edin.", parent=self)
            return

        paket = self.son_kategorize_veri
        metin_rapor = self._kategorize_veriyi_metne_dok(paket)

        # Ana uygulamadaki 'Kazınan Veri & Analiz Merkezi' sekmesini hemen güncelle
        if hasattr(self.main_app, "analiz_sekmesine_veri_ekle"):
            self.main_app.analiz_sekmesine_veri_ekle(paket, metin_rapor)

        # Vektörel Hafızaya (ChromaDB) gömme işlemini arayüzü dondurmamak için arka planda yap
        def _rag_kaydet():
            try:
                self.main_app.db_manager.mesaj_kaydet("document", f"KATEGORİZE WEB VERİSİ:\n{metin_rapor}")
            except Exception:
                pass

        threading.Thread(target=_rag_kaydet, daemon=True).start()

        self.log_yaz("🧠 Veri başarıyla Altar '📊 Kazınan Veri & Analiz Merkezi' sekmesine ve RAG hafızasına aktarıldı!")
        messagebox.showinfo(
            "Aktarım Tamamlandı",
            "Kategorize edilen tüm veriler Altar'ın '📊 Kazınan Veri & Analiz Merkezi' sekmesine aktarıldı!",
            parent=self
        )

    # =========================================================================
    # CANLI NASA VERİ SETİ İZLEME DÖNGÜSÜ
    # =========================================================================
    def toggle_tarama(self):
        if not self.taramaya_devam_et:
            hedef_url = self.url_entry.get().strip()
            if not hedef_url.startswith("http"):
                messagebox.showerror("Hata", "Lütfen geçerli bir 'http://' veya 'https://' URL'si girin.", parent=self)
                return

            self.taramaya_devam_et = True
            self.btn_tara.configure(text="🛑 İzlemeyi Durdur", fg_color="#8B0000", hover_color="#5C0000")
            self.lbl_status.configure(text="Durum: Hedef Web Sitesi Sürekli İzleniyor...", text_color=BTN_COLOR)
            self.log_yaz(f"📡 '{hedef_url}' adresi canlı izlemeye alındı. Yeni veri setleri aranıyor...")

            threading.Thread(target=self.web_site_dinleme_dongusu, args=(hedef_url,), daemon=True).start()
        else:
            self.taramaya_devam_et = False
            self.btn_tara.configure(text="📡 Canlı İzle", fg_color=BTN_COLOR, hover_color=BTN_HOVER)
            self.lbl_status.configure(text="Durum: Tarama Durduruldu.", text_color="#778DA9")
            self.log_yaz("🛑 Canlı izleme görevi durduruldu.")

    def web_site_dinleme_dongusu(self, url):
        while self.taramaya_devam_et:
            try:
                res = self._http_session.get(url, timeout=10)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.content, 'html.parser')

                    for a_tag in soup.find_all('a', href=True):
                        link = a_tag['href']
                        temiz_link_yol = link.split('?')[0].split('#')[0]
                        if temiz_link_yol.lower().endswith(('.csv', '.json', '.txt')):
                            tam_link = urljoin(url, link)
                            ham_ad = os.path.basename(urlparse(tam_link).path) or "veri_seti.txt"
                            dosya_adi = "".join(c if c.isalnum() or c in "._-" else "_" for c in ham_ad)

                            if tam_link not in self.bulunan_linkler:
                                self.bulunan_linkler.add(tam_link)
                                self.log_yaz(f"⚠️ YENİ VERİ BULUNDU: {dosya_adi}")
                                self.after(0, lambda l=tam_link, d=dosya_adi: self.kullanici_onayi_ve_indir(l, d))
                else:
                    self.log_yaz(f"Web sitesine erişilemedi. Durum Kodu: {res.status_code}")
            except Exception as e:
                self.log_yaz(f"Tarama hatası: {e}")

            for _ in range(15):
                if not self.taramaya_devam_et:
                    break
                time.sleep(1)

    def kullanici_onayi_ve_indir(self, link, dosya_adi):
        cevap = messagebox.askyesno(
            "Yeni Veri Seti Bulundu!",
            f"Taranan sayfaya yeni bir veri seti eklendi:\n\n'{dosya_adi}'\n\nBu veriyi indirip Altar Çekirdeği ile analize başlayalım mı?",
            parent=self
        )
        if cevap:
            self.log_yaz(f"📥 İndirme başlatılıyor: {dosya_adi}...")
            threading.Thread(target=self.dosyayi_indir_ve_aktar, args=(link, dosya_adi), daemon=True).start()
        else:
            self.log_yaz(f"🚫 İndirme reddedildi: {dosya_adi}")

    def dosyayi_indir_ve_aktar(self, link, dosya_adi):
        kayit_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nasa_datasets")
        os.makedirs(kayit_klasoru, exist_ok=True)

        temiz_ad = "".join(c if c.isalnum() or c in "._-" else "_" for c in os.path.basename(dosya_adi)) or "veri.txt"
        zaman_eki = datetime.now().strftime("%Y%m%d_%H%M%S")
        guvenli_ad = f"{zaman_eki}_{temiz_ad}"
        dosya_yolu = os.path.join(kayit_klasoru, guvenli_ad)

        try:
            parsed = urlparse(link)
            if parsed.scheme.lower() not in ("http", "https"):
                self.log_yaz("❌ Güvenlik Hatası: Yalnızca HTTP ve HTTPS protokolleri desteklenir.")
                return
            if parsed.hostname and parsed.hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254.169.254"):
                self.log_yaz("❌ Güvenlik Uyarısı (SSRF): Yerel veya iç ağ IP adreslerine erişim engellendi.")
                return

            # Akışlı indirme ve DoS/Bellek taşması önleme (50 MB Sınırı)
            max_boyut = 50 * 1024 * 1024
            toplam_okunan = 0
            with self._http_session.get(link, timeout=25, stream=True) as res:
                res.raise_for_status()
                with open(dosya_yolu, "xb") as f:
                    for blok in res.iter_content(chunk_size=65536):
                        if blok:
                            f.write(blok)
                            toplam_okunan += len(blok)
                            if toplam_okunan > max_boyut:
                                raise ValueError("Dosya boyutu 50 MB sınırını aştı (DoS & Bellek Koruma Devrede).")

            self.log_yaz(f"✅ Başarıyla indirildi ({toplam_okunan / 1024:.1f} KB): {dosya_yolu}")
            self.veriyi_ana_koda_isle(dosya_yolu, guvenli_ad)

        except Exception as e:
            if os.path.exists(dosya_yolu):
                try:
                    os.remove(dosya_yolu)
                except Exception:
                    pass
            self.log_yaz(f"❌ İndirme hatası: {e}")

    def veriyi_ana_koda_isle(self, dosya_yolu, dosya_adi):
        self.log_yaz("⚙️ Veri Ana Çekirdeğe aktarılıyor. Lütfen ana pencereyi (Altar) kontrol edin...")
        self.main_app.gecmis.clear()
        self.main_app._belgeyi_isle_ve_kaydet(dosya_yolu)
        time.sleep(1.0)

        sorgu = (
            f"--- DİKKAT: YENİ DENEY/WEB VERİSİ İNDİRİLDİ ({dosya_adi}) ---\n"
            "Vektörel hafızana az önce web tarayıcı modülü tarafından yüklenen bu yeni veriyi analiz et. "
            "Eski analizleri unuttun, KESİNLİKLE sadece bu yeni veriye odaklan.\n"
        )

        self.main_app.update_chat_safe(
            f"\n📡 [VERİ KÖPRÜSÜ]: '{dosya_adi}' modül üzerinden başarıyla indirildi. Analiz başlatılıyor...\n",
            tag="warning_style", final=True
        )

        def _ana_thread_ai_tetikle():
            aktif_motor = self.main_app.motor_var.get()
            secilen_dil = self.main_app.active_lang_var.get()
            if aktif_motor == "Yerel (Ollama)":
                secilen_model = self.main_app.active_model_var.get()
                threading.Thread(
                    target=self.main_app.model_ile_konus, args=(secilen_model, secilen_dil, sorgu), daemon=True
                ).start()
            else:
                secilen_api_modeli = self.main_app.active_api_model_var.get()
                threading.Thread(
                    target=self.main_app.api_ile_konus, args=(secilen_api_modeli, secilen_dil, sorgu), daemon=True
                ).start()

        if hasattr(self.main_app, "_ui_gorevi_ekle"):
            self.main_app._ui_gorevi_ekle(_ana_thread_ai_tetikle)
        else:
            self.after(0, _ana_thread_ai_tetikle)

    def _tam_ekran_yap(self):
        try:
            if self.winfo_exists():
                self.attributes("-fullscreen", True)
                self._tam_ekran_mi = True
                self.lift()
                self.focus_force()
        except Exception:
            pass

    def _tam_ekran_degistir(self, event=None):
        try:
            self._tam_ekran_mi = not getattr(self, "_tam_ekran_mi", False)
            self.attributes("-fullscreen", self._tam_ekran_mi)
        except Exception:
            pass

    def _tam_ekrandan_cik(self, event=None):
        try:
            if getattr(self, "_tam_ekran_mi", False):
                self._tam_ekran_mi = False
                self.attributes("-fullscreen", False)
        except Exception:
            pass

    def on_closing(self):
        self.taramaya_devam_et = False
        try:
            self._http_session.close()
        except Exception:
            pass
        self.destroy()