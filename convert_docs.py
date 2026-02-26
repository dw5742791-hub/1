#!/usr/bin/env python3
"""Convert markdown documentation files to static HTML pages for GitHub Pages."""
import markdown
import os

# list of markdown files to convert
md_files = [
    'README_NEW.md',
    'START_HERE_PUBLIC.md',
    'PUBLIC_ACCESS.md',
    'PUBLIC_OPTIONS.md',
    'DOCUMENTATION_INDEX.md',
    'FEATURES_CHECKLIST.md',
    'ARCHITECTURE.md',
    'DEPLOYMENT.md',
    'SUMMARY.md'
]

html_template = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>body{{padding:2rem;}}</style>
</head>
<body>
<div class="container">
{content}
</div>
</body>
</html>"""

for md in md_files:
    if not os.path.exists(md):
        continue
    with open(md, 'r', encoding='utf-8') as f:
        text = f.read()
    html_body = markdown.markdown(text, extensions=['extra', 'smarty'])
    title = os.path.splitext(md)[0]
    html = html_template.format(title=title, content=html_body)
    outname = title.lower() + '.html'
    with open(outname, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Converted {md} -> {outname}")
