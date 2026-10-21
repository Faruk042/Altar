import os
import sys
import time
import queue
import shutil
import ctypes
import subprocess
import threading
from datetime import datetime
import numpy as np

os.environ["OPENCV_LOG_LEVEL"] = "OFF"

try:
    import cv2
    try:
        cv2.setLogLevel(0)
    except Exception:
        pass
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

try:
    from PIL import Image, ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

try:
    import customtkinter as ctk
    from tkinter import messagebox
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
_ANA_DIZIN = os.path.dirname(os.path.abspath(__file__))
VIDEO_KLASORU = os.path.join(_ANA_DIZIN, "Video_Kayitlari")
os.makedirs(VIDEO_KLASORU, exist_ok=True)


def _guvenli_cv2_yolu(tam_yol: str) -> str:
    """OpenCV VideoWriter için Türkçe karakter içermeyen göreceli veya kısa (8.3) yol döndürür."""
    try:
        rel = os.path.relpath(tam_yol)
        if rel.isascii():
            return rel
    except Exception:
        pass

    if os.name == 'nt':
        try:
            dizin = os.path.dirname(tam_yol)
            dosya_adi = os.path.basename(tam_yol)
            if os.path.exists(dizin):
                buf = ctypes.create_unicode_buffer(512)
                if ctypes.windll.kernel32.GetShortPathNameW(dizin, buf, 512) > 0:
                    aday = os.path.join(buf.value, dosya_adi)
                    if aday.isascii():
                        return aday
        except Exception:
            pass
    return tam_yol


def _ffmpeg_yolu_bul() -> str:
    yerel_ffmpeg = os.path.join(_ANA_DIZIN, "ffmpeg.exe")
    if os.path.exists(yerel_ffmpeg):
        return yerel_ffmpeg
    yol = shutil.which("ffmpeg")
    if yol:
        return yol
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return ""


class GelismisEkranVideoMotoru:
    """
    Sıfır kasma (Zero-Lag) mimarisiyle bilgisayar ekranını ve mikrofon sesini
    eşzamanlı (AV-Sync) olarak kaydeden çoklu iş parçacıklı motor.
    """
    def __init__(self):
        self.kayit_aktif = False
        self.duraklatildi = False
        self.toplam_sure = 0.0
        self.anlik_ses_seviyesi = 0.0
        self.aktif_video_yolu = ""
        self.aktif_ses_yolu = ""
        self.nihai_dosya_yolu = ""
        self.son_onizleme_karesi = None

        self._ses_kuyrugu = queue.Queue()
        self._video_kuyrugu = queue.Queue(maxsize=90)

    def _ses_callback(self, indata, frames, time_info, status):
        if not self.kayit_aktif or self.duraklatildi:
            self.anlik_ses_seviyesi = 0.0
            return
        self._ses_kuyrugu.put_nowait(indata.copy())
        try:
            rms = float(np.sqrt(np.mean(np.square(indata))))
            self.anlik_ses_seviyesi = min(1.0, rms * 8.5)
        except Exception:
            self.anlik_ses_seviyesi = 0.0

    def kaydi_baslat(self, cozunurluk_modu="1080p (Full HD)", fps=20, ses_kaydet=True, bitti_callback=None) -> str:
        if self.kayit_aktif:
            return self.aktif_video_yolu

        while not self._ses_kuyrugu.empty():
            try:
                self._ses_kuyrugu.get_nowait()
            except queue.Empty:
                break
        while not self._video_kuyrugu.empty():
            try:
                self._video_kuyrugu.get_nowait()
            except queue.Empty:
                break

        zaman_etiketi = datetime.now().strftime("%Y%m%d_%H%M%S")
        ham_video_adi = f"Altar_Ekran_Ham_{zaman_etiketi}.mp4"
        ses_adi = f"Altar_Ekran_Ses_{zaman_etiketi}.wav"
        birlesik_ad = f"Altar_Ekran_Kaydi_{zaman_etiketi}.mp4"

        self.aktif_video_yolu = os.path.join(VIDEO_KLASORU, ham_video_adi)
        self.aktif_ses_yolu = os.path.join(VIDEO_KLASORU, ses_adi)
        self.nihai_dosya_yolu = os.path.join(VIDEO_KLASORU, birlesik_ad)

        self.kayit_aktif = True
        self.duraklatildi = False
        self.toplam_sure = 0.0

        if "720p" in cozunurluk_modu:
            hedef_w, hedef_h = 1280, 720
        else:
            hedef_w, hedef_h = 1920, 1080

        ses_thread = None
        if ses_kaydet and AUDIO_AVAILABLE:
            def _ses_yazici():
                for hiz in (48000, 44100, 16000):
                    try:
                        with sf.SoundFile(self.aktif_ses_yolu, mode='w', samplerate=hiz, channels=1) as s_file:
                            with sd.InputStream(samplerate=hiz, channels=1, callback=self._ses_callback):
                                while self.kayit_aktif:
                                    try:
                                        blok = self._ses_kuyrugu.get(timeout=0.15)
                                        s_file.write(blok)
                                        while not self._ses_kuyrugu.empty():
                                            s_file.write(self._ses_kuyrugu.get_nowait())
                                    except queue.Empty:
                                        continue
                        break
                    except Exception:
                        if not self.kayit_aktif:
                            break
                        continue

            ses_thread = threading.Thread(target=_ses_yazici, daemon=True)
            ses_thread.start()

        def _video_yazici():
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            guvenli_yol = _guvenli_cv2_yolu(self.aktif_video_yolu)
            writer = cv2.VideoWriter(guvenli_yol, fourcc, float(fps), (hedef_w, hedef_h))
            try:
                while self.kayit_aktif or not self._video_kuyrugu.empty():
                    try:
                        bgr_kare = self._video_kuyrugu.get(timeout=0.2)
                        writer.write(bgr_kare)
                    except queue.Empty:
                        continue
            finally:
                writer.release()

        yazici_thread = threading.Thread(target=_video_yazici, daemon=True)
        yazici_thread.start()

        def _ekran_yakalayici():
            kare_suresi = 1.0 / float(fps)
            son_zaman = time.perf_counter()
            sct = mss.mss() if MSS_AVAILABLE else None
            monitor = sct.monitors[1] if (sct and len(sct.monitors) > 1) else (sct.monitors[0] if sct else None)

            try:
                while self.kayit_aktif:
                    dongu_basi = time.perf_counter()
                    if self.duraklatildi:
                        son_zaman = dongu_basi
                        time.sleep(0.05)
                        continue

                    self.toplam_sure += (dongu_basi - son_zaman)
                    son_zaman = dongu_basi

                    if sct and monitor:
                        ham = np.array(sct.grab(monitor))
                        bgr = cv2.cvtColor(ham, cv2.COLOR_BGRA2BGR)
                    else:
                        pil_img = ImageGrab.grab()
                        bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

                    if bgr.shape[1] != hedef_w or bgr.shape[0] != hedef_h:
                        bgr = cv2.resize(bgr, (hedef_w, hedef_h), interpolation=cv2.INTER_LINEAR)

                    zaman_metni = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                    cv2.putText(
                        bgr, f"ALTAR REC | {zaman_metni}", (hedef_w - 360, hedef_h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 136), 2, cv2.LINE_AA
                    )

                    self.son_onizleme_karesi = bgr

                    if not self._video_kuyrugu.full():
                        self._video_kuyrugu.put_nowait(bgr)

                    gecen = time.perf_counter() - dongu_basi
                    uyku = kare_suresi - gecen
                    if uyku > 0:
                        time.sleep(uyku)
            finally:
                if sct:
                    try:
                        sct.close()
                    except Exception:
                        pass

                yazici_thread.join(timeout=5.0)
                if ses_thread:
                    ses_thread.join(timeout=2.0)

                son_dosya = self._ses_ve_videoyu_birlestir(ses_kaydet)
                if bitti_callback:
                    bitti_callback(True, son_dosya)

        threading.Thread(target=_ekran_yakalayici, daemon=True).start()
        return self.nihai_dosya_yolu

    def _ses_ve_videoyu_birlestir(self, ses_kaydedildi: bool) -> str:
        ffmpeg_exe = _ffmpeg_yolu_bul()
        if ses_kaydedildi and os.path.exists(self.aktif_ses_yolu) and os.path.exists(self.aktif_video_yolu) and ffmpeg_exe:
            try:
                komut = [
                    ffmpeg_exe, "-y",
                    "-i", self.aktif_video_yolu,
                    "-i", self.aktif_ses_yolu,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    self.nihai_dosya_yolu
                ]
                sonuc = subprocess.run(
                    komut, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=_NO_WINDOW, timeout=30
                )
                if sonuc.returncode == 0 and os.path.exists(self.nihai_dosya_yolu):
                    try:
                        os.remove(self.aktif_video_yolu)
                        os.remove(self.aktif_ses_yolu)
                    except Exception:
                        pass
                    return self.nihai_dosya_yolu
            except Exception:
                pass

        if os.path.exists(self.aktif_video_yolu):
            try:
                os.replace(self.aktif_video_yolu, self.nihai_dosya_yolu)
                return self.nihai_dosya_yolu
            except Exception:
                return self.aktif_video_yolu
        return self.aktif_video_yolu

    def duraklat_devam_et(self) -> bool:
        if not self.kayit_aktif:
            return False
        self.duraklatildi = not self.duraklatildi
        return self.duraklatildi

    def kaydi_durdur(self) -> str:
        self.kayit_aktif = False
        self.duraklatildi = False
        self.anlik_ses_seviyesi = 0.0
        return self.nihai_dosya_yolu


if CTK_AVAILABLE:
    class AltarVideoKaydediciPenceresi(ctk.CTkToplevel):
        """Ekran + Ses eşzamanlı kayıt stüdyosu arayüzü."""
        def __init__(self, parent, motor: GelismisEkranVideoMotoru = None):
            super().__init__(parent)
            self.title("🎬 Altar Ekran & Ses Eşzamanlı Video Kayıt Stüdyosu")
            self.geometry("700x520")
            self.resizable(False, False)
            self.transient(parent)
            self.configure(fg_color="#090D16")

            self.motor = motor if motor else GelismisEkranVideoMotoru()
            self._son_sure_str = ""

            self._arayuz_olustur()
            self._arsivi_yenile()
            self._canli_panel_dongusu()

        def _arayuz_olustur(self):
            ctk.CTkLabel(
                self, text="🎬 ALTAR EKRAN & MİKROFON EŞZAMANLI VİDEO STÜDYOSU",
                font=ctk.CTkFont(family="Consolas", size=15, weight="bold"), text_color="#00FFCC"
            ).pack(pady=(10, 4))

            ayar_bar = ctk.CTkFrame(self, fg_color="#121824", corner_radius=8)
            ayar_bar.pack(fill="x", padx=14, pady=4)

            ctk.CTkLabel(ayar_bar, text="Çözünürlük:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(10, 4), pady=6)
            self.combo_coz = ctk.CTkOptionMenu(ayar_bar, values=["1080p (Full HD)", "720p (HD - Hızlı)"], width=155)
            self.combo_coz.pack(side="left", padx=4, pady=6)

            ctk.CTkLabel(ayar_bar, text="FPS:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(10, 4), pady=6)
            self.combo_fps = ctk.CTkOptionMenu(ayar_bar, values=["20", "24", "30", "15"], width=75)
            self.combo_fps.pack(side="left", padx=4, pady=6)

            self.ses_dahil_var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(
                ayar_bar, text="Mikrofon Sesini Eşzamanlı Kaydet",
                variable=self.ses_dahil_var, text_color="#00FF88"
            ).pack(side="right", padx=12, pady=6)

            self.onizleme_kutu = ctk.CTkLabel(
                self, text="🖥️ Canlı Ekran Önizlemesi\n(Kayıt başladığında burada düşük CPU'lu önizleme görünür)",
                fg_color="#05080F", corner_radius=8, width=660, height=230, text_color="#778DA9",
                font=ctk.CTkFont(family="Consolas", size=12)
            )
            self.onizleme_kutu.pack(padx=14, pady=6)

            sayac_bar = ctk.CTkFrame(self, fg_color="#05080F", corner_radius=8)
            sayac_bar.pack(fill="x", padx=14, pady=4)

            self.lbl_sure = ctk.CTkLabel(
                sayac_bar, text="⏺️ 00:00:00 | Durum: Hazır",
                font=ctk.CTkFont(family="Consolas", size=16, weight="bold"), text_color="#00FF88"
            )
            self.lbl_sure.pack(side="left", padx=12, pady=6)

            self.vu_bar = ctk.CTkProgressBar(sayac_bar, width=280, height=12, progress_color="#00FF88")
            self.vu_bar.pack(side="right", padx=12, pady=6)
            self.vu_bar.set(0.0)

            btn_bar = ctk.CTkFrame(self, fg_color="transparent")
            btn_bar.pack(fill="x", padx=14, pady=4)

            self.btn_baslat = ctk.CTkButton(
                btn_bar, text="🔴 Video Kaydını Başlat", height=32,
                fg_color="#C62828", hover_color="#8E0000", font=ctk.CTkFont(weight="bold"),
                command=self.baslat_tetikle
            )
            self.btn_baslat.pack(side="left", fill="x", expand=True, padx=3)

            self.btn_duraklat = ctk.CTkButton(
                btn_bar, text="⏸️ Duraklat", height=32,
                fg_color="#B85C00", state="disabled", command=self.duraklat_tetikle
            )
            self.btn_duraklat.pack(side="left", fill="x", expand=True, padx=3)

            self.btn_durdur = ctk.CTkButton(
                btn_bar, text="⏹️ Bitir & Birleştir", height=32,
                fg_color="#2E7D32", state="disabled", command=self.durdur_tetikle
            )
            self.btn_durdur.pack(side="left", fill="x", expand=True, padx=3)

            arsiv_bar = ctk.CTkFrame(self, fg_color="#121824", corner_radius=8)
            arsiv_bar.pack(fill="x", padx=14, pady=(4, 10))

            ctk.CTkLabel(arsiv_bar, text="📂 Videolar:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=8, pady=6)
            self.combo_videolar = ctk.CTkOptionMenu(arsiv_bar, values=["Kayıt Yok"], width=310)
            self.combo_videolar.pack(side="left", padx=6, pady=6)

            ctk.CTkButton(
                arsiv_bar, text="▶️ Videoyu Aç", width=110, height=26,
                fg_color="#1f538d", command=self.secili_videoyu_ac
            ).pack(side="left", padx=4, pady=6)

            ctk.CTkButton(
                arsiv_bar, text="📁 Klasörü Aç", width=105, height=26,
                fg_color="#008080", command=lambda: os.startfile(VIDEO_KLASORU) if os.name == 'nt' else None
            ).pack(side="right", padx=8, pady=6)

        def baslat_tetikle(self):
            if not CV2_AVAILABLE:
                messagebox.showerror("Eksik Kütüphane", "Video kaydı için 'pip install opencv-python' kurmalısınız.", parent=self)
                return
            coz = self.combo_coz.get()
            fps = int(self.combo_fps.get())
            ses = self.ses_dahil_var.get()

            self.motor.kaydi_baslat(cozunurluk_modu=coz, fps=fps, ses_kaydet=ses, bitti_callback=self._bitti_cb)
            self.btn_baslat.configure(state="disabled")
            self.btn_duraklat.configure(state="normal")
            self.btn_durdur.configure(state="normal")

        def duraklat_tetikle(self):
            d = self.motor.duraklat_devam_et()
            self.btn_duraklat.configure(
                text="▶️ Devam Et" if d else "⏸️ Duraklat",
                fg_color="#00A86B" if d else "#B85C00"
            )

        def durdur_tetikle(self):
            self.lbl_sure.configure(text="⏳ Ses ve Görüntü Birleştiriliyor...", text_color="#FFD700")
            self.motor.kaydi_durdur()
            self.btn_baslat.configure(state="normal")
            self.btn_duraklat.configure(state="disabled", text="⏸️ Duraklat", fg_color="#B85C00")
            self.btn_durdur.configure(state="disabled")

        def _bitti_cb(self, basarili: bool, dosya_yolu: str):
            def _ui():
                if not self.winfo_exists():
                    return
                self._arsivi_yenile()
                self.lbl_sure.configure(text=f"✅ Kaydedildi: {os.path.basename(dosya_yolu)}", text_color="#00FF88")
            self.after(0, _ui)

        def _arsivi_yenile(self):
            dosyalar = sorted(
                [f for f in os.listdir(VIDEO_KLASORU) if f.lower().endswith((".mp4", ".avi", ".wav"))],
                reverse=True
            )
            if dosyalar:
                self.combo_videolar.configure(values=dosyalar)
                self.combo_videolar.set(dosyalar[0])

        def secili_videoyu_ac(self):
            secili = self.combo_videolar.get()
            tam_yol = os.path.join(VIDEO_KLASORU, secili)
            if os.path.exists(tam_yol):
                try:
                    from altar_video_oynatici import sinematik_video_oynat
                    sinematik_video_oynat(tam_yol, parent=self)
                    return
                except Exception:
                    pass
                if os.name == 'nt':
                    os.startfile(tam_yol)

        def _canli_panel_dongusu(self):
            if not self.winfo_exists():
                return
            if self.motor.kayit_aktif:
                sn = int(self.motor.toplam_sure)
                sa, kalan = divmod(sn, 3600)
                dk, saniye = divmod(kalan, 60)
                durum = "DURAKLATILDI" if self.motor.duraklatildi else "KAYITTA (EKRAN+SES)"
                yeni_str = f"🔴 {sa:02d}:{dk:02d}:{saniye:02d} | {durum}"
                if yeni_str != self._son_sure_str:
                    self._son_sure_str = yeni_str
                    self.lbl_sure.configure(text=yeni_str, text_color="#FF4444" if not self.motor.duraklatildi else "#FFD700")
                self.vu_bar.set(self.motor.anlik_ses_seviyesi)

                if self.motor.son_onizleme_karesi is not None and PIL_AVAILABLE:
                    try:
                        kucuk = cv2.resize(self.motor.son_onizleme_karesi, (480, 215))
                        rgb = cv2.cvtColor(kucuk, cv2.COLOR_BGR2RGB)
                        pil_im = Image.fromarray(rgb)
                        ctk_im = ctk.CTkImage(light_image=pil_im, dark_image=pil_im, size=(480, 215))
                        self.onizleme_kutu.configure(image=ctk_im, text="")
                    except Exception:
                        pass
            else:
                self.vu_bar.set(0.0)

            self.after(180, self._canli_panel_dongusu)