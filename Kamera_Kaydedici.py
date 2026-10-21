import os
import sys
import time
import queue
import shutil
import ctypes
import tempfile
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
    from PIL import Image
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
KAMERA_KLASORU = os.path.join(_ANA_DIZIN, "Kamera_Kayitlari")
os.makedirs(KAMERA_KLASORU, exist_ok=True)


def _guvenli_cv2_yolu(tam_yol: str) -> str:
    """
    OpenCV C++ katmanının Türkçe karakterli ('E:\\Yazılım\\...' gibi) yollarda
    verdiği 'Can't open file' hatasını önlemek için ASCII uyumlu yol üretir.
    """
    try:
        rel = os.path.relpath(tam_yol)
        if rel.isascii():
            return rel
    except Exception:
        pass

    if os.name == 'nt':
        try:
            hedef = tam_yol if os.path.exists(tam_yol) else os.path.dirname(tam_yol)
            if os.path.exists(hedef):
                buf = ctypes.create_unicode_buffer(512)
                if ctypes.windll.kernel32.GetShortPathNameW(hedef, buf, 512) > 0:
                    aday = buf.value if os.path.exists(tam_yol) else os.path.join(buf.value, os.path.basename(tam_yol))
                    if aday.isascii():
                        return aday
        except Exception:
            pass
    return tam_yol


def _haar_xml_guvenli_yukle():
    """Haar Cascade XML dosyasını Türkçe karakter engeline takılmadan yükler."""
    if not CV2_AVAILABLE:
        return None
    try:
        orijinal_xml = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
        if not os.path.exists(orijinal_xml):
            return None

        cv2_yolu = _guvenli_cv2_yolu(orijinal_xml)
        if not cv2_yolu.isascii():
            gecici_dizin = r"C:\Users\Public" if os.path.exists(r"C:\Users\Public") else tempfile.gettempdir()
            kopya_xml = os.path.join(gecici_dizin, "altar_haarcascade_frontalface.xml")
            if not os.path.exists(kopya_xml):
                shutil.copyfile(orijinal_xml, kopya_xml)
            cv2_yolu = _guvenli_cv2_yolu(kopya_xml)

        cascade = cv2.CascadeClassifier(cv2_yolu)
        return cascade if not cascade.empty() else None
    except Exception:
        return None


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


class GelismisKameraKayitMotoru:
    """
    Kullanıcının kendisini (Webcam + Mikrofon Sesi) sıfır kasma ve
    tam senkronizasyonla (AV-Sync) kaydetmesini sağlayan kamera motoru.
    """
    def __init__(self):
        self.kamera_acik = False
        self.kayit_aktif = False
        self.duraklatildi = False
        self.ayna_modu = True
        self.filtre_modu = "Normal (Renkli)"
        self.yuz_odak_aktif = False

        self.toplam_sure = 0.0
        self.anlik_ses_seviyesi = 0.0
        self.son_kamera_karesi = None

        self.aktif_video_yolu = ""
        self.aktif_ses_yolu = ""
        self.nihai_dosya_yolu = ""

        self._ses_kuyrugu = queue.Queue()
        self._video_kuyrugu = queue.Queue(maxsize=90)
        self._cap = None
        self._face_cascade = _haar_xml_guvenli_yukle()

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

    def kamerayi_baslat(self, kamera_indeksi=0):
        if self.kamera_acik or not CV2_AVAILABLE:
            return
        self.kamera_acik = True

        def _kamera_okuyucu():
            backend = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY
            self._cap = cv2.VideoCapture(kamera_indeksi, backend)
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self._cap.set(cv2.CAP_PROP_FPS, 30)

            son_zaman = time.perf_counter()
            kare_sayaci = 0
            son_yuzler = []

            try:
                while self.kamera_acik and self._cap.isOpened():
                    ret, frame = self._cap.read()
                    if not ret:
                        time.sleep(0.02)
                        continue

                    simdi = time.perf_counter()
                    if self.kayit_aktif and not self.duraklatildi:
                        self.toplam_sure += (simdi - son_zaman)
                    son_zaman = simdi

                    if self.ayna_modu:
                        frame = cv2.flip(frame, 1)

                    if self.filtre_modu == "Siber Gece Görüşü":
                        gri = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        frame = cv2.applyColorMap(gri, cv2.COLORMAP_WINTER)
                    elif self.filtre_modu == "Sinematik Siyah-Beyaz":
                        gri = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        frame = cv2.cvtColor(gri, cv2.COLOR_GRAY2BGR)

                    if self.yuz_odak_aktif and self._face_cascade is not None:
                        kare_sayaci += 1
                        if kare_sayaci % 5 == 0:
                            kucuk_gri = cv2.cvtColor(cv2.resize(frame, (320, 180)), cv2.COLOR_BGR2GRAY)
                            algilanan = self._face_cascade.detectMultiScale(kucuk_gri, 1.2, 4)
                            olcek_x = frame.shape[1] / 320.0
                            olcek_y = frame.shape[0] / 180.0
                            son_yuzler = [
                                (int(x * olcek_x), int(y * olcek_y), int(w * olcek_x), int(h * olcek_y))
                                for (x, y, w, h) in algilanan
                            ]
                        for (fx, fy, fw, fh) in son_yuzler:
                            cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), (0, 255, 204), 2)
                            cv2.putText(frame, "HEDEF KILITLI", (fx, max(20, fy - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 204), 1)

                    if self.kayit_aktif:
                        durum_yazisi = "DURAKLATILDI" if self.duraklatildi else "REC"
                        renk_osd = (0, 215, 255) if self.duraklatildi else (0, 0, 255)
                        cv2.circle(frame, (28, 28), 8, renk_osd, -1)
                        cv2.putText(
                            frame, f"{durum_yazisi} | {datetime.now().strftime('%H:%M:%S')}",
                            (44, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA
                        )
                        if not self.duraklatildi and not self._video_kuyrugu.full():
                            self._video_kuyrugu.put_nowait(frame.copy())

                    self.son_kamera_karesi = frame
                    time.sleep(0.015)
            finally:
                if self._cap is not None:
                    self._cap.release()
                self.kamera_acik = False

        threading.Thread(target=_kamera_okuyucu, daemon=True).start()

    def fotograf_cek(self) -> str:
        if self.son_kamera_karesi is None or not CV2_AVAILABLE:
            return ""
        zaman = datetime.now().strftime("%Y%m%d_%H%M%S")
        foto_yolu = os.path.join(KAMERA_KLASORU, f"Altar_Foto_{zaman}.png")
        try:
            basarili, tampon = cv2.imencode(".png", self.son_kamera_karesi)
            if basarili:
                tampon.tofile(foto_yolu)
                return foto_yolu
        except Exception:
            pass
        return ""

    def kaydi_baslat(self, ses_kaydet=True, bitti_callback=None) -> str:
        if self.kayit_aktif:
            return self.nihai_dosya_yolu
        if not self.kamera_acik:
            self.kamerayi_baslat(0)
            time.sleep(0.4)

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

        zaman = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.aktif_video_yolu = os.path.join(KAMERA_KLASORU, f"Altar_Kamera_Ham_{zaman}.mp4")
        self.aktif_ses_yolu = os.path.join(KAMERA_KLASORU, f"Altar_Kamera_Ses_{zaman}.wav")
        self.nihai_dosya_yolu = os.path.join(KAMERA_KLASORU, f"Altar_Kamera_Kaydi_{zaman}.mp4")

        self.kayit_aktif = True
        self.duraklatildi = False
        self.toplam_sure = 0.0

        ses_thread = None
        if ses_kaydet and AUDIO_AVAILABLE:
            def _ses_yaz():
                for hiz in (48000, 44100, 16000):
                    try:
                        with sf.SoundFile(self.aktif_ses_yolu, mode='w', samplerate=hiz, channels=1) as sf_file:
                            with sd.InputStream(samplerate=hiz, channels=1, callback=self._ses_callback):
                                while self.kayit_aktif:
                                    try:
                                        blok = self._ses_kuyrugu.get(timeout=0.15)
                                        sf_file.write(blok)
                                        while not self._ses_kuyrugu.empty():
                                            sf_file.write(self._ses_kuyrugu.get_nowait())
                                    except queue.Empty:
                                        continue
                        break
                    except Exception:
                        if not self.kayit_aktif:
                            break
                        continue

            ses_thread = threading.Thread(target=_ses_yaz, daemon=True)
            ses_thread.start()

        def _video_yaz_ve_birlestir():
            w, h = 1280, 720
            if self.son_kamera_karesi is not None:
                h, w = self.son_kamera_karesi.shape[:2]

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            guvenli_video_yolu = _guvenli_cv2_yolu(self.aktif_video_yolu)
            writer = cv2.VideoWriter(guvenli_video_yolu, fourcc, 24.0, (w, h))
            try:
                while self.kayit_aktif or not self._video_kuyrugu.empty():
                    try:
                        kare = self._video_kuyrugu.get(timeout=0.2)
                        if kare.shape[1] != w or kare.shape[0] != h:
                            kare = cv2.resize(kare, (w, h))
                        writer.write(kare)
                    except queue.Empty:
                        continue
            finally:
                writer.release()
                if ses_thread:
                    ses_thread.join(timeout=2.0)

                son_dosya = self._ses_ve_videoyu_birlestir(ses_kaydet)
                if bitti_callback:
                    bitti_callback(True, son_dosya)

        threading.Thread(target=_video_yaz_ve_birlestir, daemon=True).start()
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

    def kamerayi_kapat(self):
        self.kayit_aktif = False
        self.kamera_acik = False


if CTK_AVAILABLE:
    class AltarKameraStüdyosuPenceresi(ctk.CTkToplevel):
        """Canlı kamera önizleme, filtre, fotoğraf çekme ve sesli video kayıt stüdyosu."""
        def __init__(self, parent, motor: GelismisKameraKayitMotoru = None):
            super().__init__(parent)
            self.title("📷 Altar Kamera, Özçekim ve Görüntülü Kayıt Stüdyosu")
            self.geometry("740x560")
            self.resizable(False, False)
            self.transient(parent)
            self.configure(fg_color="#090D16")
            self.protocol("WM_DELETE_WINDOW", self.pencereyi_kapat)

            self.motor = motor if motor else GelismisKameraKayitMotoru()
            self.motor.kamerayi_baslat(0)

            self._arayuz_olustur()
            self._arsivi_yenile()
            self._canli_kamera_dongusu()

        def _arayuz_olustur(self):
            ctk.CTkLabel(
                self, text="📷 ALTAR AKILLI KAMERA VE GÖRÜNTÜLÜ KAYIT STÜDYOSU",
                font=ctk.CTkFont(family="Consolas", size=15, weight="bold"), text_color="#00FFCC"
            ).pack(pady=(10, 4))

            ust_bar = ctk.CTkFrame(self, fg_color="#121824", corner_radius=8)
            ust_bar.pack(fill="x", padx=14, pady=4)

            ctk.CTkLabel(ust_bar, text="Filtre:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(10, 4), pady=6)
            self.combo_filtre = ctk.CTkOptionMenu(
                ust_bar,
                values=["Normal (Renkli)", "Siber Gece Görüşü", "Sinematik Siyah-Beyaz"],
                width=165,
                command=lambda v: setattr(self.motor, "filtre_modu", v)
            )
            self.combo_filtre.pack(side="left", padx=4, pady=6)

            self.ayna_var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(
                ust_bar, text="Ayna Modu", variable=self.ayna_var, width=95,
                command=lambda: setattr(self.motor, "ayna_modu", self.ayna_var.get())
            ).pack(side="left", padx=8, pady=6)

            self.yuz_var = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(
                ust_bar, text="Yüz Odak Radarı", variable=self.yuz_var, width=120, text_color="#00FFCC",
                command=lambda: setattr(self.motor, "yuz_odak_aktif", self.yuz_var.get())
            ).pack(side="left", padx=6, pady=6)

            self.ses_var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(
                ust_bar, text="Sesli Kayıt", variable=self.ses_var, width=90, text_color="#00FF88"
            ).pack(side="right", padx=10, pady=6)

            self.kamera_etiketi = ctk.CTkLabel(
                self, text="📷 Kamera Başlatılıyor...",
                fg_color="#05080F", corner_radius=8, width=680, height=290,
                font=ctk.CTkFont(family="Consolas", size=13), text_color="#00FF88"
            )
            self.kamera_etiketi.pack(padx=14, pady=6)

            sayac_bar = ctk.CTkFrame(self, fg_color="#05080F", corner_radius=8)
            sayac_bar.pack(fill="x", padx=14, pady=4)

            self.lbl_durum = ctk.CTkLabel(
                sayac_bar, text="⏺️ 00:00:00 | Kamera Aktif",
                font=ctk.CTkFont(family="Consolas", size=15, weight="bold"), text_color="#00FF88"
            )
            self.lbl_durum.pack(side="left", padx=12, pady=6)

            self.vu_bar = ctk.CTkProgressBar(sayac_bar, width=280, height=12, progress_color="#00FF88")
            self.vu_bar.pack(side="right", padx=12, pady=6)
            self.vu_bar.set(0.0)

            btn_bar = ctk.CTkFrame(self, fg_color="transparent")
            btn_bar.pack(fill="x", padx=14, pady=4)

            self.btn_baslat = ctk.CTkButton(
                btn_bar, text="🔴 Kamera Kaydını Başlat", height=32,
                fg_color="#C62828", hover_color="#8E0000", font=ctk.CTkFont(weight="bold"),
                command=self.kayit_baslat_tetikle
            )
            self.btn_baslat.pack(side="left", fill="x", expand=True, padx=3)

            self.btn_duraklat = ctk.CTkButton(
                btn_bar, text="⏸️ Duraklat", height=32,
                fg_color="#B85C00", state="disabled", command=self.duraklat_tetikle
            )
            self.btn_duraklat.pack(side="left", fill="x", expand=True, padx=3)

            self.btn_durdur = ctk.CTkButton(
                btn_bar, text="⏹️ Kaydı Bitir", height=32,
                fg_color="#2E7D32", state="disabled", command=self.durdur_tetikle
            )
            self.btn_durdur.pack(side="left", fill="x", expand=True, padx=3)

            ctk.CTkButton(
                btn_bar, text="📸 Fotoğraf Çek", height=32, width=130,
                fg_color="#4B0082", hover_color="#2b004d", command=self.foto_cek_tetikle
            ).pack(side="left", padx=3)

            arsiv_bar = ctk.CTkFrame(self, fg_color="#121824", corner_radius=8)
            arsiv_bar.pack(fill="x", padx=14, pady=(4, 10))

            ctk.CTkLabel(arsiv_bar, text="📂 Kamera Arşivi:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=8, pady=6)
            self.combo_arsiv = ctk.CTkOptionMenu(arsiv_bar, values=["Kayıt Yok"], width=300)
            self.combo_arsiv.pack(side="left", padx=6, pady=6)

            ctk.CTkButton(
                arsiv_bar, text="▶️ Aç / İzle", width=105, height=26,
                fg_color="#1f538d", command=self.secili_kaydi_ac
            ).pack(side="left", padx=4, pady=6)

            ctk.CTkButton(
                arsiv_bar, text="📁 Klasörü Aç", width=105, height=26,
                fg_color="#008080", command=lambda: os.startfile(KAMERA_KLASORU) if os.name == 'nt' else None
            ).pack(side="right", padx=8, pady=6)

        def kayit_baslat_tetikle(self):
            self.motor.kaydi_baslat(ses_kaydet=self.ses_var.get(), bitti_callback=self._bitti_cb)
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
            self.lbl_durum.configure(text="⏳ Video ve Ses Birleştiriliyor...", text_color="#FFD700")
            self.motor.kaydi_durdur()
            self.btn_baslat.configure(state="normal")
            self.btn_duraklat.configure(state="disabled", text="⏸️ Duraklat", fg_color="#B85C00")
            self.btn_durdur.configure(state="disabled")

        def foto_cek_tetikle(self):
            yol = self.motor.fotograf_cek()
            if yol:
                self._arsivi_yenile()
                self.lbl_durum.configure(text=f"📸 Fotoğraf Kaydedildi: {os.path.basename(yol)}", text_color="#00FFCC")

        def _bitti_cb(self, basarili: bool, dosya_yolu: str):
            def _ui():
                if not self.winfo_exists():
                    return
                self._arsivi_yenile()
                self.lbl_durum.configure(text=f"✅ Kaydedildi: {os.path.basename(dosya_yolu)}", text_color="#00FF88")
            self.after(0, _ui)

        def _arsivi_yenile(self):
            dosyalar = sorted(
                [f for f in os.listdir(KAMERA_KLASORU) if f.lower().endswith((".mp4", ".png", ".jpg", ".wav"))],
                reverse=True
            )
            if dosyalar:
                self.combo_arsiv.configure(values=dosyalar)
                self.combo_arsiv.set(dosyalar[0])

        def secili_kaydi_ac(self):
            secili = self.combo_arsiv.get()
            tam_yol = os.path.join(KAMERA_KLASORU, secili)
            if os.path.exists(tam_yol) and os.name == 'nt':
                os.startfile(tam_yol)

        def _canli_kamera_dongusu(self):
            if not self.winfo_exists():
                return

            if self.motor.son_kamera_karesi is not None and PIL_AVAILABLE:
                try:
                    kucuk = cv2.resize(self.motor.son_kamera_karesi, (520, 275))
                    rgb = cv2.cvtColor(kucuk, cv2.COLOR_BGR2RGB)
                    pil_im = Image.fromarray(rgb)
                    ctk_im = ctk.CTkImage(light_image=pil_im, dark_image=pil_im, size=(520, 275))
                    self.kamera_etiketi.configure(image=ctk_im, text="")
                except Exception:
                    pass

            if self.motor.kayit_aktif:
                sn = int(self.motor.toplam_sure)
                sa, kalan = divmod(sn, 3600)
                dk, saniye = divmod(kalan, 60)
                durum = "DURAKLATILDI" if self.motor.duraklatildi else "KAMERA KAYITTA"
                self.lbl_durum.configure(
                    text=f"🔴 {sa:02d}:{dk:02d}:{saniye:02d} | {durum}",
                    text_color="#FF4444" if not self.motor.duraklatildi else "#FFD700"
                )
                self.vu_bar.set(self.motor.anlik_ses_seviyesi)
            else:
                self.vu_bar.set(0.0)

            self.after(45, self._canli_kamera_dongusu)

        def pencereyi_kapat(self):
            self.motor.kamerayi_kapat()
            self.destroy()