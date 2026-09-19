from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import csv
import json
import requests
import fitz
from openpyxl import Workbook

ROOT = Path("/tmp/sovereign-fixtures")
ROOT.mkdir(exist_ok=True)

def make_docx(path: Path):
    xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Maintenance report: Pump A vibration measured 4.2 mm/s and requires review.</w:t></w:r></w:p></w:body></w:document>'
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", xml)

def make_pptx(path: Path):
    xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>Safety briefing: inspect the north valve before startup.</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>'
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("ppt/slides/slide1.xml", xml)

def make_files():
    (ROOT / "notes.txt").write_text("Project note: the cooling system inspection is due on 19 September 2026.", encoding="utf-8")
    (ROOT / "records.csv").write_text("asset,value\nPump A,4.2 mm/s\nPump B,1.1 mm/s\n", encoding="utf-8")
    (ROOT / "data.json").write_text(json.dumps({"owner": "MRPL", "status": "controlled", "priority": "high"}), encoding="utf-8")
    make_docx(ROOT / "report.docx")
    make_pptx(ROOT / "briefing.pptx")
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Measurements"
    sheet.append(["Asset", "Value", "Status"])
    sheet.append(["Pump A", 4.2, "Review"])
    sheet.append(["Pump B", 1.1, "Normal"])
    workbook.save(ROOT / "measurements.xlsx")
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "PDF report: Pump A vibration is 4.2 mm/s and exceeds the review threshold.")
    pdf.save(ROOT / "report.pdf")
    pdf.close()

make_files()
health = requests.get("http://127.0.0.1:8001/health", timeout=10)
assert health.ok and health.json()["status"] == "ok", health.text
files = [open(path, "rb") for path in sorted(ROOT.iterdir())]
try:
    response = requests.post(
        "http://127.0.0.1:8001/api/agent/tasks",
        data={"task": "Which asset has the highest vibration and what action is required?"},
        files=[("files", (path.name, handle, "application/octet-stream")) for path, handle in zip(sorted(ROOT.iterdir()), files)],
        timeout=30,
    )
finally:
    for handle in files:
        handle.close()
print("status", response.status_code)
print(json.dumps(response.json(), indent=2))
assert response.ok
payload = response.json()
assert payload["success"] is True
assert "Pump A" in payload["answer"]
assert len(payload["documents"]) == 7
assert any(item["file"] == "measurements.xlsx" for item in payload["evidence"])
print("integration test: PASS")
