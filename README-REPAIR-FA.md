# تعمیر خطای GitHub Actions

خطای CI به این دلیل رخ داده که فایل `pyproject.toml` از ریشهٔ مخزن حذف شده است.
هم‌زمان فایل‌های `README.md` و `CITATION.cff` نیز در آخرین Commit حذف شده‌اند.

## نصب

چهار فایل این بسته را مستقیماً در ریشهٔ مخزن قرار دهید؛ یعنی کنار این پوشه‌ها:

- app
- docs
- tests
- .github

فایل‌ها نباید داخل پوشهٔ دیگری قرار بگیرند.

## Commit پیشنهادی

Restore project metadata and Python build configuration

پس از Push، GitHub Actions باید مراحل زیر را اجرا کند:

- Set up Python
- Install dependencies
- Lint
- Test
- Build Docker image
