#!/usr/bin/env python3
"""Build UserDefaults payloads for the Lugali App Store 6.9 captures.

Writes JSON (same Codable shape as VisitStore) and a merge-plist that can be
imported into the Simulator container without changing production code.
"""
from __future__ import annotations

import argparse
import json
import plistlib
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

BRT = timezone(timedelta(hours=-3))


def ts(hour: int, minute: int) -> float:
    return datetime(2026, 9, 8, hour, minute, tzinfo=BRT).timestamp()


def place(name: str, region: str, country: str) -> dict:
    return {
        "name": name,
        "region": region,
        "country": country,
        "population": None,
    }


def visit(p: dict, entered_at: float) -> dict:
    return {
        "id": str(uuid.uuid4()).upper(),
        "place": p,
        "enteredAt": entered_at,
        "isSimulated": False,
    }


def dumps(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    foz = place("Foz do Iguaçu", "Paraná", "Brasil")
    iguazu = place("Puerto Iguazú", "Misiones", "Argentina")
    santa = place("Santa Terezinha de Itaipu", "Paraná", "Brasil")

    visits = [
        visit(foz, ts(9, 41)),
        visit(iguazu, ts(8, 50)),
        visit(santa, ts(8, 10)),
    ]

    visits_bytes = dumps(visits)
    current_bytes = dumps(foz)
    notified = datetime(2026, 9, 8, 12, 41, 0)  # naive UTC for plistlib

    (out / "visits.json").write_bytes(visits_bytes)
    (out / "currentPlace.json").write_bytes(current_bytes)
    (out / "visits.hex").write_text(visits_bytes.hex())
    (out / "currentPlace.hex").write_text(current_bytes.hex())

    plist = {
        "isMonitoring": True,
        "visits": visits_bytes,
        "currentPlace": current_bytes,
        "lastNotificationAt": notified,
    }
    (out / "com.pixelun.Lugali.plist").write_bytes(plistlib.dumps(plist, fmt=plistlib.FMT_BINARY))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
