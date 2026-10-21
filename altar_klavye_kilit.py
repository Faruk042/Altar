# -*- coding: utf-8 -*-
"""
========================================================================================
ALTAR DONANIM KLAVYE & FARE ÇİFT KİLİT MOTORU (altar_klavye_kilit.py)
========================================================================================
* Tema yanındaki kilit butonuna tıklandığında veya F11 ile tetiklendiğinde:
  - Hem KLAVYE hem de FARE / DOKUNMATİK YÜZEY (Touchpad) eş zamanlı olarak kilitlenir.
  - Windows işletim sistemi çekirdek seviyesinde (WH_KEYBOARD_LL ve WH_MOUSE_LL hook)
    tüm tuş basımları, imleç hareketleri ve tıklamalar yutulur (drop event).
  - Ekranda hafif saydam siber HUD Toast bildirimi ve işitsel geri bildirim (Beep) verilir.
  - Açıldığında ise hem klavye hem de fare kilidi anında eş zamanlı serbest bırakılır.
* Açma (Kilit Çözme) Yöntemleri:
  - Klavyeden 'ESC' veya 'F11' tuşuna basıldığında kilit anında açılır.
  - Fareden hızlıca 'Çift Tık' yapıldığında kilit anında açılır.
  - Acil durum mandalı: 'Pause/Break' tuşu kilidi doğrudan düşürür.
  - Windows çekirdek koruması (Ctrl+Alt+Del) her zaman açıktır (%0 kilitli kalma riski).
  - Altar kapatıldığında kancalar otomatik olarak serbest bırakılır.
========================================================================================
"""

from __future__ import annotations

import os
import sys
import time
import threading
import tkinter as tk
from typing import Callable, Optional

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    try:
        import winsound
        WINSOUND_VAR = True
    except ImportError:
        WINSOUND_VAR = False
else:
    ctypes = None
    wintypes = None
    WINSOUND_VAR = False


# Windows Düşük Seviyeli Hook Sabitleri
WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_LBUTTONDOWN = 0x0201

VK_ESCAPE = 0x1B   # ESC Tuşu (En kolay kilit açma tuşu)
VK_F11 = 0x7A      # F11 Tuşu
VK_PAUSE = 0x13    # Pause/Break Tuşu (Acil Çıkış)

# 64-Bit / 32-Bit Tip Uyumluluğu
LRESULT = ctypes.c_longlong if (ctypes and sys.maxsize > 2**32) else (ctypes.c_long if ctypes else int)
WPARAM = wintypes.WPARAM if wintypes else int
LPARAM = wintypes.LPARAM if wintypes else int

if ctypes and wintypes:
    class KBDLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("vkCode", wintypes.DWORD),
            ("scanCode", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_ulonglong if sys.maxsize > 2**32 else wintypes.DWORD)
        ]

    class MSLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("pt", wintypes.POINT),
            ("mouseData", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_ulonglong if sys.maxsize > 2**32 else wintypes.DWORD)
        ]

    HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, WPARAM, LPARAM)
else:
    KBDLLHOOKSTRUCT = None
    MSLLHOOKSTRUCT = None
    HOOKPROC = None


class AltarKlavyeFareKilitServisi:
    """
    Windows Düşük Seviyeli Klavye ve Fare Filtresi (WH_KEYBOARD_LL & WH_MOUSE_LL).
    Tema yanındaki kilit butonuyla klavye ve fareyi eş zamanlı kilitler ve açar.
    """
    _ornek: Optional["AltarKlavyeFareKilitServisi"] = None
    _kilit = threading.Lock()

    def __init__(self):
        self.kilitli: bool = False
        self.calisiyor: bool = False
        self._kbd_hook_id = None
        self._mouse_hook_id = None
        self._kbd_hook_proc = None
        self._mouse_hook_proc = None
        self._thread: Optional[threading.Thread] = None
        self._son_tetikleme_zamani = 0.0
        self._son_mouse_tiklama = 0.0
        self._durum_degisti_callback: Optional[Callable[[bool], None]] = None

    @classmethod
    def ornek_al(cls) -> "AltarKlavyeFareKilitServisi":
        with cls._kilit:
            if cls._ornek is None:
                cls._ornek = AltarKlavyeFareKilitServisi()
            return cls._ornek

    def durum_callback_kaydet(self, callback: Callable[[bool], None]) -> None:
        """Kilit durumu değiştiğinde arayüz butonunu güncellemek için geri çağırım kaydeder."""
        self._durum_degisti_callback = callback

    def kilit_durumu_ayarla(self, kilitli: bool) -> None:
        """Kilit durumunu programatik veya buton üzerinden günceller."""
        if self.kilitli != kilitli:
            self.kilitli = kilitli
            self._sesli_ve_gorsel_bildirim(self.kilitli)
            if callable(self._durum_degisti_callback):
                try:
                    self._durum_degisti_callback(self.kilitli)
                except Exception:
                    pass

    def baslat(self) -> None:
        """Klavye ve fare kanca izleyicisini arka planda başlatır."""
        if sys.platform != "win32" or not ctypes:
            return

        with self._kilit:
            if self.calisiyor:
                return
            self.calisiyor = True

        self._thread = threading.Thread(target=self._hook_dongusu, daemon=True, name="AltarKlavyeFareKilitHook")
        self._thread.start()

    def durdur(self) -> None:
        """Kilitleri çözer ve Windows kancalarını temizce kaldırır."""
        with self._kilit:
            self.kilitli = False
            self.calisiyor = False
            if ctypes:
                if self._kbd_hook_id:
                    try:
                        ctypes.windll.user32.UnhookWindowsHookEx(self._kbd_hook_id)
                    except Exception:
                        pass
                    self._kbd_hook_id = None
                if self._mouse_hook_id:
                    try:
                        ctypes.windll.user32.UnhookWindowsHookEx(self._mouse_hook_id)
                    except Exception:
                        pass
                    self._mouse_hook_id = None

    def _sesli_ve_gorsel_bildirim(self, kilitlendi: bool) -> None:
        """Kullanıcıya kilitlenme veya açılma anında sesli ve odak çalmayan HUD bildirimi sunar."""
        # Sesli Geri Bildirim
        if WINSOUND_VAR:
            try:
                if kilitlendi:
                    winsound.Beep(700, 180)
                else:
                    winsound.Beep(1200, 180)
            except Exception:
                pass

        # Hafif Siber HUD Toast Bildirimi (Pencere odağını kesinlikle çalmaz)
        def _toast_goster():
            try:
                toast = tk.Tk()
                toast.overrideredirect(True)
                toast.attributes("-topmost", True)
                toast.attributes("-alpha", 0.92)
                toast.configure(bg="#050A14")

                ekran_g = toast.winfo_screenwidth()
                tw, th = 560, 56
                tx = (ekran_g - tw) // 2
                ty = 30
                toast.geometry(f"{tw}x{th}+{tx}+{ty}")

                renk = "#EF4444" if kilitlendi else "#10B981"
                metin = (
                    "🔒 KLAVYE & FARE KİLİTLENDİ (Açmak için: [ESC] veya Çift Tık)"
                    if kilitlendi else
                    "🔓 KLAVYE & FARE SERBEST (Tüm Girişler Aktif)"
                )

                lbl = tk.Label(
                    toast, text=metin, font=("Consolas", 12, "bold"),
                    fg=renk, bg="#050A14", padx=16, pady=12
                )
                lbl.pack(expand=True, fill="both")

                # 1.8 saniye sonra otomatik kapan
                toast.after(1800, toast.destroy)
                toast.mainloop()
            except Exception:
                pass

        threading.Thread(target=_toast_goster, daemon=True).start()

    def _hook_dongusu(self) -> None:
        """Windows düşük seviyeli klavye ve fare kancalarını kurup mesaj döngüsünü yürütür."""
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # 64-bit DLL fonksiyon imza tanımlamaları
        kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]

        user32.SetWindowsHookExW.restype = wintypes.HHOOK
        user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
        user32.UnhookWindowsHookEx.restype = wintypes.BOOL
        user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        user32.CallNextHookEx.restype = LRESULT
        user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, WPARAM, LPARAM]

        h_mod = kernel32.GetModuleHandleW(None)

        def _low_level_keyboard_proc(nCode, wParam, lParam):
            if nCode >= 0:
                kb = KBDLLHOOKSTRUCT.from_address(lParam)
                vk = kb.vkCode

                if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    simdi = time.time()
                    # F11 tuşu ile geçiş
                    if vk == VK_F11 and (simdi - self._son_tetikleme_zamani) > 0.35:
                        self._son_tetikleme_zamani = simdi
                        self.kilit_durumu_ayarla(not self.kilitli)
                        return 1

                    # Kilitliyken ESC veya Pause/Break basıldığında kilidi doğrudan aç
                    if self.kilitli and vk in (VK_ESCAPE, VK_PAUSE):
                        self.kilit_durumu_ayarla(False)
                        return 1

                # Eğer kilitliyse diğer tüm klavye girişlerini yut (Drop Key Event)
                if self.kilitli:
                    return 1

            return user32.CallNextHookEx(self._kbd_hook_id, nCode, wParam, lParam)

        def _low_level_mouse_proc(nCode, wParam, lParam):
            if nCode >= 0 and self.kilitli:
                # Kilitliyken hızlı çift tıklama ile kilit açma kontrolü
                if wParam == WM_LBUTTONDOWN:
                    simdi = time.time()
                    if (simdi - self._son_mouse_tiklama) < 0.40:
                        # 400ms içinde çift tıklama yapıldı -> Kilidi Aç!
                        self.kilit_durumu_ayarla(False)
                        return 1
                    self._son_mouse_tiklama = simdi
                    return 1

                # Kilitliyken tüm fare hareketlerini, kaydırmaları ve tıklamaları engelle
                return 1
            return user32.CallNextHookEx(self._mouse_hook_id, nCode, wParam, lParam)

        self._kbd_hook_proc = HOOKPROC(_low_level_keyboard_proc)
        self._mouse_hook_proc = HOOKPROC(_low_level_mouse_proc)

        self._kbd_hook_id = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self._kbd_hook_proc,
            h_mod,
            0
        )
        self._mouse_hook_id = user32.SetWindowsHookExW(
            WH_MOUSE_LL,
            self._mouse_hook_proc,
            h_mod,
            0
        )

        if not self._kbd_hook_id and not self._mouse_hook_id:
            return

        # Windows Mesaj Döngüsü
        msg = wintypes.MSG()
        while self.calisiyor:
            bRet = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if bRet == 0 or bRet == -1:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        # Kapanış Temizliği
        if self._kbd_hook_id:
            try:
                user32.UnhookWindowsHookEx(self._kbd_hook_id)
            except Exception:
                pass
            self._kbd_hook_id = None

        if self._mouse_hook_id:
            try:
                user32.UnhookWindowsHookEx(self._mouse_hook_id)
            except Exception:
                pass
            self._mouse_hook_id = None


# Geriye dönük uyumluluk takma adı (alias)
AltarKlavyeKilitServisi = AltarKlavyeFareKilitServisi


def klavye_kalkanini_baslat():
    """Altar açılışında arka plan klavye ve fare kilit servisini sessizce başlatır."""
    servis = AltarKlavyeFareKilitServisi.ornek_al()
    servis.baslat()
    return servis


def klavye_kalkanini_durdur():
    """Altar kapanışında servisi ve kancaları güvenle sonlandırır."""
    servis = AltarKlavyeFareKilitServisi.ornek_al()
    servis.durdur()


if __name__ == "__main__":
    print("[*] Altar Klavye & Fare Çift Kilit Servisi Test Modu")
    print("[*] Tema yanındaki kilit butonu veya Fn+F11 ile kilitlenir.")
    print("[*] Kilit açma: ESC tuşu veya ekrana Çift Tıklama")
    print("[*] Testi bitirmek için Ctrl+C'ye basın.")
    k = klavye_kalkanini_baslat()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        klavye_kalkanini_durdur()
        print("\n[OK] Kilit servisi sonlandırıldı.")
