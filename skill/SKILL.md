---
name: alux-pick-ingest
description: Use when editor picked footage in HTML. Download and import.
---
# ALUX: footage pilihan editor -> download -> import Premiere

Dipakai SETELAH editor memilih footage di HTML pick. Jalan di mesin editor ini (akun Envato dan Premiere milik editor).

## Syarat (cek dulu, jangan lanjut kalau salah satu gagal)
1. `python %LOCALAPPDATA%\hermes\bridge\hermes_bridge.py ping` -> `alive`. Kalau timeout/`not alive`: tab Hermes Bridge harus TERLIHAT di depan di Premiere, klik timeline sekali, kirim SATU `eval "app.version"`. Jangan antre job saat macet; kalau tetap macet restart Premiere.
2. `curl http://127.0.0.1:9222/json/version` hidup (jalankan `2_BUKA_CHROME.bat`, login Envato).
3. Premiere membuka SALINAN MASTER dan sequence master aktif.

## Alur footage
Minta SATU path: folder berisi `pilihan_<NAMA>.json`.
1. Dry-run: `python <skill>/scripts/ingest.py --picks <folder> --dry-run`. Baca rencananya ke editor (jumlah slot, FLIP, slot yang dilewati).
2. Tes 1 slot dulu (salin `full_catalog.json` + file pilihan berisi 1 entri ke folder sementara), cek hasil, baru jalankan semua.
3. Jalankan: `python <skill>/scripts/ingest.py --picks <folder> --out <FOLDER_PROJECT>\FOOTAGE`
   - Kecocokan lewat NAMA marking (`B012 :` di V4, `A004 :` di V5), bukan timecode.
   - ENVATO -> V1, ARCHIVE -> V2 (Ken Burns 100->105). Skala menutup frame (cover).
   - Slot yang di HTML ENVATO tapi marking-nya masih V5 = FLIP: marking V5 dipindah ke V4 dengan kode `B###` baru.
   - Menolak menimpa track yang sudah terisi. Jalankan ulang aman: klip yang sama dilewati (`ALREADY`).
4. Laporkan `ingest_report.json` APA ADANYA. Baris `WARN` (SHORT = footage lebih pendek dari marking, LOWRES = resolusi kecil) dan `ERR` disebut satu-satu.
5. Verifikasi: baca ulang track dari Premiere. Jumlah klip V4/V5/V6 harus sama dengan sebelum ingest (+1/-1 hanya untuk FLIP).
6. Undo: `python <skill>/scripts/ingest.py --undo` (memakai `ingest_manifest.json`).

## Alur graphic
Setelah editor selesai render motion graphic ke satu folder: file bernama `EP005-###*.mp4|mov|png` (kode marking di awal nama, akhiran huruf boleh, mis. `EP005-001A`).
`python <skill>/scripts/ingest.py --graphics <folder> --dry-run` lalu tanpa `--dry-run`. Masuk ke V3 persis di marking V6 dengan kode itu.

## Aturan
- Jangan hapus/ubah marking selain lewat skrip. Jangan ubah V8/V9/V11/A1.
- Jangan pernah memasang footage di V1/V2 tanpa marking V4/V5 yang cocok.
- Kegagalan download: tampilkan pesan dialog Envato yang dicetak skrip (login/lisensi/kuota). Jangan menebak.
- Gambar tidak bisa dilihat AI: minta editor cek visual 2-3 slot pertama.
