# Submission artefacts (PM-003)

Rebuild:

```bash
# PDF (no extra deps beyond reportlab)
python3 build-pdf.py

# PPTX
npm install pptxgenjs
node build-deck.js
```

Risa: copy beats into the **official SIH PPT template**. Do not restyle that template.
