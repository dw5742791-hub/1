# Simple Content Management App

Run locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Default admin login: username `228820` password `228820`.

Enhancements added:
- CSRF protection using `Flask-WTF`.
- Audit logs for admin actions stored in `audit_logs` table and an audit viewer at `/admin/audit`.
- Admin search, pagination, `/admin/export` JSON endpoint and `/admin/export/csv` for logs.
- WYSIWYG editor (TinyMCE) for content editing.
- File upload support for content (stored under `static/uploads`).
- HTML sanitization via `bleach` to reduce XSS risk while allowing basic tags.
- Content fit-to-screen scaling: pages wrap content in a scalable viewport that auto-scales to preserve aspect ratio on any device (see `static/fit.js` and `static/style.css`).
 - Settings page at `/admin/settings` to control options like generated password length and HTML sanitization.
# 1