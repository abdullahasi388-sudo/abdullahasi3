"""
Calc & Hang — İşlem Yap, Harfi Kurtar
Python konsol oyunu

Bu dosya, kullanıcı tarafından istenen proje şartlarına uygun tek dosyalık bir oyundur.
Çalıştırma: python calc_and_hang.py

Özellikler:
- Rastgele kategori ve kelime seçimi (meyve, hayvan, teknoloji)
- Harf tahmini sistemi (geçersiz giriş kontrolü)
- Hesap makinesi entegrasyonu (toplama, çıkarma, çarpma, bölme) — her bir işlem birer defa kullanılabilir
- Bonus ve ipucu sistemi
- Skorların scores.json dosyasında saklanması (en yüksek 5 skor)
- Tolerans ile ondalık karşılaştırma (1e-6)
- Temiz, modüler ve yorumlu kod

Yazan: ChatGPT (örnek uygulama)
"""

import json
import math
import os
import random
import sys
import time
from typing import Dict, List, Tuple

# Optional: renkli çıktı (colorama yüklü değilse yedek davranış)
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
except Exception:
    class _C:
        def __getattr__(self, name):
            return ""
    Fore = Style = _C()

SCOREFILE = "scores.json"
MAX_ERRORS = 6
FLOAT_TOL = 1e-6

WORDS = {
    "meyve": ["elma", "muz", "armut", "çilek", "karpuz", "kiraz", "portakal"],
    "hayvan": ["aslan", "kaplan", "kedi", "kopek", "fil", "zebra", "maymun"],
    "teknoloji": ["bilgisayar", "yazilim", "sunucu", "ag", "robot", "kamera", "kamera"],
}

HANGMAN_PICS = [
    "\n\n\n\n\n\n",
    "\n\n\n\n\n\n____",
    "  |\n  |\n  |\n  |\n  |\n__|__",
    "  _______\n  |/    |\n  |\n  |\n  |\n__|__",
    "  _______\n  |/    |\n  |     O\n  |\n  |\n__|__",
    "  _______\n  |/    |\n  |     O\n  |    /|\\n  |\n__|__",
    "  _______\n  |/    |\n  |     O\n  |    /|\\\n  |    / \\n__|__",
]


# -------------------- Utility functions --------------------

def clear_console():
    """Terminali temizlemeye çalışır (platforma göre)."""
    os.system("cls" if os.name == "nt" else "clear")


def load_scores() -> List[Dict]:
    """scores.json'dan skor listesini yükler; dosya yoksa boş liste döner."""
    try:
        with open(SCOREFILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except FileNotFoundError:
        return []
    except Exception:
        print(Fore.YELLOW + "Skor dosyası okunurken hata oldu, yeni dosya oluşturulacak.")
    return []


def save_score(entry: Dict):
    """Yeni bir skor girişi ekleyip en yüksek 5'i scores.json'a kaydeder."""
    scores = load_scores()
    scores.append(entry)
    # En yüksek ilk 5'e göre sırala
    scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)[:5]
    try:
        with open(SCOREFILE, "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(Fore.YELLOW + f"Skor kaydedilemedi: {e}")


# -------------------- Game logic --------------------

def choose_word() -> Tuple[str, str]:
    """Rastgele kategori ve o kategoriden rastgele bir kelime seçer.

    Returns: (kategori, kelime)
    """
    category = random.choice(list(WORDS.keys()))
    word = random.choice(WORDS[category]).lower()
    return category, word


class GameState:
    """Oyun durumunu tutar."""

    def __init__(self, category: str, word: str):
        self.category = category
        self.word = word
        self.masked = ["_" if ch != " " else " " for ch in word]
        self.guessed_letters: List[str] = []
        self.errors = 0
        self.bonus = 0
        self.score = 0
        # İşlemler: her bir tür bir kere kullanılabilir
        self.operations_allowed = {"+": True, "-": True, "*": True, "/": True}

    def reveal_random_letter(self) -> None:
        """Kelime içinde rastgele kapalı bir harf açar (varsa)."""
        indices = [i for i, ch in enumerate(self.masked) if ch == "_"]
        if not indices:
            return
        i = random.choice(indices)
        self.masked[i] = self.word[i]

    def is_won(self) -> bool:
        return "_" not in self.masked

    def is_lost(self) -> bool:
        return self.errors >= MAX_ERRORS


# -------------------- Input validation --------------------

def valid_letter_input(s: str) -> bool:
    """Girilen karakterin tek bir alfabetik harf olup olmadığını kontrol eder (Türkçe karakterleri kabullenir)."""
    return len(s) == 1 and s.isalpha()


# -------------------- Calculator integration --------------------

def do_operation(game: GameState) -> None:
    """Kullanıcının bir işlem seçip çözmesini sağlar. Doğruysa bonus verir, yanlışsa hata ekler.

    Kurallar:
    - Her işlem tipi ( + - * / ) oyunda bir kez kullanılabilir.
    - Bölmede bölen 0 kontrol edilir.
    - Ondalık karşılaştırma tolerance FLOAT_TOL ile yapılır.
    - Kullanıcı 'iptal' yazarak işlemi iptal edebilir.
    """
    print("\nİşlem türü seçin: +  -  *  /")
    op = input("İşlem (veya 'iptal' yaz): ").strip()
    if op.lower() == "iptal":
        print("İşlem iptal edildi.")
        return
    if op not in game.operations_allowed:
        print(Fore.YELLOW + "Geçersiz işlem türü.")
        return
    if not game.operations_allowed[op]:
        print(Fore.YELLOW + "Bu işlem türünü zaten kullandınız.")
        return

    # Operasyon bir kere kullanılacak
    game.operations_allowed[op] = False

    # Sayıları al
    try:
        a_raw = input("Birinci sayı: ").strip()
        if a_raw.lower() == "iptal":
            print("İşlem iptal edildi.")
            game.operations_allowed[op] = True
            return
        b_raw = input("İkinci sayı: ").strip()
        if b_raw.lower() == "iptal":
            print("İşlem iptal edildi.")
            game.operations_allowed[op] = True
            return
        a = float(a_raw)
        b = float(b_raw)
    except ValueError:
        print(Fore.YELLOW + "Sayilar uygun formatta değil. İşlem iptal edildi.")
        game.operations_allowed[op] = True
        return

    # Bölme için bölen 0 kontrolü
    if op == "/" and abs(b) <= FLOAT_TOL:
        print(Fore.RED + "Bölen 0 olamaz! Hata sayınız artıyor.")
        game.errors += 1
        return

    # Beklenen sonucu hesapla
    if op == "+":
        expected = a + b
    elif op == "-":
        expected = a - b
    elif op == "*":
        expected = a * b
    elif op == "/":
        expected = a / b
    else:
        print(Fore.YELLOW + "Bilinmeyen işlem."
) 
        return

    # Kullanıcıdan sonucu al
    try:
        ans_raw = input("İşlemin sonucu: ").strip()
        if ans_raw.lower() == "iptal":
            print("İşlem iptal edildi.")
            game.operations_allowed[op] = True
            return
        ans = float(ans_raw)
    except ValueError:
        print(Fore.YELLOW + "Sonuç uygun formatta değil. Hata sayınız artıyor.")
        game.errors += 1
        return

    if math.isclose(ans, expected, rel_tol=0.0, abs_tol=FLOAT_TOL):
        # Doğru işlem
        game.bonus += 1
        game.score += 15
        print(Fore.GREEN + "Doğru! 1 bonus kazandınız ve rastgele bir harf açılıyor.")
        game.reveal_random_letter()
    else:
        game.errors += 1
        game.score -= 10
        print(Fore.RED + f"Yanlış sonuç. Beklenen yaklaşık: {expected}. Hata hakkınız azaldı.")


# -------------------- Main game UI --------------------

def print_status(game: GameState) -> None:
    """Her turda oyuncuya gösterilecek bilgileri yazdırır."""
    clear_console()
    print(Fore.CYAN + "=== Calc & Hang — İşlem Yap, Harfi Kurtar ===")
    print(HANGMAN_PICS[min(game.errors, len(HANGMAN_PICS)-1)])
    print("Kelime: ", " ".join(game.masked))
    print(f"Tahmin edilen harfler: {', '.join(game.guessed_letters) if game.guessed_letters else '-'}")
    print(f"Kalan hata hakkı: {MAX_ERRORS - game.errors}")
    print(f"Bonus puanı: {game.bonus}")
    print(f"Puan: {game.score}")
    print("Seçenekler: (1) Harf Tahmini  (2) İşlem Çözme  (3) İpucu Alma  (q) Çıkış")


def take_hint(game: GameState) -> None:
    """İpucu: 1 bonus puan harcar ve kategori gösterir."""
    if game.bonus <= 0:
        print(Fore.YELLOW + "Yeterli bonusunuz yok. İpucu için 1 bonus gerekli.")
        return
    game.bonus -= 1
    
    print(Fore.MAGENTA + f"İpucu — Kategori: {game.category}")


def guess_letter(game: GameState) -> None:
    """Kullanıcıdan bir harf alır, geçerliyse kontrol eder ve durumu günceller."""
    s = input("Tahmin ettiğiniz harfi girin: ").strip().lower()
    if not valid_letter_input(s):
        print(Fore.YELLOW + "Lütfen tek bir alfabetik karakter girin.")
        return
    if s in game.guessed_letters:
        print(Fore.YELLOW + "Bu harfi zaten tahmin ettiniz.")
        return
    game.guessed_letters.append(s)
    if s in game.word:
        # Açılan tüm pozisyonları güncelle
        for i, ch in enumerate(game.word):
            if ch == s:
                game.masked[i] = s
        game.score += 10
        print(Fore.GREEN + "Doğru tahmin! Harf açıldı.")
    else:
        game.errors += 1
        game.score -= 5
        print(Fore.RED + "Yanlış tahmin. Hata hakkınız azaldı.")


# -------------------- Game loop --------------------

def play_game():
    """Ana oyun döngüsü. Oyun burada başlar ve sonuç kaydedilir."""
    category, word = choose_word()
    game = GameState(category, word)

    # Oyun döngüsü
    while True:
        print_status(game)
        # Kontroller: kazanma veya kaybetme
        if game.is_won():
            game.score += 50  # final bonus
            print(Fore.GREEN + f"Tebrikler! Kelime: {game.word}")
            print(Fore.GREEN + f"Toplam puan: {game.score}")
            name = input("Skor kaydetmek için isminizi girin (enter atla): ").strip()
            if name:
                save_score({"name": name, "score": game.score, "word": game.word, "date": time.strftime('%Y-%m-%d %H:%M:%S')})
                print(Fore.CYAN + "Skor kaydedildi.")
            else:
                print("Skor kaydedilmedi.")
            break
        if game.is_lost():
            game.score -= 20  # final penalty
            print(Fore.RED + f"Kaybettiniz! Doğru kelime: {game.word}")
            print(Fore.RED + f"Toplam puan: {game.score}")
            name = input("Skor kaydetmek için isminizi girin (enter atla): ").strip()
            if name:
                save_score({"name": name, "score": game.score, "word": game.word, "date": time.strftime('%Y-%m-%d %H:%M:%S')})
                print(Fore.CYAN + "Skor kaydedildi.")
            else:
                print("Skor kaydedilmedi.")
            break

        choice = input("Seçiminiz: ").strip().lower()
        if choice == "1":
            guess_letter(game)
        elif choice == "2":
            do_operation(game)
        elif choice == "3":
            take_hint(game)
        elif choice == "q":
            print("Oyundan çıkılıyor. Hoşçakal!")
            break
        else:
            print(Fore.YELLOW + "Geçersiz seçenek. Lütfen 1,2,3 ya da q girin.")

    # Oyun sonu: skor tablosunu göster
    print("\n=== En Yüksek Skorlar ===")
    scores = load_scores()
    if not scores:
        print("Henüz kayıtlı skor yok.")
    else:
        for i, s in enumerate(scores, 1):
            print(f"{i}. {s.get('name','-')} — {s.get('score',0)} — Kelime: {s.get('word','-')} — {s.get('date','-')}")


# -------------------- Entry point --------------------

if __name__ == "__main__":
    try:
        play_game()
    except KeyboardInterrupt:
        print("\nOyundan çıkıldı (Ctrl+C).")
        sys.exit(0)