# اصلاح استخراج PDF فارسی دانشیار

فایل‌های این بسته را در مسیرهای هم‌نام مخزن جایگزین کنید:

- app/services/pdf_ingestion.py
- app/services/text_utils.py
- render.yaml
- tests/test_persian_pdf_quality.py

پیام Commit پیشنهادی:

Fix Persian PDF extraction and OCR fallback

پس از Push، Render خودکار Deploy می‌شود. کتاب قبلی را حذف و PDF را دوباره بارگذاری کنید؛
زیرا قطعات متنی قبلی از استخراج خراب ساخته شده‌اند.
