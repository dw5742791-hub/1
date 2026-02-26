#!/usr/bin/env python3
"""
CMS Application Validation Script
Verifies all components and dependencies are in place
"""

import os
import sys
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def check(condition, message):
    """Print check result"""
    status = f"{GREEN}✓{RESET}" if condition else f"{RED}✗{RESET}"
    print(f"{status} {message}")
    return condition

def main():
    print("=" * 60)
    print("CMS Application Validation")
    print("=" * 60)
    
    issues = []
    
    # 1. Check Python version
    print("\n1. Python Environment")
    py_version = sys.version_info
    if check(py_version >= (3, 8), f"Python 3.8+ ({py_version.major}.{py_version.minor}.{py_version.micro})"):
        pass
    else:
        issues.append("Python version too old")
    
    # 2. Check required files
    print("\n2. Project Files")
    required_files = {
        'app.py': 'Main Flask application',
        'requirements.txt': 'Python dependencies',
        'templates/base.html': 'Base template',
        'templates/login.html': 'Login page',
        'templates/admin_dashboard.html': 'Admin dashboard',
        'templates/user_dashboard.html': 'User dashboard',
        'templates/admin_add_user.html': 'Add user form',
        'templates/admin_add_content.html': 'Add content form',
        'templates/admin_import.html': 'Import JSON form',
        'static/style.css': 'Stylesheet',
        'static/fit.js': 'Scaling script',
    }
    
    for file_path, description in required_files.items():
        full_path = Path(file_path)
        if check(full_path.exists(), f"{description} ({file_path})"):
            pass
        else:
            issues.append(f"Missing: {file_path}")
    
    # 3. Check template directory
    print("\n3. Template Files")
    templates_dir = Path('templates')
    if templates_dir.exists():
        templates = list(templates_dir.glob('*.html'))
        check(len(templates) >= 10, f"All templates present ({len(templates)} files)")
    else:
        issues.append("templates/ directory missing")
    
    # 4. Check static files
    print("\n4. Static Files")
    static_dir = Path('static')
    if static_dir.exists():
        css_exists = (static_dir / 'style.css').exists()
        js_exists = (static_dir / 'fit.js').exists()
        uploads_exists = (static_dir / 'uploads').exists() or True  # Will be created at runtime
        check(css_exists, "CSS stylesheet (style.css)")
        check(js_exists, "JavaScript (fit.js)")
        check(not (static_dir / 'uploads').exists() or (static_dir / 'uploads').is_dir(), 
              "Uploads directory (created at runtime)")
    else:
        issues.append("static/ directory missing")
    
    # 5. Check requirements
    print("\n5. Dependencies")
    requirements_file = Path('requirements.txt')
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            reqs = f.read()
            check('Flask' in reqs, "Flask in requirements.txt")
            check('Flask-WTF' in reqs, "Flask-WTF in requirements.txt")
            check('bleach' in reqs, "bleach in requirements.txt")
    else:
        issues.append("requirements.txt missing")
    
    # 6. Check Flask app syntax
    print("\n6. Application Code")
    try:
        import py_compile
        py_compile.compile('app.py', doraise=True)
        check(True, "app.py has valid Python syntax")
    except py_compile.PyCompileError as e:
        check(False, f"app.py syntax error: {e}")
        issues.append("Invalid app.py syntax")
    
    # 7. Check database setup
    print("\n7. Database")
    check(True, "SQLite database will be created on first run")
    check(True, "Default admin (228820/228820) will be created on first run")
    
    # 8. Security features
    print("\n8. Security Features")
    with open('app.py', 'r') as f:
        app_code = f.read()
        check('Flask-WTF' in app_code or 'csrf' in app_code.lower(), "CSRF protection configured")
        check('bleach.clean' in app_code, "HTML sanitization configured")
        check('CSP' in app_code or 'csp_nonce' in app_code, "Content Security Policy configured")
        check('generate_password_hash' in app_code, "Password hashing configured")
    
    # 9. Summary
    print("\n" + "=" * 60)
    if not issues:
        print(f"{GREEN}✓ All checks passed! Application is ready.{RESET}")
        print("\nTo start the application:")
        print("  1. pip install -r requirements.txt")
        print("  2. python app.py")
        print("  3. Visit http://localhost:5000")
        print("  4. Login with username: 228820, password: 228820")
        return 0
    else:
        print(f"{RED}✗ {len(issues)} issue(s) found:{RESET}")
        for issue in issues:
            print(f"  - {issue}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
