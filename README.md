# ALUX Kit EP005 - ingest footage & graphic ke Premiere

Kit ini bikin Hermes di komputermu bisa: download footage Envato/arsip yang kamu pilih, rename, lalu pasang ke Premiere. Setelah itu pasang juga graphic hasil motion-mu.

Dipakai oleh: AGIL, ZULFIKAR, SULTAN, REPI.

**Paling cepat:** buka `PROMPT_HERMES.md`, copy prompt-nya ke Hermes-mu. Hermes akan memasang dan menjalankan semuanya, dan berhenti saat butuh kamu.

## Yang harus sudah ada

- Windows, Premiere Pro (2024 ke atas), Chrome
- Hermes sudah terpasang dan jalan (Python ikut terpasang bersama Hermes)
- ffmpeg (supaya `ffprobe` jalan)
- Akun Envato milikmu sendiri yang boleh download
- Git for Windows: https://git-scm.com/download/win (klik Next terus)
- Salinan master Premiere EP005 (`PROJECT 5 - HOW BIG OIL ACTUALLY WORKS.prproj`)
- Folder pilihan footage-mu dari yang membagikan kit: `EP005_PILIH_FOOTAGE_<NAMAMU>.zip`. Unzip, isinya `pick.html`, `full_catalog.json`, dan nanti `pilihan_<NAMAMU>.json` (dibuat otomatis saat kamu memilih). Ingest membaca katalog dari folder itu.

## A. Pasang (sekali saja)

1. Terima undangan repo ini lewat email GitHub (klik Accept).
2. Buka folder tempat kamu mau simpan kit, mis. `D:\`. Klik kanan di area kosong, pilih "Open in Terminal" (atau "Git Bash Here"), lalu ketik:
   ```
   git clone https://github.com/zlfkraffandi-dev/alux-kit.git
   ```
   Login GitHub saat browser terbuka.
3. Buka folder `alux-kit`, double-click **`1_PASANG_DULU.bat`**.
   - Harus berakhir dengan tulisan `SELESAI`.
   - Kalau ada tulisan `[GAGAL]`, baca pesannya. Python/ffmpeg belum ada adalah penyebab paling umum.
   - Aman dijalankan berulang. Bridge dan panel yang sudah terpasang tidak ditimpa.
4. **Tutup Premiere sepenuhnya lalu buka lagi**, buka salinan master.
5. Di Premiere: menu **Window > Extensions > Hermes Bridge**.
   - Tab itu harus **terlihat di depan**. Kalau tersembunyi di belakang tab lain, bridge bisa berhenti menjawab.
   - Klik sekali di timeline sequence master supaya aktif.
6. Double-click **`2_BUKA_CHROME.bat`**. Chrome terbuka, login Envato di jendela itu. Jangan ditutup selama ingest.

## B. Pakai: footage

1. Pilih footage di HTML sampai selesai. File `pilihan_<NAMAMU>.json` tersimpan otomatis di folder HTML itu.
2. Pastikan A.4, A.5, A.6 sudah beres (Premiere + Hermes Bridge terlihat + Chrome Envato login).
3. Bilang ke Hermes:
   ```
   ingest footage dari folder <path folder hasil unzip, yang berisi pilihan_NAMAMU.json dan full_catalog.json>
   ```
4. Hermes akan:
   1. dry-run dulu (daftar rencana, belum ada yang dipasang)
   2. coba 1 slot dulu
   3. kalau cocok, jalankan semua
5. Setelah selesai Hermes memberi laporan. Baca baris yang berawalan `WARN` atau `ERR`:
   - `WARN SHORT`: footage lebih pendek dari marking, ada celah. Kamu yang tutup.
   - `ERR ... busy`: track target sudah terisi, tidak ditimpa.
   - `ERR MARKINGS CHANGED`: ada marking berubah. Stop, jangan save, kabari yang membagikan kit ini.
6. **Cek visual 2-3 slot pertama dengan matamu** (footage menutupi frame, tidak ada bar hitam). AI tidak bisa melihat hasilnya.

Hasil: Envato masuk **V1**, arsip masuk **V2** (zoom pelan), cocok lewat NAMA marking (`B012`, `A004`), bukan timecode.

## C. Pakai: graphic

1. Selesai bikin motion graphic dari Figma, render tiap graphic dengan nama diawali kode marking: `EP005-014.mp4`, `EP005-001A.mov` (akhiran huruf boleh).
2. Kumpulkan semua di satu folder.
3. Bilang ke Hermes:
   ```
   ingest graphic dari folder <path folder render>
   ```
4. Graphic masuk **V3**, tepat di marking V6 dengan kode itu.

## D. Batal / salah

Bilang ke Hermes: `undo ingest`. Semua yang tadi dipasang dihapus (marking tidak disentuh).

## E. Update kit

Kalau ada kabar ada update:
```
cd alux-kit
git pull
```
lalu double-click `1_PASANG_DULU.bat` lagi.

## F. Kalau macet

| Gejala | Yang dilakukan |
|---|---|
| `Hermes Bridge not alive` atau timeout | Tab Hermes Bridge ke depan, klik timeline, tunggu 1 menit. Belum juga: tutup dan buka lagi Premiere. Jangan kirim perintah berulang saat macet. |
| `Tidak ada sequence` | Buka salinan master, klik timeline. |
| Download gagal / `download timeout` | Cek sudah login Envato di Chrome dari `2_BUKA_CHROME.bat`. Pesan dialog Envato ikut dicetak, kirim ke yang membagikan kit ini. |
| Panel Hermes Bridge tidak ada di menu Extensions | Jalankan ulang `1_PASANG_DULU.bat`, restart Premiere. |
| Python/ffprobe tidak ketemu | Pasang, lalu buka terminal baru dan jalankan `.bat` lagi. |

Kirim isi `ingest_report.json` ke yang membagikan kit ini kalau ada baris `ERR`.

## Aturan

- Pakai **salinan** master, bukan master asli.
- Jangan Save ke master asli kalau ingest memberi `ERR MARKINGS CHANGED`.
- Jangan ubah marking (V4/V5/V6) dengan tangan sebelum ingest selesai.
- Akun Envato dipakai milikmu sendiri. Jangan simpan password di repo ini.

## Isi folder

| File | Fungsi |
|---|---|
| `1_PASANG_DULU.bat` | Pasang websockets, Hermes Bridge, panel Premiere, skill |
| `2_BUKA_CHROME.bat` | Buka Chrome dengan port debug untuk download Envato |
| `ingest.py` | Skrip utama: download, rename, import, undo |
| `bridge/`, `panel/` | Hermes Bridge dan panel Premiere |
| `skill/SKILL.md` | Instruksi untuk Hermes |
