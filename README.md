# Daneshyar Educational Content Engine — Public Beta

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21481330.svg)](https://doi.org/10.5281/zenodo.21481330)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.3.0-0aa7a5.svg)](https://github.com/FaramarzKowsari/daneshyar-educational-content-engine/releases)

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
MAX_UPLOAD_MB=10
MAX_PDF_PAGES=120
PUBLIC_BOOK_TTL_HOURS=2
PUBLIC_UPLOADS_PER_HOUR=2
PUBLIC_CHAT_PER_HOUR=20
PUBLIC_GENERATIONS_PER_HOUR=6
OCR_MAX_PAGES=60
```

## استقرار

- راهنمای نسخهٔ عمومی: [`docs/PUBLIC_BETA_DEPLOYMENT.md`](docs/PUBLIC_BETA_DEPLOYMENT.md)
- حریم خصوصی: [`docs/PRIVACY_PUBLIC_BETA.md`](docs/PRIVACY_PUBLIC_BETA.md)
- فایل Render Blueprint: [`render.yaml`](render.yaml)
- راهنمای معماری، محدودیت‌ها و هزینه‌ها: [`docs/demo-guide.html`](https://faramarzkowsari.github.io/daneshyar-educational-content-engine/demo-guide.html)
- صفحهٔ رسمی استناد و DOI: [`docs/citation.html`](https://faramarzkowsari.github.io/daneshyar-educational-content-engine/citation.html)

برای یک تست عمومی محدود، یک Web Service دارای Persistent Disk قابل استفاده است. برای ترافیک هم‌زمان زیاد و مقیاس افقی، PostgreSQL، Object Storage، Queue/Worker و Rate Limiter مبتنی بر Redis لازم است.

## کنترل کیفیت

```bash
ruff check app tests scripts
pytest
```

## استناد و DOI

نسخهٔ `0.3.0` این نرم‌افزار در Zenodo آرشیو شده است:

- **DOI:** [`10.5281/zenodo.21481330`](https://doi.org/10.5281/zenodo.21481330)
- **Resource type:** Software
- **Version:** 0.3.0
- **Release date:** 2026-07-21

استناد پیشنهادی:

> Kowsari, F., & Siadat, S. (2026). *Daneshyar Educational Content Engine — Public Beta* (Version 0.3.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.21481330

```bibtex
@software{Kowsari_Siadat_Daneshyar_2026,
  author    = {Faramarz Kowsari and Safieh Siadat},
  title     = {Daneshyar Educational Content Engine — Public Beta},
  version   = {0.3.0},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.21481330},
  url       = {https://doi.org/10.5281/zenodo.21481330}
}
```

اطلاعات ماشین‌خوان استناد در فایل [`CITATION.cff`](CITATION.cff) قرار دارد.

## نویسندگان و راهبری علمی

- Faramarz Kowsari — Software Engineering & AI Architecture
- Dr. Safieh Siadat — Academic Lead & Educational Design

## مجوز

کد تحت MIT License منتشر می‌شود. حقوق PDFهای بارگذاری‌شده متعلق به صاحبان همان محتواست و بارگذاری‌کننده باید مجوز پردازش آن را داشته باشد.
