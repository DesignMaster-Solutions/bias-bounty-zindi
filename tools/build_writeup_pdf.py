"""Build WRITEUP.pdf from WRITEUP.md (pandoc -> Typst -> PDF).

Only layout changes on top of pandoc's default Typst template: narrower margins, 9 pt tables, and a
flexible label column in the two wide tables so tract and area names do not wrap letter by letter.
Usage: python tools/build_writeup_pdf.py
"""
import pathlib
import re
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
WIDE = {  # text that identifies the table -> Typst column spec
    "San Carlos Reservation": "(auto, 1fr, auto, auto, auto, auto, auto)",
    "tribal rural": "(1fr, auto, auto, auto, auto, auto, auto)",
}


def layout(typ: str) -> str:
    margin = "margin: (x: 1.25in, y: 1.25in)"
    assert margin in typ, "pandoc template changed: margin default not found"
    typ = typ.replace(margin, "margin: (x: 0.9in, y: 0.9in)", 1)
    typ = typ.replace("#show: doc => conf(", "#show table: set text(size: 9pt)\n#show: doc => conf(", 1)
    blocks = typ.split("#figure(")
    for marker, spec in WIDE.items():
        hits = [i for i, b in enumerate(blocks) if marker in b and re.search(r"columns: \d+,", b)]
        assert len(hits) >= 1, f"table with {marker!r} not found"
        i = hits[0]
        blocks[i] = re.sub(r"columns: \d+,", f"columns: {spec},", blocks[i], count=1)
    return "#figure(".join(blocks)


def main() -> None:
    typ = subprocess.run(
        ["pandoc", str(ROOT / "WRITEUP.md"), "-s", "-t", "typst", "--columns=400"],
        check=True, capture_output=True, text=True,
    ).stdout
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / "writeup.typ"
        src.write_text(layout(typ))
        subprocess.run(["typst", "compile", str(src), str(ROOT / "WRITEUP.pdf")], check=True)


if __name__ == "__main__":
    main()
