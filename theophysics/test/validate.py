#!/usr/bin/env python3
import json, pathlib, re
root=pathlib.Path(__file__).resolve().parents[2]
for name in ('behavior-event.schema.json','crawl4ai-capture.schema.json','preference-projection.schema.json'):
    json.loads((root/'theophysics/contracts'/name).read_text())
json.loads((root/'theophysics/feature-registry.json').read_text())
js=(root/'code/services-application/search-service/resources/static/theophysics/workbench.js').read_text()
html=(root/'code/services-application/search-service/resources/static/theophysics/index.html').read_text()
assert "truthGrade:null" in js and "localOnly:true" in js
assert "explicitUserIntent:true" in js
assert "provider:'marginalia'" in js and 'provider=marginalia' in js
assert 'fetch(' not in js and 'XMLHttpRequest' not in js and 'sendBeacon' not in js
assert 'NOT CONNECTED' in html and 'Download media' in html
assert 'PERSONAL RELEVANCE — NOT A TRUTH OR QUALITY GRADE' in html
# Existing resources are additive: profile filenames present at base are untouched.
expected={'academia.xml','blogs.xml','default.xml','docs.xml','food.xml','forum.xml','no-filter.xml','plain-text.xml','small-web.xml','tilde.xml','vintage.xml','wiki.xml'}
actual={p.name for p in (root/'code/functions/search-query/resources/filters').glob('*.xml')}
assert expected <= actual and actual-expected == {'theophysics.xml'}
print('validated schemas, privacy boundary, provenance, explicit crawl intent, and additive profile')
