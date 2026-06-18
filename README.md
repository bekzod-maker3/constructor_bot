# 🛠️ Telegram Bot Constructor

Ushbu loyiha foydalanuvchilarga oʻzlarining shaxsiy Telegram botlarini qulay va tezkor tarzda yaratish, sozlash va boshqarish imkoniyatini beruvchi mukammal **Konstruktor Bot** hisoblanadi. Loyiha arxitekturasi modulli va yuqori yuklamalarga chidamli qilib loyihalashtirilgan.

## 🚀 Texnologiyalar va Arxitektura

Loyiha quyidagi zamonaviy texnologiyalar asosida qurilgan:
* **Backend:** Python (aiogram / asinxron arxitektura)
* **Ma'lumotlar bazasi:** `database.py` (ORM / SQL) va `models/` moduli
* **Ulanish turi:** Telegram Webhook (`webhook/` va `nginx/` integratsiyasi)
* **Konteynerizatsiya:** Docker & Docker Compose (`Dockerfile`, `docker-compose.yml`)

---

## 📁 Loyiha Strukturasi

```text
├── handlers/          # Botning buyruqlari va biznes mantiqini boshqaruvchi qism
├── keyboards/         # Inline va Reply tugmalar (klaviaturalar)
├── models/            # Ma'lumotlar bazasi modellari va sxemalari
├── nginx/             # Nginx konfiguratsiyasi (Webhook uchun proksi)
├── templates/         # Bot xabarlari yoki HTML shablonlar
├── utils/             # Yordamchi funksiyalar va instrumentlar
├── webhook/           # Webhook sozlmalari va server qismi
├── .env.example       # Atrof-muhit oʻzgaruvchilari namunasi
├── .gitignore         # Git uchun e'tibor berilmaydigan fayllar roʻyxati
├── DEPLOY.md          # Serverga yuklash boʻyicha yoʻriqnoma
├── Dockerfile         # Loyiha uchun Docker obrazi arxitekturasi
├── config.py          # Bot va tizim sozlamalari (Configuration)
├── database.py        # Ma'lumotlar bazasiga ulanish va sozlamalar
└── docker-compose.yml # Konteynerlarni birgalikda ishga tushirish fayli
