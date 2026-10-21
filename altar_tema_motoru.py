# -*- coding: utf-8 -*-
"""
Altar Çoklu Tema Motoru (altar_tema_motoru.py)

Kullanıcının tek tıkla arayüz renk paletini değiştirebilmesini sağlar:
  1) 🌲 Zümrüt Doğa & Şelale (Emerald River Nature) - Göz dinlendirici yeşil ve nehir tonları
  2) 🌌 Altar Siber Orijinal - İleri teknoloji lacivert ve neon turkuaz
  3) ⚡ Matrix Neon - Saf siyah ve hacker yeşili
  4) 🔮 Cyberpunk Synthwave - Mor plazma ve neon pembe/camgöbeği

Hiçbir harici dosya indirmez; tamamen yerel CustomTkinter renk haritasıyla çalışır.
"""

from __future__ import annotations

from typing import Any, Dict


class AltarTemaMotoru:
    """Arayüz renk temalarını yöneten yapılandırma sınıfı."""

    TEMALAR = {
        "🌲 Zümrüt Doğa & Şelale": {
            "ad": "🌲 Zümrüt Doğa & Şelale",
            "ana_bg": "#021A14",
            "panel_bg": "#052E24",
            "kart_bg": "#0A3D30",
            "kenarlik": "#10B981",
            "vurgu": "#059669",
            "vurgu_hover": "#047857",
            "neon": "#34D399",
            "yazi_ana": "#ECFDF5",
            "yazi_ikincil": "#A7F3D0",
        },
        "🌌 Altar Siber Orijinal": {
            "ad": "🌌 Altar Siber Orijinal",
            "ana_bg": "#0B0F19",
            "panel_bg": "#111827",
            "kart_bg": "#1F2937",
            "kenarlik": "#1E293B",
            "vurgu": "#1E3A8A",
            "vurgu_hover": "#2563EB",
            "neon": "#00F5D4",
            "yazi_ana": "#E2E8F0",
            "yazi_ikincil": "#94A3B8",
        },
        "⚡ Matrix Neon": {
            "ad": "⚡ Matrix Neon",
            "ana_bg": "#020703",
            "panel_bg": "#051307",
            "kart_bg": "#08210C",
            "kenarlik": "#00FF66",
            "vurgu": "#008F39",
            "vurgu_hover": "#00BF4C",
            "neon": "#00FF66",
            "yazi_ana": "#E6FFE6",
            "yazi_ikincil": "#80FF9E",
        },
        "🔮 Cyberpunk Synthwave": {
            "ad": "🔮 Cyberpunk Synthwave",
            "ana_bg": "#130026",
            "panel_bg": "#1F043D",
            "kart_bg": "#2E0854",
            "kenarlik": "#EC4899",
            "vurgu": "#831843",
            "vurgu_hover": "#9D174D",
            "neon": "#06B6D4",
            "yazi_ana": "#FDF2F8",
            "yazi_ikincil": "#F472B6",
        },
    }

    _aktif_tema_adi = "🌲 Zümrüt Doğa & Şelale"

    @classmethod
    def aktif_tema_getir(cls) -> Dict[str, str]:
        return cls.TEMALAR.get(cls._aktif_tema_adi, cls.TEMALAR["🌲 Zümrüt Doğa & Şelale"])

    @classmethod
    def tema_degistir(cls, yeni_tema_adi: str) -> Dict[str, str]:
        if yeni_tema_adi in cls.TEMALAR:
            cls._aktif_tema_adi = yeni_tema_adi
        return cls.aktif_tema_getir()

    @classmethod
    def tema_listesi(cls) -> list[str]:
        return list(cls.TEMALAR.keys())
