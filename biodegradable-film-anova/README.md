# Biodegradable Film ANOVA
## Excel to CSV & Factorial ANOVA Automation

Project ini bertujuan untuk mengotomatisasi pemrosesan data penelitian biodegradable film, mulai dari pembacaan file Excel mentah (seringkali dalam format non-tidy yang diekspor dari alat/template), konversi ke CSV bersih, pembersihan data (preprocessing), uji asumsi, analisis Factorial ANOVA, uji post-hoc Tukey, hingga pembuatan visualisasi dan laporan statistik otomatis berformat HTML.

### Desain Eksperimen
Penelitian ini dirancang menggunakan Rancangan Acak Lengkap (RAL) faktorial dengan 3 faktor utama:
* **Faktor A (CMC):** 1g, 2g, 3g (3 level)
* **Faktor B (PVA):** 0g, 1g, 2g, 3g (4 level)
* **Faktor C (Plasticizer):** Sorbitol, Gliserol (2 level)

**Total kombinasi:** 3 × 4 × 2 = 24 kombinasi.
**Ulangan:** 3 kali.
**Total observasi yang diharapkan:** 72.

> **Catatan Formulasi (A-L):** Kode formulasi (A-L) digunakan sebagai identifier untuk kombinasi (CMC × PVA). Program secara otomatis akan memetakan kode ini ke dalam nilai CMC dan PVA jika nilai numeriknya tidak tersedia.

### Struktur Data (Format Input)
Program mendukung format input **.xls**, **.xlsx**, dan **.csv**. Program dapat menangani format *tidy* maupun *non-tidy*:

1. **Format Tidy:** Data memiliki satu baris header (mis. CMC, PVA, Plasticizer, Replicate, FTL, dll) dan satu baris untuk setiap observasi.
2. **Format Non-Tidy:** Data terbagi dalam beberapa blok atau sheet berdasarkan Plasticizer (mis. sheet "FTL Kimia Sorbitol"). Program akan mendeteksi baris judul blok atau sheet untuk menandai data berikutnya dengan Plasticizer yang sesuai secara otomatis. 

### Instalasi & Penggunaan

1. **Persyaratan:** Python 3.8+
2. **Instal dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Jalankan analisis:**
   Letakkan file data mentah (misal: `pengujian.xlsx`) di dalam folder `data/` dan jalankan:
   ```bash
   python main.py
   ```
   Atau Anda dapat merujuk file secara spesifik:
   ```bash
   python main.py --input "data/pengujian.xlsx" --alpha 0.05
   ```
4. **Hanya Konversi & Preprocessing:**
   Jika Anda hanya ingin merapikan data tanpa menjalankan analisis statistik:
   ```bash
   python main.py --input "data/pengujian.xlsx" --convert-only
   ```

### Alur Analisis
1. **Excel Converter:** Membaca data dan memisahkan ke raw CSV per sheet.
2. **Preprocessing:** Merapikan nama kolom, mengisi nilai formulasi (forward fill), menambahkan nilai CMC dan PVA jika hilang, mendeteksi plasticizer, dan menghapus baris tak valid.
3. **Validasi:** Mengecek keseimbangan desain (3 ulangan), duplikasi, dan konsistensi FTL vs Kelarutan (Kelarutan = 100 - FTL).
4. **Descriptive Statistics:** N, Mean, SD, SE, 95% CI.
5. **Assumption Testing:** Uji Normalitas (Shapiro-Wilk) dan Homogenitas Varians (Levene's Test).
6. **Factorial ANOVA:** Menggunakan model `Response ~ C(CMC) * C(PVA) * C(Plasticizer)`. Program memilih secara otomatis antara Type II (desain seimbang) dan Type III (tidak seimbang).
7. **Post-Hoc (Tukey HSD):** Hanya dilakukan pada faktor utama yang signifikan.
8. **Simple Effects / Interaction:** Dilakukan jika efek interaksi signifikan.
9. **Visualisasi:** Plot rata-rata, plot interaksi, dan diagnostik residual (Q-Q plot & Residual plot).
10. **HTML Report:** Menghasilkan `output/report/statistical_report.html` yang merangkum hasil keseluruhan dan menginterpretasikannya.

### Keterbatasan
- Interpretasi Signifikansi (p-value): Signifikansi statistik tidak berarti optimasi terbaik secara praktis. Untuk mencari formulasi optimum, disarankan menggunakan metode optimasi lanjutan seperti RSM (Response Surface Methodology).
- Data yang Kosong (Missing Values): Observasi di mana semua respons kosong akan dibuang. Missing value pada satu respons tidak menghilangkan observasi untuk respons lainnya. Tidak ada pengisian (imputation) data otomatis.
- Imputasi Rata-Rata: Program menggunakan observasi individu. Jika baris rata-rata ditemukan dalam raw data, baris tersebut akan diabaikan (karena tidak merepresentasikan replikasi independen).

### Output
Semua hasil disimpan di dalam folder `output/`. Hasil terpenting termasuk:
- `output/cleaned_dataset.csv`: Data mentah yang siap dianalisis di program lain.
- `output/report/statistical_report.html`: Laporan eksekutif beserta grafik dan narasi interpretatif.
- `output/anova/`: Menyimpan p-value, tabel ANOVA, asumsí, dan simple effects.
- `output/plots/`: Semua grafik beresolusi 300 DPI.
