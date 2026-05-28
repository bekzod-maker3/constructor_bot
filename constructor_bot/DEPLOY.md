# 🚀 Constructor Bot — Deploy Qo'llanmasi

## 1. Server tayyorlash (Hetzner CAX11)

### Server ochish
1. https://hetzner.com → Cloud → New Server
2. **Location:** Nuremberg yoki Helsinki
3. **Image:** Ubuntu 24.04
4. **Type:** CAX11 (ARM, 2 CPU, 4GB RAM) — €3.99/oy
5. SSH key qo'shing → **Create**

---

### Serverga ulaning
```bash
ssh root@YOUR_SERVER_IP
```

---

### Tizimni yangilash
```bash
apt update && apt upgrade -y
```

---

### Docker o'rnatish
```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# Docker Compose
apt install docker-compose-plugin -y

# Tekshirish
docker --version
docker compose version
```

---

## 2. Domen sozlash

### DNS qo'shish
Domen registratoringizda (Namecheap, GoDaddy va h.k.):
```
A record:  yourdomain.com  →  YOUR_SERVER_IP
A record:  www.yourdomain.com  →  YOUR_SERVER_IP
```

DNS tarqalishi 5-30 daqiqa ketadi.

### Tekshirish
```bash
ping yourdomain.com
# YOUR_SERVER_IP ko'rinishi kerak
```

---

## 3. Loyihani serverga yuklash

### GitHub orqali (tavsiya etiladi)
```bash
# Serverdaaa
cd /root
git clone https://github.com/sizning_username/constructor_bot.git
cd constructor_bot
```

### Yoki to'g'ridan-to'g'ri yuklash
```bash
# Lokal kompyuterda
scp -r ./constructor_bot root@YOUR_SERVER_IP:/root/
```

---

## 4. .env fayl yaratish

```bash
cd /root/constructor_bot
nano .env
```

Quyidagini to'ldiring:
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_ID=987654321
DATABASE_URL=postgresql://postgres:KUCHLI_PAROL@db:5432/constructor_bot
DB_PASSWORD=KUCHLI_PAROL
WEBHOOK_HOST=https://yourdomain.com
WEBHOOK_PORT=8000
TRIAL_DAYS=7
DAILY_PRICE=3000
REFERRAL_BONUS=5000
PAYMENT_CARD=8600123456789012
```

> ⚠️ DB_PASSWORD ni murakkab qilib yozing!
> Masalan: `Xk9mP2qL8nR5vT3w`

---

## 5. Nginx sozlash

```bash
# nginx.conf dagi yourdomain.com ni o'zingiznikiga almashtiring
nano nginx/nginx.conf
```

---

## 6. SSL sertifikat olish

### Birinchi marta — HTTP bilan ishga tushirish
```bash
# Avval nginx.conf da SSL qismini comment qiling
# va faqat HTTP ishlasin

docker compose up -d nginx
```

### Certbot bilan sertifikat olish
```bash
docker compose run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your@email.com \
  --agree-tos \
  --no-eff-email \
  -d yourdomain.com
```

### SSL ni yoqish
```bash
# nginx.conf da SSL qismini ochib qo'ying
nano nginx/nginx.conf

# Nginx qayta yuklash
docker compose restart nginx
```

---

## 7. Botni ishga tushirish

```bash
cd /root/constructor_bot

# Build va ishga tushirish
docker compose up -d --build

# Loglarni ko'rish
docker compose logs -f bot

# Barcha containerlar holati
docker compose ps
```

---

## 8. Tekshirish

```bash
# Health check
curl https://yourdomain.com/health
# {"status": "ok", "running_bots": 0} ko'rinishi kerak

# Bot loglar
docker compose logs bot --tail=50

# DB loglar
docker compose logs db --tail=20
```

---

## 9. SSL yangilash (avtomatik)

```bash
# Crontab ochish
crontab -e

# Quyidagini qo'shish (har 60 kunda avtomatik yangilanadi)
0 0 1 * * docker compose -f /root/constructor_bot/docker-compose.yml run --rm certbot renew && docker compose -f /root/constructor_bot/docker-compose.yml restart nginx
```

---

## 10. Foydali buyruqlar

```bash
# Botni to'xtatish
docker compose stop bot

# Botni qayta ishga tushirish
docker compose restart bot

# Barcha to'xtatish
docker compose down

# Kod yangilanganda qayta deploy
git pull
docker compose up -d --build bot

# DB ga kirish
docker compose exec db psql -U postgres -d constructor_bot

# Bot ichida buyruq
docker compose exec bot python -c "print('Hello')"

# Container loglar (oxirgi 100 qator)
docker compose logs bot --tail=100 -f
```

---

## 11. Monitoring (ixtiyoriy)

```bash
# Resurslar holati
docker stats

# Disk holati
df -h

# RAM holati
free -h
```

---

## Muammolar va yechimlar

### Bot ishga tushmayapti
```bash
docker compose logs bot --tail=50
# Xato xabarini o'qing
```

### DB ulanmayapti
```bash
docker compose logs db --tail=20
# DB_PASSWORD .env da to'g'rimi tekshiring
```

### Webhook ishlamayapti
```bash
# Domen SSL to'g'ri sozlanganmi?
curl -I https://yourdomain.com
# 200 yoki 307 ko'rinishi kerak

# Telegram webhook holati
curl https://api.telegram.org/botYOUR_TOKEN/getWebhookInfo
```

### Port band
```bash
# 80 yoki 443 portni kim ishlatayotganini tekshirish
lsof -i :80
lsof -i :443
```
