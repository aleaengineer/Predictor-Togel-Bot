import os
from collections import Counter, defaultdict
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Konfigurasi Awal ---
# Ganti dengan token bot yang Anda dapatkan dari @BotFather
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Setup logging untuk melihat error (opsional tapi sangat disarankan)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# =======================================================
# === BAGIAN ANALISIS (KODE ASLI ANDA YANG DISEMPURNAKAN) ===
# =======================================================

# === Fungsi Angka Cermin ===
def mirror_number(n):
    mirror_map = {0: 5, 1: 6, 2: 7, 3: 8, 4: 9,
                  5: 0, 6: 1, 7: 2, 8: 3, 9: 4}
    # Mengonversi input ke integer jika berupa string
    return mirror_map.get(int(n), int(n))

# === Fungsi Membaca File TXT ===
# Dimodifikasi untuk membaca dari path file yang diunduh
def baca_history_dari_file(nama_file):
    try:
        with open(nama_file, 'r') as file:
            # Memastikan tidak ada baris kosong dan membersihkan spasi
            lines = [line.strip() for line in file.readlines() if line.strip()]
            return [str(h) for h in lines]
    except FileNotFoundError:
        logger.error(f"File '{nama_file}' tidak ditemukan.")
        return []
    except Exception as e:
        logger.error(f"Error saat membaca file: {e}")
        return []


# === Analisis Digit dan Posisi ===
def analisis_digit(history):
    semua_digit = []
    posisi_digit = defaultdict(list)

    for angka in history:
        for i, d in enumerate(angka):
            try:
                digit = int(d)
                semua_digit.append(digit)
                posisi_digit[i].append(digit)
            except ValueError:
                # Abaikan karakter yang bukan digit
                continue

    return semua_digit, posisi_digit

# === Hitung Angka Ikut ===
def hitung_angka_ikut(history):
    pair_counter = Counter()
    for angka in history:
        digit_unik = sorted(list(set(angka))) # diurutkan agar (1,2) dan (2,1) sama
        for i in range(len(digit_unik)):
            for j in range(i + 1, len(digit_unik)):
                # Memastikan keduanya adalah digit
                if digit_unik[i].isdigit() and digit_unik[j].isdigit():
                    pair_counter[(digit_unik[i], digit_unik[j])] += 1
    return pair_counter

# === Fungsi Utama Analisis (SEKARANG LENGKAP) ===
def generate_bbfs_prediktif(history, top_n=7):
    if not history:
        return "Data histori kosong atau tidak valid. Tidak ada yang bisa dianalisis."

    semua_digit, posisi_digit = analisis_digit(history)
    if not semua_digit:
        return "Tidak ada digit valid yang ditemukan dalam histori."

    frekuensi = Counter(semua_digit)
    angka_teratas = frekuensi.most_common(top_n)

    # Menyiapkan hasil dalam format teks yang rapi
    pesan_hasil = f"🔥 *Hasil Analisis dari {len(history)} Data Terakhir* 🔥\n\n"
    pesan_hasil += f"1️⃣ *Top {len(angka_teratas)} Angka Paling Sering Muncul:*\n"
    for digit, freq in angka_teratas:
        pesan_hasil += f"   - Angka `{digit}`: muncul {freq} kali\n"

    top_digits_set = [str(d[0]) for d in angka_teratas]
    pesan_hasil += f"\n2️⃣ *Rekomendasi BBFS {len(top_digits_set)} Digit:*\n"
    pesan_hasil += f"   `{''.join(top_digits_set)}`\n"

    pesan_hasil += f"\n3️⃣ *Angka Cermin (Mirror) dari Top Digit:*\n"
    mirror_digits = [str(mirror_number(d)) for d in top_digits_set]
    pesan_hasil += f"   `{''.join(mirror_digits)}`\n"

    # Analisis Angka Ikut
    pair_counter = hitung_angka_ikut(history)
    if pair_counter:
        top_pairs = pair_counter.most_common(5)
        pesan_hasil += f"\n4️⃣ *Top 5 Pasangan Angka Ikut Terkuat:*\n"
        for pair, freq in top_pairs:
            pesan_hasil += f"   - Pasangan `({pair[0]}, {pair[1]})`: muncul bersama {freq} kali\n"
            
    pesan_hasil += f"\n\n_Disclaimer: Analisis ini berdasarkan data historis dan hanya untuk referensi. Gunakan dengan bijak._"
    
    return pesan_hasil


# =================================================
# === BAGIAN KODE BOT TELEGRAM ===
# =================================================

# Handler untuk perintah /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        f"Halo {user.mention_html()}!\n\n"
        "Selamat datang di Bot Analisis Angka.\n"
        "Kirimkan saya file `.txt` yang berisi histori angka (satu angka per baris), lalu balas file tersebut dengan perintah `/analisis`.\n\n"
        "Gunakan perintah /help untuk melihat bantuan."
    )

# Handler untuk perintah /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "💡 *Cara Penggunaan Bot:*\n\n"
        "1. Siapkan data histori Anda dalam sebuah file teks (`.txt`). Pastikan setiap angka berada di baris baru.\n\n"
        "2. Kirim file `.txt` tersebut ke chat ini.\n\n"
        "3. *Balas (Reply)* pesan file yang baru Anda kirim dengan perintah `/analisis`.\n\n"
        "Anda juga bisa menambahkan jumlah digit yang ingin dianalisis, contoh: `/analisis 8` (untuk mendapatkan 8 digit teratas). Jika tidak diisi, defaultnya adalah 7 digit.",
        parse_mode='Markdown'
    )

# Handler untuk menangani file yang dikirim pengguna
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    document = update.message.document
    if document.mime_type == 'text/plain':
        await update.message.reply_text(
            "✅ File `.txt` diterima. Sekarang, silakan *balas (reply)* pesan file ini dengan perintah `/analisis` untuk memulai."
        )
    else:
        await update.message.reply_text(
            "❌ Format file tidak didukung. Harap kirim file dengan format `.txt`."
        )
        
# Handler untuk perintah /analisis
async def analisis_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Memeriksa apakah perintah ini adalah balasan untuk sebuah pesan file
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text(
            "⚠️ *Perintah salah!* Harap jalankan perintah `/analisis` dengan cara *membalas (reply)* pesan file `.txt` yang berisi histori." ,
            parse_mode='Markdown'
        )
        return

    # Memeriksa ulang tipe file
    document = update.message.reply_to_message.document
    if document.mime_type != 'text/plain':
        await update.message.reply_text(
            "❌ Anda membalas pesan yang bukan file `.txt`. Harap balas file histori yang benar.",
        )
        return

    # Mengambil argumen (jika ada) untuk top_n
    try:
        top_n = int(context.args[0]) if context.args else 7
    except (ValueError, IndexError):
        top_n = 7

    await update.message.reply_text("⏳ Sedang memproses analisis, mohon tunggu sebentar...")

    # Mengunduh file
    file = await document.get_file()
    file_path = f"history_{update.effective_user.id}.txt"
    await file.download_to_drive(file_path)

    # Membaca dan menganalisis
    history = baca_history_dari_file(file_path)
    hasil_analisis = generate_bbfs_prediktif(history, top_n)
    
    # Mengirim hasil
    await update.message.reply_text(hasil_analisis, parse_mode='Markdown')

    # Membersihkan file yang diunduh
    os.remove(file_path)
    
# Handler untuk pesan teks biasa yang bukan perintah
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Saya tidak mengerti pesan itu. Coba kirim file `.txt` atau gunakan perintah /help."
    )


def main() -> None:
    """Jalankan bot."""
    if TELEGRAM_BOT_TOKEN == 'GANTI_DENGAN_TOKEN_BOT_ANDA':
        print("!!! KESALAHAN: Token bot belum diisi. Silakan edit file dan isi variabel TELEGRAM_BOT_TOKEN.")
        return
        
    # Buat aplikasi bot
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Daftarkan handler untuk setiap perintah
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("analisis", analisis_command))
    
    # Daftarkan handler untuk pesan file dan teks
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Jalankan bot sampai pengguna menekan Ctrl-C
    print("Bot sedang berjalan... Tekan Ctrl+C untuk berhenti.")
    application.run_polling()


if __name__ == '__main__':
    main()
