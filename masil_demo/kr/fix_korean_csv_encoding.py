import sys
import csv
from pathlib import Path

def sniff_delimiter(sample_text: str) -> str:
    try:
        return csv.Sniffer().sniff(sample_text, delimiters=[",", "\t", ";", "|"]).delimiter
    except Exception:
        return ","  # fallback

def best_guess_encoding(path: Path) -> str:
    # Try charset-normalizer if available (works great on Windows)
    try:
        from charset_normalizer import from_bytes
        raw = path.read_bytes()
        result = from_bytes(raw).best()
        if result and result.encoding:
            return result.encoding
    except Exception:
        pass
    return "cp949"  # common for Korean public data

def read_text_with_fallback(path: Path, encodings: list[str]) -> tuple[str, str]:
    for enc in encodings:
        try:
            text = path.read_text(encoding=enc, errors="strict")
            return text, enc
        except Exception:
            continue
    # last resort: replace errors so we at least convert
    enc = encodings[0]
    text = path.read_text(encoding=enc, errors="replace")
    return text, enc

def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_korean_csv_encoding.py input.csv [output.csv]")
        sys.exit(1)

    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else in_path.with_name(in_path.stem + "_utf8.csv")

    guess = best_guess_encoding(in_path)
    candidates = [
        "utf-8-sig",
        "utf-8",
        guess,
        "cp949",
        "euc-kr",
    ]
    # keep unique order
    seen = set()
    candidates = [x for x in candidates if not (x in seen or seen.add(x))]

    text, used_enc = read_text_with_fallback(in_path, candidates)

    # delimiter check from first ~10KB
    sample = text[:10_000]
    delim = sniff_delimiter(sample)

    # re-save as UTF-8 with BOM (best for Excel)
    out_path.write_text(text, encoding="utf-8-sig", newline="")

    print(f"[OK] Read: {in_path.name}")
    print(f"     Detected/used encoding: {used_enc}")
    print(f"     Detected delimiter: {repr(delim)}")
    print(f"[OK] Saved as UTF-8(BOM): {out_path.name}")

if __name__ == "__main__":
    main()
