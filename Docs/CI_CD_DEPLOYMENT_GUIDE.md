# Panduan CI/CD Backend ke Home Server (Tailscale)

Repositori Backend (`RetailBE`) ini dilengkapi dengan pipeline **Continuous Deployment (CD)** menggunakan GitHub Actions. Setiap kali ada perubahan pada file inti Backend yang di-*push* ke *branch* `main`, GitHub Actions akan otomatis mendeteksi, masuk ke jaringan Tailscale Anda, dan memerintahkan Home Server Debian Anda untuk memperbarui Docker Container.

## Langkah 1: Persiapan di Home Server (Debian)

Karena skrip ini akan melakukan SSH ke server Anda dan mengeksekusi `docker compose`, server rumah Anda harus sudah siap terlebih dahulu.

**Catatan Penting:** Repositori ML (`RetailML`) akan secara otomatis di-clone dan dimasukkan ke dalam Docker container Backend saat proses build berlangsung. Oleh karena itu, Anda **TIDAK PERLU** melakukan clone repositori ML secara manual di server rumah Anda.

1. Buka terminal server Debian Anda via SSH.
2. Lakukan *Clone* repositori ini di *home directory* Anda:
   ```bash
   cd ~
   git clone https://github.com/ramadhafidz/RetailBE.git
   cd RetailBE
   ```
3. Siapkan file otentikasi. Karena ini lingkungan produksi, file tidak boleh ikut ter-*commit*.
   - Buat file `.env` di dalam folder `RetailBE` berdasarkan `.env.example`.
   - Buat file otentikasi GCP Anda, misalnya `credential.json`, dan tempatkan di dalam folder `RetailBE` (sesuaikan _path_-nya di file `.env` Anda).

## Langkah 2: Membuat Tailscale OAuth Client

Agar robot GitHub bisa menumpang masuk ke jaringan Tailscale Anda dengan aman, Anda membutuhkan kredensial khusus.

1. Buka [Tailscale Admin Console](https://login.tailscale.com/admin/settings/oauth).
2. Pergi ke menu **Settings > OAuth clients** dan klik **Generate OAuth client**.
3. Beri nama, misalnya `github-actions-retailbe`.
4. Pilih **Devices > Write** agar mesin sementara GitHub Actions diperbolehkan membuat identitas baru (node). Anda juga bisa menambahkan tag opsional `tag:ci` di menu Access Controls (ACL) jika sudah mengonfigurasinya.
5. Klik **Generate client**.
6. Simpan **Client ID** dan **Client Secret** yang muncul. Ini hanya ditampilkan satu kali!

## Langkah 3: Menambahkan Rahasia (Secrets) di GitHub

1. Buka repositori `RetailBE` di GitHub Anda.
2. Masuk ke tab **Settings** > **Secrets and variables** > **Actions**.
3. Klik **New repository secret**.
4. Tambahkan rahasia-rahasia berikut secara berurutan:
   
   - **`TS_OAUTH_CLIENT_ID`**: Masukkan *Client ID* dari Tailscale.
   - **`TS_OAUTH_SECRET`**: Masukkan *Client Secret* dari Tailscale.
   - **`SSH_USERNAME`**: Masukkan nama user Debian Anda, yaitu: `ramadhafidz`.
   - **`SSH_PRIVATE_KEY`**: Masukkan *Private Key* SSH Anda (yang berpasangan dengan public key `~/.ssh/authorized_keys` di server Debian Anda). Jika Anda belum punya, Anda harus membuat SSH key pair baru menggunakan `ssh-keygen` di laptop Anda, salin *public key*-nya ke `~/.ssh/authorized_keys` di Debian, lalu tempel *private key*-nya (biasanya dari file `id_rsa`) ke rahasia GitHub ini.

## Langkah 4: Pengujian

1. Lakukan *commit* dan *push* pada file apa saja di dalam *backend* (misalnya `main.py`).
2. Buka tab **Actions** di GitHub repositori Anda.
3. Anda akan melihat sebuah proses *workflow* berjalan.
4. Jika lampu hijau muncul, berarti GitHub berhasil melakukan SSH melalui Tailscale `100.71.233.70` dan memicu `docker compose up -d --build`!
