# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import glob
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

proje_kok = os.path.abspath(r"e:\Gemini API\Dosyalama_Projesi_Guncel")

# 1. Birlikte paketlenecek veri dosyaları (assets, config, veriler)
datas = [
    (os.path.join(proje_kok, "assets"), "assets"),
    (os.path.join(proje_kok, "data"), "data"),
    (os.path.join(proje_kok, ".env"), "."),
    (os.path.join(proje_kok, "earth_horizon_bg.jpg"), "."),
    (os.path.join(proje_kok, "supheli_bireysel_bilgisayarlar.txt"), "."),
    (os.path.join(proje_kok, "supheli_sunucular.txt"), "."),
    (os.path.join(proje_kok, "altar_app.ico"), "."),
    (os.path.join(proje_kok, "images.jpg"), "."),
]

# Dinamik yükleme (importlib spec_from_file_location) ile çağrılan yardımcı kod dosyaları
for py_file in glob.glob(os.path.join(proje_kok, "*.py")):
    datas.append((py_file, "."))

# CustomTkinter tema ve stil JSON dosyaları
datas += collect_data_files("customtkinter")

# 2. Birlikte paketlenecek ikili programlar (ffmpeg, ffprobe)
binaries = []
for bin_name in ["ffmpeg.exe", "ffprobe.exe"]:
    bin_path = os.path.join(proje_kok, bin_name)
    if os.path.isfile(bin_path):
        binaries.append((bin_path, "."))

# 3. Gizli içe aktarmalar (Tüm Altar modülleri ve harici kütüphaneler)
hiddenimports = [
    "customtkinter",
    "darkdetect",
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
    "PIL.ImageGrab",
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "PyQt6.QtMultimedia",
    "PyQt6.QtMultimediaWidgets",
    "pyqtgraph",
    "pyqtgraph.opengl",
    "pygame",
    "cv2",
    "scapy",
    "scapy.all",
    "yt_dlp",
    "ollama",
    "psutil",
    "cryptography",
    "cryptography.fernet",
    "speech_recognition",
    "winreg",
    "winsound",
    "bs4",
    "requests",
    "urllib3",
    "pydivert",
    "sounddevice",
    "soundfile",
    "matplotlib",
    "pyqtgraph",
    "docx",
    "ezdxf",
    "altar_klavye_kilit",
    "altar_oyun_merkezi",
    "altar_muzik_merkezi",
    "altar_video_oynatici",
    "altar_canva_sunum",
    "altar_ollama_kurucu",
    "altar_readme",
    "altar_sekmeler_gezgini",
    "altar_animasyon_motoru",
    "altar_edr_kalkan",
    "altar_karantina",
    "altar_oturum_yoneticisi",
    "altar_komut_paleti",
    "altar_tema_motoru",
    "altar_ag_radari",
    "altar_pip_yoneticisi",
    "altar_python_ide",
    "altar_zeka_cekirdegi",
    "uzay_telemetri_merkezi",
    "siber_hex_analizor",
    "ag_operasyon_merkezi",
    "scraper",
    "dosya_gezgini_kasa",
    "Swansoft",
    "altar_kimlik_yoneticisi",
    "altar_kod_sablonlari",
    "Guvenlik_Duvari_Tuzakli",
    "Dosya_Sifreleme",
    "Word_Programi",
    "Port_scanner",
    "Ses_kaydedici",
    "DPI",
    "Kamera_Kaydedici",
]
hiddenimports += collect_submodules("customtkinter")

a = Analysis(
    [os.path.join(proje_kok, "Local AI.py")],
    pathex=[proje_kok],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets", "PyQt5.QtOpenGL", "tkinter.test", "unittest", "test"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Altar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon=os.path.join(proje_kok, "altar_app.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Altar",
)
