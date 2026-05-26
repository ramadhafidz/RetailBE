# Panduan CI/CD Backend ke Home Server (Tailscale)

Repositori Backend (`RetailBE`) ini dilengkapi dengan pipeline **Continuous Deployment (CD)** menggunakan GitHub Actions. Setiap kali ada perubahan pada file inti Backend yang di-_push_ ke _branch_ `main`, GitHub Actions akan otomatis mendeteksi, masuk ke jaringan Tailscale Anda, dan memerintahkan Home Server Debian Anda untuk memperbarui Docker Container.

## Langkah 1: Persiapan di Home Server (Debian)

Karena skrip ini akan melakukan SSH ke server Anda dan mengeksekusi `docker compose`, server rumah Anda harus sudah siap terlebih dahulu.

**Catatan Penting:** Repositori ML (`RetailML`) akan secara otomatis di-clone dan dimasukkan ke dalam Docker container Backend saat proses build berlangsung. Oleh karena itu, Anda **TIDAK PERLU** melakukan clone repositori ML secara manual di server rumah Anda.

### Menyiapkan Akses SSH untuk CI/CD (User `datawarehousing`)

Agar GitHub Actions dapat mengakses server dengan aman, kita akan menggunakan user `datawarehousing` dan membuat kunci SSH khusus.

1. Login ke server sebagai root atau user Anda, lalu pindah ke user baru:
   ```bash
   su - datawarehousing
   ```
2. Buat direktori SSH:
   ```bash
   mkdir -p ~/.ssh && chmod 700 ~/.ssh
   ```
3. Buat kunci SSH khusus CI/CD:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/github_action_key -N ""
   ```
4. Masukkan public key ke daftar yang diizinkan:
   ```bash
   cat ~/.ssh/github_action_key.pub >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys
   ```
5. Tampilkan private key:
   ```bash
   cat ~/.ssh/github_action_key
   ```
   Salin seluruh isi private key tersebut untuk dimasukkan ke rahasia `SSH_PRIVATE_KEY` di GitHub pada langkah selanjutnya.

### Menyiapkan Repositori

1. Buka terminal server Debian Anda via SSH dan pastikan Anda login sebagai user `datawarehousing`.
2. Lakukan _Clone_ repositori ini di _home directory_ Anda:
   ```bash
   cd ~
   git clone https://github.com/ramadhafidz/RetailBE.git
   cd RetailBE
   ```
3. Siapkan file otentikasi. Karena ini lingkungan produksi, file tidak boleh ikut ter-_commit_.
   - Buat file `.env` di dalam folder `RetailBE` berdasarkan `.env.example`.
   - Buat file otentikasi GCP Anda, misalnya `credential.json`, dan tempatkan di dalam folder `RetailBE` (sesuaikan _path_-nya di file `.env` Anda).

## Langkah 2: Membuat Tailscale OAuth Client

Agar robot GitHub bisa menumpang masuk ke jaringan Tailscale Anda dengan aman, Anda membutuhkan kredensial khusus.

1. Buka [Tailscale Admin Console](https://login.tailscale.com/admin/settings/oauth).
2. Pergi ke menu **Settings > OAuth clients** dan klik **Generate OAuth client**.
3. Beri nama, misalnya `github-actions-retailbe`.
4. Pada bagian **Scopes**, pilih **Custom scopes**. Gulir ke bawah ke kategori **Devices**, lalu centang kotak **Write** (dan **Read**) pada opsi **Core** (Read or modify devices and their properties). Ini penting agar GitHub Actions bisa mendaftarkan dirinya sebagai mesin sementara di jaringan Anda.
5. Pada bagian **Tags (required for write scope)**, ketikkan dan pilih **`tag:ci`**.
   - _Penting:_ Jika Anda tidak bisa menemukan atau mengetik `tag:ci`, klik tautan biru **"Manage tags in Access Controls"** di bawah kotak pencarian. Di editor JSON ACL yang terbuka, tambahkan blok berikut di bagian `"tagOwners"`:
     ```json
     "tagOwners": {
         "tag:ci": ["autogroup:admin"]
     },
     ```
   - Simpan ACL tersebut, lalu kembali ke halaman pembuatan OAuth client untuk memilih `tag:ci`.
6. Klik **Generate client**.
7. Simpan **Client ID** dan **Client Secret** yang muncul. Ini hanya ditampilkan satu kali!

## Langkah 3: Menambahkan Rahasia (Secrets) di GitHub

1. Buka repositori `RetailBE` di GitHub Anda.
2. Masuk ke tab **Settings** > **Secrets and variables** > **Actions**.
3. Klik **New repository secret**.
4. Tambahkan rahasia-rahasia berikut secara berurutan:
   - **`TS_OAUTH_CLIENT_ID`**: Masukkan _Client ID_ dari Tailscale.
   - **`TS_OAUTH_SECRET`**: Masukkan _Client Secret_ dari Tailscale.
   - **`SSH_USERNAME`**: Masukkan nama user Debian Anda, yaitu: `datawarehousing`.
   - **`SSH_PRIVATE_KEY`**: Masukkan _Private Key_ SSH khusus yang sudah Anda buat sebelumnya (hasil dari `cat ~/.ssh/github_action_key` di Langkah 1).

## Langkah 4: Pengujian

1. Lakukan _commit_ dan _push_ pada file apa saja di dalam _backend_ (misalnya `main.py`).
2. Buka tab **Actions** di GitHub repositori Anda.
3. Anda akan melihat sebuah proses _workflow_ berjalan.
4. Jika lampu hijau muncul, berarti GitHub berhasil melakukan SSH melalui Tailscale `100.71.233.70` dan memicu `docker compose up -d --build`!
