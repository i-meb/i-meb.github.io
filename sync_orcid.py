from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
VARS = yaml.safe_load((ROOT / "_variables.yml").read_text(encoding="utf-8"))
ORCID_ID = VARS["orcid"]["id"]
TOKEN_URL = "https://orcid.org/oauth/token"
API_BASE = "https://pub.orcid.org/v3.0"
OUT = ROOT / "generated" / "publications.yml"
MANUAL = ROOT / "data" / "publications_manual.yml"
OVERRIDES = ROOT / "data" / "publication_overrides.yml"

INCLUDE_TYPES = {
    "journal-article",
    "preprint",
    "book",
    "book-chapter",
    "conference-paper",
    "dissertation-thesis",
    "edited-book",
    "encyclopedia-entry",
    "magazine-article",
    "newspaper-article",
    "report",
    "review",
    "working-paper",
}

TYPE_LABELS = {
    "journal-article": "Journal article",
    "preprint": "Preprint",
    "book": "Book",
    "book-chapter": "Book chapter",
    "conference-paper": "Conference paper",
    "dissertation-thesis": "Thesis",
    "edited-book": "Edited book",
    "encyclopedia-entry": "Encyclopedia entry",
    "magazine-article": "Magazine article",
    "newspaper-article": "Newspaper article",
    "report": "Report",
    "review": "Review",
    "working-paper": "Working paper",
}


def value(obj: Any, *keys: str, default: Any = "") -> Any:
    cur = obj
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
        if cur is None:
            return default
    return cur


def normalize_doi(raw: str) -> str:
    raw = (raw or "").strip().lower()
    raw = re.sub(r"^https?://(dx\.)?doi\.org/", "", raw)
    raw = re.sub(r"^doi:\s*", "", raw)
    return raw.rstrip(" .")


def get_token() -> str:
    client_id = os.environ["ORCID_CLIENT_ID"]
    client_secret = os.environ["ORCID_CLIENT_SECRET"]
    r = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
            "scope": "/read-public",
        },
        headers={"Accept": "application/json"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def api_get(path: str, token: str) -> dict[str, Any]:
    r = requests.get(
        f"{API_BASE}/{ORCID_ID}/{path.lstrip('/')}",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def external_ids(work: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for ext in value(work, "external-ids", "external-id", default=[]) or []:
        ext_type = str(ext.get("external-id-type", "")).lower()
        ext_value = str(ext.get("external-id-value", ""))
        if ext_type and ext_value and ext_type not in result:
            result[ext_type] = ext_value
    return result


def contributors(work: dict[str, Any]) -> str:
    names: list[str] = []
    for c in value(work, "contributors", "contributor", default=[]) or []:
        name = value(c, "credit-name", "value")
        if name:
            names.append(str(name).strip())
    return ", ".join(dict.fromkeys(names))


def pub_year(work: dict[str, Any]) -> int:
    raw = value(work, "publication-date", "year", "value")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def work_to_item(work: dict[str, Any], put_code: int | str) -> dict[str, Any] | None:
    work_type = str(work.get("type", ""))
    if work_type not in INCLUDE_TYPES:
        return None

    ids = external_ids(work)
    doi = normalize_doi(ids.get("doi", ""))
    item_id = f"doi:{doi}" if doi else f"orcid:{put_code}"
    title = value(work, "title", "title", "value")
    venue = value(work, "journal-title", "value")
    work_url = value(work, "url", "value")
    doi_url = f"https://doi.org/{doi}" if doi else ""

    return {
        "id": item_id,
        "title": str(title).strip(),
        "year": pub_year(work),
        "type": TYPE_LABELS.get(work_type, work_type.replace("-", " ").title()),
        "authors": contributors(work),
        "venue": str(venue).strip(),
        "doi": doi,
        "doi_url": doi_url,
        "url": str(work_url or doi_url).strip(),
        "orcid_put_code": int(put_code) if str(put_code).isdigit() else str(put_code),
        "orcid_url": f"https://orcid.org/{ORCID_ID}",
        "source": "ORCID",
    }


def read_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return default if data is None else data


def main() -> None:
    token = get_token()
    works = api_get("works", token)

    items: list[dict[str, Any]] = []
    seen_put_codes: set[str] = set()

    for group in works.get("group", []) or []:
        summaries = group.get("work-summary", []) or []
        if not summaries:
            continue

        # Prefer the first displayed summary for grouped duplicate records.
        summary = summaries[0]
        put_code = summary.get("put-code")
        if put_code is None or str(put_code) in seen_put_codes:
            continue
        seen_put_codes.add(str(put_code))

        work = api_get(f"work/{put_code}", token)
        item = work_to_item(work, put_code)
        if item and item["title"] and item["year"]:
            items.append(item)

    manual = read_yaml(MANUAL, [])
    if not isinstance(manual, list):
        raise TypeError("data/publications_manual.yml must contain a YAML list")
    items.extend(manual)

    overrides = read_yaml(OVERRIDES, {})
    if not isinstance(overrides, dict):
        raise TypeError("data/publication_overrides.yml must contain a YAML mapping")

    merged: list[dict[str, Any]] = []
    for item in items:
        key = item.get("id", "")
        patch = overrides.get(key, {}) or {}
        updated = {**item, **patch}
        if updated.get("exclude"):
            continue
        updated.pop("exclude", None)
        merged.append(updated)

    # Deduplicate by stable ID, preferring later entries (manual/override-friendly).
    deduped = {str(item["id"]): item for item in merged if item.get("id")}
    final = sorted(
        deduped.values(),
        key=lambda x: (-int(x.get("year", 0)), str(x.get("title", "")).lower()),
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        yaml.safe_dump(final, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    print(json.dumps({"orcid": ORCID_ID, "publications": len(final)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
