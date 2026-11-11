"""template.html + parts.json -> <name>.html (artifact page, no doctype) and standalone.html
(with doctype/head, opens from disk or a local server).
  python build_html.py <guide folder> <page name>      e.g.  python build_html.py . handle-unit-assembly"""
import os, sys
HERE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
NAME = sys.argv[2] if len(sys.argv) > 2 else "assembly"
t = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
data = open(os.path.join(HERE, "parts.json"), encoding="utf-8").read()
assert "</" not in data, "parts.json would close the <script> tag"
page = t.replace("__PARTS_JSON__", data)
open(os.path.join(HERE, NAME + ".html"), "w", encoding="utf-8").write(page)
standalone = ('<!doctype html>\n<html lang="ar" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
              '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
              '</head>\n<body>\n' + page + '\n</body>\n</html>\n')
open(os.path.join(HERE, "standalone.html"), "w", encoding="utf-8").write(standalone)
print("page bytes", len(page.encode()), "standalone", len(standalone.encode()))
