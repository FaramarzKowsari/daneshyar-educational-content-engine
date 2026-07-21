# اتصال GitHub Pages به Backend واقعی

GitHub Pages می‌تواند همان رابط `index.html` را نمایش دهد، اما API باید روی یک سرور جدا اجرا شود.

پس از استقرار Backend:

1. فایل `docs/config.js` را باز کنید.
2. نشانی Backend را جایگزین کنید:

```js
window.DANESHYAR_API_BASE = "https://YOUR-BACKEND-DOMAIN";
```

3. در Environment سرور این مقدار را تنظیم کنید:

```env
ALLOWED_ORIGINS=https://faramarzkowsari.github.io
```

4. Commit و Push کنید.

صفحهٔ GitHub Pages از آن پس PDF را مستقیم به Backend ارسال می‌کند و نتیجهٔ واقعی را نمایش می‌دهد.

> کلید OpenAI در `config.js` یا HTML قرار نمی‌گیرد. این کلید فقط در Environment سرور ذخیره می‌شود.
