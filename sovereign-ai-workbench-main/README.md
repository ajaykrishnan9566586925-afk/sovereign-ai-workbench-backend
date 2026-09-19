# Sovereign AI Workbench

Sovereign AI Workbench is a local-first document question-answering application. The browser UI and FastAPI backend are now connected through one service: the backend serves the frontend, accepts the original uploaded file bytes, extracts text from each file, retrieves relevant passages, and returns an answer with evidence.

## Connected architecture

- `index.html`, `app.js`, and `styles.css` provide the workbench UI.
- `api/main.py` serves the UI and exposes `/api/agent/tasks`, `/api/documents/ingest`, and `/health`.
- `api/document_intelligence.py` handles extraction and lightweight local retrieval.
- The frontend sends a `multipart/form-data` request containing `task` and one or more `files`; it no longer sends placeholder filenames to the old Spring endpoint.
- The answer path works without Ollama or a cloud service. If a local model is added later, it can be placed after retrieval without changing the frontend contract.

## Supported file types

The current extraction layer supports PDF, DOCX, PPTX, XLS/XLSX/XLSM, CSV, TSV, TXT, Markdown, JSON, PNG, JPG/JPEG, and TIFF. PDF text extraction uses PyMuPDF. Modern spreadsheet extraction uses openpyxl and legacy `.xls` extraction uses pandas/xlrd. DOCX and PPTX files are read from their standard XML packages. Images and scanned PDFs use OCR when Pillow, pytesseract, and a local Tesseract binary are available.

## Run locally

```bash
python3 -m pip install -r requirements.txt
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8001
```

Open `http://127.0.0.1:8001/`. The existing `run_agent_service.py` also starts the same API on port 8001.

## API example

```bash
curl -X POST http://127.0.0.1:8001/api/agent/tasks \
  -F 'task=Which asset requires review?' \
  -F 'files=@measurements.xlsx' \
  -F 'files=@report.pdf'
```

The response includes `answer`, `evidence`, `documents`, `errors`, `request_id`, and progress events. Files that cannot be read are reported individually in `errors` while valid files continue through the workflow.

## Verification

The repeatable integration test is `test_integration.py`. It creates representative PDF, DOCX, PPTX, XLSX, CSV, JSON, and TXT files, uploads all seven files to the live API, checks the returned answer and evidence, and confirms successful extraction.

```bash
python3 test_integration.py
```

The previous Spring Boot backend remains in `sovereign-ai-workbench-backend/` as a separate legacy service. The browser workbench is intentionally connected to the unified Python API so file upload, extraction, retrieval, and answer rendering use one consistent contract.
