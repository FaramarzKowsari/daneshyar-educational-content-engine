# استقرار نسخهٔ عمومی دانشیار

## چرا GitHub Pages کافی نیست؟

GitHub Pages فقط HTML/CSS/JavaScript است و Python، پردازش PDF، OCR، پایگاه داده و کلید محرمانهٔ هوش مصنوعی را اجرا نمی‌کند. صفحهٔ عمومی واقعی باید از یک Backend اجرا شود.

## گزینهٔ سریع: Render

1. مخزن را به Render متصل کنید.
2. گزینهٔ **New Blueprint** را بزنید و همین مخزن را انتخاب کنید.
3. Render فایل `render.yaml` را می‌خواند و یک Web Service با Persistent Disk می‌سازد.
4. در Environment، مقدار `OPENAI_API_KEY` را فقط در داشبورد Render ثبت کنید.
5. پس از Deploy، آدرس `onrender.com` سرویس همان رابط کامل و قابل استفاده است.

> Persistent Disk برای یک نمونهٔ عمومی آزمایشی مناسب است. برای مقیاس افقی و چند Replica باید فایل‌ها به Object Storage و محدودسازی درخواست‌ها به Redis منتقل شوند.

## گزینهٔ مقیاس‌پذیرتر: Azure Container Apps

برای انتشار گسترده:

- Container App برای Web/API؛
- Azure Database for PostgreSQL برای داده‌ها؛
- Azure Blob Storage برای PDFها و خروجی‌ها؛
- Azure Service Bus/Queue برای پردازش پس‌زمینه؛
- Key Vault برای API Key؛
- Front Door یا WAF برای حفاظت؛
- Autoscaling بر اساس درخواست HTTP و طول Queue.

نسخهٔ این مخزن «Public Beta تک‌نمونه‌ای» است. برای تبلیغ به هزاران نفر قابل استفاده است، اما قبل از یک رویداد پرترافیک باید Load Test، بودجهٔ API، ذخیره‌سازی و سیاست حریم خصوصی نهایی شوند.

## سیاست نسخهٔ عمومی

- هر مرورگر یک کلید خصوصی موقت دریافت می‌کند.
- کتاب‌های کاربران در فهرست عمومی دیده نمی‌شوند.
- سقف فایل، صفحه، چت و تولید محتوا با Environment Variable تنظیم می‌شود.
- کتاب و خروجی‌ها پس از مدت تعیین‌شده در `PUBLIC_BOOK_TTL_HOURS` حذف می‌شوند.
- کاربر می‌تواند پیش از انقضا کتاب و تمام خروجی‌هایش را حذف کند.
- کلید OpenAI هرگز به مرورگر ارسال نمی‌شود.
