# نظام إدارة المحتوى (Content Management System)

A comprehensive Arabic-localized CMS built with Flask, featuring admin dashboard, user management, content editing, and advanced security features.

## Installation & Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```
> **ملاحظة حول GitHub Pages:** هذا المستودع يحتوي على تطبيق Flask كامل يعمل بالخلفية. GitHub Pages يدعم فقط الملفات الثابتة (HTML/CSS/JS) ولا يمكنه تشغيل بايثون أو خادم Flask. لذلك لا يمكنك نشر التطبيق نفسه مباشرةً على Pages. إذا أردت مشاركة التطبيق:
>
> 1. استخدم أي من طرق الاستضافة التي في `START_HERE_PUBLIC.md` (مثل ngrok أو Replit أو Railway).  
> 2. أو استنسخ المشروع محلياً وشغّله بكتابة `python app.py` ثم افتح http://localhost:5000.
>  
> ملف `index.html` الموجود بالجذر هو صفحة ثابتة بسيطة توضّح هذه النقطة وتوجه الزوار إلى الوثائق.

The app will start at `http://localhost:5000`

## Default Admin Credentials

- **Username:** `228820`
- **Password:** `228820`

## Features

### 1. **User Authentication & Authorization**
   - Login system with session management
   - Admin and user role distinction
   - User role management (user/editor/manager/admin)
   - Password hashing with Werkzeug security

### 2. **Admin Dashboard** (`/admin`)
   - User management (add, edit, delete users)
   - Content management (add, edit, preview content)
   - Advanced filtering by:
     - Search term (username, title)
     - Grade level
     - Category
     - Author ID
     - Starred users
   - Pagination (20 items per page)
   - Quick admin action buttons

### 3. **User Management**
   - Add new users with auto-generated passwords (configurable length)
   - Edit user profiles (username, grade, role, admin flag)
   - Mark users as "starred" (featured for quick content access)
   - Password generation using secure random tokens

### 4. **Content Management**
   - WYSIWYG editor (TinyMCE 6) for rich HTML editing
   - Content categorization with comma-separated tags
   - Grade-level targeting (control visibility by student grade)
   - File uploads (images: PNG, JPG, JPEG, GIF, WebP; 4MB max)
   - Secure filename handling (SHA256 hash-based naming)
   - HTML sanitization via `bleach` (prevents XSS while preserving formatting)

### 5. **User Dashboard** (`/user`)
   - Grade-based content filtering (shows only content meant for user's grade)
   - Category sidebar for browsing by topic
   - Responsive card-based layout
   - Fit-to-screen scaling (aspect ratio preserved on all devices)

### 6. **Security Features**
   - **CSRF Protection:** All forms protected with Flask-WTF tokens
   - **Content Security Policy (CSP):** Per-request nonce for inline scripts
   - **HTML Sanitization:** Bleach allowlist filtering (safe tags/attrs only)
   - **Secure File Uploads:** Hash-based filenames, MIME validation, 4MB limit
   - **X-Frame-Options:** DENY (prevent clickjacking)
   - **X-Content-Type-Options:** nosniff (prevent MIME sniffing)

### 7. **Audit Logging**
   - Track all admin actions (add user, edit content, etc.)
   - Audit log viewer at `/admin/audit`
   - CSV export of logs for record keeping

### 8. **Settings Management** (`/admin/settings`)
   - Configure password generation length
   - Enable/disable HTML sanitization
   - Persistent settings stored in database

### 9. **Admin Preview** (`/admin/preview`)
   - View content as users would see it
   - Test grade filtering
   - Test category filtering

### 10. **JSON Import/Export**
   - **Export:** `/admin/contents/export/json` – Download all contents as JSON
   - **Import:** `/admin/contents/import` – Bulk upload JSON file
   - Smart duplicate detection (skips by ID if exists)
   - HTML sanitization on import

## API Endpoints

### Authentication
- `POST /login` – User login
- `GET /logout` – User logout

### Admin Routes
- `GET /admin` – Admin dashboard
- `POST /admin/users/add` – Create new user
- `GET/POST /admin/users/edit/<user_id>` – Edit user
- `GET/POST /admin/contents/add` – Create content
- `GET/POST /admin/contents/edit/<content_id>` – Edit content
- `GET /admin/preview` – Preview all content
- `GET /admin/audit` – View audit logs
- `GET /admin/export/csv` – Export logs as CSV
- `GET/POST /admin/settings` – Manage settings
- `GET/POST /admin/contents/import` – Import JSON
- `GET /admin/contents/export/json` – Export contents as JSON
- `POST /admin/upload_image` – TinyMCE image upload

### User Routes
- `GET /user` – User dashboard
- `GET /uploads/<filename>` – Serve uploaded files

## Database Schema

### Users Table
```
id (INTEGER, PK)
username (TEXT, UNIQUE)
password_hash (TEXT)
grade (INTEGER) – Student grade level
is_admin (INTEGER) – Admin flag (0/1)
role (TEXT) – Role type (user/editor/manager/admin)
starred (INTEGER) – Mark as featured (0/1)
```

### Contents Table
```
id (INTEGER, PK)
title (TEXT)
html (TEXT) – Sanitized HTML content
link (TEXT) – External link or upload URL
categories (TEXT) – Comma-separated tags
grades (TEXT) – Comma-separated grade numbers
author_id (INTEGER, FK → users.id)
```

### Audit Logs Table
```
id (INTEGER, PK)
ts (DATETIME) – Timestamp
user_id (INTEGER, FK → users.id)
action (TEXT) – Description of action
```

### Settings Table
```
key (TEXT, PK) – Setting name
value (TEXT) – Setting value
```

## File Uploads

Uploaded files are stored in `static/uploads/` with secure hash-based filenames:
- Only image files allowed: PNG, JPG, JPEG, GIF, WebP
- Max file size: 4 MB
- Filename: `<SHA256_hash_first_16_chars>.<ext>`
- Example: `/static/uploads/a1b2c3d4e5f6g7h8.jpg`

## JSON Import/Export Format

### Export Format
```json
[
  {
    "id": 1,
    "title": "محتوى العلوم",
    "html": "<p>نص محتوى مُعقّم</p>",
    "link": "/static/uploads/hash.jpg",
    "categories": "علوم,طبيعة",
    "grades": "5,6",
    "author_id": 1
  }
]
```

### Import Notes
- File must be valid JSON (`.json` extension)
- Duplicates detected by `id` field (skipped if exists)
- HTML content automatically sanitized on import
- New content assigned to importing admin user as author

## Responsive Design Features

- **Bootstrap 5.3.2** for responsive grid/components
- **RTL (Right-to-Left)** HTML support for Arabic text
- **Fit-to-Screen Scaling** (`fit.js`): Automatically scales content to fit viewport while preserving aspect ratio
- Mobile-friendly forms and navigation

## Content Security Policy

The app enforces a strict CSP header:
```
default-src 'self' https:;
script-src 'self' 'nonce-{REQUEST_NONCE}' https://cdn.tiny.cloud;
style-src 'self' 'nonce-{REQUEST_NONCE}' https:;
```

Each request generates a unique nonce for inline scripts/styles. External resources (TinyMCE, Bootstrap CDN) are explicitly whitelisted.

## HTML Sanitization Allowlist

**Allowed Tags:** `p`, `b`, `i`, `u`, `a`, `img`, `ul`, `ol`, `li`, `br`, `strong`, `em`, `h1-h4`, `iframe`, `div`, `span`

**Allowed Attributes:**
- Links: `href`, `target`, `rel`
- Images: `src`, `alt`, `style`
- Iframes: `src`, `width`, `height`, `frameborder`, `allow`, `allowfullscreen`
- All elements: `style`, `class`

## Development Notes

- Uses SQLite for simplicity (easily upgradeable to PostgreSQL)
- Decorators: `@login_required`, `@admin_required` for route protection
- Context processor injects `csrf_token()` and `csp_nonce()` into templates
- All timestamps in audit logs use server time (CURRENT_TIMESTAMP)
- Password hashing uses Werkzeug's `generate_password_hash` (pbkdf2:sha256)

## Troubleshooting

**Forgot admin password?**
- Delete `data.db` and restart the app (default admin will be recreated)

**Uploads not working?**
- Ensure `static/uploads/` directory exists (created automatically)
- Check file size (max 4MB) and format (PNG, JPG, JPEG, GIF, WebP)

**CSP errors in browser console?**
- Nonce is generated per-request; scripts should have matching `nonce` attribute
- External scripts must be whitelisted in `@app.after_request`

## License

Open source for educational use.
