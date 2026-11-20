#!/usr/bin/env python3
"""Fetch open-licensed fonts for any text role this machine cannot match (Linux and Windows lack the
Mac faces the looks were designed with), into <project>/fonts/<role>.ttf where the engine finds them.

  python3 get_fonts.py --project my-film            # only roles that would fall back to the system default
  python3 get_fonts.py --project my-film --force    # replace them all
  python3 get_fonts.py --project my-film --arabic   # Arabic faces for every role (films with Arabic on screen)

  cond -> Bebas Neue (SIL Open Font License): condensed caps for labels, numbers, stamps, captions
  hand -> Homemade Apple (Apache 2.0): handwriting for ledger entries

--arabic (all SIL Open Font License, each also covers Latin letters and digits):
  cond -> Lalezar, label -> Tajawal Bold, labelm and mono -> Tajawal Medium, serif -> Amiri, hand -> Aref Ruqaa

All come from the Google Fonts repository on GitHub. Keep the licence notes with the project if
you share it.
"""
import argparse
import pathlib
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
UA = "cinematic-film/1.0 (+https://github.com/Moh4696/cinematic-skill)"
FONTS = {
    "cond": ("https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf", "Bebas Neue", "SIL Open Font License 1.1"),
    "hand": ("https://raw.githubusercontent.com/google/fonts/main/apache/homemadeapple/HomemadeApple-Regular.ttf", "Homemade Apple", "Apache License 2.0"),
}


_GF = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
_OFL = "SIL Open Font License 1.1"
ARABIC = {
    "cond": (_GF + "lalezar/Lalezar-Regular.ttf", "Lalezar", _OFL),
    "label": (_GF + "tajawal/Tajawal-Bold.ttf", "Tajawal Bold", _OFL),
    "labelm": (_GF + "tajawal/Tajawal-Medium.ttf", "Tajawal Medium", _OFL),
    "mono": (_GF + "tajawal/Tajawal-Medium.ttf", "Tajawal Medium", _OFL),
    "serif": (_GF + "amiri/Amiri-Regular.ttf", "Amiri", _OFL),
    "hand": (_GF + "arefruqaa/ArefRuqaa-Regular.ttf", "Aref Ruqaa", _OFL),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--arabic", action="store_true", help="fetch Arabic faces for every text role")
    a = ap.parse_args()
    from engine import resolve_typeface
    fdir = pathlib.Path(a.project) / "fonts"; fdir.mkdir(parents=True, exist_ok=True)
    notes = []
    for role, (url, name, lic) in (ARABIC if a.arabic else FONTS).items():
        _, desc = resolve_typeface(role, fdir)
        if not a.arabic and not a.force and not desc.startswith("system default"):
            print(f"{role:<5} already {desc}"); continue
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            (fdir / f"{role}.ttf").write_bytes(r.read())
        print(f"{role:<5} -> fonts/{role}.ttf  ({name}, {lic})")
        notes.append(f"{role}.ttf: {name}, {lic}, from {url}")
    if notes:
        with open(fdir / "LICENSES.txt", "a") as f:
            f.write("\n".join(notes) + "\n")


if __name__ == "__main__":
    main()
