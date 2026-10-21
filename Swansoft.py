import os
import sys
import math
import time
import multiprocessing
import numpy as np

try:
    import tkinter as tk
    from tkinter import filedialog as tk_filedialog, messagebox as tk_messagebox
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False


# =========================================================================
# BAĞIMSIZ SÜREÇ İÇİNDE YÜKLENEN PYQT5 & OPENGL 3D KATI MODEL MOTORU
# (Ana Tkinter süreciyle DLL çakışması yapmaması için yalnızca çağrıldığında yüklenir)
# =========================================================================
_GERCEK_3D_SINIF = None


def _pyqt5_3d_sinifini_hazirla():
    global _GERCEK_3D_SINIF
    if _GERCEK_3D_SINIF is not None:
        return _GERCEK_3D_SINIF

    try:
        from PyQt6.QtWidgets import (
            QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QLabel, QLineEdit, QPushButton, QGroupBox, QRadioButton,
            QButtonGroup, QSlider, QTabWidget, QMessageBox,
            QCheckBox, QComboBox, QTextEdit, QGridLayout, QFileDialog
        )
        from PyQt6.QtGui import QColor, QTextFormat, QKeySequence, QAction
        from PyQt6.QtCore import Qt, QTimer
        if not hasattr(Qt, "AlignCenter"):
            setattr(Qt, "AlignCenter", Qt.AlignmentFlag.AlignCenter)
        if not hasattr(Qt, "Horizontal"):
            setattr(Qt, "Horizontal", Qt.Orientation.Horizontal)
        import pyqtgraph.opengl as gl
        import pyqtgraph as pg
    except ImportError:
        try:
            import PyQt5
            plugin_path = os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5', 'plugins')
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
        except Exception:
            pass

        from PyQt5.QtWidgets import (
            QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QLabel, QLineEdit, QPushButton, QGroupBox, QRadioButton,
            QButtonGroup, QSlider, QTabWidget, QMessageBox,
            QCheckBox, QComboBox, QTextEdit, QGridLayout, QFileDialog, QAction
        )
        from PyQt5.QtGui import QColor, QTextFormat, QKeySequence
        from PyQt5.QtCore import Qt, QTimer
        import pyqtgraph.opengl as gl
        import pyqtgraph as pg

    class _HaasSolid3DEngineV34(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Haas 3D Simülatörü - V34 (Katı Modeller & 3 Eksen Standart)")
            self.resize(1550, 950)

            self.current_pos = {'X': -20.0, 'Y': -20.0, 'Z': 50.0, 'A': 0.0, 'C': 0.0}
            self.mode = 'G00'
            self.comp_mode = 'G40'
            self.feed_rate = 100.0
            self.rapid_rate = 2000.0

            self.total_time_min = 0.0
            self.total_distance = 0.0
            self.crash_count = 0
            self.holder_crash = False
            self.vise_crash = False
            self.tool_rotation_angle = 0

            self.paths = []
            self.sim_active = False
            self.is_paused = False
            self.current_line_idx = 0
            self.current_steps = []
            self._son_vurgulanan_satir = -1

            self.surface = None
            self.stock_walls = None
            self.vise_jaws = []
            self.tool_mesh = None
            self.spindle_mesh = None
            self.coolant_mesh = None
            self.path_lines = []
            self.rotary_table_mesh = None

            self.Z_grid = None
            self.X_grid = None
            self.Y_grid = None
            self.surf_colors = None
            self.X_grid_1d = None
            self.Y_grid_1d = None

            self.orig_Z_grid = None
            self.orig_walls_verts = None
            self.orig_jaw1_verts = None
            self.orig_jaw2_verts = None
            self.orig_table_verts = None
            self.walls_faces = None
            self.jaw_faces = None
            self.table_faces = None

            self.tool_library = {}
            self.current_tool_id = 'T1'
            self.drawn_tool_id = None
            self.drawn_coolant_state = None
            self.coolant_active = False

            self.active_wcs = 'G54'
            self.wcs_offsets = {f'G{i}': {'X': 0.0, 'Y': 0.0, 'Z': 0.0} for i in range(54, 60)}
            self.macro_vars = {}

            self.timer = QTimer()
            self.timer.timeout.connect(self.sim_tick)

            self.setup_ui()
            self.init_3d_environment()
            self.reset_machine(first_start=True)

            # F11 Tam Ekran ve Escape Kısayolları
            self.action_tam_ekran = QAction("Tam Ekran (F11)", self)
            self.action_tam_ekran.setShortcut(QKeySequence("F11"))
            self.action_tam_ekran.triggered.connect(self._tam_ekran_degistir)
            self.addAction(self.action_tam_ekran)

            self.action_esc = QAction("Tam Ekrandan Çık (Esc)", self)
            self.action_esc.setShortcut(QKeySequence("Escape"))
            self.action_esc.triggered.connect(self._tam_ekrandan_cik)
            self.addAction(self.action_esc)

        def _tam_ekran_degistir(self):
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()

        def _tam_ekrandan_cik(self):
            if self.isFullScreen():
                self.showNormal()

        def safe_remove(self, obj):
            if obj:
                try:
                    self.gl_widget.removeItem(obj)
                except Exception:
                    pass

        def create_solid_cylinder_mesh(self, radius, length, cols=24):
            verts = []
            faces = []
            for i in range(cols):
                theta = i * 2 * math.pi / cols
                x = radius * math.cos(theta)
                y = radius * math.sin(theta)
                verts.append([x, y, 0])
                verts.append([x, y, length])

            center_bottom_idx = len(verts)
            verts.append([0, 0, 0])
            center_top_idx = len(verts)
            verts.append([0, 0, length])

            for i in range(cols):
                next_i = (i + 1) % cols
                v1 = i * 2
                v2 = i * 2 + 1
                v3 = next_i * 2
                v4 = next_i * 2 + 1

                faces.append([v1, v3, v4])
                faces.append([v1, v4, v2])
                faces.append([center_bottom_idx, v1, v3])
                faces.append([center_top_idx, v4, v2])

            return gl.MeshData(vertexes=np.array(verts), faces=np.array(faces))

        def setup_ui(self):
            main_widget = QWidget()
            self.setCentralWidget(main_widget)
            layout = QHBoxLayout(main_widget)
            layout.setContentsMargins(10, 10, 10, 10)

            left_panel = QWidget()
            left_panel.setFixedWidth(450)
            left_layout = QVBoxLayout(left_panel)
            left_layout.setContentsMargins(0, 0, 0, 0)

            title_lbl = QLabel("HAAS - V34 SOLID 3-AXIS ENGINE")
            title_lbl.setStyleSheet(
                "color: white; font-size: 18px; font-weight: bold; background-color: #2b2d30; padding: 10px;")
            title_lbl.setAlignment(Qt.AlignCenter)
            left_layout.addWidget(title_lbl)

            self.stats_group = QGroupBox()
            self.stats_group.setStyleSheet("QGroupBox { background-color: black; border: 2px solid #4ca1af; }")
            stats_layout = QVBoxLayout(self.stats_group)
            self.pos_lbl = QLabel("X: -20.000  Y: -20.000  Z: 50.000\nA: 0.000°   C: 0.000°")
            self.pos_lbl.setStyleSheet("color: #00ff00; font-family: Consolas; font-size: 18px; font-weight: bold;")
            stats_layout.addWidget(self.pos_lbl)
            self.stats_lbl = QLabel("Süre: 00:00:00 | Mesafe: 0.0 mm\nÇarpma: 0 | Aktif Takım: T1 | WCS: G54")
            self.stats_lbl.setStyleSheet("color: #4ca1af; font-family: Consolas; font-size: 12px;")
            stats_layout.addWidget(self.stats_lbl)

            self.comp_lbl = QLabel("Takım Telafisi: G40 (KAPALI)")
            self.comp_lbl.setStyleSheet("color: #f39c12; font-family: Consolas; font-size: 12px; font-weight: bold;")
            stats_layout.addWidget(self.comp_lbl)
            left_layout.addWidget(self.stats_group)

            settings_layout = QHBoxLayout()
            self.show_lines_cb = QCheckBox("Takım Yolu İzleri")
            self.show_lines_cb.setStyleSheet("color: white;")
            self.cb_m01 = QCheckBox("M01 Opsiyonel Duruş")
            self.cb_m01.setStyleSheet("color: yellow; font-weight: bold;")
            self.cb_m01.setChecked(True)
            settings_layout.addWidget(self.show_lines_cb)
            settings_layout.addWidget(self.cb_m01)
            left_layout.addLayout(settings_layout)

            self.tabs = QTabWidget()
            self.tabs.setStyleSheet("QTabBar::tab { height: 30px; width: 140px; }")

            self.tab_cam = QWidget()
            self.tab_mem = QWidget()
            self.tab_jog = QWidget()

            self.tabs.addTab(self.tab_cam, "OTO-CAM (DXF)")
            self.tabs.addTab(self.tab_mem, "MEM (OTOMATİK)")
            self.tabs.addTab(self.tab_jog, "JOG / OFFSET")

            left_layout.addWidget(self.tabs)
            self.setup_cam_tab()
            self.setup_mem_tab()
            self.setup_jog_tab()
            layout.addWidget(left_panel)

            self.gl_widget = gl.GLViewWidget()
            self.gl_widget.setBackgroundColor('#121417')
            self.gl_widget.setCameraPosition(distance=350, elevation=35, azimuth=-45)
            layout.addWidget(self.gl_widget, 1)

        def setup_cam_tab(self):
            layout = QVBoxLayout(self.tab_cam)
            lbl_info = QLabel("Vektörel Çizimlerden (DXF) Otonom Kod Çıkarıcı")
            lbl_info.setStyleSheet("color: #bdc3c7; font-style: italic;")
            layout.addWidget(lbl_info)

            wiz_group = QGroupBox("Parametrik Hızlı Şablon")
            wiz_group.setStyleSheet("color: #3498db; font-weight: bold;")
            w_layout = QGridLayout(wiz_group)
            w_layout.addWidget(QLabel("Merkez X:"), 0, 0)
            self.cam_cx = QLineEdit("100")
            w_layout.addWidget(self.cam_cx, 0, 1)
            w_layout.addWidget(QLabel("Merkez Y:"), 0, 2)
            self.cam_cy = QLineEdit("100")
            w_layout.addWidget(self.cam_cy, 0, 3)
            w_layout.addWidget(QLabel("Dış Çap:"), 1, 0)
            self.cam_outer = QLineEdit("120")
            w_layout.addWidget(self.cam_outer, 1, 1)
            w_layout.addWidget(QLabel("İç Çap:"), 1, 2)
            self.cam_inner = QLineEdit("60")
            w_layout.addWidget(self.cam_inner, 1, 3)
            w_layout.addWidget(QLabel("Delik Sayısı:"), 2, 0)
            self.cam_holes = QLineEdit("6")
            w_layout.addWidget(self.cam_holes, 2, 1)
            w_layout.addWidget(QLabel("Delik Ekseni:"), 2, 2)
            self.cam_pcd = QLineEdit("90")
            w_layout.addWidget(self.cam_pcd, 2, 3)
            w_layout.addWidget(QLabel("Derinlik(Z):"), 3, 0)
            self.cam_z = QLineEdit("15")
            w_layout.addWidget(self.cam_z, 3, 1)

            btn_gen = QPushButton("ŞABLONDAN G-KOD ÜRET")
            btn_gen.setStyleSheet("background-color: #3498db; color: white; height: 35px; font-weight: bold;")
            btn_gen.clicked.connect(self.generate_cam_code)
            w_layout.addWidget(btn_gen, 4, 0, 1, 4)
            layout.addWidget(wiz_group)

            dxf_group = QGroupBox("Yapay Zekasız Matematiksel DXF Analizi")
            dxf_group.setStyleSheet("color: #e67e22; font-weight: bold;")
            d_layout = QVBoxLayout(dxf_group)
            lbl_dxf = QLabel("SolidWorks/AutoCAD DXF dosyasını seçin.\nAlgoritma delikleri ve havuzları otomatik tanır.")
            lbl_dxf.setStyleSheet("color: white;")
            d_layout.addWidget(lbl_dxf)

            hz_layout = QHBoxLayout()
            hz_layout.addWidget(QLabel("Standart Z Derinliği (-mm):"))
            self.dxf_z = QLineEdit("10")
            self.dxf_z.setFixedWidth(50)
            hz_layout.addWidget(self.dxf_z)
            d_layout.addLayout(hz_layout)

            btn_dxf = QPushButton("DXF DOSYASI SEÇ VE İŞLE (.dxf)")
            btn_dxf.setStyleSheet(
                "background-color: #e67e22; color: white; height: 45px; font-weight: bold; font-size: 14px;")
            btn_dxf.clicked.connect(self.load_dxf_file)
            d_layout.addWidget(btn_dxf)
            layout.addWidget(dxf_group)
            layout.addStretch()

        def load_dxf_file(self):
            try:
                import ezdxf
            except ImportError:
                QMessageBox.warning(self, "Eksik Kütüphane",
                                    "Sistemde ezdxf kütüphanesi bulunamadı.\nTerminalden pip install ezdxf komutu ile kurun.")
                return

            options = QFileDialog.Options()
            fileName, _ = QFileDialog.getOpenFileName(self, "Teknik Resim (DXF) Seç", "", "DXF Dosyaları (*.dxf)",
                                                      options=options)
            if not fileName:
                return

            try:
                doc = ezdxf.readfile(fileName)
                msp = doc.modelspace()
                z_depth = float(self.dxf_z.text())
                code = "(V34 - DXF OTO-CAM URETIMI)\nG54\nG00 X0 Y0 Z50\n"
                circles = msp.query('CIRCLE')
                drills = [c for c in circles if c.dxf.radius < 10]
                pockets = [c for c in circles if c.dxf.radius >= 10]

                if pockets:
                    code += "\n(--- Dairesel Havuz Islemleri ---)\nT1 M06 (Havuz Frezesi Cagir)\nM08\n"
                    for p in pockets:
                        cx, cy = p.dxf.center.x, p.dxf.center.y
                        r = p.dxf.radius
                        code += f"G00 X{cx + r:.3f} Y{cy:.3f} Z5\n"
                        code += f"G01 Z-{z_depth} F150\n"
                        code += f"G03 X{cx + r:.3f} Y{cy:.3f} I-{r:.3f} J0\n"
                        code += "G00 Z50\n"
                    code += "M09\nM01\n"

                if drills:
                    code += "\n(--- Matkap Delik Islemleri - G73 Yuksek Hizli Gagalama ---)\nT3 M06 (Matkap Ucu Cagir)\nM08\n"
                    for i, d in enumerate(drills):
                        cx, cy = d.dxf.center.x, d.dxf.center.y
                        if i == 0:
                            code += f"G00 X{cx:.3f} Y{cy:.3f}\n"
                            code += f"G73 X{cx:.3f} Y{cy:.3f} Z-{z_depth + 3} R2 Q5 F100\n"
                        else:
                            code += f"G73 X{cx:.3f} Y{cy:.3f} Z-{z_depth + 3} R2 Q5\n"
                    code += "G80\nM09\n"

                code += "G00 Z100\nG00 X0 Y0\nM30"
                self.txt_code.setPlainText(code)
                self.tabs.setCurrentIndex(1)
                QMessageBox.information(self, "DXF Başarılı",
                                        f"DXF işlendi: {len(pockets)} havuz, {len(drills)} delik bulundu.")
            except Exception as e:
                QMessageBox.critical(self, "DXF Hatası", f"Hata:\n{str(e)}")

        def generate_cam_code(self):
            try:
                cx, cy = float(self.cam_cx.text()), float(self.cam_cy.text())
                outer_d, inner_d = float(self.cam_outer.text()), float(self.cam_inner.text())
                holes = max(1, int(self.cam_holes.text()))
                pcd, z_depth = float(self.cam_pcd.text()), float(self.cam_z.text())
            except Exception:
                return

            code = "(SABLON OTO-CAM)\nG54\n"
            code += "T1 M06 (Freze)\nM08\n"
            code += f"G00 X{cx + inner_d / 2} Y{cy} Z5\n"
            code += f"G01 Z-{z_depth} F150\n"
            code += f"G03 X{cx + inner_d / 2} Y{cy} I-{inner_d / 2} J0\n"
            code += "G00 Z50\nM09\nM01\n"

            code += "T3 M06 (Matkap)\nM08\n"
            for i in range(holes):
                angle = math.radians(i * (360 / holes))
                hx = cx + (pcd / 2) * math.cos(angle)
                hy = cy + (pcd / 2) * math.sin(angle)
                if i == 0:
                    code += f"G00 X{hx:.3f} Y{hy:.3f}\n"
                    code += f"G73 X{hx:.3f} Y{hy:.3f} Z-{z_depth + 5} R2 Q5 F100\n"
                else:
                    code += f"G73 X{hx:.3f} Y{hy:.3f} Z-{z_depth + 5} R2 Q5\n"

            code += "G80\nM09\nG00 Z100\nG00 X0 Y0\nM30"
            self.txt_code.setPlainText(code)
            self.tabs.setCurrentIndex(1)

        def setup_mem_tab(self):
            layout = QVBoxLayout(self.tab_mem)
            stock_group = QGroupBox("Kütük, Takım ve Fikstür Ayarları")
            stock_group.setStyleSheet("color: #4ca1af; font-weight: bold;")
            s_layout = QHBoxLayout(stock_group)
            self.entry_x = QLineEdit("200")
            self.entry_x.setFixedWidth(40)
            self.entry_y = QLineEdit("200")
            self.entry_y.setFixedWidth(40)
            self.entry_z = QLineEdit("50")
            self.entry_z.setFixedWidth(40)
            s_layout.addWidget(QLabel("X:"))
            s_layout.addWidget(self.entry_x)
            s_layout.addWidget(QLabel("Y:"))
            s_layout.addWidget(self.entry_y)
            s_layout.addWidget(QLabel("Z:"))
            s_layout.addWidget(self.entry_z)

            self.cb_vise = QCheckBox("3D Çelik Mengene Kullan")
            self.cb_vise.setChecked(True)
            self.cb_vise.setStyleSheet("color: #e74c3c;")
            s_layout.addWidget(self.cb_vise)

            self.cb_5axis = QCheckBox("5 Eksen Döner Tabla (İsteğe Bağlı)")
            self.cb_5axis.setChecked(False)
            self.cb_5axis.setStyleSheet("color: #2ecc71;")
            s_layout.addWidget(self.cb_5axis)
            layout.addWidget(stock_group)

            lib_group = QGroupBox("Takım Kütüphanesi (ATC) ve Uzunluk")
            lib_group.setStyleSheet("color: #f39c12; font-weight: bold;")
            lib_layout = QGridLayout(lib_group)

            lib_layout.addWidget(QLabel("T1:"), 0, 0)
            self.t1_type = QComboBox()
            self.t1_type.addItems(["Düz Freze", "Küre Freze", "Matkap"])
            self.t1_type.setStyleSheet("color: black;")
            self.t1_d = QLineEdit("16")
            self.t1_d.setFixedWidth(30)
            self.t1_l = QLineEdit("25")
            self.t1_l.setFixedWidth(30)
            lib_layout.addWidget(self.t1_type, 0, 1)
            lib_layout.addWidget(QLabel("Çap:"), 0, 2)
            lib_layout.addWidget(self.t1_d, 0, 3)
            lib_layout.addWidget(QLabel("Boy(H):"), 0, 4)
            lib_layout.addWidget(self.t1_l, 0, 5)

            lib_layout.addWidget(QLabel("T2:"), 1, 0)
            self.t2_type = QComboBox()
            self.t2_type.addItems(["Düz Freze", "Küre Freze", "Matkap"])
            self.t2_type.setCurrentText("Küre Freze")
            self.t2_type.setStyleSheet("color: black;")
            self.t2_d = QLineEdit("10")
            self.t2_d.setFixedWidth(30)
            self.t2_l = QLineEdit("25")
            self.t2_l.setFixedWidth(30)
            lib_layout.addWidget(self.t2_type, 1, 1)
            lib_layout.addWidget(QLabel("Çap:"), 1, 2)
            lib_layout.addWidget(self.t2_d, 1, 3)
            lib_layout.addWidget(QLabel("Boy(H):"), 1, 4)
            lib_layout.addWidget(self.t2_l, 1, 5)

            lib_layout.addWidget(QLabel("T3:"), 2, 0)
            self.t3_type = QComboBox()
            self.t3_type.addItems(["Düz Freze", "Küre Freze", "Matkap"])
            self.t3_type.setCurrentText("Matkap")
            self.t3_type.setStyleSheet("color: black;")
            self.t3_d = QLineEdit("8")
            self.t3_d.setFixedWidth(30)
            self.t3_l = QLineEdit("30")
            self.t3_l.setFixedWidth(30)
            lib_layout.addWidget(self.t3_type, 2, 1)
            lib_layout.addWidget(QLabel("Çap:"), 2, 2)
            lib_layout.addWidget(self.t3_d, 2, 3)
            lib_layout.addWidget(QLabel("Boy(H):"), 2, 4)
            lib_layout.addWidget(self.t3_l, 2, 5)

            layout.addWidget(lib_group)

            layout.addWidget(QLabel("G-Kod Programı:"))
            self.txt_code = QTextEdit()
            self.txt_code.setStyleSheet("background-color: #1e1e1e; color: white; font-family: Consolas; font-size: 14px;")

            sample = "(V34 - STANDART 3 EKSEN KATI ISLEME)\n"
            sample += "G54\n"
            sample += "T1 M06 (16mm Düz Freze)\n"
            sample += "M08\n\n"
            sample += "(3 Eksen Helisel Havuz Bosaltma)\n"
            sample += "G00 X100 Y100 Z5\n"
            sample += "G01 Z0 F150\n"
            sample += "G02 X100 Y100 Z-15 I20 J0 F200\n"
            sample += "G02 X100 Y100 Z-15 I20 J0\n"
            sample += "G00 Z50\n\n"
            sample += "(Merkeze Delik Delme)\n"
            sample += "T3 M06 (8mm Matkap)\n"
            sample += "M08\n"
            sample += "G00 X100 Y100 Z5\n"
            sample += "G83 X100 Y100 Z-20 R2 Q5 F100\n"
            sample += "G80\n"
            sample += "G00 Z100\n"
            sample += "M09\n"
            sample += "M30"

            self.txt_code.setPlainText(sample)
            layout.addWidget(self.txt_code)

            layout.addWidget(QLabel("İşleme Hızı (FPS Çarpanı):"))
            self.speed_slider = QSlider(Qt.Horizontal)
            self.speed_slider.setRange(1, 100)
            self.speed_slider.setValue(25)
            layout.addWidget(self.speed_slider)

            btn_layout = QHBoxLayout()
            self.btn_run = QPushButton("SİMÜLASYONU BAŞLAT")
            self.btn_run.setStyleSheet("background-color: #28a745; color: white; height: 40px; font-weight: bold;")
            self.btn_run.clicked.connect(self.run_simulation)

            btn_reset = QPushButton("SIFIRLA")
            btn_reset.setStyleSheet("background-color: #dc3545; color: white; height: 40px; font-weight: bold;")
            btn_reset.clicked.connect(lambda: self.reset_machine(False))

            btn_layout.addWidget(self.btn_run)
            btn_layout.addWidget(btn_reset)
            layout.addLayout(btn_layout)

        def setup_jog_tab(self):
            layout = QVBoxLayout(self.tab_jog)
            off_group = QGroupBox("G54-G59 WORK OFFSET (Çoklu İş Parçası Sıfırlama)")
            off_group.setStyleSheet("color: #f1c40f; font-weight: bold;")
            off_layout = QVBoxLayout(off_group)

            lbl_usta = QLabel("📌 USTANIN SIFIRLAMA NOTLARI:\n"
                              "Çoklu Mengene: Farklı parçalar için G54, G55, G56 koordinatlarını seçip ayrı ayrı sıfırlayabilirsiniz.\n"
                              "• Z Ekseni Sıfırlama: Takımı aşağı indirin, şeffaf naylon sıkıştığı anda Z için 'PART ZERO SET' yapın.")
            lbl_usta.setStyleSheet(
                "color: #bdc3c7; font-size: 12px; font-style: italic; background-color: #2c3e50; padding: 10px;")
            lbl_usta.setWordWrap(True)
            off_layout.addWidget(lbl_usta)

            wcs_layout = QHBoxLayout()
            wcs_layout.addWidget(QLabel("Aktif Sıfırlama Hafızası (WCS):"))
            self.combo_wcs = QComboBox()
            self.combo_wcs.addItems(["G54", "G55", "G56", "G57", "G58", "G59"])
            self.combo_wcs.setStyleSheet("color: black; font-weight: bold;")
            self.combo_wcs.currentTextChanged.connect(self.change_active_wcs)
            wcs_layout.addWidget(self.combo_wcs)
            off_layout.addLayout(wcs_layout)

            self.cb_nylon = QCheckBox("Z Sıfırlamada Şeffaf Naylon Payını (0.1 mm) Otomatik Düş")
            self.cb_nylon.setStyleSheet("color: #2ecc71; font-weight: bold; padding-top: 5px;")
            self.cb_nylon.setChecked(True)
            off_layout.addWidget(self.cb_nylon)

            btn_layout = QHBoxLayout()
            btn_x0 = QPushButton("X - ZERO SET")
            btn_x0.setStyleSheet("background-color: #34495e; color: white; height: 35px;")
            btn_y0 = QPushButton("Y - ZERO SET")
            btn_y0.setStyleSheet("background-color: #34495e; color: white; height: 35px;")
            btn_z0 = QPushButton("Z - ZERO SET")
            btn_z0.setStyleSheet("background-color: #e67e22; color: white; height: 35px;")
            btn_x0.clicked.connect(lambda: self.zero_axis('X'))
            btn_y0.clicked.connect(lambda: self.zero_axis('Y'))
            btn_z0.clicked.connect(lambda: self.zero_axis('Z'))
            btn_layout.addWidget(btn_x0)
            btn_layout.addWidget(btn_y0)
            btn_layout.addWidget(btn_z0)
            off_layout.addLayout(btn_layout)
            layout.addWidget(off_group)

            jog_group = QGroupBox("Jog / Handle (El Çarkı)")
            jog_group.setStyleSheet("color: #e74c3c; font-weight: bold;")
            jog_layout = QVBoxLayout(jog_group)

            radio_layout = QHBoxLayout()
            self.bg_jog = QButtonGroup()
            r1 = QRadioButton("0.1 mm")
            r2 = QRadioButton("2.0 mm")
            r3 = QRadioButton("10.0 mm")
            r2.setChecked(True)
            self.bg_jog.addButton(r1, 1)
            self.bg_jog.addButton(r2, 20)
            self.bg_jog.addButton(r3, 100)
            radio_layout.addWidget(r1)
            radio_layout.addWidget(r2)
            radio_layout.addWidget(r3)
            jog_layout.addLayout(radio_layout)

            jbtn_layout = QHBoxLayout()
            btn_y_p = QPushButton("Y+")
            btn_y_p.clicked.connect(lambda: self.jog_move('Y', 1))
            btn_y_m = QPushButton("Y-")
            btn_y_m.clicked.connect(lambda: self.jog_move('Y', -1))
            btn_x_m = QPushButton("X-")
            btn_x_m.clicked.connect(lambda: self.jog_move('X', -1))
            btn_x_p = QPushButton("X+")
            btn_x_p.clicked.connect(lambda: self.jog_move('X', 1))
            btn_z_p = QPushButton("Z+")
            btn_z_p.clicked.connect(lambda: self.jog_move('Z', 1))
            btn_z_m = QPushButton("Z-")
            btn_z_m.clicked.connect(lambda: self.jog_move('Z', -1))

            for b in [btn_y_p, btn_y_m, btn_x_m, btn_x_p, btn_z_p, btn_z_m]:
                b.setStyleSheet(
                    "background-color: #4a4f54; color: white; height: 40px; font-size: 14px; font-weight: bold;")
            btn_z_p.setStyleSheet("background-color: #4a4f54; color: cyan;")
            btn_z_m.setStyleSheet("background-color: #4a4f54; color: cyan;")
            jbtn_layout.addWidget(btn_x_m)
            jbtn_layout.addWidget(btn_y_m)
            jbtn_layout.addWidget(btn_y_p)
            jbtn_layout.addWidget(btn_x_p)
            jbtn_layout.addWidget(btn_z_p)
            jbtn_layout.addWidget(btn_z_m)
            jog_layout.addLayout(jbtn_layout)
            layout.addWidget(jog_group)

            mdi_group = QGroupBox("MDI (Manuel Komut İşleme)")
            mdi_group.setStyleSheet("color: #2ecc71; font-weight: bold;")
            mdi_layout = QVBoxLayout(mdi_group)
            self.entry_mdi = QLineEdit()
            self.entry_mdi.setStyleSheet("background-color: #1e1e1e; color: white; font-size: 14px; padding: 5px;")
            btn_mdi = QPushButton("MDI ÇALIŞTIR")
            btn_mdi.setStyleSheet("background-color: #d9534f; color: white; height: 35px; font-weight: bold;")
            btn_mdi.clicked.connect(self.run_mdi)
            mdi_layout.addWidget(self.entry_mdi)
            mdi_layout.addWidget(btn_mdi)
            layout.addWidget(mdi_group)
            layout.addStretch()

        def init_3d_environment(self):
            grid = gl.GLGridItem()
            grid.setSize(x=500, y=500)
            grid.setSpacing(x=50, y=50)
            self.gl_widget.addItem(grid)
            axis = gl.GLAxisItem()
            axis.setSize(x=100, y=100, z=100)
            self.gl_widget.addItem(axis)

        def get_stock_dims(self):
            try:
                return {'X': float(self.entry_x.text()), 'Y': float(self.entry_y.text()), 'Z': float(self.entry_z.text())}
            except Exception:
                return {'X': 200, 'Y': 200, 'Z': 50}

        def load_tool_library(self):
            self.tool_library = {
                'T1': {'type': self.t1_type.currentText(), 'd': float(self.t1_d.text() or 16),
                       'l': float(self.t1_l.text() or 25)},
                'T2': {'type': self.t2_type.currentText(), 'd': float(self.t2_d.text() or 10),
                       'l': float(self.t2_l.text() or 25)},
                'T3': {'type': self.t3_type.currentText(), 'd': float(self.t3_d.text() or 8),
                       'l': float(self.t3_l.text() or 30)}
            }

        def highlight_line(self, line_index):
            if self._son_vurgulanan_satir == line_index:
                return
            self._son_vurgulanan_satir = line_index
            extraSelections = []
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(255, 255, 0, 80)
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            cursor = self.txt_code.textCursor()
            cursor.setPosition(self.txt_code.document().findBlockByNumber(line_index).position())
            selection.cursor = cursor
            extraSelections.append(selection)
            self.txt_code.setExtraSelections(extraSelections)

        def change_active_wcs(self, wcs_name):
            self.active_wcs = wcs_name
            self.update_ui_labels()

        def reset_machine(self, first_start=False):
            self.sim_active = False
            self.is_paused = False
            self.timer.stop()
            self.holder_crash = False
            self.vise_crash = False
            self.tool_rotation_angle = 0
            self._son_vurgulanan_satir = -1

            if hasattr(self, 'btn_run'):
                self.btn_run.setText("SİMÜLASYONU BAŞLAT")
                self.btn_run.setStyleSheet("background-color: #28a745; color: white; height: 40px; font-weight: bold;")

            if not first_start:
                self.current_pos = {'X': -20.0, 'Y': -20.0, 'Z': 50.0, 'A': 0.0, 'C': 0.0}
            self.mode = 'G00'
            self.comp_mode = 'G40'
            self.total_time_min = 0.0
            self.total_distance = 0.0
            self.crash_count = 0
            self.paths = []
            self.current_steps = []
            self.current_tool_id = 'T1'
            self.drawn_tool_id = None
            self.drawn_coolant_state = None
            self.coolant_active = False
            self.macro_vars.clear()

            if hasattr(self, 'txt_code'):
                self.txt_code.setExtraSelections([])

            for line in self.path_lines:
                self.safe_remove(line)
            self.path_lines.clear()

            self.update_ui_labels()
            dims = self.get_stock_dims()

            self.safe_remove(self.surface)
            self.safe_remove(self.stock_walls)
            self.safe_remove(self.rotary_table_mesh)
            for jaw in self.vise_jaws:
                self.safe_remove(jaw)
            self.vise_jaws.clear()

            grid_res = max(1.0, min(dims['X'], dims['Y']) / 150.0)
            x_val = np.arange(0, dims['X'] + grid_res, grid_res)
            y_val = np.arange(0, dims['Y'] + grid_res, grid_res)
            self.X_grid_1d = x_val
            self.Y_grid_1d = y_val
            self.X_grid, self.Y_grid = np.meshgrid(x_val, y_val, indexing='ij')
            self.Z_grid = np.zeros_like(self.X_grid)

            colors = np.ones((len(x_val), len(y_val), 4))
            colors[..., 0] = 0.65
            colors[..., 1] = 0.70
            colors[..., 2] = 0.75
            self.surf_colors = colors

            self.orig_Z_grid = self.Z_grid.copy()
            self.orig_surf_colors = self.surf_colors.copy()

            self.surface = gl.GLSurfacePlotItem(x=x_val, y=y_val, z=self.Z_grid, colors=self.surf_colors.reshape(-1, 4),
                                                shader='shaded', smooth=False)
            self.gl_widget.addItem(self.surface)

            verts = np.array([
                [0, 0, 0], [dims['X'], 0, 0], [dims['X'], dims['Y'], 0], [0, dims['Y'], 0],
                [0, 0, -dims['Z']], [dims['X'], 0, -dims['Z']], [dims['X'], dims['Y'], -dims['Z']],
                [0, dims['Y'], -dims['Z']]
            ])
            faces = np.array([
                [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5], [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7], [4, 5, 6], [4, 6, 7]
            ])
            self.orig_walls_verts = verts.copy()
            self.walls_faces = faces
            self.stock_walls = gl.GLMeshItem(meshdata=gl.MeshData(vertexes=verts, faces=faces), smooth=False,
                                             color=(0.4, 0.45, 0.5, 1.0), shader='shaded')
            self.gl_widget.addItem(self.stock_walls)

            if hasattr(self, 'cb_vise') and self.cb_vise.isChecked():
                jaw1_verts = np.array([
                    [-10, 0, -10], [dims['X'] + 10, 0, -10], [dims['X'] + 10, -30, -10], [-10, -30, -10],
                    [-10, 0, -dims['Z'] - 20], [dims['X'] + 10, 0, -dims['Z'] - 20], [dims['X'] + 10, -30, -dims['Z'] - 20],
                    [-10, -30, -dims['Z'] - 20]
                ])
                self.orig_jaw1_verts = jaw1_verts.copy()
                self.jaw_faces = faces
                jaw1_mesh = gl.GLMeshItem(meshdata=gl.MeshData(vertexes=jaw1_verts, faces=faces), smooth=False,
                                          color=(0.2, 0.2, 0.2, 1.0), shader='shaded')
                self.gl_widget.addItem(jaw1_mesh)
                self.vise_jaws.append(jaw1_mesh)

                jaw2_verts = np.array([
                    [-10, dims['Y'] + 30, -10], [dims['X'] + 10, dims['Y'] + 30, -10], [dims['X'] + 10, dims['Y'], -10],
                    [-10, dims['Y'], -10],
                    [-10, dims['Y'] + 30, -dims['Z'] - 20], [dims['X'] + 10, dims['Y'] + 30, -dims['Z'] - 20],
                    [dims['X'] + 10, dims['Y'], -dims['Z'] - 20], [-10, dims['Y'], -dims['Z'] - 20]
                ])
                self.orig_jaw2_verts = jaw2_verts.copy()
                jaw2_mesh = gl.GLMeshItem(meshdata=gl.MeshData(vertexes=jaw2_verts, faces=faces), smooth=False,
                                          color=(0.2, 0.2, 0.2, 1.0), shader='shaded')
                self.gl_widget.addItem(jaw2_mesh)
                self.vise_jaws.append(jaw2_mesh)

            if hasattr(self, 'cb_5axis') and self.cb_5axis.isChecked():
                rt_mesh_data = self.create_solid_cylinder_mesh(dims['X'] / 1.2, 20, cols=36)
                self.orig_table_verts = rt_mesh_data.vertexes().copy()
                for v in self.orig_table_verts:
                    v[0] += dims['X'] / 2
                    v[1] += dims['Y'] / 2
                    v[2] -= dims['Z'] + 20
                self.table_faces = rt_mesh_data.faces()
                self.rotary_table_mesh = gl.GLMeshItem(
                    meshdata=gl.MeshData(vertexes=self.orig_table_verts, faces=self.table_faces), smooth=False,
                    color=(0.25, 0.25, 0.25, 1.0), shader='shaded')
                self.gl_widget.addItem(self.rotary_table_mesh)

            self.apply_5axis_transform(self.current_pos['A'], self.current_pos['C'])
            if hasattr(self, 't1_type'):
                self.load_tool_library()
            self.update_tool_mesh()

        def apply_5axis_transform(self, a_angle, c_angle):
            dims = self.get_stock_dims()
            cx = dims['X'] / 2
            cy = dims['Y'] / 2
            cz = -dims['Z']

            transform = pg.Transform3D()
            transform.translate(cx, cy, cz)
            transform.rotate(c_angle, 0, 0, 1)
            transform.rotate(a_angle, 1, 0, 0)
            transform.translate(-cx, -cy, -cz)

            if self.surface:
                self.surface.setTransform(transform)
            if self.stock_walls:
                self.stock_walls.setTransform(transform)
            for jaw in self.vise_jaws:
                jaw.setTransform(transform)

            if self.rotary_table_mesh:
                rt_trans = pg.Transform3D()
                rt_trans.translate(cx, cy, cz)
                rt_trans.rotate(c_angle, 0, 0, 1)
                rt_trans.rotate(a_angle, 1, 0, 0)
                rt_trans.translate(-cx, -cy, -cz)
                self.rotary_table_mesh.setTransform(rt_trans)

        def update_tool_mesh(self):
            tool_data = self.tool_library.get(self.current_tool_id, {'d': 16.0, 'type': 'Düz Freze', 'l': 25.0})
            tool_r = tool_data['d'] / 2.0
            tool_l = tool_data['l']

            if self.drawn_tool_id == self.current_tool_id and self.tool_mesh is not None:
                self.tool_rotation_angle = getattr(self, 'tool_rotation_angle', 0) + (15 if self.sim_active else 0)

                self.tool_mesh.resetTransform()
                self.tool_mesh.rotate(self.tool_rotation_angle, 0, 0, 1)
                self.tool_mesh.translate(self.current_pos['X'], self.current_pos['Y'], self.current_pos['Z'])

                self.spindle_mesh.resetTransform()
                self.spindle_mesh.rotate(self.tool_rotation_angle, 0, 0, 1)
                self.spindle_mesh.translate(self.current_pos['X'], self.current_pos['Y'], self.current_pos['Z'] + tool_l)

                if self.coolant_active:
                    if self.coolant_mesh is None or not self.drawn_coolant_state:
                        self.safe_remove(self.coolant_mesh)
                        c_mesh = gl.MeshData.cylinder(rows=1, cols=16, radius=[tool_r + 15, tool_r + 2], length=tool_l + 5)
                        self.coolant_mesh = gl.GLMeshItem(meshdata=c_mesh, smooth=True, color=(0.0, 0.6, 1.0, 0.4), shader='shaded')
                        self.gl_widget.addItem(self.coolant_mesh)
                        self.drawn_coolant_state = True
                    self.coolant_mesh.resetTransform()
                    self.coolant_mesh.translate(self.current_pos['X'], self.current_pos['Y'], self.current_pos['Z'])
                elif self.drawn_coolant_state:
                    self.safe_remove(self.coolant_mesh)
                    self.coolant_mesh = None
                    self.drawn_coolant_state = False
                return

            self.safe_remove(self.tool_mesh)
            self.safe_remove(self.spindle_mesh)
            self.safe_remove(self.coolant_mesh)
            self.coolant_mesh = None

            t_color = (0.83, 0.68, 0.21, 1)
            if tool_data['type'] == 'Matkap':
                t_color = (0.2, 0.2, 0.25, 1)
            elif tool_data['type'] == 'Küre Freze':
                t_color = (0.7, 0.7, 0.7, 1)

            md_tool = self.create_solid_cylinder_mesh(tool_r, tool_l, cols=16)
            self.tool_mesh = gl.GLMeshItem(meshdata=md_tool, smooth=False, color=t_color, shader='shaded')
            self.tool_mesh.translate(self.current_pos['X'], self.current_pos['Y'], self.current_pos['Z'])
            self.gl_widget.addItem(self.tool_mesh)

            md_spindle = self.create_solid_cylinder_mesh(tool_r + 14, 40, cols=20)
            self.spindle_mesh = gl.GLMeshItem(meshdata=md_spindle, smooth=False, color=(0.15, 0.15, 0.15, 1),
                                              shader='shaded')
            self.spindle_mesh.translate(self.current_pos['X'], self.current_pos['Y'], self.current_pos['Z'] + tool_l)
            self.gl_widget.addItem(self.spindle_mesh)

            if self.coolant_active:
                c_mesh = gl.MeshData.cylinder(rows=1, cols=16, radius=[tool_r + 15, tool_r + 2], length=tool_l + 5)
                self.coolant_mesh = gl.GLMeshItem(meshdata=c_mesh, smooth=True, color=(0.0, 0.6, 1.0, 0.4), shader='shaded')
                self.coolant_mesh.translate(self.current_pos['X'], self.current_pos['Y'], self.current_pos['Z'])
                self.gl_widget.addItem(self.coolant_mesh)

            self.drawn_tool_id = self.current_tool_id
            self.drawn_coolant_state = self.coolant_active

        def zero_axis(self, axis):
            if axis == 'Z' and self.cb_nylon.isChecked():
                self.current_pos[axis] = 0.1
                msg = f"{self.active_wcs} Work Offset:\nZ Ekseni başarıyla sıfırlandı.\n(Şeffaf naylon payı olan 0.1mm telafi edildi.)"
            else:
                self.current_pos[axis] = 0.0
                msg = f"{self.active_wcs} Work Offset:\n{axis} Ekseni başarıyla 0.000 olarak sıfırlandı."

            self.update_ui_labels()
            self.update_tool_mesh()
            QMessageBox.information(self, f"{self.active_wcs} Part Zero Offset", msg)

        def jog_move(self, axis, direction):
            val = float(self.bg_jog.checkedId()) / 10.0
            val = val * direction
            self.current_pos[axis] += val
            if self.current_pos['Z'] < 0:
                self.crash_count += 1
            self.update_ui_labels()
            self.update_tool_mesh()
            if axis in ['A', 'C']:
                self.apply_5axis_transform(self.current_pos['A'], self.current_pos['C'])

        def update_ui_labels(self):
            if hasattr(self, 'pos_lbl'):
                self.pos_lbl.setText(
                    f"X: {self.current_pos['X']:8.3f}  Y: {self.current_pos['Y']:8.3f}  Z: {self.current_pos['Z']:8.3f}\nA: {self.current_pos['A']:8.3f}°   C: {self.current_pos['C']:8.3f}°")
                h, m, s = int(self.total_time_min // 60), int(self.total_time_min % 60), int(
                    (self.total_time_min * 60) % 60)
                cool_str = "AÇIK" if self.coolant_active else "KAPALI"
                self.stats_lbl.setText(
                    f"Süre: {h:02d}:{m:02d}:{s:02d} | Mesafe: {self.total_distance:.1f} mm\nÇarpma: {self.crash_count} | Takım: {self.current_tool_id} | WCS: {self.active_wcs} | Soğutma: {cool_str}")

                if self.crash_count > 0 or self.holder_crash or self.vise_crash:
                    self.stats_lbl.setStyleSheet("color: red; font-family: Consolas; font-size: 12px; font-weight: bold;")

                comp_str = "KAPALI"
                if self.comp_mode == 'G41':
                    comp_str = "SOLA"
                elif self.comp_mode == 'G42':
                    comp_str = "SAĞA"
                self.comp_lbl.setText(f"Takım Telafisi: {self.comp_mode} ({comp_str})")
                if self.comp_mode != 'G40':
                    self.comp_lbl.setStyleSheet(
                        "color: #2ecc71; font-family: Consolas; font-size: 12px; font-weight: bold;")
                else:
                    self.comp_lbl.setStyleSheet(
                        "color: #f39c12; font-family: Consolas; font-size: 12px; font-weight: bold;")

        def calculate_dist(self, start, end, is_rapid, arc_length=0):
            dist = arc_length if arc_length > 0 else math.sqrt(
                (end['X'] - start['X']) ** 2 + (end['Y'] - start['Y']) ** 2 + (end['Z'] - start['Z']) ** 2)
            self.total_distance += dist
            if is_rapid:
                self.total_time_min += dist / self.rapid_rate
            elif self.feed_rate > 0:
                self.total_time_min += dist / self.feed_rate

        def run_mdi(self):
            code = self.entry_mdi.text().strip().upper()
            if not code:
                return
            self.run_gcode_text(code)
            self.entry_mdi.clear()

        def run_simulation(self):
            if self.sim_active and not self.is_paused:
                self.pause_simulation()
                return
            if self.is_paused:
                self.resume_simulation()
                return
            self.load_tool_library()
            start_pos = self.current_pos.copy()
            self.reset_machine()
            self.current_pos = start_pos
            self.coolant_active = False

            self.btn_run.setText("DURAKLAT (PAUSE)")
            self.btn_run.setStyleSheet("background-color: #f39c12; color: black; height: 40px; font-weight: bold;")

            code = self.txt_code.toPlainText().strip().upper()
            self.run_gcode_text(code)

        def pause_simulation(self):
            self.is_paused = True
            self.timer.stop()
            self.btn_run.setText("DEVAM ET (RESUME)")
            self.btn_run.setStyleSheet("background-color: #3498db; color: white; height: 40px; font-weight: bold;")

        def resume_simulation(self):
            self.is_paused = False
            self.timer.start(16)
            self.btn_run.setText("DURAKLAT (PAUSE)")
            self.btn_run.setStyleSheet("background-color: #f39c12; color: black; height: 40px; font-weight: bold;")

        def run_gcode_text(self, text):
            if not text:
                return
            self.paths = []
            sim_pos = self.current_pos.copy()

            r_val, q_val = 2.0, 5.0
            parsing_tool = self.current_tool_id
            pending_tool = parsing_tool

            for line_idx, line in enumerate(text.split('\n')):
                line_clean = line.split('(')[0].strip()
                if not line_clean:
                    continue

                words = line_clean.split()
                target = sim_pos.copy()
                is_move = False
                i_val, j_val = 0.0, 0.0
                is_arc = False

                for w in words:
                    if w in ['G40', 'G41', 'G42']:
                        self.comp_mode = w
                        self.paths.append(
                            {'mode': 'COMP', 'start': sim_pos.copy(), 'end': sim_pos.copy(), 'tool_id': parsing_tool,
                             'line_idx': line_idx, 'comp': w})
                    elif w in ['G54', 'G55', 'G56', 'G57', 'G58', 'G59']:
                        self.paths.append(
                            {'mode': 'WCS', 'start': sim_pos.copy(), 'end': sim_pos.copy(), 'tool_id': parsing_tool,
                             'line_idx': line_idx, 'wcs': w})
                    elif w.startswith('F'):
                        try:
                            self.feed_rate = float(w[1:])
                        except Exception:
                            pass
                    elif w.startswith('R'):
                        try:
                            r_val = float(w[1:])
                        except Exception:
                            pass
                    elif w.startswith('Q'):
                        try:
                            q_val = max(abs(float(w[1:])), 0.5)
                        except Exception:
                            pass
                    elif w.startswith('T'):
                        pending_tool = w
                    elif w.startswith('M'):
                        if w in ['M06', 'M6']:
                            p_zmax = sim_pos.copy()
                            p_zmax['Z'] = 100.0
                            if sim_pos['Z'] != 100.0:
                                self.paths.append(
                                    {'mode': 'G00', 'is_crash': False, 'start': sim_pos.copy(), 'end': p_zmax.copy(),
                                     'rapid': True, 'tool_id': parsing_tool, 'line_idx': line_idx, 'comp': self.comp_mode})
                                sim_pos = p_zmax.copy()
                            self.paths.append(
                                {'mode': 'M06', 'start': sim_pos.copy(), 'end': sim_pos.copy(), 'tool_id': pending_tool,
                                 'line_idx': line_idx, 'rapid': True, 'comp': self.comp_mode})
                            parsing_tool = pending_tool
                        elif w in ['M01', 'M1', 'M08', 'M8', 'M09', 'M9']:
                            self.paths.append(
                                {'mode': w, 'start': sim_pos.copy(), 'end': sim_pos.copy(), 'tool_id': parsing_tool,
                                 'line_idx': line_idx, 'rapid': True, 'comp': self.comp_mode})

                for w in words:
                    letter, value = w[0], w[1:]
                    try:
                        val = float(value)
                        if letter == 'G':
                            if w not in ['G54', 'G55', 'G56', 'G57', 'G58', 'G59', 'G40', 'G41', 'G42']:
                                self.mode = w
                            if self.mode in ['G02', 'G03']:
                                is_arc = True
                        elif letter in ['X', 'Y', 'Z', 'A', 'C']:
                            target[letter] = val
                            is_move = True
                        elif letter == 'I':
                            i_val = val
                        elif letter == 'J':
                            j_val = val
                    except Exception:
                        continue

                if self.mode in ['G02', 'G03']:
                    is_arc = True

                if is_move and self.mode in ['G00', 'G01', 'G02', 'G03']:
                    is_rapid = (self.mode == 'G00')
                    is_crash = (is_rapid and target['Z'] < 0)
                    path_info = {'mode': self.mode, 'is_crash': is_crash, 'start': sim_pos.copy(), 'end': target.copy(),
                                 'rapid': is_rapid, 'is_arc': is_arc, 'I': i_val, 'J': j_val, 'tool_id': parsing_tool,
                                 'line_idx': line_idx, 'comp': self.comp_mode}
                    self.paths.append(path_info)
                    sim_pos = target.copy()

                elif is_move and self.mode in ['G81', 'G83', 'G73']:
                    p1 = sim_pos.copy()
                    p1['X'] = target['X']
                    p1['Y'] = target['Y']
                    if p1['X'] != sim_pos['X'] or p1['Y'] != sim_pos['Y']:
                        self.paths.append(
                            {'mode': 'G00', 'is_crash': False, 'start': sim_pos.copy(), 'end': p1.copy(), 'rapid': True,
                             'is_arc': False, 'tool_id': parsing_tool, 'line_idx': line_idx, 'comp': self.comp_mode})
                        sim_pos = p1.copy()

                    p2 = sim_pos.copy()
                    p2['Z'] = r_val
                    if p2['Z'] != sim_pos['Z']:
                        self.paths.append(
                            {'mode': 'G00', 'is_crash': False, 'start': sim_pos.copy(), 'end': p2.copy(), 'rapid': True,
                             'is_arc': False, 'tool_id': parsing_tool, 'line_idx': line_idx, 'comp': self.comp_mode})
                        sim_pos = p2.copy()

                    if self.mode == 'G81':
                        p3 = sim_pos.copy()
                        p3['Z'] = target['Z']
                        self.paths.append(
                            {'mode': 'G01', 'is_crash': False, 'start': sim_pos.copy(), 'end': p3.copy(), 'rapid': False,
                             'is_arc': False, 'tool_id': parsing_tool, 'line_idx': line_idx, 'comp': self.comp_mode})
                        sim_pos = p3.copy()
                        p4 = sim_pos.copy()
                        p4['Z'] = r_val
                        self.paths.append(
                            {'mode': 'G00', 'is_crash': False, 'start': sim_pos.copy(), 'end': p4.copy(), 'rapid': True,
                             'is_arc': False, 'tool_id': parsing_tool, 'line_idx': line_idx, 'comp': self.comp_mode})
                        sim_pos = p4.copy()
                    elif self.mode in ['G83', 'G73']:
                        curr_z = r_val
                        while curr_z > target['Z']:
                            next_z = max(curr_z - q_val, target['Z'])
                            pz = sim_pos.copy()
                            pz['Z'] = next_z
                            self.paths.append({'mode': 'G01', 'is_crash': False, 'start': sim_pos.copy(), 'end': pz.copy(),
                                               'rapid': False, 'is_arc': False, 'tool_id': parsing_tool,
                                               'line_idx': line_idx, 'comp': self.comp_mode})
                            sim_pos = pz.copy()

                            if self.mode == 'G73':
                                retract_z = min(r_val, next_z + 1.0)
                            else:
                                retract_z = r_val

                            pr = sim_pos.copy()
                            pr['Z'] = retract_z
                            self.paths.append(
                                {'mode': 'G00', 'is_crash': False, 'start': sim_pos.copy(), 'end': pr.copy(), 'rapid': True,
                                 'is_arc': False, 'tool_id': parsing_tool, 'line_idx': line_idx, 'comp': self.comp_mode})
                            sim_pos = pr.copy()

                            if next_z > target['Z']:
                                pc = sim_pos.copy()
                                pc['Z'] = next_z + 0.5
                                self.paths.append(
                                    {'mode': 'G00', 'is_crash': False, 'start': sim_pos.copy(), 'end': pc.copy(),
                                     'rapid': True, 'is_arc': False, 'tool_id': parsing_tool, 'line_idx': line_idx,
                                     'comp': self.comp_mode})
                                sim_pos = pc.copy()
                            curr_z = next_z

            self.sim_active = True
            self.current_line_idx = 0
            self.generate_next_steps()
            self.timer.start(16)

        def generate_next_steps(self):
            if self.current_line_idx >= len(self.paths):
                self.sim_active = False
                self.timer.stop()
                self.btn_run.setText("SİMÜLASYONU BAŞLAT")
                self.btn_run.setStyleSheet("background-color: #28a745; color: white; height: 40px; font-weight: bold;")
                if self.crash_count > 0:
                    QMessageBox.warning(self, "Çarpışma", "G00 ile parçaya daldınız (Eksen Çarpışması)!")
                if self.holder_crash:
                    QMessageBox.critical(self, "TUTUCU ÇARPIŞMASI", "Spindle parçaya gömüldü!")
                if self.vise_crash:
                    QMessageBox.critical(self, "MENGENE ÇARPIŞMASI",
                                         "DİKKAT: Takım çelik mengeneye (Fixture) daldı! Uç kırıldı.")
                return

            p = self.paths[self.current_line_idx]
            p_start, p_end = p['start'], p['end']

            self.highlight_line(p['line_idx'])
            mode = p.get('mode', '')

            if mode == 'WCS':
                self.active_wcs = p.get('wcs', 'G54')
                self.combo_wcs.setCurrentText(self.active_wcs)
                self.current_line_idx += 1
                self.generate_next_steps()
                return

            if mode == 'COMP':
                self.comp_mode = p.get('comp', 'G40')
                self.update_ui_labels()
                self.current_line_idx += 1
                self.generate_next_steps()
                return

            if mode in ['M01', 'M1']:
                if self.cb_m01.isChecked():
                    self.pause_simulation()
                    self.current_line_idx += 1
                    return
                else:
                    self.current_line_idx += 1
                    self.generate_next_steps()
                    return

            if mode in ['M06', 'M6']:
                self.current_tool_id = p.get('tool_id', 'T1')
                self.update_tool_mesh()
                self.current_line_idx += 1
                self.generate_next_steps()
                return

            if mode in ['M08', 'M8']:
                self.coolant_active = True
                self.update_ui_labels()
                self.update_tool_mesh()
                self.current_line_idx += 1
                self.generate_next_steps()
                return

            if mode in ['M09', 'M9']:
                self.coolant_active = False
                self.update_ui_labels()
                self.update_tool_mesh()
                self.current_line_idx += 1
                self.generate_next_steps()
                return

            if p.get('is_crash', False):
                self.crash_count += 1
            speed_mult = self.speed_slider.value() / 5.0

            render_start = p_start.copy()
            render_end = p_end.copy()
            c_mode = p.get('comp', 'G40')

            if c_mode in ['G41', 'G42'] and not p.get('is_arc', False) and (
                    render_end['X'] != render_start['X'] or render_end['Y'] != render_start['Y']):
                tool_d = self.tool_library.get(self.current_tool_id, {'d': 16.0})['d']
                tool_r = tool_d / 2.0
                dx = render_end['X'] - render_start['X']
                dy = render_end['Y'] - render_start['Y']
                angle = math.atan2(dy, dx)
                if c_mode == 'G41':
                    offset_angle = angle + (math.pi / 2)
                else:
                    offset_angle = angle - (math.pi / 2)
                ox = math.cos(offset_angle) * tool_r
                oy = math.sin(offset_angle) * tool_r
                render_start['X'] += ox
                render_start['Y'] += oy
                render_end['X'] += ox
                render_end['Y'] += oy

            if p.get('is_arc', False):
                cx = render_start['X'] + p['I']
                cy = render_start['Y'] + p['J']
                r = math.hypot(p['I'], p['J'])

                if r < 0.001:
                    dist = np.hypot(render_end['X'] - render_start['X'], render_end['Y'] - render_start['Y'])
                    step_count = max(int(dist / speed_mult), 2)
                    xs = np.linspace(render_start['X'], render_end['X'], step_count)
                    ys = np.linspace(render_start['Y'], render_end['Y'], step_count)
                    zs = np.linspace(render_start['Z'], render_end['Z'], step_count)
                    self.calculate_dist(self.current_pos, p_end, p['rapid'])
                    _a = [render_start['A']] * step_count
                    _c = [render_start['C']] * step_count
                else:
                    theta_start = math.atan2(render_start['Y'] - cy, render_start['X'] - cx)
                    theta_end = math.atan2(render_end['Y'] - cy, render_end['X'] - cx)
                    if p['mode'] == 'G02':
                        if theta_end > theta_start:
                            theta_end -= 2 * math.pi
                    else:
                        if theta_end < theta_start:
                            theta_end += 2 * math.pi
                    if abs(theta_end - theta_start) < 1e-4 and (abs(render_start['X'] - render_end['X']) < 0.01 and abs(
                            render_start['Y'] - render_end['Y']) < 0.01):
                        if p['mode'] == 'G02':
                            theta_end -= 2 * math.pi
                        else:
                            theta_end += 2 * math.pi

                    arc_length = abs(theta_end - theta_start) * r
                    dist_3d = math.sqrt(arc_length ** 2 + (render_end['Z'] - render_start['Z']) ** 2)
                    self.calculate_dist(self.current_pos, render_end, p['rapid'], arc_length=dist_3d)

                    step_count = max(int(dist_3d / speed_mult), 2)
                    angles = np.linspace(theta_start, theta_end, step_count)
                    xs = cx + r * np.cos(angles)
                    ys = cy + r * np.sin(angles)
                    zs = np.linspace(render_start['Z'], render_end['Z'], step_count)
                    _a = np.linspace(render_start['A'], render_end['A'], step_count) if 'A' in render_end else [render_start['A']] * step_count
                    _c = np.linspace(render_start['C'], render_end['C'], step_count) if 'C' in render_end else [render_start['C']] * step_count
            else:
                dist = np.hypot(render_end['X'] - render_start['X'], render_end['Y'] - render_start['Y'])
                step_count = max(int(dist / speed_mult), 2)
                xs = np.linspace(render_start['X'], render_end['X'], step_count)
                ys = np.linspace(render_start['Y'], render_end['Y'], step_count)
                zs = np.linspace(render_start['Z'], render_end['Z'], step_count)
                self.calculate_dist(self.current_pos, render_end, p.get('rapid', False))
                _a = np.linspace(render_start['A'], render_end['A'], step_count) if 'A' in render_end else [render_start['A']] * step_count
                _c = np.linspace(render_start['C'], render_end['C'], step_count) if 'C' in render_end else [render_start['C']] * step_count

            self.current_steps = list(zip(xs, ys, zs, _a, _c))
            self.current_path_info = p

            if self.show_lines_cb.isChecked() and (render_start['Z'] > 0 or render_end['Z'] > 0):
                color = (1, 0.5, 0, 1) if p.get('is_crash', False) else (
                    (1, 0, 0, 1) if p['mode'] == 'G00' else (0, 1, 1, 1))
                pts = np.vstack((xs, ys, zs)).T
                line = gl.GLLinePlotItem(pos=pts, color=color, width=2, antialias=True)
                self.gl_widget.addItem(line)
                self.path_lines.append(line)

        def get_local_tool_pos(self, tx, ty, tz, a_angle, c_angle):
            dims = self.get_stock_dims()
            cx = dims['X'] / 2
            cy = dims['Y'] / 2
            cz = -dims['Z']

            x = tx - cx
            y = ty - cy
            z = tz - cz

            c_rad = math.radians(-c_angle)
            x_new = x * math.cos(c_rad) - y * math.sin(c_rad)
            y_new = x * math.sin(c_rad) + y * math.cos(c_rad)
            x, y = x_new, y_new

            a_rad = math.radians(-a_angle)
            y_new = y * math.cos(a_rad) - z * math.sin(a_rad)
            z_new = y * math.sin(a_rad) + z * math.cos(a_rad)
            y, z = y_new, z_new

            return x + cx, y + cy, z + cz

        def sim_tick(self):
            if not self.current_steps:
                self.current_line_idx += 1
                self.generate_next_steps()
                return

            x, y, z, a, c = self.current_steps.pop(0)
            self.current_pos = {'X': x, 'Y': y, 'Z': z, 'A': a, 'C': c}
            self.update_ui_labels()
            self.update_tool_mesh()

            if hasattr(self, 'cb_5axis') and self.cb_5axis.isChecked():
                self.apply_5axis_transform(a, c)

            tool_data = self.tool_library.get(self.current_tool_id, {'d': 16.0, 'type': 'Düz Freze', 'l': 25.0})
            tool_r = tool_data['d'] / 2.0
            tool_type = tool_data['type']
            tool_length = tool_data['l']

            local_x, local_y, local_z = self.get_local_tool_pos(x, y, z, a, c)

            if hasattr(self, 'cb_vise') and self.cb_vise.isChecked() and local_z <= -10:
                dims = self.get_stock_dims()
                jaw1_hit = (-10 - tool_r <= local_x <= dims['X'] + 10 + tool_r) and (-30 - tool_r <= local_y <= 0 + tool_r)
                jaw2_hit = (-10 - tool_r <= local_x <= dims['X'] + 10 + tool_r) and (
                            dims['Y'] - tool_r <= local_y <= dims['Y'] + 30 + tool_r)

                if jaw1_hit or jaw2_hit:
                    self.vise_crash = True
                    self.sim_active = False
                    self.timer.stop()
                    self.btn_run.setText("SİMÜLASYONU BAŞLAT")
                    self.btn_run.setStyleSheet("background-color: #28a745; color: white; height: 40px; font-weight: bold;")
                    self.update_ui_labels()
                    QMessageBox.critical(self, "MENGENE ÇARPIŞMASI!",
                                         f"DIKKAT! Takım, kütüğü tutan çelik mengeneye çarptı.\nKonum: X{x:.1f} Y{y:.1f} Z{z:.1f}\nE-STOP (Acil Durdurma) Devrede!")
                    return

            if local_z < 0:
                if z < -tool_length:
                    self.holder_crash = True
                    self.sim_active = False
                    self.timer.stop()
                    self.btn_run.setText("SİMÜLASYONU BAŞLAT")
                    self.btn_run.setStyleSheet("background-color: #28a745; color: white; height: 40px; font-weight: bold;")
                    self.update_ui_labels()
                    QMessageBox.critical(self, "KIRIM TEHLİKESİ!",
                                         f"Dikkat! Takım boyu {tool_length} mm olmasına rağmen makine Z{z:.1f} derinliğine indi.\n\nTakım tutucu (Spindle) parçaya çarptı ve simülasyon durduruldu!")
                    return

                dist_sq = (self.X_grid - local_x) ** 2 + (self.Y_grid - local_y) ** 2
                mask = dist_sq <= tool_r ** 2

                if tool_type == "Düz Freze":
                    update_mask = mask & (self.Z_grid > local_z)
                    if np.any(update_mask):
                        self.Z_grid[update_mask] = local_z
                        self.surf_colors[update_mask] = [0.9, 0.6, 0.1, 1.0]
                        self.surface.setData(z=self.Z_grid, colors=self.surf_colors.reshape(-1, 4))

                elif tool_type == "Küre Freze":
                    z_sphere = local_z + tool_r - np.sqrt(np.maximum(0, tool_r ** 2 - dist_sq))
                    update_mask = mask & (self.Z_grid > z_sphere)
                    if np.any(update_mask):
                        self.Z_grid[update_mask] = z_sphere[update_mask]
                        self.surf_colors[update_mask] = [0.9, 0.6, 0.1, 1.0]
                        self.surface.setData(z=self.Z_grid, colors=self.surf_colors.reshape(-1, 4))

                elif tool_type == "Matkap":
                    tip_h = tool_r / 1.66
                    dist_radial = np.sqrt(np.maximum(0, dist_sq))
                    z_cone = local_z + tip_h - (dist_radial / 1.66)
                    update_mask = mask & (self.Z_grid > z_cone)
                    if np.any(update_mask):
                        self.Z_grid[update_mask] = z_cone[update_mask]
                        self.surf_colors[update_mask] = [0.9, 0.6, 0.1, 1.0]
                        self.surface.setData(z=self.Z_grid, colors=self.surf_colors.reshape(-1, 4))

    _GERCEK_3D_SINIF = _HaasSolid3DEngineV34
    return _GERCEK_3D_SINIF


def AdvancedCNCSimulatorV34(*args, **kwargs):
    """Geriye dönük uyumluluk için çağrıldığı anda PyQt5 3D sınıfını hazırlar ve örneklendirir."""
    cls = _pyqt5_3d_sinifini_hazirla()
    return cls(*args, **kwargs)


def _bagimsiz_swansoft_3d_sureci(gcode_metni=""):
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        from PyQt5.QtWidgets import QApplication
    mevcut_app = QApplication.instance()
    if isinstance(mevcut_app, QApplication):
        app = mevcut_app
    else:
        app = QApplication(sys.argv)
    app.setStyle("Fusion")
    sim = AdvancedCNCSimulatorV34()
    if gcode_metni and gcode_metni.strip():
        sim.txt_code.setPlainText(gcode_metni)
    sim.showFullScreen()
    exec_func = getattr(app, "exec", getattr(app, "exec_", None))
    sys.exit(exec_func())


# =========================================================================
# ALTAR ANA PENCERESİ İÇİN GÖMÜLÜ SWANSOFT V34 3D SİMÜLATÖR SEKMESİ
# =========================================================================
if CTK_AVAILABLE:
    class SwansoftCNCSekmesi(ctk.CTkFrame):
        """
        Swansoft.py (Haas V34 Solid 3-Axis Engine) içindeki tüm özellikleri:
        1. OTO-CAM (DXF) Şablon ve .dxf Okuyucu
        2. MEM (OTOMATİK) Kütük X/Y/Z, Mengene, 5-Eksen, T1-T3 ATC Takım Kütüphanesi, G-Kod & Hız Kontrolü
        3. JOG / OFFSET (G54-G59 WCS, 0.1mm Naylon Payı, X/Y/Z Zero Set, El Çarkı Jog, MDI)
        4. Canlı 3D İzometrik Katı Kütük/Mengene/Takım/Soğutma Simülasyonu + PyQt5 OpenGL 3D Tam Ekran Köprüsü
        doğrudan Altar CNC sekmesi içinde sunar.
        """
        def __init__(self, parent):
            super().__init__(parent, fg_color="transparent")
            self.current_pos = {'X': -20.0, 'Y': -20.0, 'Z': 50.0, 'A': 0.0, 'C': 0.0}
            self.mode = 'G00'
            self.comp_mode = 'G40'
            self.active_wcs = 'G54'
            self.current_tool_id = 'T1'
            self.coolant_active = False
            self.feed_rate = 150.0
            self.rapid_rate = 2000.0
            self.total_time_min = 0.0
            self.total_distance = 0.0
            self.crash_count = 0
            self.sim_active = False
            self.is_paused = False
            self.paths = []
            self.current_steps = []
            self.current_line_idx = 0
            self.izlenen_noktalar = []
            self.kamera_aci_z = -45.0
            self.kamera_aci_x = 30.0
            self._son_dondurme_zamani = 0.0
            self._resize_timer = None

            self._arayuz_olustur()
            self.reset_machine(first_start=True)

        def _arayuz_olustur(self):
            ana = ctk.CTkFrame(self, fg_color="transparent")
            ana.pack(fill="both", expand=True, padx=4, pady=4)

            # SOL PANEL: HAAS V34 KONTROL ÜNİTESİ (DRO + 3 SEKME)
            sol = ctk.CTkFrame(ana, width=440, fg_color="#1B1D20", corner_radius=8)
            sol.pack(side="left", fill="y", padx=(0, 6))
            sol.pack_propagate(False)

            baslik = ctk.CTkLabel(
                sol, text="⚙️ HAAS - V34 SOLID 3-AXIS ENGINE (SWANSOFT)",
                font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
                fg_color="#2B2D30", text_color="#FFFFFF", corner_radius=6, height=30
            )
            baslik.pack(fill="x", padx=6, pady=(6, 4))

            # DRO (Canlı Koordinat ve Telemetri Ekranı)
            dro_frame = ctk.CTkFrame(sol, fg_color="#000000", border_width=2, border_color="#4CA1AF", corner_radius=6)
            dro_frame.pack(fill="x", padx=6, pady=4)

            self.pos_lbl = ctk.CTkLabel(
                dro_frame, text="X:  -20.000  Y:  -20.000  Z:   50.000\nA:    0.000° C:    0.000°",
                font=ctk.CTkFont(family="Consolas", size=15, weight="bold"), text_color="#00FF00", justify="left"
            )
            self.pos_lbl.pack(anchor="w", padx=8, pady=(4, 2))

            self.stats_lbl = ctk.CTkLabel(
                dro_frame, text="Süre: 00:00:00 | Mesafe: 0.0 mm\nÇarpma: 0 | Takım: T1 | WCS: G54 | Soğutma: KAPALI",
                font=ctk.CTkFont(family="Consolas", size=11), text_color="#4CA1AF", justify="left"
            )
            self.stats_lbl.pack(anchor="w", padx=8, pady=1)

            self.comp_lbl = ctk.CTkLabel(
                dro_frame, text="Takım Telafisi: G40 (KAPALI)",
                font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#F39C12"
            )
            self.comp_lbl.pack(anchor="w", padx=8, pady=(1, 4))

            # Üst Onay Kutuları + Tam Ekran OpenGL Butonu
            ayar_bar = ctk.CTkFrame(sol, fg_color="transparent")
            ayar_bar.pack(fill="x", padx=6, pady=2)
            self.show_lines_var = ctk.BooleanVar(value=True)
            self.cb_m01_var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(
                ayar_bar, text="Takım İzleri", variable=self.show_lines_var,
                width=90, checkbox_width=16, checkbox_height=16, command=self.sahneyi_ciz
            ).pack(side="left", padx=2)
            ctk.CTkCheckBox(ayar_bar, text="M01 Duruş", variable=self.cb_m01_var, width=85, checkbox_width=16, checkbox_height=16, text_color="#FFD700").pack(side="left", padx=2)
            ctk.CTkButton(
                ayar_bar, text="🖥️ OpenGL 3D Tam Ekran", width=160, height=24,
                fg_color="#008080", hover_color="#005959", command=self.opengl_3d_penceresini_ac
            ).pack(side="right", padx=2)

            # 3 SEKME: OTO-CAM (DXF) | MEM (OTOMATİK) | JOG / OFFSET
            self.tabs = ctk.CTkTabview(sol, corner_radius=6)
            self.tabs.pack(fill="both", expand=True, padx=6, pady=(2, 6))

            self.tab_cam = self.tabs.add("OTO-CAM (DXF)")
            self.tab_mem = self.tabs.add("MEM (OTOMATİK)")
            self.tab_jog = self.tabs.add("JOG / OFFSET")
            self.tabs.set("MEM (OTOMATİK)")

            self._setup_cam_tab()
            self._setup_mem_tab()
            self._setup_jog_tab()

            # SAĞ PANEL: 3D İZOMETRİK KATI MODEL & TAKIM YOLU SİMÜLASYON EKRANI
            sag = ctk.CTkFrame(ana, fg_color="#121417", corner_radius=8, border_width=1, border_color="#30363D")
            sag.pack(side="right", fill="both", expand=True)

            sag_ust = ctk.CTkFrame(sag, fg_color="#1B1D20", corner_radius=6)
            sag_ust.pack(side="top", fill="x", padx=6, pady=4)

            ctk.CTkLabel(
                sag_ust,
                text="🟥 G00 (Hızlı) | 🟦 G01/G02/G03 (Kesim) | 🟨 Talaş Yüzeyi | 🖱️ Sol Tık Sürükle: 3D Açıyı Döndür",
                font=ctk.CTkFont(family="Consolas", size=11), text_color="#00FFCC"
            ).pack(side="left", padx=8, pady=3)

            self.canvas = tk.Canvas(sag, bg="#121417", highlightthickness=0)
            self.canvas.pack(fill="both", expand=True, padx=6, pady=(0, 6))
            self.canvas.bind("<B1-Motion>", self._fare_ile_dondur)
            self.canvas.bind("<Configure>", self._boyut_degisti_debounce)

        def _boyut_degisti_debounce(self, _event=None):
            if not self.winfo_exists():
                return
            if self._resize_timer:
                self.after_cancel(self._resize_timer)
            self._resize_timer = self.after(100, self.sahneyi_ciz)

        def _setup_cam_tab(self):
            f = ctk.CTkFrame(self.tab_cam, fg_color="transparent")
            f.pack(fill="both", expand=True, padx=4, pady=4)

            ctk.CTkLabel(f, text="📐 Parametrik Hızlı Şablon", text_color="#3498DB", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=2)
            grid = ctk.CTkFrame(f, fg_color="transparent")
            grid.pack(fill="x", pady=4)

            self.cam_cx = self._kutu_ekle(grid, "Merkez X:", "100", 0, 0)
            self.cam_cy = self._kutu_ekle(grid, "Merkez Y:", "100", 0, 2)
            self.cam_outer = self._kutu_ekle(grid, "Dış Çap:", "120", 1, 0)
            self.cam_inner = self._kutu_ekle(grid, "İç Çap:", "60", 1, 2)
            self.cam_holes = self._kutu_ekle(grid, "Delik Sayısı:", "6", 2, 0)
            self.cam_pcd = self._kutu_ekle(grid, "Delik Ekseni:", "90", 2, 2)
            self.cam_z = self._kutu_ekle(grid, "Derinlik(Z):", "15", 3, 0)

            ctk.CTkButton(
                f, text="⚡ ŞABLONDAN G-KOD ÜRET", fg_color="#3498DB", height=30,
                command=self.generate_cam_code
            ).pack(fill="x", pady=6)

            ctk.CTkLabel(f, text="📂 Matematiksel DXF Analizi (.dxf)", text_color="#E67E22", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(8, 2))
            dxf_bar = ctk.CTkFrame(f, fg_color="transparent")
            dxf_bar.pack(fill="x", pady=2)
            ctk.CTkLabel(dxf_bar, text="Standart Z Derinliği (-mm):").pack(side="left")
            self.dxf_z = ctk.CTkEntry(dxf_bar, width=60)
            self.dxf_z.pack(side="left", padx=6)
            self.dxf_z.insert(0, "10")

            ctk.CTkButton(
                f, text="📄 DXF DOSYASI SEÇ VE İŞLE (.dxf)", fg_color="#E67E22", height=34,
                command=self.load_dxf_file
            ).pack(fill="x", pady=6)

        def _kutu_ekle(self, parent, etiket, varsayilan, r, c):
            ctk.CTkLabel(parent, text=etiket, font=ctk.CTkFont(size=11)).grid(row=r, column=c, padx=3, pady=2, sticky="w")
            e = ctk.CTkEntry(parent, width=65, height=24)
            e.grid(row=r, column=c + 1, padx=3, pady=2)
            e.insert(0, varsayilan)
            return e

        def _setup_mem_tab(self):
            f = ctk.CTkFrame(self.tab_mem, fg_color="transparent")
            f.pack(fill="both", expand=True)

            kutuk_bar = ctk.CTkFrame(f, fg_color="transparent")
            kutuk_bar.pack(fill="x", pady=2)
            ctk.CTkLabel(kutuk_bar, text="Kütük X/Y/Z:").pack(side="left")
            self.entry_x = ctk.CTkEntry(kutuk_bar, width=48, height=22); self.entry_x.pack(side="left", padx=2); self.entry_x.insert(0, "200")
            self.entry_y = ctk.CTkEntry(kutuk_bar, width=48, height=22); self.entry_y.pack(side="left", padx=2); self.entry_y.insert(0, "200")
            self.entry_z = ctk.CTkEntry(kutuk_bar, width=42, height=22); self.entry_z.pack(side="left", padx=2); self.entry_z.insert(0, "50")

            self.cb_vise_var = ctk.BooleanVar(value=True)
            self.cb_5axis_var = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(kutuk_bar, text="Mengene", variable=self.cb_vise_var, width=75, checkbox_width=15, checkbox_height=15, text_color="#E74C3C", command=self.sahneyi_ciz).pack(side="left", padx=3)
            ctk.CTkCheckBox(kutuk_bar, text="5-Eksen", variable=self.cb_5axis_var, width=70, checkbox_width=15, checkbox_height=15, text_color="#2ECC71").pack(side="left", padx=2)

            atc = ctk.CTkFrame(f, fg_color="#141619", corner_radius=6)
            atc.pack(fill="x", pady=3, padx=2)
            self.t_widgets = {}
            varsayilan_takimlar = [
                ("T1", "Düz Freze", "16", "25"),
                ("T2", "Küre Freze", "10", "25"),
                ("T3", "Matkap", "8", "30")
            ]
            for idx, (tid, ttip, tcap, tboy) in enumerate(varsayilan_takimlar):
                ctk.CTkLabel(atc, text=f"{tid}:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#F39C12").grid(row=idx, column=0, padx=3, pady=1)
                cmb = ctk.CTkOptionMenu(atc, values=["Düz Freze", "Küre Freze", "Matkap"], width=105, height=20, font=ctk.CTkFont(size=11))
                cmb.set(ttip)
                cmb.grid(row=idx, column=1, padx=2, pady=1)
                ctk.CTkLabel(atc, text="Çap:", font=ctk.CTkFont(size=11)).grid(row=idx, column=2, padx=2)
                ed = ctk.CTkEntry(atc, width=42, height=20); ed.insert(0, tcap); ed.grid(row=idx, column=3, padx=2)
                ctk.CTkLabel(atc, text="Boy:", font=ctk.CTkFont(size=11)).grid(row=idx, column=4, padx=2)
                el = ctk.CTkEntry(atc, width=42, height=20); el.insert(0, tboy); el.grid(row=idx, column=5, padx=2)
                self.t_widgets[tid] = (cmb, ed, el)

            self.txt_code = ctk.CTkTextbox(f, font=ctk.CTkFont(family="Consolas", size=12), fg_color="#121212", height=130)
            self.txt_code.pack(fill="both", expand=True, pady=3)
            ornek = (
                "(V34 - STANDART 3 EKSEN KATI ISLEME)\n"
                "G54\n"
                "T1 M06 (16mm Duz Freze)\n"
                "M08\n"
                "G00 X100 Y100 Z5\n"
                "G01 Z0 F150\n"
                "G02 X100 Y100 Z-15 I20 J0 F200\n"
                "G02 X100 Y100 Z-15 I20 J0\n"
                "G00 Z50\n"
                "T3 M06 (8mm Matkap)\n"
                "M08\n"
                "G00 X100 Y100 Z5\n"
                "G83 X100 Y100 Z-20 R2 Q5 F100\n"
                "G80\n"
                "G00 Z100\n"
                "M09\n"
                "M30"
            )
            self.txt_code.insert("1.0", ornek)

            hiz_bar = ctk.CTkFrame(f, fg_color="transparent")
            hiz_bar.pack(fill="x", pady=1)
            ctk.CTkLabel(hiz_bar, text="Hız:", font=ctk.CTkFont(size=11)).pack(side="left", padx=4)
            self.speed_slider = ctk.CTkSlider(hiz_bar, from_=1, to=100, number_of_steps=99, height=14)
            self.speed_slider.set(30)
            self.speed_slider.pack(side="left", fill="x", expand=True, padx=4)

            alt_btn = ctk.CTkFrame(f, fg_color="transparent")
            alt_btn.pack(fill="x", pady=2)
            self.btn_run = ctk.CTkButton(alt_btn, text="▶️ SİMÜLASYONU BAŞLAT", fg_color="#28A745", height=30, command=self.run_simulation)
            self.btn_run.pack(side="left", fill="x", expand=True, padx=(0, 3))
            ctk.CTkButton(alt_btn, text="🔄 SIFIRLA", fg_color="#DC3545", width=95, height=30, command=lambda: self.reset_machine(False)).pack(side="right")

        def _setup_jog_tab(self):
            f = ctk.CTkFrame(self.tab_jog, fg_color="transparent")
            f.pack(fill="both", expand=True, padx=4, pady=4)

            wcs_bar = ctk.CTkFrame(f, fg_color="transparent")
            wcs_bar.pack(fill="x", pady=2)
            ctk.CTkLabel(wcs_bar, text="Aktif WCS:", text_color="#F1C40F", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=4)
            self.combo_wcs = ctk.CTkOptionMenu(wcs_bar, values=["G54", "G55", "G56", "G57", "G58", "G59"], width=95, command=self.change_active_wcs)
            self.combo_wcs.pack(side="left", padx=4)

            self.cb_nylon_var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(f, text="Z Sıfırlamada Şeffaf Naylon Payını (0.1 mm) Düş", variable=self.cb_nylon_var, text_color="#2ECC71").pack(anchor="w", pady=4)

            z_bar = ctk.CTkFrame(f, fg_color="transparent")
            z_bar.pack(fill="x", pady=3)
            ctk.CTkButton(z_bar, text="X - ZERO SET", width=115, fg_color="#34495E", command=lambda: self.zero_axis('X')).pack(side="left", padx=2)
            ctk.CTkButton(z_bar, text="Y - ZERO SET", width=115, fg_color="#34495E", command=lambda: self.zero_axis('Y')).pack(side="left", padx=2)
            ctk.CTkButton(z_bar, text="Z - ZERO SET", width=115, fg_color="#E67E22", command=lambda: self.zero_axis('Z')).pack(side="left", padx=2)

            ctk.CTkLabel(f, text="🕹️ Jog / Handle (El Çarkı)", text_color="#E74C3C", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(6, 2))
            self.jog_step_var = ctk.DoubleVar(value=2.0)
            step_bar = ctk.CTkFrame(f, fg_color="transparent")
            step_bar.pack(fill="x", pady=2)
            for adim in (0.1, 2.0, 10.0):
                ctk.CTkRadioButton(step_bar, text=f"{adim} mm", variable=self.jog_step_var, value=adim).pack(side="left", padx=8)

            j_bar = ctk.CTkFrame(f, fg_color="transparent")
            j_bar.pack(fill="x", pady=4)
            for eks, yon, lbl in [("X", -1, "X-"), ("X", 1, "X+"), ("Y", -1, "Y-"), ("Y", 1, "Y+"), ("Z", 1, "Z+"), ("Z", -1, "Z-")]:
                ctk.CTkButton(j_bar, text=lbl, width=56, height=30, fg_color="#4A4F54", command=lambda a=eks, d=yon: self.jog_move(a, d)).pack(side="left", padx=2)

            ctk.CTkLabel(f, text="⌨️ MDI (Manuel Komut İşleme)", text_color="#2ECC71", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(6, 2))
            self.entry_mdi = ctk.CTkEntry(f, placeholder_text="Örn: G00 X50 Y50 Z10")
            self.entry_mdi.pack(fill="x", pady=2)
            ctk.CTkButton(f, text="MDI ÇALIŞTIR", fg_color="#D9534F", height=28, command=self.run_mdi).pack(fill="x", pady=3)

        def opengl_3d_penceresini_ac(self):
            mevcut_kod = self.txt_code.get("1.0", "end").strip()
            p = multiprocessing.Process(target=_bagimsiz_swansoft_3d_sureci, args=(mevcut_kod,), daemon=True)
            p.start()

        def get_stock_dims(self):
            try:
                return {'X': float(self.entry_x.get()), 'Y': float(self.entry_y.get()), 'Z': float(self.entry_z.get())}
            except Exception:
                return {'X': 200.0, 'Y': 200.0, 'Z': 50.0}

        def load_tool_library(self):
            self.tool_library = {}
            for tid, (cmb, ed, el) in self.t_widgets.items():
                try:
                    self.tool_library[tid] = {'type': cmb.get(), 'd': float(ed.get() or 16), 'l': float(el.get() or 25)}
                except Exception:
                    self.tool_library[tid] = {'type': 'Düz Freze', 'd': 16.0, 'l': 25.0}

        def change_active_wcs(self, wcs_name):
            self.active_wcs = wcs_name
            self.update_ui_labels()

        def zero_axis(self, axis):
            if axis == 'Z' and self.cb_nylon_var.get():
                self.current_pos[axis] = 0.1
                msg = f"{self.active_wcs}: Z Ekseni 0.1mm şeffaf naylon payı düşülerek sıfırlandı."
            else:
                self.current_pos[axis] = 0.0
                msg = f"{self.active_wcs}: {axis} Ekseni 0.000 olarak sıfırlandı."
            self.update_ui_labels()
            self._sadece_takimi_guncelle()
            tk_messagebox.showinfo("Work Offset", msg)

        def jog_move(self, axis, direction):
            adim = float(self.jog_step_var.get()) * direction
            self.current_pos[axis] += adim
            if self.current_pos['Z'] < 0:
                self.crash_count += 1
            self.update_ui_labels()
            self._sadece_takimi_guncelle()

        def run_mdi(self):
            kod = self.entry_mdi.get().strip().upper()
            if kod:
                self.entry_mdi.delete(0, "end")
                self.run_gcode_text(kod)

        def generate_cam_code(self):
            try:
                cx, cy = float(self.cam_cx.get()), float(self.cam_cy.get())
                inner_d = float(self.cam_inner.get())
                holes = max(1, int(self.cam_holes.get()))
                pcd, z_depth = float(self.cam_pcd.get()), float(self.cam_z.get())
            except Exception:
                return

            code = f"(SABLON OTO-CAM)\nG54\nT1 M06 (Freze)\nM08\nG00 X{cx + inner_d / 2} Y{cy} Z5\n"
            code += f"G01 Z-{z_depth} F150\nG03 X{cx + inner_d / 2} Y{cy} I-{inner_d / 2} J0\nG00 Z50\nM09\nM01\n"
            code += "T3 M06 (Matkap)\nM08\n"
            for i in range(holes):
                angle = math.radians(i * (360 / holes))
                hx = cx + (pcd / 2) * math.cos(angle)
                hy = cy + (pcd / 2) * math.sin(angle)
                code += f"G00 X{hx:.3f} Y{hy:.3f}\nG73 X{hx:.3f} Y{hy:.3f} Z-{z_depth + 5} R2 Q5 F100\n"
            code += "G80\nM09\nG00 Z100\nG00 X0 Y0\nM30"
            self.txt_code.delete("1.0", "end")
            self.txt_code.insert("1.0", code)
            self.tabs.set("MEM (OTOMATİK)")

        def load_dxf_file(self):
            try:
                import ezdxf
            except ImportError:
                tk_messagebox.showwarning("Eksik Kütüphane", "DXF analizi için 'pip install ezdxf' kurun.")
                return
            dosya = tk_filedialog.askopenfilename(filetypes=[("DXF Dosyası", "*.dxf")])
            if not dosya:
                return
            try:
                doc = ezdxf.readfile(dosya)
                msp = doc.modelspace()
                z_depth = float(self.dxf_z.get() or 10)
                code = "(V34 - DXF OTO-CAM URETIMI)\nG54\nG00 X0 Y0 Z50\n"
                circles = list(msp.query('CIRCLE'))
                drills = [c for c in circles if c.dxf.radius < 10]
                pockets = [c for c in circles if c.dxf.radius >= 10]
                if pockets:
                    code += "\nT1 M06\nM08\n"
                    for p in pockets:
                        cx, cy, r = p.dxf.center.x, p.dxf.center.y, p.dxf.radius
                        code += f"G00 X{cx + r:.3f} Y{cy:.3f} Z5\nG01 Z-{z_depth} F150\nG03 X{cx + r:.3f} Y{cy:.3f} I-{r:.3f} J0\nG00 Z50\n"
                if drills:
                    code += "\nT3 M06\nM08\n"
                    for d in drills:
                        cx, cy = d.dxf.center.x, d.dxf.center.y
                        code += f"G00 X{cx:.3f} Y{cy:.3f}\nG73 X{cx:.3f} Y{cy:.3f} Z-{z_depth + 3} R2 Q5 F100\n"
                code += "G80\nM09\nG00 Z100\nM30"
                self.txt_code.delete("1.0", "end")
                self.txt_code.insert("1.0", code)
                self.tabs.set("MEM (OTOMATİK)")
            except Exception as e:
                tk_messagebox.showerror("DXF Hatası", str(e))

        def update_ui_labels(self):
            if not self.winfo_exists():
                return
            self.pos_lbl.configure(
                text=f"X: {self.current_pos['X']:8.3f}  Y: {self.current_pos['Y']:8.3f}  Z: {self.current_pos['Z']:8.3f}\nA: {self.current_pos['A']:8.3f}° C: {self.current_pos['C']:8.3f}°"
            )
            h, m, s = int(self.total_time_min // 60), int(self.total_time_min % 60), int((self.total_time_min * 60) % 60)
            cool = "AÇIK" if self.coolant_active else "KAPALI"
            self.stats_lbl.configure(
                text=f"Süre: {h:02d}:{m:02d}:{s:02d} | Mesafe: {self.total_distance:.1f} mm\nÇarpma: {self.crash_count} | Takım: {self.current_tool_id} | WCS: {self.active_wcs} | Soğutma: {cool}"
            )
            comp_str = "SOLA" if self.comp_mode == "G41" else ("SAĞA" if self.comp_mode == "G42" else "KAPALI")
            self.comp_lbl.configure(text=f"Takım Telafisi: {self.comp_mode} ({comp_str})")

        def reset_machine(self, first_start=False):
            self.sim_active = False
            self.is_paused = False
            if not first_start:
                self.current_pos = {'X': -20.0, 'Y': -20.0, 'Z': 50.0, 'A': 0.0, 'C': 0.0}
            self.mode = 'G00'
            self.comp_mode = 'G40'
            self.total_time_min = 0.0
            self.total_distance = 0.0
            self.crash_count = 0
            self.paths.clear()
            self.current_steps.clear()
            self.izlenen_noktalar.clear()
            self.load_tool_library()
            self.btn_run.configure(text="▶️ SİMÜLASYONU BAŞLAT", fg_color="#28A745")
            self.update_ui_labels()
            self.sahneyi_ciz()

        def run_simulation(self):
            if self.sim_active and not self.is_paused:
                self.is_paused = True
                self.btn_run.configure(text="▶️ DEVAM ET (RESUME)", fg_color="#3498DB")
                return
            if self.is_paused:
                self.is_paused = False
                self.btn_run.configure(text="⏸️ DURAKLAT (PAUSE)", fg_color="#F39C12")
                self._sim_adim()
                return

            self.reset_machine(first_start=False)
            self.btn_run.configure(text="⏸️ DURAKLAT (PAUSE)", fg_color="#F39C12")
            kod = self.txt_code.get("1.0", "end").strip().upper()
            self.run_gcode_text(kod)

        def run_gcode_text(self, text):
            if not text:
                return
            self.paths = []
            sim_pos = self.current_pos.copy()
            r_val, q_val = 2.0, 5.0
            parsing_tool = self.current_tool_id
            pending_tool = parsing_tool

            for line_idx, line in enumerate(text.splitlines()):
                line_clean = line.split('(')[0].strip()
                if not line_clean:
                    continue
                words = line_clean.split()
                target = sim_pos.copy()
                is_move = False
                i_val, j_val = 0.0, 0.0
                is_arc = False

                for w in words:
                    if w in ['G40', 'G41', 'G42']:
                        self.comp_mode = w
                    elif w in ['G54', 'G55', 'G56', 'G57', 'G58', 'G59']:
                        self.active_wcs = w
                    elif w.startswith('F'):
                        try:
                            self.feed_rate = float(w[1:])
                        except Exception:
                            pass
                    elif w.startswith('R'):
                        try:
                            r_val = float(w[1:])
                        except Exception:
                            pass
                    elif w.startswith('Q'):
                        try:
                            q_val = max(abs(float(w[1:])), 0.5)
                        except Exception:
                            pass
                    elif w.startswith('T'):
                        pending_tool = w
                    elif w in ['M06', 'M6']:
                        parsing_tool = pending_tool
                        self.paths.append({'mode': 'M06', 'start': sim_pos.copy(), 'end': sim_pos.copy(), 'tool_id': parsing_tool})
                    elif w in ['M08', 'M8', 'M09', 'M9', 'M01', 'M1']:
                        self.paths.append({'mode': w, 'start': sim_pos.copy(), 'end': sim_pos.copy(), 'tool_id': parsing_tool})

                for w in words:
                    if len(w) < 2:
                        continue
                    letter, value = w[0], w[1:]
                    try:
                        val = float(value)
                        if letter == 'G' and w not in ['G54', 'G55', 'G56', 'G57', 'G58', 'G59', 'G40', 'G41', 'G42']:
                            self.mode = f"G{int(val):02d}" if val < 10 else f"G{int(val)}"
                            if self.mode in ['G02', 'G03']:
                                is_arc = True
                        elif letter in ['X', 'Y', 'Z', 'A', 'C']:
                            target[letter] = val
                            is_move = True
                        elif letter == 'I':
                            i_val = val
                        elif letter == 'J':
                            j_val = val
                    except Exception:
                        continue

                if self.mode in ['G02', 'G03']:
                    is_arc = True

                if is_move and self.mode in ['G00', 'G01', 'G02', 'G03']:
                    is_rapid = (self.mode == 'G00')
                    is_crash = (is_rapid and target['Z'] < 0)
                    self.paths.append({
                        'mode': self.mode, 'is_crash': is_crash, 'start': sim_pos.copy(), 'end': target.copy(),
                        'rapid': is_rapid, 'is_arc': is_arc, 'I': i_val, 'J': j_val, 'tool_id': parsing_tool
                    })
                    sim_pos = target.copy()
                elif is_move and self.mode in ['G81', 'G83', 'G73']:
                    p_xy = sim_pos.copy(); p_xy['X'] = target['X']; p_xy['Y'] = target['Y']; p_xy['Z'] = r_val
                    self.paths.append({'mode': 'G00', 'start': sim_pos.copy(), 'end': p_xy.copy(), 'rapid': True, 'tool_id': parsing_tool})
                    p_dip = p_xy.copy(); p_dip['Z'] = target['Z']
                    self.paths.append({'mode': 'G01', 'start': p_xy.copy(), 'end': p_dip.copy(), 'rapid': False, 'tool_id': parsing_tool})
                    self.paths.append({'mode': 'G00', 'start': p_dip.copy(), 'end': p_xy.copy(), 'rapid': True, 'tool_id': parsing_tool})
                    sim_pos = p_xy.copy()

            self.sim_active = True
            self.current_line_idx = 0
            self._sonraki_hareketi_hazirla()
            self._sim_adim()

        def _sonraki_hareketi_hazirla(self):
            if self.current_line_idx >= len(self.paths):
                self.sim_active = False
                self.btn_run.configure(text="▶️ SİMÜLASYONU BAŞLAT", fg_color="#28A745")
                return

            p = self.paths[self.current_line_idx]
            mode = p.get('mode', '')
            if mode == 'M06':
                self.current_tool_id = p.get('tool_id', 'T1')
                self.current_line_idx += 1
                self._sonraki_hareketi_hazirla()
                return
            if mode in ['M08', 'M8']:
                self.coolant_active = True
                self.current_line_idx += 1
                self._sonraki_hareketi_hazirla()
                return
            if mode in ['M09', 'M9']:
                self.coolant_active = False
                self.current_line_idx += 1
                self._sonraki_hareketi_hazirla()
                return
            if mode in ['M01', 'M1'] and self.cb_m01_var.get():
                self.is_paused = True
                self.btn_run.configure(text="▶️ DEVAM ET (M01)", fg_color="#3498DB")
                self.current_line_idx += 1
                return

            s, e = p['start'], p['end']
            if p.get('is_crash'):
                self.crash_count += 1
            hiz = max(1.0, self.speed_slider.get() / 4.0)

            if p.get('is_arc'):
                cx, cy = s['X'] + p.get('I', 0.0), s['Y'] + p.get('J', 0.0)
                r = max(1.0, math.hypot(p.get('I', 0.0), p.get('J', 0.0)))
                t1 = math.atan2(s['Y'] - cy, s['X'] - cx)
                t2 = math.atan2(e['Y'] - cy, e['X'] - cx)
                if mode == 'G02' and t2 >= t1:
                    t2 -= 2 * math.pi
                elif mode == 'G03' and t2 <= t1:
                    t2 += 2 * math.pi
                adim_sayisi = max(int((abs(t2 - t1) * r) / hiz), 12)
                acilar = np.linspace(t1, t2, adim_sayisi)
                xs = cx + r * np.cos(acilar)
                ys = cy + r * np.sin(acilar)
                zs = np.linspace(s['Z'], e['Z'], adim_sayisi)
                mesafe = abs(t2 - t1) * r
            else:
                mesafe = math.sqrt((e['X'] - s['X']) ** 2 + (e['Y'] - s['Y']) ** 2 + (e['Z'] - s['Z']) ** 2)
                adim_sayisi = max(int(mesafe / hiz), 2)
                xs = np.linspace(s['X'], e['X'], adim_sayisi)
                ys = np.linspace(s['Y'], e['Y'], adim_sayisi)
                zs = np.linspace(s['Z'], e['Z'], adim_sayisi)

            self.total_distance += mesafe
            self.total_time_min += mesafe / (self.rapid_rate if p.get('rapid') else max(self.feed_rate, 1.0))
            self.current_steps = [(xs[i], ys[i], zs[i], mode) for i in range(len(xs))]

        def _sim_adim(self):
            if not self.winfo_exists() or not self.sim_active or self.is_paused:
                return
            if not self.current_steps:
                self.current_line_idx += 1
                self._sonraki_hareketi_hazirla()
                if self.sim_active and not self.is_paused and self.winfo_exists():
                    self.after(20, self._sim_adim)
                return

            ox, oy, oz = self.current_pos['X'], self.current_pos['Y'], self.current_pos['Z']
            nx, ny, nz, mod = self.current_steps.pop(0)
            self.current_pos['X'], self.current_pos['Y'], self.current_pos['Z'] = nx, ny, nz
            seg = (ox, oy, oz, nx, ny, nz, mod)
            self.izlenen_noktalar.append(seg)
            self.update_ui_labels()

            self._yeni_segment_ve_takim_ciz(seg)
            if self.winfo_exists():
                self.after(20, self._sim_adim)

        def _fare_ile_dondur(self, event):
            simdi = time.perf_counter()
            if simdi - self._son_dondurme_zamani < 0.016:
                return
            self._son_dondurme_zamani = simdi

            w = max(self.canvas.winfo_width(), 400)
            h = max(self.canvas.winfo_height(), 300)
            self.kamera_aci_z = ((event.x / w) - 0.5) * 180.0
            self.kamera_aci_x = max(10.0, min(80.0, (event.y / h) * 80.0))
            self.sahneyi_ciz()

        def _izometrik_projeksiyon(self, x, y, z, cx, cy, olcek, dims):
            mx, my = x - dims['X'] / 2.0, y - dims['Y'] / 2.0
            rz = math.radians(self.kamera_aci_z)
            rx = math.radians(self.kamera_aci_x)
            rx_val = mx * math.cos(rz) - my * math.sin(rz)
            ry_val = mx * math.sin(rz) + my * math.cos(rz)
            ekran_x = cx + rx_val * olcek
            ekran_y = cy - (ry_val * math.sin(rx) + z * math.cos(rx)) * olcek
            return ekran_x, ekran_y

        def _sadece_takimi_guncelle(self):
            if not self.winfo_exists():
                return
            w = max(self.canvas.winfo_width(), 500)
            h = max(self.canvas.winfo_height(), 400)
            dims = self.get_stock_dims()
            olcek = min(w, h) / max(dims['X'], dims['Y'], 120.0) * 0.55
            cx, cy = w * 0.5, h * 0.56
            self.canvas.delete("tool_tag")

            tx, ty, tz = self.current_pos['X'], self.current_pos['Y'], self.current_pos['Z']
            t_uc = self._izometrik_projeksiyon(tx, ty, tz, cx, cy, olcek, dims)
            t_ust = self._izometrik_projeksiyon(tx, ty, tz + 30, cx, cy, olcek, dims)
            sp_ust = self._izometrik_projeksiyon(tx, ty, tz + 65, cx, cy, olcek, dims)

            if self.coolant_active:
                self.canvas.create_oval(t_uc[0] - 14, t_uc[1] - 8, t_uc[0] + 14, t_uc[1] + 8, outline="#00AAFF", width=2, tags="tool_tag")
            self.canvas.create_line(t_ust[0], t_ust[1], sp_ust[0], sp_ust[1], fill="#7F8C8D", width=12, tags="tool_tag")
            self.canvas.create_line(t_uc[0], t_uc[1], t_ust[0], t_ust[1], fill="#FFD700", width=6, tags="tool_tag")
            self.canvas.create_oval(t_uc[0] - 4, t_uc[1] - 4, t_uc[0] + 4, t_uc[1] + 4, fill="#00FF88", outline="#00FF88", tags="tool_tag")

        def _yeni_segment_ve_takim_ciz(self, seg):
            if not self.winfo_exists():
                return
            if self.show_lines_var.get():
                w = max(self.canvas.winfo_width(), 500)
                h = max(self.canvas.winfo_height(), 400)
                dims = self.get_stock_dims()
                olcek = min(w, h) / max(dims['X'], dims['Y'], 120.0) * 0.55
                cx, cy = w * 0.5, h * 0.56
                x1, y1, z1, x2, y2, z2, mod = seg
                s1 = self._izometrik_projeksiyon(x1, y1, z1, cx, cy, olcek, dims)
                s2 = self._izometrik_projeksiyon(x2, y2, z2, cx, cy, olcek, dims)
                if mod == 'G00':
                    self.canvas.create_line(s1[0], s1[1], s2[0], s2[1], fill="#FF4444", dash=(3, 3), width=1.5, tags="path_tag")
                else:
                    renk = "#F39C12" if z2 < 0 else "#00E5FF"
                    self.canvas.create_line(s1[0], s1[1], s2[0], s2[1], fill=renk, width=2.5, tags="path_tag")

            self._sadece_takimi_guncelle()

        def sahneyi_ciz(self):
            if not self.winfo_exists():
                return
            self.canvas.delete("all")
            w = max(self.canvas.winfo_width(), 500)
            h = max(self.canvas.winfo_height(), 400)
            dims = self.get_stock_dims()
            olcek = min(w, h) / max(dims['X'], dims['Y'], 120.0) * 0.55
            cx, cy = w * 0.5, h * 0.56

            # 1. 3D Çelik Mengene Çizimi
            if self.cb_vise_var.get():
                for y1, y2 in [(-25, 0), (dims['Y'], dims['Y'] + 25)]:
                    p1 = self._izometrik_projeksiyon(-10, y1, -5, cx, cy, olcek, dims)
                    p2 = self._izometrik_projeksiyon(dims['X'] + 10, y1, -5, cx, cy, olcek, dims)
                    p3 = self._izometrik_projeksiyon(dims['X'] + 10, y2, -5, cx, cy, olcek, dims)
                    p4 = self._izometrik_projeksiyon(-10, y2, -5, cx, cy, olcek, dims)
                    self.canvas.create_polygon(p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], p4[0], p4[1], fill="#2C3E50", outline="#E74C3C")

            # 2. 3D Katı Kütük (Stock) Çizimi
            ust_kose = [
                self._izometrik_projeksiyon(0, 0, 0, cx, cy, olcek, dims),
                self._izometrik_projeksiyon(dims['X'], 0, 0, cx, cy, olcek, dims),
                self._izometrik_projeksiyon(dims['X'], dims['Y'], 0, cx, cy, olcek, dims),
                self._izometrik_projeksiyon(0, dims['Y'], 0, cx, cy, olcek, dims)
            ]
            alt_kose = [
                self._izometrik_projeksiyon(0, 0, -dims['Z'], cx, cy, olcek, dims),
                self._izometrik_projeksiyon(dims['X'], 0, -dims['Z'], cx, cy, olcek, dims),
                self._izometrik_projeksiyon(dims['X'], dims['Y'], -dims['Z'], cx, cy, olcek, dims),
                self._izometrik_projeksiyon(0, dims['Y'], -dims['Z'], cx, cy, olcek, dims)
            ]
            self.canvas.create_polygon(*[c for p in ust_kose for c in p], fill="#3B4252", outline="#88C0D0", width=2)
            for i in range(4):
                self.canvas.create_line(ust_kose[i][0], ust_kose[i][1], alt_kose[i][0], alt_kose[i][1], fill="#4C566A", width=1.5)
                ni = (i + 1) % 4
                self.canvas.create_line(alt_kose[i][0], alt_kose[i][1], alt_kose[ni][0], alt_kose[ni][1], fill="#4C566A", width=1.5)

            # 3. Takım Yolu ve Talaş İzleri
            if self.show_lines_var.get() and self.izlenen_noktalar:
                for x1, y1, z1, x2, y2, z2, mod in self.izlenen_noktalar:
                    s1 = self._izometrik_projeksiyon(x1, y1, z1, cx, cy, olcek, dims)
                    s2 = self._izometrik_projeksiyon(x2, y2, z2, cx, cy, olcek, dims)
                    if mod == 'G00':
                        self.canvas.create_line(s1[0], s1[1], s2[0], s2[1], fill="#FF4444", dash=(3, 3), width=1.5, tags="path_tag")
                    else:
                        renk = "#F39C12" if z2 < 0 else "#00E5FF"
                        self.canvas.create_line(s1[0], s1[1], s2[0], s2[1], fill=renk, width=2.5, tags="path_tag")

            # 4. Canlı 3D Takım + Spindle + Soğutma Suyu Çizimi
            self._sadece_takimi_guncelle()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    _bagimsiz_swansoft_3d_sureci()