from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator, Tuple

from pdf2image import convert_from_path, pdfinfo_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError
from PIL import Image


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "makkot_vilna_images"
START_PAGE = 3  # PDF page number (1-indexed) where real content begins
END_PAGE = 48  # Optionally stop before the PDF ends
DPI = 400
THUMBNAIL_SIZE = (256, 278)
TRACTATE_NAME = "Makkot"
POPPLER_PATH = os.environ.get("POPPLER_PATH")  # Directory containing pdfinfo/pdftoppm


def find_pdf() -> Path:
    """Return the single PDF file sitting next to this script."""
    pdf_files = sorted(BASE_DIR.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError("No PDF file found in the current directory.")
    if len(pdf_files) > 1:
        names = ", ".join(p.name for p in pdf_files)
        raise RuntimeError(f"Multiple PDF files found ({names}); cannot determine which to use.")
    return pdf_files[0]


def page_labels() -> Iterator[str]:
    """Yield folio labels (2a, 2b, ...) starting from 2a."""
    daf = 2
    side = "a"
    while True:
        yield f"{TRACTATE_NAME}_{daf}{side}"
        if side == "a":
            side = "b"
        else:
            side = "a"
            daf += 1


def iter_pdf_pages(pdf_path: Path) -> Iterator[Tuple[int, Image.Image]]:
    """Render each page (START_PAGE through END_PAGE) to an in-memory PIL image."""
    try:
        info = pdfinfo_from_path(str(pdf_path), poppler_path=POPPLER_PATH)
    except PDFInfoNotInstalledError as err:
        raise RuntimeError(
            "Poppler utilities (pdfinfo, pdftoppm) are required. Install them or set POPPLER_PATH."
        ) from err
    total_pages = info.get("Pages", 0)
    if total_pages < START_PAGE:
        raise RuntimeError(f"PDF only has {total_pages} pages; cannot start from page {START_PAGE}.")

    last_page = END_PAGE if END_PAGE is not None else total_pages
    if last_page > total_pages:
        raise RuntimeError(f"END_PAGE ({END_PAGE}) exceeds the total pages in the PDF ({total_pages}).")
    if last_page < START_PAGE:
        raise RuntimeError("END_PAGE must be greater than or equal to START_PAGE.")

    # Convert one page at a time to keep memory usage manageable.
    for page_num in range(START_PAGE, last_page + 1):
        image = convert_from_path(
            str(pdf_path),
            fmt="jpeg",
            dpi=DPI,
            first_page=page_num,
            last_page=page_num,
            poppler_path=POPPLER_PATH,
        )[0]
        yield page_num, image


def save_page(image: Image.Image, label: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    main_path = OUTPUT_DIR / f"{label}.jpg"
    thumb_path = OUTPUT_DIR / f"{label}_thumbnail.jpg"

    image.save(main_path, format="JPEG")

    thumb = image.copy()
    thumb.thumbnail(THUMBNAIL_SIZE)
    thumb.save(thumb_path, format="JPEG")
    thumb.close()
    image.close()


def main() -> None:
    pdf_path = find_pdf()
    label_iter = page_labels()

    for page_num, image in iter_pdf_pages(pdf_path):
        label = next(label_iter)
        print(f"Rendering PDF page {page_num} -> {label}")
        save_page(image, label)


if __name__ == "__main__":
    main()
