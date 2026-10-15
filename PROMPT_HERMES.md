# Prompt untuk Hermes editor

Copy semua isi blok di bawah, ganti `<NAMAMU>` (AGIL / ZULFIKAR / SULTAN / REPI), lalu tempel ke chat Hermes di komputermu.

```
Kamu asistenku untuk proyek ALUX EP005 ("How Big Oil Actually Works"). Namaku <NAMAMU>.
Tugasmu: pasang ALUX Kit, lalu bantu aku memasukkan footage pilihanku dan graphic ke Premiere.
Kerjakan berurutan. Setiap tahap: jalankan, BACA hasilnya, laporkan apa adanya (jangan klaim sukses tanpa output). Kalau gagal, berhenti dan jelaskan, jangan menebak.

ATURAN KERAS
- Jangan pernah mengetik, meminta, atau menyimpan password / kode login Envato. Aku yang login sendiri di jendela Chrome.
- Jangan Save project Premiere. Jangan ubah marking (klip di V4, V5, V6) kecuali lewat ingest.py.
- Jangan jalankan ingest sungguhan sebelum dry-run dan tes 1 slot kubaca dan kusetujui.
- Jangan kirim banyak job ke Hermes Bridge sekaligus. Satu per satu.
- Kalau ada baris ERR atau WARN di laporan, sebutkan satu per satu.

TAHAP 1 - CEK SYARAT (laporkan tiap baris: ada / tidak)
  git --version
  python --version
  ffprobe -version
  Chrome: C:\Program Files\Google\Chrome\Application\chrome.exe (atau Program Files (x86))
  Premiere Pro terpasang.
Kalau ada yang tidak ada, berhenti dan beri tahu cara memasangnya (git: git-scm.com, ffmpeg: ffmpeg.org atau winget install ffmpeg). Jangan lanjut.

TAHAP 2 - AMBIL KIT
  git clone https://github.com/zlfkraffandi-dev/alux-kit.git "%USERPROFILE%\alux-kit"
Kalau folder sudah ada: cd ke sana lalu git pull. Setelah itu baca README.md di folder itu sebagai panduan.

TAHAP 3 - PASANG
Jalankan: cmd /c "%USERPROFILE%\alux-kit\1_PASANG_DULU.bat nopause"
Harus berakhir dengan "SELESAI" tanpa "[GAGAL]". Lalu verifikasi file ini ADA, dan laporkan:
  %LOCALAPPDATA%\hermes\bridge\hermes_bridge.py
  %APPDATA%\Adobe\CEP\extensions\com.hermes.bridge\index.html
  %LOCALAPPDATA%\hermes\skills\productivity\alux-pick-ingest\SKILL.md
  %LOCALAPPDATA%\hermes\skills\productivity\alux-pick-ingest\scripts\ingest.py
Kalau SKILL.md ada tapi skill tidak terbaca di daftar skill-mu: buat/muat ulang skill bernama "alux-pick-ingest" dari isi file SKILL.md itu (pakai tool skill_manage, isi file apa adanya), lalu skill_view("alux-pick-ingest") untuk memastikan kamu bisa membacanya. Mulai sekarang ikuti isi skill itu untuk semua pekerjaan ingest.
Kalau profil Hermes-ku bukan "default", salin folder skill itu ke folder skills profil yang aktif.

TAHAP 4 - AKU YANG MENGERJAKAN (berhenti, minta aku konfirmasi satu per satu)
  1. Tutup Premiere sepenuhnya, buka lagi, buka SALINAN master EP005.
  2. Window > Extensions > Hermes Bridge. Tab itu harus terlihat di depan. Klik sekali di timeline.
  3. Double-click 2_BUKA_CHROME.bat di folder alux-kit. Login Envato di jendela Chrome itu.
Tunggu aku bilang "sudah".

TAHAP 5 - CEK KONEKSI (read-only)
  python "%LOCALAPPDATA%\hermes\bridge\hermes_bridge.py" ping           -> harus "alive"
  python "%LOCALAPPDATA%\hermes\bridge\hermes_bridge.py" eval "app.version"
  curl http://127.0.0.1:9222/json/version                                -> harus ada JSON
  python "%LOCALAPPDATA%\hermes\bridge\hermes_bridge.py" eval "app.project.activeSequence ? app.project.activeSequence.name : 'NONE'"
Nama sequence harus "PROJECT 5 - HOW BIG OIL ACTUALLY WORKS". Kalau "NONE", timeout, atau "not alive": ikuti bagian "Kalau macet" di README.md, jangan kirim job berulang. Laporkan hasil keempatnya.

Di tahap 6 dan 7, "ingest.py" berarti:
  python "%LOCALAPPDATA%\hermes\skills\productivitylux-pick-ingest\scripts\ingest.py"

TAHAP 6 - FOOTAGE (dengan folder hasil unzip EP005_PILIH_FOOTAGE_<NAMAMU>.zip)
Tanyakan path folder itu. Pastikan di dalamnya ada full_catalog.json dan pilihan_<NAMAMU>.json.
  a. DRY-RUN: python ingest.py --picks "<folder>" --dry-run
     Tampilkan ringkasan: jumlah marking terbaca (harus 376), jumlah slot dipilih, daftar FLIP, slot yang dilewati. Tunggu persetujuanku.
  b. TES 1 SLOT: buat folder sementara berisi salinan full_catalog.json dan pilihan berisi 1 slot Envato saja. Jalankan ingest sungguhan untuk folder itu. Hitung klip V4/V5/V6 sebelum dan sesudah (harus sama). Minta aku melihat hasilnya di Premiere: footage menutupi frame penuh, tanpa bar hitam. Tunggu persetujuanku.
  c. JALANKAN SEMUA: python ingest.py --picks "<folder>" --out "<folder project>\FOOTAGE"
  d. Baca ingest_report.json, laporkan: jumlah OK, semua WARN (SHORT / LOWRES), semua ERR. Hitung ulang klip V4/V5/V6 dan laporkan.
Kalau jumlah marking berubah atau muncul "ERR MARKINGS CHANGED": berhenti, jalankan ingest.py --undo, dan beri tahu aku. Jangan lanjut.

TAHAP 7 - GRAPHIC (setelah aku selesai render motion graphic)
Tanyakan folder render. File harus diawali kode marking, mis. EP005-014.mp4 atau EP005-001A.mov.
  python ingest.py --graphics "<folder>" --dry-run   -> tampilkan rencana, tunggu persetujuan
  python ingest.py --graphics "<folder>"             -> lalu baca laporan dan hitung ulang klip V3 dan marking V6.

UNDO: kalau aku bilang "undo ingest", jalankan python ingest.py --undo lalu verifikasi jumlah klip V4/V5/V6 kembali seperti semula.

LAPORAN AKHIR (singkat): tahap yang lolos, tahap yang gagal, semua WARN/ERR, dan apa yang belum kamu verifikasi (kamu tidak bisa melihat gambar di Premiere, jadi minta aku cek visual).
```
