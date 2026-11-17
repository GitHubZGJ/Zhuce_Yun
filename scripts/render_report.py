"""用 Word COM 更新目录/页码并导出 PDF。

Word COM 在部分中文路径下会报“文档已损坏”，因此先在 ASCII 临时路径
更新与导出，再复制回中文文件名。
"""

import json
import shutil
from pathlib import Path

import win32com.client

ROOT = Path(__file__).resolve().parents[1]
DELIVERABLE = ROOT / "deliverable"
SOURCE = DELIVERABLE / "学号-班级-姓名.docx"
PDF = DELIVERABLE / "学号-班级-姓名.pdf"
WORK_DOCX = DELIVERABLE / "_report_work.docx"
WORK_PDF = DELIVERABLE / "_report_work.pdf"


def main():
    shutil.copy2(SOURCE, WORK_DOCX)
    if WORK_PDF.exists():
        WORK_PDF.unlink()

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    doc = None
    try:
        doc = word.Documents.Open(str(WORK_DOCX), False, False)
        doc.Fields.Update()
        for index in range(1, doc.TablesOfContents.Count + 1):
            doc.TablesOfContents.Item(index).Update()
        doc.Repaginate()
        pages = doc.ComputeStatistics(2)
        words = doc.ComputeStatistics(0)
        doc.Save()
        doc.ExportAsFixedFormat(str(WORK_PDF), 17)
        doc.Close(0)
        doc = None
    finally:
        if doc is not None:
            try:
                doc.Close(0)
            except Exception:
                pass
        word.Quit()

    shutil.copy2(WORK_DOCX, SOURCE)
    shutil.copy2(WORK_PDF, PDF)
    WORK_DOCX.unlink(missing_ok=True)
    WORK_PDF.unlink(missing_ok=True)

    result = {
        "docx": str(SOURCE),
        "pdf": str(PDF),
        "pages": int(pages),
        "words": int(words),
        "pdf_size": PDF.stat().st_size,
    }
    (ROOT / "evidence" / "report_render.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
