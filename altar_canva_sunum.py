# -*- coding: utf-8 -*-
"""
================================================================================
ALTAR CANVA SLAYT & SUNUM STÜDYOSU (PROFESYONEL SUNUM VE TASARIM MERKEZİ)
================================================================================
* Canva & PowerPoint tarzı modern, kapsamlı ve etkileşimli sunum hazırlama stüdyosu.
* 16:9 Geniş Ekran Tasarım Tuvali (Drag & Drop metinler, kartlar, şekiller, görseller).
* Canva Tarzı Hazır Şablonlar:
  - Başlık & Giriş Slaytı
  - Gündem & İçindekiler
  - 3'lü Özellik & Hizmet Tanıtımı (Glassmorphism Kartlar)
  - Metrik & İstatistik KPI Kartları
  - Karşılaştırma & Analiz Tablosu
  - Sonuç & Teşekkür Slaytı
* Arka Plan Temaları: Kozmik Siber, Zümrüt Doğa, Matrix Synthwave, Minimalist Açık.
* Tam Ekran Canlı Sunum Modu (F5) ve Slaytlar Arası Klavye Geçişi (← / → / Space / ESC).
* Proje Kaydetme (.altarsunumu / JSON) ve Çok Sayfalı PDF / PNG Olarak Dışa Aktarma.
* Altar Belge için 60 FPS Sinematik Açılış Animasyon Penceresi.
================================================================================
"""

import os
import sys
import json
import time
import math
import random
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QSplitter,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsTextItem,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPixmapItem,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QComboBox,
    QSpinBox, QColorDialog, QFileDialog, QMessageBox, QFrame,
    QToolBar, QMenu, QInputDialog, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import (
    QColor, QFont, QPen, QBrush, QPainter, QLinearGradient, QRadialGradient,
    QPainterPath, QPixmap, QImage, QTransform, QKeySequence, QAction, QIcon
)
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal

# Windows API Entegrasyonu (Ön Plan Odaklanması)
if os.name == "nt":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass


CANVAS_W = 1280
CANVAS_H = 720


# ==============================================================================
# SİNEMATİK AÇILIŞ ANİMASYON PENCERESİ (ALTAR BELGE & CANVA STÜDYOSU)
# ==============================================================================
class AltarSinematikAcilisPenceresi(QWidget):
    """Altar Belge açılırken 60 FPS çalışan sinematik doğa/siber açılış sahnesi."""
    tamamlandi = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Tam ekran boyutu
        screen = self.screen() or (self.window().screen() if self.window() else None)
        if screen:
            geom = screen.geometry()
            self.setGeometry(geom)
            self.ekran_g = geom.width()
            self.ekran_y = geom.height()
        else:
            self.ekran_g, self.ekran_y = 1920, 1080
            self.setGeometry(0, 0, 1920, 1080)

        self.adim = 0
        self.toplam_adim = 42
        self.parcaciklar = [
            {
                "x": self.ekran_g / 2 + math.cos(i) * (i * 14),
                "y": self.ekran_y / 2 + math.sin(i) * (i * 14),
                "vx": math.cos(i) * 3.8,
                "vy": math.sin(i) * 3.8,
                "r": random.randint(2, 5),
                "renk": random.choice(["#00FFCC", "#38BDF8", "#0284C7", "#10B981"])
            }
            for i in range(50)
        ]

        # Sinematik intro görseli (images.jpg) yükle
        self.pixmap = None
        proje_kok = os.path.dirname(os.path.abspath(__file__))
        olasi_gorseller = [
            r"C:\Users\Burak\Desktop\images.jpg",
            os.path.join(proje_kok, "images.jpg"),
            os.path.join(proje_kok, "assets", "altar_intro_images.jpg"),
        ]
        if getattr(sys, "frozen", False):
            exe_d = os.path.dirname(sys.executable)
            mei = getattr(sys, "_MEIPASS", "")
            olasi_gorseller.insert(0, os.path.join(exe_d, "images.jpg"))
            olasi_gorseller.insert(0, os.path.join(mei, "images.jpg"))
        for og in olasi_gorseller:
            if os.path.isfile(og):
                self.pixmap = QPixmap(og)
                break

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animasyon_tik)
        self.timer.start(25)

    def _animasyon_tik(self):
        self.adim += 1
        for p in self.parcaciklar:
            p["x"] += p["vx"]
            p["y"] += p["vy"]

        self.update()

        if self.adim >= self.toplam_adim:
            self.timer.stop()
            self.tamamlandi.emit()
            self.close()

    def keyPressEvent(self, event):
        # Herhangi bir tuşla animasyon anında atlanabilir
        self.timer.stop()
        self.tamamlandi.emit()
        self.close()

    def mousePressEvent(self, event):
        # Tıklama ile anında atlanabilir
        self.timer.stop()
        self.tamamlandi.emit()
        self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Arka Plan: Koyu Gece Gradyanı ve images.jpg Sinematik Görseli
        cx, cy = self.ekran_g / 2, self.ekran_y / 2
        ilerleme = min(1.0, self.adim / self.toplam_adim)

        grad = QRadialGradient(cx, cy, self.ekran_g / 1.5)
        grad.setColorAt(0.0, QColor(8, 20, 36))
        grad.setColorAt(0.7, QColor(4, 8, 18))
        grad.setColorAt(1.0, QColor(2, 4, 8))
        painter.fillRect(self.rect(), grad)

        if self.pixmap and not self.pixmap.isNull():
            painter.save()
            painter.setOpacity(min(0.65, ilerleme * 0.7))
            target_h = int(self.ekran_y * 0.65)
            scaled = self.pixmap.scaledToHeight(target_h, Qt.TransformationMode.SmoothTransformation)
            px = int((self.ekran_g - scaled.width()) / 2)
            py = int((self.ekran_y - scaled.height()) / 2)
            painter.drawPixmap(px, py, scaled)
            painter.restore()

        # Parçacıklar
        for p in self.parcaciklar:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(p["renk"]))
            r = p["r"]
            painter.drawEllipse(QPointF(p["x"], p["y"]), r, r)

        # Merkez Parıltı Halkaları
        ilerleme = min(1.0, self.adim / self.toplam_adim)
        dalga_r = ilerleme * (self.ekran_g / 2.5)

        pen = QPen(QColor(0, 255, 204, int(180 * (1.0 - ilerleme * 0.5))))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), dalga_r, dalga_r * 0.6)

        # Başlık ve Alt Başlık
        painter.setPen(QColor("#00FFCC"))
        font_b = QFont("Consolas", 24, QFont.Weight.Bold)
        painter.setFont(font_b)
        painter.drawText(QRectF(0, cy - 50, self.ekran_g, 40), Qt.AlignmentFlag.AlignCenter, "ALTAR BELGE & CANVA SUNUM STÜDYOSU")

        painter.setPen(QColor("#94A3B8"))
        font_s = QFont("Consolas", 12)
        painter.setFont(font_s)
        painter.drawText(QRectF(0, cy + 5, self.ekran_g, 30), Qt.AlignmentFlag.AlignCenter, "Profesyonel Doküman & Slayt Tasarım Merkezi Yükleniyor...")

        # İlerleme Çubuğu
        bar_w = 400
        bar_h = 8
        bx = (self.ekran_g - bar_w) / 2
        by = cy + 55
        painter.setBrush(QColor(15, 23, 42))
        painter.setPen(QColor(30, 41, 59))
        painter.drawRoundedRect(QRectF(bx, by, bar_w, bar_h), 4, 4)

        painter.setBrush(QColor(0, 229, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(bx, by, bar_w * ilerleme, bar_h), 4, 4)


# ==============================================================================
# CANVA ETKİLEŞİMLİ GRAFİK ÖĞELERİ (METİN, KART, ŞEKİL)
# ==============================================================================
class AltarCanvaTextItem(QGraphicsTextItem):
    """Sürüklenip taşınabilen, çift tıklamayla düzenlenebilen Canva metin kutusu."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setDefaultTextColor(QColor("#E2E8F0"))
        self.setFont(QFont("Segoe UI", 18, QFont.Weight.Normal))

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if self.isSelected():
            painter.setPen(QPen(QColor("#00FFCC"), 1, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect())


class AltarCanvaShapeItem(QGraphicsRectItem):
    """Sürüklenip taşınabilen, rengi ve köşeleri ayarlanabilen Canva kartı/şekli."""
    def __init__(self, x, y, w, h, parent=None):
        super().__init__(x, y, w, h, parent)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setPen(QPen(QColor("#00E5FF"), 1.5))
        self.setBrush(QBrush(QColor(15, 23, 42, 220)))

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRoundedRect(self.rect(), 12, 12)

        if self.isSelected():
            painter.setPen(QPen(QColor("#FACC15"), 2, Qt.PenStyle.DotLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self.rect().adjusted(-2, -2, 2, 2), 14, 14)


# ==============================================================================
# CANVA SLAYT VERİSİ & ŞABLON FABRİKASI
# ==============================================================================
class AltarSlaytVerisi:
    """Tek bir sunum slaytının tüm görsel ve metin verilerini tutar."""
    def __init__(self, baslik="Yeni Slayt", tema="siber"):
        self.baslik = baslik
        self.tema = tema  # "siber", "doga", "matrix", "minimalist"
        self.ogeler = []

    def to_dict(self):
        return {
            "baslik": self.baslik,
            "tema": self.tema,
            "ogeler": self.ogeler
        }

    @classmethod
    def from_dict(cls, veri):
        obj = cls(baslik=veri.get("baslik", "Slayt"), tema=veri.get("tema", "siber"))
        obj.ogeler = veri.get("ogeler", [])
        return obj


def sablon_olustur(sablon_tipi: str) -> AltarSlaytVerisi:
    """Canva tarzı zengin hazır slayt şablonları üretir."""
    slayt = AltarSlaytVerisi(baslik=sablon_tipi, tema="siber")

    if sablon_tipi == "baslik":
        slayt.tema = "siber"
        slayt.ogeler = [
            {
                "tip": "kart", "x": 140, "y": 120, "w": 1000, "h": 480,
                "bg": "#0B132B", "border": "#1E3A8A", "alpha": 210
            },
            {
                "tip": "metin", "x": 200, "y": 180, "w": 880, "h": 90,
                "metin": "PROJE VE SUNUM BAŞLIĞI",
                "font": "Segoe UI", "size": 36, "bold": True, "renk": "#00FFCC", "align": "center"
            },
            {
                "tip": "metin", "x": 200, "y": 290, "w": 880, "h": 60,
                "metin": "Altar Canva Sunum Stüdyosu ile Hazırlanmış Profesyonel Slayt",
                "font": "Segoe UI", "size": 18, "bold": False, "renk": "#94A3B8", "align": "center"
            },
            {
                "tip": "metin", "x": 200, "y": 450, "w": 880, "h": 40,
                "metin": "Sunum Yapan: Altar Mühendislik & Siber Güvenlik Ekibi  |  Tarih: " + datetime.now().strftime("%d.%m.%Y"),
                "font": "Segoe UI", "size": 13, "bold": True, "renk": "#38BDF8", "align": "center"
            }
        ]

    elif sablon_tipi == "gundem":
        slayt.tema = "siber"
        slayt.ogeler = [
            {
                "tip": "metin", "x": 100, "y": 60, "w": 1080, "h": 60,
                "metin": "GÜNDEM & İÇİNDEKİLER",
                "font": "Segoe UI", "size": 28, "bold": True, "renk": "#00FFCC"
            }
        ]
        maddeler = [
            ("01", "Giriş & Proje Hedefleri", "Genel mimari, vizyon ve çözülen problem."),
            ("02", "Teknolojik Altyapı", "Yapay zeka modelleri, yerel çekirdek ve hızlandırma."),
            ("03", "Siber Güvenlik Standartları", "Kriptografik kasa, EDR kalkanı ve ağ güvenliği."),
            ("04", "Sonuç & Gelecek Planları", "Yayına alma, donanım optimizasyonu ve yol haritası.")
        ]
        for i, (no, bas, acik) in enumerate(maddeler):
            kx = 100 + (i % 2) * 550
            ky = 150 + (i // 2) * 230
            slayt.ogeler.extend([
                {
                    "tip": "kart", "x": kx, "y": ky, "w": 520, "h": 190,
                    "bg": "#0A1128", "border": "#1E293B", "alpha": 220
                },
                {
                    "tip": "metin", "x": kx + 20, "y": ky + 20, "w": 60, "h": 40,
                    "metin": no, "font": "Segoe UI", "size": 24, "bold": True, "renk": "#00E5FF"
                },
                {
                    "tip": "metin", "x": kx + 85, "y": ky + 22, "w": 410, "h": 35,
                    "metin": bas, "font": "Segoe UI", "size": 16, "bold": True, "renk": "#F1F5F9"
                },
                {
                    "tip": "metin", "x": kx + 85, "y": ky + 65, "w": 410, "h": 90,
                    "metin": acik, "font": "Segoe UI", "size": 13, "bold": False, "renk": "#94A3B8"
                }
            ])

    elif sablon_tipi == "3_kart":
        slayt.tema = "doga"
        slayt.ogeler = [
            {
                "tip": "metin", "x": 100, "y": 60, "w": 1080, "h": 60,
                "metin": "ÖNE ÇIKAN TEMEL ÖZELLİKLER",
                "font": "Segoe UI", "size": 28, "bold": True, "renk": "#34D399"
            }
        ]
        kartlar = [
            ("⚡", "Yüksek Hızlı AI Çekirdeği", "Yerel ve bulut yapay zeka modelleriyle sıfır gecikmeli, çevrimdışı ve gizlilik odaklı akıl yürütme."),
            ("🛡", "5-Katmanlı Siber Kalkan", "Bellek koruması, EDR tehdit avcılığı, şifreli kasa ve ağ saldırı önleme kalkanı."),
            ("📐", "Mühendislik & CNC", "Haas V34 2D/3D simülatörü, G-Code güvenlik analizörü ve telemetri laboratuvarı.")
        ]
        for i, (ikon, bas, acik) in enumerate(kartlar):
            kx = 90 + i * 370
            ky = 160
            slayt.ogeler.extend([
                {
                    "tip": "kart", "x": kx, "y": ky, "w": 340, "h": 460,
                    "bg": "#061A14", "border": "#059669", "alpha": 220
                },
                {
                    "tip": "metin", "x": kx + 20, "y": ky + 30, "w": 300, "h": 50,
                    "metin": ikon, "font": "Segoe UI", "size": 32, "bold": True, "renk": "#34D399", "align": "center"
                },
                {
                    "tip": "metin", "x": kx + 20, "y": ky + 95, "w": 300, "h": 50,
                    "metin": bas, "font": "Segoe UI", "size": 17, "bold": True, "renk": "#ECFDF5", "align": "center"
                },
                {
                    "tip": "metin", "x": kx + 25, "y": ky + 160, "w": 290, "h": 260,
                    "metin": acik, "font": "Segoe UI", "size": 13, "bold": False, "renk": "#A7F3D0"
                }
            ])

    elif sablon_tipi == "metrik":
        slayt.tema = "siber"
        slayt.ogeler = [
            {
                "tip": "metin", "x": 100, "y": 60, "w": 1080, "h": 60,
                "metin": "PERFORMANS VE BAŞARI METRİKLERİ",
                "font": "Segoe UI", "size": 28, "bold": True, "renk": "#38BDF8"
            }
        ]
        metrikler = [
            ("%99.9", "Sistem Güvenilirliği", "Sıfır bellek sızıntısı ve kesintisiz arka plan süreç kararlılığı."),
            ("45+", "Token / Saniye Üretim", "NVIDIA CUDA hızlandırmalı yerel dil modeli yanıt performansı."),
            ("10x", "Geliştirme Verimliliği", "Entegre Python IDE, şablonlar ve tek tıkla canlı terminal derleme.")
        ]
        for i, (deger, baslik, alt) in enumerate(metrikler):
            kx = 90 + i * 370
            ky = 200
            slayt.ogeler.extend([
                {
                    "tip": "kart", "x": kx, "y": ky, "w": 340, "h": 360,
                    "bg": "#0B1528", "border": "#0284C7", "alpha": 220
                },
                {
                    "tip": "metin", "x": kx + 15, "y": ky + 40, "w": 310, "h": 70,
                    "metin": deger, "font": "Segoe UI", "size": 42, "bold": True, "renk": "#00FFCC", "align": "center"
                },
                {
                    "tip": "metin", "x": kx + 20, "y": ky + 130, "w": 300, "h": 40,
                    "metin": baslik, "font": "Segoe UI", "size": 17, "bold": True, "renk": "#F8FAFC", "align": "center"
                },
                {
                    "tip": "metin", "x": kx + 25, "y": ky + 185, "w": 290, "h": 140,
                    "metin": alt, "font": "Segoe UI", "size": 13, "bold": False, "renk": "#94A3B8"
                }
            ])

    elif sablon_tipi == "sonuc":
        slayt.tema = "siber"
        slayt.ogeler = [
            {
                "tip": "kart", "x": 160, "y": 140, "w": 960, "h": 440,
                "bg": "#0A1128", "border": "#10B981", "alpha": 220
            },
            {
                "tip": "metin", "x": 200, "y": 190, "w": 880, "h": 70,
                "metin": "TEŞEKKÜRLER & SORULAR",
                "font": "Segoe UI", "size": 34, "bold": True, "renk": "#10B981", "align": "center"
            },
            {
                "tip": "metin", "x": 200, "y": 285, "w": 880, "h": 50,
                "metin": "Altar Çevrimdışı Mühendislik & Güvenlik Platformu",
                "font": "Segoe UI", "size": 18, "bold": False, "renk": "#F1F5F9", "align": "center"
            },
            {
                "tip": "metin", "x": 200, "y": 380, "w": 880, "h": 90,
                "metin": "Sorularınız, iş birliği ve teknik geri bildirimleriniz için oturumu başlatabilirsiniz.\n(F5 ile tam ekran sunumu başlatabilir, ESC ile düzenleme moduna dönebilirsiniz.)",
                "font": "Segoe UI", "size": 13, "bold": False, "renk": "#94A3B8", "align": "center"
            }
        ]

    return slayt


# ==============================================================================
# CANVA SLAYT & SUNUM STÜDYOSU (ANA ARAYÜZ BİLEŞENİ)
# ==============================================================================
class AltarCanvaSunumStudyosu(QWidget):
    """
    Altar Belge içerisine entegre edilen, tam donanımlı Canva tarzı sunum stüdyosu.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.slaytlar = [
            sablon_olustur("baslik"),
            sablon_olustur("gundem"),
            sablon_olustur("3_kart"),
            sablon_olustur("metrik"),
            sablon_olustur("sonuc")
        ]
        self.aktif_slayt_indeks = 0

        self._arayuz_olustur()
        self._slayt_listesini_yenile()
        self._slayti_tuvale_yukle(0)

    def _arayuz_olustur(self):
        ana_duzen = QVBoxLayout(self)
        ana_duzen.setContentsMargins(6, 6, 6, 6)
        ana_duzen.setSpacing(6)

        # 1. ÜST CANVA ARAÇ ÇUBUĞU (TOOLBAR)
        self.toolbar = QToolBar("Canva Düzenleme Çubuğu")
        self.toolbar.setStyleSheet("""
            QToolBar { background-color: #0B132B; border: 1px solid #1E293B; border-radius: 6px; padding: 4px; spacing: 6px; }
            QPushButton { background-color: #1E293B; color: #E2E8F0; border: 1px solid #334155; border-radius: 4px; padding: 4px 10px; font-weight: bold; font-family: Consolas; font-size: 11px; }
            QPushButton:hover { background-color: #334155; border-color: #00E5FF; }
            QComboBox { background-color: #1E293B; color: #E2E8F0; border: 1px solid #334155; border-radius: 4px; padding: 3px 8px; font-family: Consolas; font-size: 11px; }
        """)
        ana_duzen.addWidget(self.toolbar)

        # Şablon Seçici
        self.combo_sablon = QComboBox()
        self.combo_sablon.addItems([
            "📑 Şablon Ekle: Başlık Slaytı",
            "📑 Şablon Ekle: Gündem & İçindekiler",
            "📑 Şablon Ekle: 3'lü Özellik Kartı",
            "📑 Şablon Ekle: İstatistik & Metrik",
            "📑 Şablon Ekle: Sonuç & Teşekkür"
        ])
        btn_sablon_uygula = QPushButton("➕ Şablonu Ekle")
        btn_sablon_uygula.clicked.connect(self._sablon_ekle_tiklandi)
        self.toolbar.addWidget(self.combo_sablon)
        self.toolbar.addWidget(btn_sablon_uygula)
        self.toolbar.addSeparator()

        # Öğe Ekle Butonları
        btn_metin = QPushButton("🔤 +Metin")
        btn_metin.clicked.connect(self._metin_ekle_tiklandi)
        self.toolbar.addWidget(btn_metin)

        btn_kart = QPushButton("🔲 +Kart/Şekil")
        btn_kart.clicked.connect(self._kart_ekle_tiklandi)
        self.toolbar.addWidget(btn_kart)

        btn_resim = QPushButton("🖼 +Resim")
        btn_resim.clicked.connect(self._resim_ekle_tiklandi)
        self.toolbar.addWidget(btn_resim)

        self.toolbar.addSeparator()

        # Tema Seçici
        self.combo_tema = QComboBox()
        self.combo_tema.addItems([
            "🎨 Arka Plan: Kozmik Siber",
            "🎨 Arka Plan: Zümrüt Doğa",
            "🎨 Arka Plan: Matrix Synthwave",
            "🎨 Arka Plan: Minimalist Açık"
        ])
        self.combo_tema.currentIndexChanged.connect(self._tema_degisti)
        self.toolbar.addWidget(self.combo_tema)

        self.toolbar.addSeparator()

        # Kaydet, Aç, PDF ve Sunumu Başlat (F5) Butonları
        btn_kaydet = QPushButton("💾 Sunumu Kaydet")
        btn_kaydet.clicked.connect(self.sunumu_kaydet)
        self.toolbar.addWidget(btn_kaydet)

        btn_ac = QPushButton("📂 Sunumu Aç")
        btn_ac.clicked.connect(self.sunumu_ac)
        self.toolbar.addWidget(btn_ac)

        btn_pdf = QPushButton("🖨 PDF Dışa Aktar")
        btn_pdf.clicked.connect(self.pdf_olarak_aktar)
        self.toolbar.addWidget(btn_pdf)

        # TAM EKRAN SUNUM MODU (F5)
        self.btn_f5_sunum = QPushButton("▶ SUNUMU BAŞLAT (F5)")
        self.btn_f5_sunum.setStyleSheet("""
            QPushButton { background-color: #059669; color: #FFFFFF; border: 1px solid #10B981; border-radius: 4px; padding: 5px 14px; font-weight: bold; font-family: Consolas; font-size: 11px; }
            QPushButton:hover { background-color: #047857; }
        """)
        self.btn_f5_sunum.clicked.connect(self.tam_ekran_sunumu_baslat)
        self.toolbar.addWidget(self.btn_f5_sunum)

        # 2. ORTA BÖLÜM: Sol Slayt Gezgini + Sağ 16:9 Tuval
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)
        ana_duzen.addWidget(splitter, 1)

        # Sol Slayt Thumbnails Listesi
        sol_panel = QFrame()
        sol_panel.setStyleSheet("background-color: #080E1C; border: 1px solid #1E293B; border-radius: 6px;")
        sol_layout = QVBoxLayout(sol_panel)
        sol_layout.setContentsMargins(6, 6, 6, 6)

        lbl_slaytlar = QLabel("📽 SLAYTLAR (SUNUM AKIŞI)")
        lbl_slaytlar.setStyleSheet("color: #00FFCC; font-weight: bold; font-family: Consolas; font-size: 11px;")
        sol_layout.addWidget(lbl_slaytlar)

        self.liste_slaytlar = QListWidget()
        self.liste_slaytlar.setStyleSheet("""
            QListWidget { background-color: #040812; border: 1px solid #1E293B; border-radius: 4px; color: #E2E8F0; font-family: Consolas; font-size: 11px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #0F172A; }
            QListWidget::item:selected { background-color: #0284C7; color: #FFFFFF; font-weight: bold; }
        """)
        self.liste_slaytlar.currentRowChanged.connect(self._slayt_secimi_degisti)
        sol_layout.addWidget(self.liste_slaytlar, 1)

        # Slayt Ekle/Sil/Çoğalt Butonları
        slayt_btn_layout = QHBoxLayout()
        btn_yeni = QPushButton("➕ Ekle")
        btn_yeni.clicked.connect(self.yeni_slayt_ekle)
        btn_cogalt = QPushButton("📋 Çoğalt")
        btn_cogalt.clicked.connect(self.slayti_cogalt)
        btn_sil = QPushButton("🗑 Sil")
        btn_sil.clicked.connect(self.slayti_sil)

        for b in (btn_yeni, btn_cogalt, btn_sil):
            b.setStyleSheet("background-color: #1E293B; color: #E2E8F0; border-radius: 4px; padding: 4px; font-size: 10px; font-weight: bold;")
            slayt_btn_layout.addWidget(b)
        sol_layout.addLayout(slayt_btn_layout)

        splitter.addWidget(sol_panel)
        splitter.setStretchFactor(0, 1)

        # Sağ: 16:9 Grafik Tuvali
        sag_panel = QFrame()
        sag_panel.setStyleSheet("background-color: #02040A; border: 1px solid #1E293B; border-radius: 6px;")
        sag_layout = QVBoxLayout(sag_panel)
        sag_layout.setContentsMargins(4, 4, 4, 4)

        self.scene = QGraphicsScene(0, 0, CANVAS_W, CANVAS_H)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setStyleSheet("background-color: #010306; border: none;")
        sag_layout.addWidget(self.view)

        splitter.addWidget(sag_panel)
        splitter.setStretchFactor(1, 4)

    def _slayt_listesini_yenile(self):
        self.liste_slaytlar.blockSignals(True)
        self.liste_slaytlar.clear()
        for idx, s in enumerate(self.slaytlar):
            item = QListWidgetItem(f"[{idx+1:02d}] {s.baslik[:24]}")
            self.liste_slaytlar.addItem(item)
        if self.aktif_slayt_indeks < len(self.slaytlar):
            self.liste_slaytlar.setCurrentRow(self.aktif_slayt_indeks)
        self.liste_slaytlar.blockSignals(False)

    def _slayt_secimi_degisti(self, row):
        if 0 <= row < len(self.slaytlar):
            self._guncel_tuvali_kaydet()
            self.aktif_slayt_indeks = row
            self._slayti_tuvale_yukle(row)

    def _guncel_tuvali_kaydet(self):
        """Mevcut tuvaldeki öğelerin güncel pozisyonlarını slayt nesnesine kaydeder."""
        if not (0 <= self.aktif_slayt_indeks < len(self.slaytlar)):
            return

        slayt = self.slaytlar[self.aktif_slayt_indeks]
        yeni_ogeler = []

        for item in self.scene.items():
            if isinstance(item, AltarCanvaTextItem):
                pos = item.pos()
                yeni_ogeler.append({
                    "tip": "metin",
                    "x": pos.x(),
                    "y": pos.y(),
                    "w": item.boundingRect().width(),
                    "h": item.boundingRect().height(),
                    "metin": item.toPlainText(),
                    "font": item.font().family(),
                    "size": item.font().pointSize(),
                    "bold": item.font().bold(),
                    "renk": item.defaultTextColor().name()
                })
            elif isinstance(item, AltarCanvaShapeItem):
                rect = item.rect()
                pos = item.pos()
                yeni_ogeler.append({
                    "tip": "kart",
                    "x": rect.x() + pos.x(),
                    "y": rect.y() + pos.y(),
                    "w": rect.width(),
                    "h": rect.height(),
                    "bg": item.brush().color().name(),
                    "border": item.pen().color().name(),
                    "alpha": item.brush().color().alpha()
                })
            elif isinstance(item, QGraphicsPixmapItem):
                pos = item.pos()
                dosya_yolu = getattr(item, "_dosya_yolu", "")
                yeni_ogeler.append({
                    "tip": "resim",
                    "x": pos.x(),
                    "y": pos.y(),
                    "dosya": dosya_yolu
                })

        slayt.ogeler = list(reversed(yeni_ogeler))

    def _slayti_tuvale_yukle(self, idx):
        self.scene.clear()
        if not (0 <= idx < len(self.slaytlar)):
            return

        slayt = self.slaytlar[idx]

        # Arka Plan Çizimi
        self._arka_plan_ciz(slayt.tema)

        # Öğeleri Yükle
        for o in slayt.ogeler:
            tip = o.get("tip")
            if tip == "kart":
                kart = AltarCanvaShapeItem(o.get("x", 100), o.get("y", 100), o.get("w", 300), o.get("h", 200))
                c = QColor(o.get("bg", "#0B132B"))
                c.setAlpha(o.get("alpha", 220))
                kart.setBrush(QBrush(c))
                kart.setPen(QPen(QColor(o.get("border", "#1E3A8A")), 1.5))
                self.scene.addItem(kart)

            elif tip == "metin":
                txt_item = AltarCanvaTextItem(o.get("metin", "Metin"))
                txt_item.setPos(o.get("x", 150), o.get("y", 150))
                f = QFont(o.get("font", "Segoe UI"), o.get("size", 18))
                f.setBold(o.get("bold", False))
                txt_item.setFont(f)
                txt_item.setDefaultTextColor(QColor(o.get("renk", "#E2E8F0")))
                if o.get("w"):
                    txt_item.setTextWidth(o.get("w"))
                self.scene.addItem(txt_item)

            elif tip == "resim":
                dosya = o.get("dosya")
                if dosya and os.path.isfile(dosya):
                    pix = QPixmap(dosya)
                    if not pix.isNull():
                        pix_item = self.scene.addPixmap(pix)
                        pix_item.setPos(o.get("x", 200), o.get("y", 200))
                        pix_item.setFlags(
                            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
                        )
                        pix_item._dosya_yolu = dosya

        # Tuvali 16:9 sığacak şekilde ölçekle
        self.view.fitInView(QRectF(0, 0, CANVAS_W, CANVAS_H), Qt.AspectRatioMode.KeepAspectRatio)

    def _arka_plan_ciz(self, tema):
        bg_rect = QGraphicsRectItem(0, 0, CANVAS_W, CANVAS_H)
        bg_rect.setPen(QPen(QColor("#00E5FF"), 1))

        if tema == "doga":
            grad = QLinearGradient(0, 0, CANVAS_W, CANVAS_H)
            grad.setColorAt(0.0, QColor("#022C22"))
            grad.setColorAt(0.5, QColor("#064E3B"))
            grad.setColorAt(1.0, QColor("#021A14"))
            bg_rect.setBrush(QBrush(grad))
        elif tema == "matrix":
            grad = QLinearGradient(0, 0, CANVAS_W, CANVAS_H)
            grad.setColorAt(0.0, QColor("#1E1B4B"))
            grad.setColorAt(0.5, QColor("#311042"))
            grad.setColorAt(1.0, QColor("#0A061E"))
            bg_rect.setBrush(QBrush(grad))
        elif tema == "minimalist":
            bg_rect.setBrush(QBrush(QColor("#F8FAFC")))
            bg_rect.setPen(QPen(QColor("#CBD5E1"), 1))
        else:
            # Siber Orijinal
            grad = QLinearGradient(0, 0, CANVAS_W, CANVAS_H)
            grad.setColorAt(0.0, QColor("#0B132B"))
            grad.setColorAt(0.5, QColor("#0A0E1A"))
            grad.setColorAt(1.0, QColor("#030712"))
            bg_rect.setBrush(QBrush(grad))

        bg_rect.setZValue(-100)
        self.scene.addItem(bg_rect)

    def _tema_degisti(self, idx):
        if not (0 <= self.aktif_slayt_indeks < len(self.slaytlar)):
            return
        temalar = ["siber", "doga", "matrix", "minimalist"]
        self.slaytlar[self.aktif_slayt_indeks].tema = temalar[idx]
        self._guncel_tuvali_kaydet()
        self._slayti_tuvale_yukle(self.aktif_slayt_indeks)

    def _sablon_ekle_tiklandi(self):
        sablon_adlari = ["baslik", "gundem", "3_kart", "metrik", "sonuc"]
        secilen = sablon_adlari[self.combo_sablon.currentIndex()]
        yeni = sablon_olustur(secilen)
        self.slaytlar.append(yeni)
        self.aktif_slayt_indeks = len(self.slaytlar) - 1
        self._slayt_listesini_yenile()
        self._slayti_tuvale_yukle(self.aktif_slayt_indeks)

    def _metin_ekle_tiklandi(self):
        txt, ok = QInputDialog.getText(self, "Yeni Metin", "Metin içeriğini girin:")
        if ok and txt.strip():
            t = AltarCanvaTextItem(txt)
            t.setPos(CANVAS_W / 2 - 150, CANVAS_H / 2 - 30)
            self.scene.addItem(t)
            self._guncel_tuvali_kaydet()

    def _kart_ekle_tiklandi(self):
        kart = AltarCanvaShapeItem(CANVAS_W / 2 - 200, CANVAS_H / 2 - 120, 400, 240)
        self.scene.addItem(kart)
        self._guncel_tuvali_kaydet()

    def _resim_ekle_tiklandi(self):
        dosya, _ = QFileDialog.getOpenFileName(
            self, "Slayta Resim Ekle", "", "Resimler (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if dosya:
            pix = QPixmap(dosya)
            if not pix.isNull():
                if pix.width() > 600 or pix.height() > 400:
                    pix = pix.scaled(600, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                p_item = self.scene.addPixmap(pix)
                p_item.setPos(CANVAS_W / 2 - pix.width() / 2, CANVAS_H / 2 - pix.height() / 2)
                p_item.setFlags(
                    QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                    QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
                )
                p_item._dosya_yolu = dosya
                self._guncel_tuvali_kaydet()

    def yeni_slayt_ekle(self):
        yeni = AltarSlaytVerisi(baslik=f"Slayt {len(self.slaytlar)+1}", tema="siber")
        yeni.ogeler = [
            {
                "tip": "metin", "x": 100, "y": 80, "w": 1000, "h": 50,
                "metin": "YENİ SLAYT BAŞLIĞI",
                "font": "Segoe UI", "size": 30, "bold": True, "renk": "#00FFCC"
            }
        ]
        self.slaytlar.append(yeni)
        self.aktif_slayt_indeks = len(self.slaytlar) - 1
        self._slayt_listesini_yenile()
        self._slayti_tuvale_yukle(self.aktif_slayt_indeks)

    def slayti_cogalt(self):
        if not (0 <= self.aktif_slayt_indeks < len(self.slaytlar)):
            return
        self._guncel_tuvali_kaydet()
        secili = self.slaytlar[self.aktif_slayt_indeks]
        kopya = AltarSlaytVerisi.from_dict(secili.to_dict())
        kopya.baslik = f"{secili.baslik} (Kopya)"
        self.slaytlar.insert(self.aktif_slayt_indeks + 1, kopya)
        self.aktif_slayt_indeks += 1
        self._slayt_listesini_yenile()
        self._slayti_tuvale_yukle(self.aktif_slayt_indeks)

    def slayti_sil(self):
        if len(self.slaytlar) <= 1:
            QMessageBox.warning(self, "Uyarı", "Sunumda en az 1 slayt bulunmalıdır.")
            return
        del self.slaytlar[self.aktif_slayt_indeks]
        self.aktif_slayt_indeks = max(0, self.aktif_slayt_indeks - 1)
        self._slayt_listesini_yenile()
        self._slayti_tuvale_yukle(self.aktif_slayt_indeks)

    def sunumu_kaydet(self):
        self._guncel_tuvali_kaydet()
        dosya, _ = QFileDialog.getSaveFileName(
            self, "Altar Sunumu Kaydet", "", "Altar Sunumu (*.altarsunumu *.json)"
        )
        if dosya:
            if not dosya.endswith((".altarsunumu", ".json")):
                dosya += ".altarsunumu"
            veri = [s.to_dict() for s in self.slaytlar]
            try:
                with open(dosya, "w", encoding="utf-8") as f:
                    json.dump(veri, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Başarılı", f"Sunum başarıyla kaydedildi:\n{os.path.basename(dosya)}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kaydedilemedi:\n{e}")

    def sunumu_ac(self):
        dosya, _ = QFileDialog.getOpenFileName(
            self, "Altar Sunumu Aç", "", "Altar Sunumu (*.altarsunumu *.json)"
        )
        if dosya and os.path.isfile(dosya):
            try:
                with open(dosya, "r", encoding="utf-8") as f:
                    veri = json.load(f)
                self.slaytlar = [AltarSlaytVerisi.from_dict(v) for v in veri]
                self.aktif_slayt_indeks = 0
                self._slayt_listesini_yenile()
                self._slayti_tuvale_yukle(0)
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Sunum açılamadı:\n{e}")

    def pdf_olarak_aktar(self):
        """Tüm slaytları tek bir çok sayfalı PDF dosyası olarak dışa aktarır."""
        self._guncel_tuvali_kaydet()
        dosya, _ = QFileDialog.getSaveFileName(
            self, "PDF Sunumu Dışa Aktar", "", "PDF Dokümanı (*.pdf)"
        )
        if dosya:
            if not dosya.endswith(".pdf"):
                dosya += ".pdf"
            try:
                from PyQt6.QtPrintSupport import QPrinter
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(dosya)
                printer.setPageOrientation(QPrinter.Orientation.Landscape)

                painter = QPainter(printer)
                for i in range(len(self.slaytlar)):
                    if i > 0:
                        printer.newPage()
                    self._slayti_tuvale_yukle(i)
                    self.scene.render(painter)
                painter.end()

                self._slayti_tuvale_yukle(self.aktif_slayt_indeks)
                QMessageBox.information(self, "Başarılı", f"PDF sunumu başarıyla oluşturuldu:\n{os.path.basename(dosya)}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"PDF oluşturulamadı:\n{e}")

    def pdf_disa_aktar(self):
        """PDF dışa aktarma takma fonksiyonu."""
        return self.pdf_olarak_aktar()

    def resim_disa_aktar(self):
        """Aktif slaytı yüksek çözünürlüklü PNG görseli olarak dışa aktarır."""
        self._guncel_tuvali_kaydet()
        dosya, _ = QFileDialog.getSaveFileName(
            self, "Slaytı PNG Olarak Dışa Aktar", f"Slayt_{self.aktif_slayt_indeks + 1}.png", "PNG Görseli (*.png)"
        )
        if dosya:
            if not dosya.endswith(".png"):
                dosya += ".png"
            try:
                img = QImage(CANVAS_W, CANVAS_H, QImage.Format.Format_ARGB32_Premultiplied)
                img.fill(Qt.GlobalColor.transparent)
                p = QPainter(img)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                self.scene.render(p)
                p.end()
                img.save(dosya, "PNG")
                QMessageBox.information(self, "Başarılı", f"Slayt görseli kaydedildi:\n{os.path.basename(dosya)}")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Görsel kaydedilemedi:\n{e}")

    def resim_olarak_aktar(self):
        """PNG dışa aktarma takma fonksiyonu."""
        return self.resim_disa_aktar()

    def tam_ekran_sunumu_baslat(self):
        """F5 Canlı Tam Ekran Sunum Modunu Başlatır."""
        self._guncel_tuvali_kaydet()
        sunum_penceresi = AltarTamEkranSunumPenceresi(self.slaytlar, self.aktif_slayt_indeks, self)
        sunum_penceresi.showFullScreen()


# ==============================================================================
# TAM EKRAN SUNUM OYNATICI MODU (F5 SUNUMU)
# ==============================================================================
class AltarTamEkranSunumPenceresi(QMainWindow):
    """1920x1080 Gerçek Çerçevesiz Tam Ekran Canlı Sunum Görüntüleyici."""
    def __init__(self, slaytlar, baslangic_indeks=0, parent=None):
        super().__init__(parent)
        self.slaytlar = slaytlar
        self.guncel_indeks = baslangic_indeks

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #000000;")

        self.scene = QGraphicsScene(0, 0, CANVAS_W, CANVAS_H)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setStyleSheet("background-color: #000000; border: none;")
        self.setCentralWidget(self.view)

        # Alt Bilgi HUD
        self.lbl_hud = QLabel(self)
        self.lbl_hud.setStyleSheet("""
            background-color: rgba(10, 15, 30, 200);
            color: #00FFCC;
            border: 1px solid #1E293B;
            border-radius: 6px;
            padding: 6px 14px;
            font-family: Consolas;
            font-size: 13px;
            font-weight: bold;
        """)

        if os.name == "nt":
            self.showFullScreen()
            try:
                hwnd = int(self.winId())
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass

        self._slayti_goster(self.guncel_indeks)

    def _slayti_goster(self, idx):
        if not (0 <= idx < len(self.slaytlar)):
            return
        self.guncel_indeks = idx
        slayt = self.slaytlar[idx]

        self.scene.clear()

        # Arka Plan
        bg_rect = QGraphicsRectItem(0, 0, CANVAS_W, CANVAS_H)
        if slayt.tema == "doga":
            grad = QLinearGradient(0, 0, CANVAS_W, CANVAS_H)
            grad.setColorAt(0.0, QColor("#022C22"))
            grad.setColorAt(1.0, QColor("#021A14"))
            bg_rect.setBrush(QBrush(grad))
        elif slayt.tema == "matrix":
            grad = QLinearGradient(0, 0, CANVAS_W, CANVAS_H)
            grad.setColorAt(0.0, QColor("#1E1B4B"))
            grad.setColorAt(1.0, QColor("#0A061E"))
            bg_rect.setBrush(QBrush(grad))
        elif slayt.tema == "minimalist":
            bg_rect.setBrush(QBrush(QColor("#F8FAFC")))
        else:
            grad = QLinearGradient(0, 0, CANVAS_W, CANVAS_H)
            grad.setColorAt(0.0, QColor("#0B132B"))
            grad.setColorAt(1.0, QColor("#030712"))
            bg_rect.setBrush(QBrush(grad))
        bg_rect.setZValue(-100)
        self.scene.addItem(bg_rect)

        # Öğeler
        for o in slayt.ogeler:
            tip = o.get("tip")
            if tip == "kart":
                kart = QGraphicsRectItem(o.get("x", 100), o.get("y", 100), o.get("w", 300), o.get("h", 200))
                c = QColor(o.get("bg", "#0B132B"))
                c.setAlpha(o.get("alpha", 220))
                kart.setBrush(QBrush(c))
                kart.setPen(QPen(QColor(o.get("border", "#1E3A8A")), 1.5))
                self.scene.addItem(kart)

            elif tip == "metin":
                t = QGraphicsTextItem(o.get("metin", ""))
                t.setPos(o.get("x", 150), o.get("y", 150))
                f = QFont(o.get("font", "Segoe UI"), o.get("size", 18))
                f.setBold(o.get("bold", False))
                t.setFont(f)
                t.setDefaultTextColor(QColor(o.get("renk", "#E2E8F0")))
                if o.get("w"):
                    t.setTextWidth(o.get("w"))
                self.scene.addItem(t)

            elif tip == "resim":
                dosya = o.get("dosya")
                if dosya and os.path.isfile(dosya):
                    pix = QPixmap(dosya)
                    if not pix.isNull():
                        p_item = self.scene.addPixmap(pix)
                        p_item.setPos(o.get("x", 200), o.get("y", 200))

        self.view.fitInView(QRectF(0, 0, CANVAS_W, CANVAS_H), Qt.AspectRatioMode.KeepAspectRatio)

        # HUD Güncelle
        self.lbl_hud.setText(f"Slayt {idx+1} / {len(self.slaytlar)}  (← / → veya Boşluk | Çıkış: ESC)")
        self.lbl_hud.adjustSize()
        self.lbl_hud.move((self.width() - self.lbl_hud.width()) // 2, self.height() - 55)

    def keyPressEvent(self, event):
        k = event.key()
        if k in (Qt.Key.Key_Right, Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_PageDown):
            if self.guncel_indeks < len(self.slaytlar) - 1:
                self._slayti_goster(self.guncel_indeks + 1)
        elif k in (Qt.Key.Key_Left, Qt.Key.Key_Backspace, Qt.Key.Key_PageUp):
            if self.guncel_indeks > 0:
                self._slayti_goster(self.guncel_indeks - 1)
        elif k in (Qt.Key.Key_Escape, Qt.Key.Key_Q):
            self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.guncel_indeks < len(self.slaytlar) - 1:
                self._slayti_goster(self.guncel_indeks + 1)
            else:
                self.close()
        elif event.button() == Qt.MouseButton.RightButton:
            if self.guncel_indeks > 0:
                self._slayti_goster(self.guncel_indeks - 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.view.fitInView(QRectF(0, 0, CANVAS_W, CANVAS_H), Qt.AspectRatioMode.KeepAspectRatio)
        self.lbl_hud.move((self.width() - self.lbl_hud.width()) // 2, self.height() - 55)


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    splash = AltarSinematikAcilisPenceresi()
    ana_pencere = QMainWindow()
    ana_pencere.setWindowTitle("Altar Canva Slayt & Sunum Stüdyosu")
    ana_pencere.resize(1366, 768)
    studyosu = AltarCanvaSunumStudyosu(ana_pencere)
    ana_pencere.setCentralWidget(studyosu)

    def _baslat():
        ana_pencere.showFullScreen()
        ana_pencere.raise_()
        ana_pencere.activateWindow()

    splash.tamamlandi.connect(_baslat)
    splash.showFullScreen()
    sys.exit(app.exec())
