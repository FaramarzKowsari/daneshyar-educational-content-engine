# Daneshyar Educational Content Engine — Public Beta

**دانشیار** یک اپلیکیشن قابل اجراست که به هر کاربر اجازه می‌دهد PDF دانشگاهی خودش را بارگذاری کند و از همان کتاب، پاسخ منبع‌محور، خلاصه، آزمون، فلش‌کارت، نقشهٔ مفهومی و PowerPoint بگیرد.

این نسخه دیگر یک نمایش از پیش‌ساخته با کتاب ثابت نیست. رابط عمومی به Backend واقعی متصل است و هر کتاب در یک فضای موقت و خصوصی مخصوص همان مرورگر پردازش می‌شود.

## قابلیت‌های نسخهٔ عمومی

- بارگذاری PDF دلخواه کاربر؛
- استخراج متن صفحه‌به‌صفحه و تشخیص اولیهٔ فصل‌ها؛
- OCR اختیاری برای PDFهای اسکن‌شدهٔ فارسی و انگلیسی؛
- گفت‌وگو با کتاب همراه با شمارهٔ صفحه و قطعهٔ منبع؛
- تولید خلاصه، آزمون، فلش‌کارت و نقشهٔ مفهومی؛
- ساخت و دانلود فایل PowerPoint؛
- مخزن پیش‌نویس‌های واقعی در Backend؛
- تأیید و دانلود خروجی‌ها؛
- کلید خصوصی تصادفی برای جداسازی کتاب هر کاربر؛
- حذف دستی یا خودکار کتاب‌ها پس از زمان تعیین‌شده؛
- محدودیت حجم، صفحه، بارگذاری، چت و تولید برای کنترل هزینه و سوءاستفاده؛
- رابط فارسی RTL، Docker، تست خودکار و GitHub Actions.

## نکتهٔ معماری

GitHub Pages فقط برای محتوای استاتیک مناسب است و Backend پایتون، OCR، پایگاه داده و پردازش PDF را اجرا نمی‌کند. برای نسخهٔ قابل استفاده باید همین Docker application روی یک Web Service یا Container Platform مستقر شود.

## اجرای محلی

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

سپس:

- رابط عمومی: `http://localhost:8000`
- مستندات API: `http://localhost:8000/docs`
- رابط کلاسیک توسعه: `http://localhost:8000/classic`
- سلامت سرویس: `http://localhost:8000/health`

## اجرای Docker

```bash
cp .env.example .env
docker compose up --build
```

## فعال‌کردن هوش مولد

در محیط سرور تنظیم کنید:

```env
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5-mini
USE_OPENAI_EMBEDDINGS=false
```

کلید API نباید در HTML، JavaScript یا GitHub Pages قرار گیرد. کلید فقط در Environment Variable سرور نگه‌داری می‌شود.

بدون کلید OpenAI نیز استخراج PDF، جست‌وجوی محلی، پاسخ استخراجی و خروجی‌های ساده فعال می‌مانند؛ برای کیفیت مناسب نسخهٔ عمومی، فعال‌کردن مدل مولد توصیه می‌شود.

## حدود پیش‌فرض نسخهٔ عمومی

```env
MAX_UPLOAD_MB=25
MAX_PDF_PAGES=250
PUBLIC_BOOK_TTL_HOURS=24
PUBLIC_UPLOADS_PER_HOUR=3
PUBLIC_CHAT_PER_HOUR=30
PUBLIC_GENERATIONS_PER_HOUR=12
OCR_MAX_PAGES=60
```

## استقرار

- راهنمای نسخهٔ عمومی: [`docs/PUBLIC_BETA_DEPLOYMENT.md`](docs/PUBLIC_BETA_DEPLOYMENT.md)
- حریم خصوصی: [`docs/PRIVACY_PUBLIC_BETA.md`](docs/PRIVACY_PUBLIC_BETA.md)
- فایل Render Blueprint: [`render.yaml`](render.yaml)

برای یک تست عمومی محدود، یک Web Service دارای Persistent Disk قابل استفاده است. برای ترافیک هم‌زمان زیاد و مقیاس افقی، PostgreSQL، Object Storage، Queue/Worker و Rate Limiter مبتنی بر Redis لازم است.

## کنترل کیفیت

```bash
ruff check app tests scripts
pytest
```

## نویسندگان و راهبری علمی

- Faramarz Kowsari — Software Engineering & AI Architecture
- Dr. Safieh Siadat — Academic Lead & Educational Design

## مجوز

کد تحت MIT License منتشر می‌شود. حقوق PDFهای بارگذاری‌شده متعلق به صاحبان همان محتواست و بارگذاری‌کننده باید مجوز پردازش آن را داشته باشد.
