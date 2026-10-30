# ShopBD — দারাজ/অ্যামাজনের মতো ই-কমার্স ওয়েবসাইট

**Stack:** HTML + CSS + JavaScript (Frontend) → Python + Django 5 (Backend) → MySQL (Database)

সম্পূর্ণ ডায়নামিক — প্রোডাক্ট, ক্যাটাগরি, ব্যানার, ডেলিভারি চার্জ, পেমেন্ট নম্বর, কুপন, পেজ — সবকিছু Admin প্যানেল থেকে কন্ট্রোল করা যায়, কোড না ছুঁয়েই।

---

## ১. ওয়েবসাইটে যা যা আছে (Features)

### কাস্টমারের জন্য
| বিভাগ | ফিচার |
|---|---|
| হোম পেজ | অটো স্লাইডার, সাইড/মিডল ব্যানার, ফ্ল্যাশ সেল (কাউন্টডাউন), ক্যাটাগরি, ফিচার্ড, বেস্ট সেলার, ক্যাটাগরি অনুযায়ী প্রোডাক্ট, নিউ অ্যারাইভাল |
| প্রোডাক্ট লিস্ট | সার্চ, ক্যাটাগরি/সাব-ক্যাটাগরি, ব্র্যান্ড, দাম (min–max), রেটিং, স্টক, ডিসকাউন্ট ফিল্টার; ৫ রকম সর্টিং; পেজিনেশন |
| লাইভ সার্চ | টাইপ করলেই ছবি ও দামসহ সাজেশন |
| প্রোডাক্ট পেজ | গ্যালারি + জুম, কালার/সাইজ ভ্যারিয়েশন (দাম অটো আপডেট), স্টক স্ট্যাটাস, Buy Now, Add to Cart, উইশলিস্ট, ডিসক্রিপশন/স্পেসিফিকেশন/রিভিউ ট্যাব, রেটিং ব্রেকডাউন, রিলেটেড প্রোডাক্ট |
| কার্ট | AJAX add-to-cart, পরিমাণ পরিবর্তন, রিমুভ, কুপন কোড, স্টকের বেশি যোগ করা যায় না |
| চেকআউট | গেস্ট বা লগইন করে, সেভ করা ঠিকানা এক ক্লিকে, ঢাকার ভেতরে/বাইরে ডেলিভারি চার্জ, ফ্রি ডেলিভারি লিমিট, Cash on Delivery / bKash / Nagad (Transaction ID সহ) |
| অর্ডার | অর্ডার নম্বর, কনফার্মেশন ইমেইল, প্রিন্টযোগ্য ইনভয়েস (PDF সেভ), স্ট্যাটাস ট্র্যাকার, হিস্টরি, ক্যানসেল (স্টক ফেরত যায়), অর্ডার নম্বর+ফোন দিয়ে ট্র্যাক |
| অ্যাকাউন্ট | রেজিস্টার, ইউজারনেম **বা** ইমেইল দিয়ে লগইন, পাসওয়ার্ড রিসেট, প্রোফাইল ও ছবি, অ্যাড্রেস বুক, ড্যাশবোর্ড, আমার অর্ডার, উইশলিস্ট |
| অন্যান্য | Contact ফর্ম, নিউজলেটার, About/Privacy/Terms/Return পেজ, 404 পেজ, মোবাইল রেসপন্সিভ + নিচে বটম ন্যাভ |
| ভাষা | হেডারে 🌐 ভাষা অপশন: English, বাংলা, हिन्दी, اردو, العربية — ক্লিক করলেই পুরো সাইটের লেখা বদলে যায় (আরবি/উর্দুতে ডান থেকে বাম লেআউট, বাংলায় দাম বাংলা সংখ্যায়) |

### অ্যাডমিন/সেলারের জন্য
- **Seller Dashboard** (`/dashboard/`): আজকের বিক্রি, ৩০ দিনের বিক্রি, ১৪ দিনের চার্ট, পেন্ডিং অর্ডার, পেমেন্ট ভেরিফাই, লো-স্টক অ্যালার্ট, টপ প্রোডাক্ট।
- **🎨 Theme & Colors** (Admin → Theme & Colors): ৯টি রেডিমেড থিম, যেকোনো রং কালার পিকারে বদলানো, লাইভ প্রিভিউ, কোণের গোলাকৃতি ও ফন্ট পরিবর্তন, এক ক্লিকে ডিফল্টে ফেরত।
- **Admin Panel** (`/admin/`): প্রোডাক্ট (একাধিক ছবি + ভ্যারিয়েশন), ক্যাটাগরি, ব্র্যান্ড, অর্ডার (স্ট্যাটাস বদলালে হিস্টরি সেভ হয়, ক্যানসেল করলে স্টক ফেরত), কুপন, ব্যানার, পেজ, রিভিউ অনুমোদন, মেসেজ, সাবস্ক্রাইবার, **Site Settings** (সাইটের নাম, লোগো, ফোন, ডেলিভারি চার্জ, bKash/Nagad নম্বর, পেমেন্ট অন/অফ)।

---

## ২. ফোল্ডার স্ট্রাকচার

```
shopbd/
├── config/          ← settings.py, urls.py, wsgi.py
├── core/            ← হোম, সাইট সেটিং, ব্যানার, পেজ, কন্টাক্ট, সেলার ড্যাশবোর্ড, seed_demo
├── accounts/        ← রেজিস্টার, লগইন, প্রোফাইল, ঠিকানা
├── store/           ← ক্যাটাগরি, ব্র্যান্ড, প্রোডাক্ট, রিভিউ, উইশলিস্ট, সার্চ
├── cart/            ← সেশন-ভিত্তিক কার্ট (cart.py)
├── orders/          ← কুপন, চেকআউট, অর্ডার, ইনভয়েস, ট্র্যাকিং, tests.py
├── templates/       ← সব HTML
├── static/css/style.css, static/js/main.js
├── locale/          ← বাংলা, হিন্দি, উর্দু, আরবি অনুবাদ (.po / .mo)
├── deploy/          ← nginx, gunicorn, MySQL স্ক্রিপ্ট
├── passenger_wsgi.py ← cPanel হোস্টিং এর জন্য
├── requirements.txt
└── .env.example
```

---

## ৩. নিজের কম্পিউটারে চালানো (Windows / Mac / Linux)

### ধাপ ১ — প্রয়োজনীয় সফটওয়্যার
- **Python 3.10+** → https://www.python.org/downloads/ (Windows এ ইনস্টলের সময় *Add Python to PATH* টিক দিন)
- **MySQL 8** → https://dev.mysql.com/downloads/installer/ (অথবা XAMPP এর MySQL/MariaDB)

### ধাপ ২ — প্রজেক্ট ফোল্ডারে টার্মিনাল খুলুন
```bash
cd shopbd
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```
> **Windows এ `mysqlclient` ইনস্টল এরর দিলে:** `pip install --upgrade pip wheel` চালিয়ে আবার চেষ্টা করুন। তবুও না হলে আপাতত `.env` এ `DB_ENGINE=sqlite` দিয়ে কাজ চালান।

### ধাপ ৩ — MySQL ডাটাবেস তৈরি
MySQL Workbench / phpMyAdmin / টার্মিনালে:
```sql
CREATE DATABASE shopbd_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'shopbd_user'@'localhost' IDENTIFIED BY 'MyPass123!';
GRANT ALL PRIVILEGES ON shopbd_db.* TO 'shopbd_user'@'localhost';
FLUSH PRIVILEGES;
```

### ধাপ ৪ — `.env` ফাইল
`.env.example` কপি করে নাম দিন `.env`, তারপর পাসওয়ার্ড বসান:
```
DB_ENGINE=mysql
DB_NAME=shopbd_db
DB_USER=shopbd_user
DB_PASSWORD=MyPass123!
```

### ধাপ ৫ — টেবিল তৈরি, ডেমো ডেটা, রান
```bash
python manage.py migrate
python manage.py seed_demo        # ৩৯টি ডেমো প্রোডাক্ট, ক্যাটাগরি, ব্যানার, কুপন
python manage.py runserver
```
ব্রাউজারে খুলুন: **http://127.0.0.1:8000**

| কী | লগইন |
|---|---|
| Admin প্যানেল `/admin/` | `admin` / `admin12345` |
| ডেমো কাস্টমার | `customer` / `customer12345` |
| ডেমো কুপন | `WELCOME10` (১০%, সর্বোচ্চ ৳৫০০), `FLAT200` (৳২০০০+ এ ৳২০০ ছাড়) |

> ⚠️ লাইভ সার্ভারে যাওয়ার আগে admin পাসওয়ার্ড অবশ্যই বদলাবেন, অথবা `seed_demo --no-users` ব্যবহার করে `python manage.py createsuperuser` দিয়ে নিজের অ্যাডমিন বানাবেন।

### টেস্ট চালানো
```bash
python manage.py test
```
(কার্ট, ভ্যারিয়েশন, কুপন, COD/bKash চেকআউট, স্টক কমা/ফেরত, অর্ডার প্রাইভেসি, রেজিস্টার/লগইন, উইশলিস্ট — সব টেস্ট করা হয়)

---

## ৪. নিজের দোকান সাজানো (Admin থেকে)

1. `/admin/` → **Site Settings** → সাইটের নাম, লোগো, ফোন, ঠিকানা, ডেলিভারি চার্জ, bKash/Nagad নম্বর।
2. **Categories** → মূল ক্যাটাগরি, তারপর Parent দিয়ে সাব-ক্যাটাগরি। Icon ঘরে Font Awesome ক্লাস (যেমন `fa-laptop`) — https://fontawesome.com/icons
3. **Brands** → ব্র্যান্ড যোগ।
4. **Products** → নাম, দাম, সেল প্রাইস, স্টক, ছবি; নিচে আরও ছবি ও Size/Color ভ্যারিয়েশন। Featured / Flash sale টিক দিলে হোম পেজে দেখাবে। Specification ঘরে প্রতি লাইনে `Key: Value`।
5. **Banners** → Position: Home Slider (১৪০০×৫৬০ সাইজ ভালো), Side (৭০০×৪০০), Middle (৮০০×৩০০)।
6. **Coupons**, **Pages** (About/Privacy ইত্যাদি)।
7. ডেমো ডেটা মুছতে: Admin এ Products/Categories/Banners সিলেক্ট করে Delete।

### অর্ডার ম্যানেজ করা
- নতুন অর্ডার *Pending* থাকে → কাস্টমারকে ফোন করে **Confirmed** করুন → **Processing** → **Shipped** → **Delivered**।
- bKash/Nagad অর্ডারে Transaction ID মিলিয়ে **Payment status = Paid** করুন।
- লিস্ট পেজে একসাথে অনেক অর্ডার সিলেক্ট করে *Action* দিয়ে স্ট্যাটাস বদলানো যায়।
- COD অর্ডার Delivered করলে অটো Paid হয়। Cancelled করলে স্টক অটো ফেরত যায়।

### ডিজাইন/রং বদলানো
কোড ছাড়াই: Admin → **🎨 Theme & Colors** (উপরের ডান কোণেও লিংক আছে)। নিচে বিস্তারিত দেখুন।

---

## ৫. লাইভ সার্ভারে তোলা (Deploy)

দুইটি সহজ উপায় দেওয়া হলো। আগে একটি ডোমেইন কিনুন এবং DNS এ সার্ভারের IP সেট করুন (A record)।

### উপায় A — VPS (Ubuntu 22.04/24.04) — সবচেয়ে ভালো
DigitalOcean / Vultr / Contabo / দেশি VPS যেকোনোটা।

```bash
# ১) সার্ভারে লগইন
ssh root@YOUR_SERVER_IP

# ২) প্যাকেজ ইনস্টল
apt update && apt upgrade -y
apt install -y python3-venv python3-dev build-essential pkg-config \
               default-libmysqlclient-dev mysql-server nginx certbot python3-certbot-nginx git unzip

# ৩) MySQL ডাটাবেস (deploy/mysql_setup.sql এর পাসওয়ার্ড আগে বদলে নিন)
mysql_secure_installation

# ৪) কোড আপলোড — হয় git clone, নয়তো নিজের PC থেকে:
#    scp shopbd.zip root@YOUR_SERVER_IP:/var/www/
mkdir -p /var/www && cd /var/www
unzip shopbd.zip            # অথবা git clone <your-repo> shopbd
cd shopbd
mysql < deploy/mysql_setup.sql

# ৫) Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# ৬) .env তৈরি
cp .env.example .env
nano .env
```
`.env` এ লিখুন:
```
SECRET_KEY=<নিচের কমান্ডের আউটপুট>
DEBUG=False
ALLOWED_HOSTS=example.com,www.example.com,YOUR_SERVER_IP
CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
DB_ENGINE=mysql
DB_NAME=shopbd_db
DB_USER=shopbd_user
DB_PASSWORD=ChangeThisPassword123!
```
SECRET_KEY বানাতে: `python -c "import secrets;print(secrets.token_urlsafe(50))"`

```bash
# ৭) ডাটাবেস ও স্ট্যাটিক ফাইল
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py seed_demo --no-users     # ঐচ্ছিক: ডেমো প্রোডাক্ট
chown -R www-data:www-data /var/www/shopbd

# ৮) Gunicorn সার্ভিস
cp deploy/gunicorn.service /etc/systemd/system/shopbd.service
systemctl daemon-reload
systemctl enable --now shopbd
systemctl status shopbd          # active (running) দেখাবে

# ৯) Nginx (deploy/nginx.conf এ নিজের ডোমেইন বসান)
cp deploy/nginx.conf /etc/nginx/sites-available/shopbd
ln -s /etc/nginx/sites-available/shopbd /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# ১০) ফ্রি SSL (https)
certbot --nginx -d example.com -d www.example.com
```
✅ এখন `https://example.com` এ সাইট লাইভ!

পরে কোড আপডেট করলে: `bash deploy/deploy.sh`

> SSL দেওয়ার আগে http তে টেস্ট করতে চাইলে `.env` এ সাময়িকভাবে `HTTPS_ENABLED=False` দিন, না হলে লগইন/ফর্ম কাজ করবে না।

### উপায় B — cPanel শেয়ার্ড হোস্টিং (যেখানে "Setup Python App" আছে)
1. cPanel → **MySQL® Databases** → ডাটাবেস + ইউজার তৈরি, ইউজারকে ALL PRIVILEGES দিন।
2. **File Manager** → হোম ফোল্ডারে `shopbd.zip` আপলোড করে Extract করুন (যেমন `/home/USER/shopbd`)।
3. **Setup Python App** → Create Application:
   - Python version: 3.10+
   - Application root: `shopbd`
   - Application URL: আপনার ডোমেইন
   - Application startup file: `passenger_wsgi.py`, Entry point: `application`
4. পেজের উপরে দেখানো `source .../activate` কমান্ডটি কপি করে cPanel **Terminal** এ চালান, তারপর:
   ```bash
   cd ~/shopbd
   pip install -r requirements.txt
   cp .env.example .env && nano .env     # DEBUG=False, ডোমেইন, DB তথ্য (DB_NAME সাধারণত USER_shopbd)
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```
5. Static/Media দেখানোর জন্য `public_html` এ symlink দিন:
   ```bash
   ln -s ~/shopbd/staticfiles ~/public_html/static
   ln -s ~/shopbd/media ~/public_html/media
   ```
6. Setup Python App পেজে **Restart** চাপুন।
> `mysqlclient` ইনস্টল না হলে হোস্টিং সাপোর্টকে MySQL development library চালু করতে বলুন।

---

## ৬. ইমেইল চালু করা (অর্ডার কনফার্মেশন ও পাসওয়ার্ড রিসেট)
Gmail দিয়ে: Google Account → Security → 2-Step Verification চালু → **App passwords** থেকে পাসওয়ার্ড বানান। `.env`:
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=yourmail@gmail.com
EMAIL_HOST_PASSWORD=<16 অক্ষরের app password>
DEFAULT_FROM_EMAIL=ShopBD <yourmail@gmail.com>
```
খালি রাখলে ইমেইল শুধু টার্মিনালে প্রিন্ট হবে।

---

## ৭. পরবর্তীতে যা যোগ করা যায়
- **অটোমেটিক অনলাইন পেমেন্ট:** এখন bKash/Nagad ম্যানুয়াল (Send Money + Transaction ID)। ট্রেড লাইসেন্স থাকলে SSLCommerz / bKash Merchant API নিয়ে `orders/views.py` এর `checkout` এ গেটওয়েতে রিডাইরেক্ট যোগ করা যাবে।
- SMS নোটিফিকেশন (দেশি SMS গেটওয়ে API), কুরিয়ার API (Pathao / Steadfast / RedX), মাল্টি-ভেন্ডর, প্রোডাক্ট কম্পেয়ার।

## ৮. সমস্যা ও সমাধান
| সমস্যা | সমাধান |
|---|---|
| `Access denied for user` | `.env` এর DB_USER/DB_PASSWORD ঠিক আছে কিনা দেখুন |
| `Did you install mysqlclient?` | `pip install mysqlclient`; Ubuntu তে আগে `default-libmysqlclient-dev pkg-config` |
| লাইভে CSS/ছবি আসছে না | `collectstatic` চালান, nginx এর `alias` পাথ ও `chown www-data` দেখুন |
| `DisallowedHost` | `.env` এর `ALLOWED_HOSTS` এ ডোমেইন যোগ করুন |
| `CSRF verification failed` | `CSRF_TRUSTED_ORIGINS` এ `https://ডোমেইন` দিন; SSL না থাকলে `HTTPS_ENABLED=False` |
| 502 Bad Gateway | `systemctl status shopbd` ও `journalctl -u shopbd -n 50` দেখুন |
| বাংলা লেখা ??? দেখাচ্ছে | ডাটাবেস `utf8mb4` দিয়ে তৈরি করুন (উপরের SQL) |

---

## ৯. ভাষা পরিবর্তন (Language)

হেডারে 🌐 আইকনে (মোবাইলে উপরে ডানে) এবং ফুটারে ভাষার তালিকা আছে: **English, বাংলা, हिन्दी, اردو, العربية**। কাস্টমার যে ভাষা বাছবে, পুরো সাইট সেই ভাষায় দেখাবে এবং ব্রাউজার সেটা ১ বছর মনে রাখবে।

দুই ধরনের লেখা আছে:

| লেখা | কীভাবে অনুবাদ হয় |
|---|---|
| সাইটের নির্দিষ্ট লেখা (বাটন, মেনু, চেকআউট, মেসেজ, ইমেইল, এরর) | আগে থেকেই ৪টি ভাষায় অনুবাদ করা আছে, নিজে থেকে বদলায় |
| আপনি Admin-এ যা লেখেন (প্রোডাক্টের নাম ও বিবরণ, ক্যাটাগরি, ব্যানার, পেজ, নোটিশ) | প্রতিটির Admin পেজের নিচে **Translations** অংশে ভাষা বেছে লিখে দিন। না লিখলে ইংরেজিটাই দেখাবে |

- নতুন ভিজিটর প্রথমে কোন ভাষায় সাইট দেখবে: Admin → Site Settings → **Default language**।
- পণ্যের ছবির ভেতরের লেখা (ডেমো ছবিতে ইংরেজি নাম আঁকা) অনুবাদ হয় না; আসল ছবি দিলে এ সমস্যা থাকবে না।
- সার্চে বাংলা/হিন্দি নাম লিখেও পণ্য খোঁজা যায়।

**অনুবাদ নিজে বদলাতে চাইলে:** `locale/bn/LC_MESSAGES/django.po` (হিন্দি `hi`, উর্দু `ur`, আরবি `ar`) Notepad দিয়ে খুলে `msgstr "..."` লাইন বদলান, তারপর:
```
python manage.py compile_translations
```
চালিয়ে সার্ভার রিস্টার্ট দিন। (এর জন্য আলাদা কোনো সফটওয়্যার লাগে না।)

**নতুন ভাষা যোগ করতে** (যেমন চাইনিজ `zh-hans`): `config/settings.py` এর `LANGUAGES` তালিকায় যোগ করুন, `locale/bn` ফোল্ডার কপি করে `locale/zh_Hans` নাম দিন, msgstr গুলো সেই ভাষায় লিখে `compile_translations` চালান, তারপর `python manage.py makemigrations` ও `migrate`।

---

## ১০. ওয়েবসাইটের রং পরিবর্তন (Theme & Colors)

Admin → **🎨 Theme & Colors** (উপরের ডান কোণে লিংক, অথবা Seller Dashboard এর বাটন):

1. **রেডিমেড থিম:** Daraz Orange, Amazon Dark, Green, Blue, Purple, Red, Pink, Teal, Black — একটিতে ক্লিক করুন।
2. **নিজের মতো রং:** যেকোনো রঙের বক্সে ক্লিক করলে কালার পিকার খুলবে — মূল রং, হেডার, হেডারের লেখা, উপরের বার, অ্যাকসেন্ট (Buy Now/স্টার), ডিসকাউন্ট ব্যাজ, পেজের ব্যাকগ্রাউন্ড, লেখার রং, ফুটার।
3. **আকার ও ফন্ট:** কোণ কতটা গোল হবে (0–24) আর ফন্ট (Inter, Poppins, Roboto, Hind Siliguri)।
4. ডানে **Live preview**-তে সাথে সাথে দেখবেন। পছন্দ হলে **SAVE** → সাইট রিফ্রেশ করুন।
5. ভুল হলে **↺ Reset to default colors**।

বাটনের লেখা সাদা হবে নাকি কালো, সেটা রং দেখে নিজে থেকেই ঠিক হয়, তাই হালকা রং দিলেও লেখা পড়া যাবে।

---

## ১১. আপডেট করার নিয়ম (আগে থেকে সাইট চালু থাকলে)
নতুন ফাইলগুলো পুরনো ফোল্ডারের উপর কপি করে (`.env`, `db.sqlite3`, `media` রেখে) চালান:
```
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```
`seed_demo` আবার চালালে ডেমো ক্যাটাগরি/ব্যানার/পণ্যের অনুবাদ যোগ হবে; আপনার নিজের ডেটা মুছবে না।

---

## ১২. মোবাইল অ্যাপ (Play Store)

ওয়েবসাইটে অ্যাপ সাপোর্ট (PWA) যোগ করা আছে:
- `/manifest.json`: অ্যাপের নাম, আইকন আর রং (Admin-এর Theme থেকে নেয়)
- `/sw.js`: ইন্টারনেট না থাকলে "অফলাইন" পেজ দেখায়, সাইট দ্রুত লোড করে
- `/.well-known/assetlinks.json`: Android অ্যাপের সাথে সাইট যুক্ত করে (`.env`-এর `ANDROID_PACKAGE_NAME`, `ANDROID_SHA256_FINGERPRINTS`)
- অ্যাপ আইকন: `static/img/icons/` (নিজের লোগো দিতে চাইলে একই নাম ও সাইজে বদলে দিন)

Play Store-এর অ্যাপ বানানোর পুরো গাইড আলাদা **shopbd-android** ফোল্ডারের `README.md`-তে আছে।

---

## ১৩. দোকানে বিক্রি (POS রশিদ) ও মাল্টি-ব্রাঞ্চ

দোকানে কেউ সরাসরি পণ্য কিনলে ওয়েবসাইট থেকেই রশিদ (receipt) দেওয়া যায়। প্রতিটি শাখার স্টক, ক্যাশিয়ার আর বিক্রি আলাদা থাকে।

**ঠিকানাসমূহ**

| পেজ | ঠিকানা |
|---|---|
| বিক্রির স্ক্রিন (POS) | `/pos/` |
| বিক্রির তালিকা ও রশিদ | `/pos/sales/` |
| সব শাখার ড্যাশবোর্ড | `/pos/dashboard/` |
| শাখা, স্টক, ট্রান্সফার | Admin → **Shop branches & POS** |

### ধাপ ১: শাখা তৈরি
Admin → **Branches → Add**। নাম, কোড (যেমন `DHN`, রশিদ নম্বরে এটা বসবে), ঠিকানা, ফোন আর রশিদের নিচের লেখা দিন।
"Sell without stock" চালু করলে স্টক শূন্য হলেও বিক্রি করা যাবে। শুরুতে স্টক গোনা না থাকলে এটা কাজে লাগে।

### ধাপ ২: কর্মী (ম্যানেজার/ক্যাশিয়ার) যোগ
1. Admin → **Users → Add user**: ইউজারনেম আর পাসওয়ার্ড দিন।
2. ইউজারের পেজের নিচে **Shop branch** অংশে শাখা ও Role বেছে নিন।
   - **Cashier** শুধু নিজের শাখায় বিক্রি করবে, নিজের বিক্রি দেখবে আর সর্বোচ্চ যত % ছাড় দেওয়া আছে তত ছাড় দিতে পারবে।
   - **Manager** নিজের শাখার সব বিক্রি দেখবে, রিটার্ন নিতে পারবে, ড্যাশবোর্ড দেখবে আর যেকোনো ছাড় দিতে পারবে।
   - **Superuser (মালিক)** সব শাখা দেখবে। POS-এর উপরের ড্রপডাউন থেকে শাখা বদলানো যায়।
3. কর্মীদের "Staff status" দেওয়ার দরকার নেই। তারা সাধারণ লগইন দিয়েই `/pos/` খুলতে পারবে।

### ধাপ ৩: শাখার স্টক
- **Admin → Products → (একটি পণ্য)**: নিচে "Branch stock" অংশে প্রতিটি শাখার পরিমাণ দিন।
- অথবা **Admin → Branch stock** থেকে তালিকায় সরাসরি সংখ্যা বদলে Save করুন।
- পণ্যের মূল "Stock" ঘরটি শুধু **অনলাইন** বিক্রির জন্য। দোকানের স্টক আলাদা থাকে।
- **Stock transfers → Add**: এক শাখা থেকে আরেক শাখায়, বা অনলাইন গুদাম থেকে শাখায় মাল পাঠাতে। From/To খালি রাখলে বোঝাবে অনলাইন স্টক। সেভ করলে দুই দিকেই স্টক নিজে থেকে ঠিক হয়ে যায়।

### ধাপ ৪: বিক্রি ও রশিদ
1. ক্যাশিয়ার লগইন করে `/pos/` খুলবে।
2. পণ্য যোগ করার উপায়:
   - পণ্যের নাম লিখে খুঁজুন, বা পণ্যের ছবিতে চাপুন।
   - **বারকোড স্ক্যানার** দিয়ে স্ক্যান করুন। এর জন্য পণ্যের SKU-তে বারকোড নম্বরটাই লিখে রাখুন।
   - সাইজ/রং থাকলে একটা বক্স আসবে, সেখান থেকে বেছে নিন।
3. প্রয়োজনে ছাড় দিন (টাকা বা %), তারপর পেমেন্ট পদ্ধতি বাছুন: Cash, Card, bKash বা Nagad।
4. Cash হলে "নগদ গ্রহণ" ঘরে টাকার পরিমাণ দিন, ফেরত কত দিতে হবে নিজে থেকে দেখাবে।
5. **Complete sale** চাপুন (কিবোর্ডে **F9**)। রশিদ খুলে নিজে থেকেই প্রিন্টের বক্স আসবে।
6. রশিদ ৮০mm থার্মাল প্রিন্টারের মাপে বানানো, সাধারণ A4 প্রিন্টারেও প্রিন্ট হয়। প্রিন্টের বক্সে Margins: None আর Headers and footers: off রাখুন।
7. কিবোর্ড শর্টকাট: **F2** চাপলে খোঁজার ঘরে যাবে, **F9** চাপলে বিক্রি সম্পন্ন হবে।

### ধাপ ৫: রিটার্ন, হিসাব ও ড্যাশবোর্ড
- **`/pos/sales/`**:
  - তারিখ অনুযায়ী বিক্রি, মোট টাকা আর পেমেন্ট পদ্ধতি অনুযায়ী হিসাব দেখা যায়।
  - রশিদ নম্বর, ফোন বা নাম দিয়ে খোঁজা যায়।
  - **Reprint** দিয়ে রশিদ আবার প্রিন্ট করা যায়।
  - ম্যানেজার **Return** চাপলে পুরো বিক্রি ফেরত হয় আর স্টক শাখায় ফিরে যায়।
- **`/pos/dashboard/`**:
  - প্রতিটি শাখার আজকের ও ৩০ দিনের বিক্রি দেখা যায়।
  - ১৪ দিনের চার্টে শাখা আর অনলাইন বিক্রি আলাদা রঙে দেখায়।
  - এছাড়া সেরা পণ্য, আজকের ক্যাশিয়ার, পেমেন্ট পদ্ধতি আর কম স্টকের তালিকা থাকে।
- Admin → **Sales**-এ সব রশিদ আছে। এখানে খোঁজা, ফিল্টার করা আর রিটার্ন করাও যায়।

### ডেমো দিয়ে চেষ্টা
`python manage.py seed_demo` চালালে নিচের ডেমো ডেটা তৈরি হয়:
- দুটি শাখা: Dhanmondi (DHN) আর Uttara (UTT)
- ১৪ দিনের ডেমো বিক্রি
- দুটি লগইন:
  - `manager1` / `manager12345`: Dhanmondi শাখার ম্যানেজার
  - `cashier1` / `cashier12345`: Uttara শাখার ক্যাশিয়ার

⚠️ লাইভ সার্ভারে এই ডেমো পাসওয়ার্ডগুলো ব্যবহার করবেন না।
