#!/usr/bin/env python3
"""
validate-draft.py — Example validation script for the Agent Skill Validation Framework.

Validates a JSON draft file against a schema and returns structured results.

Exit codes:
  0 = PASSED  — all checks passed
  1 = FAILED  — one or more errors (exclude item from queue)
  2 = WARNINGS — non-blocking issues (proceed with note)

Output contract (JSON to stdout):
{
  "status": "PASSED" | "FAILED" | "WARNINGS",
  "checked": <int>,
  "errors": [{"field": "...", "rule": "...", "message": "..."}],
  "warnings": [{"field": "...", "rule": "...", "message": "..."}]
}

Usage:
  python3 validate-draft.py <draft_file.json>
  python3 validate-draft.py <draft_file.json> --schema <schema_file.json>
"""

import json
import sys
from pathlib import Path

# --- Default validation rules (when no schema provided) ---

REQUIRED_FIELDS = ["title", "description", "category"]
MIN_DESCRIPTION_LENGTH = 50
ALLOWED_CATEGORIES = [
    "Highlight", "Lowlight", "Observation", "Risk",
    "Blocker", "Challenge", "Health of the Business"
]
SFDC_ID_LENGTH = 18


def validate_required(item, errors):
    """Check that all required fields exist and are non-empty."""
    for field in REQUIRED_FIELDS:
        val = item.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors.append({
                "field": field,
                "rule": "required",
                "message": f"'{field}' is required and must be non-empty"
            })


def validate_description_length(item, warnings):
    """Check description meets minimum length."""
    desc = item.get("description", "")
    if desc and len(desc) < MIN_DESCRIPTION_LENGTH:
        warnings.append({
            "field": "description",
            "rule": "min_length",
            "message": f"Description is {len(desc)} chars (minimum: {MIN_DESCRIPTION_LENGTH})"
        })


def validate_category(item, errors):
    """Check category is an allowed value."""
    cat = item.get("category", "")
    if cat and cat not in ALLOWED_CATEGORIES:
        errors.append({
            "field": "category",
            "rule": "enum",
            "message": f"'{cat}' is not a valid category. Allowed: {ALLOWED_CATEGORIES}"
        })


def validate_sfdc_ids(item, warnings):
    """Check SFDC IDs are the expected length."""
    for field in ["accountId", "opportunityId", "parent_record.id"]:
        # Support nested fields with dot notation
        parts = field.split(".")
        val = item
        for part in parts:
            if isinstance(val, dict):
                val = val.get(part)
            else:
                val = None
                break
        if val and isinstance(val, str) and len(val) != SFDC_ID_LENGTH:
            warnings.append({
                "field": field,
                "rule": "sfdc_id_length",
                "message": f"'{field}' is {len(val)} chars (expected {SFDC_ID_LENGTH} for SFDC ID)"
            })


def validate_dates(item, warnings):
    """Check date fields are valid ISO format."""
    from datetime import datetime
    for field in ["activity_date", "relevantDate", "created_at"]:
        val = item.get(field)
        if val:
            try:
                datetime.fromisoformat(val.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                warnings.append({
                    "field": field,
                    "rule": "date_format",
                    "message": f"'{field}' value '{val}' is not valid ISO 8601"
                })


def validate_item(item):
    """Run all validations on a single item. Returns (errors, warnings)."""
    errors = []
    warnings = []
    validate_required(item, errors)
    validate_category(item, errors)
    validate_description_length(item, warnings)
    validate_sfdc_ids(item, warnings)
    validate_dates(item, warnings)
    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "FAILED",
            "checked": 0,
            "errors": [{"field": "input", "rule": "usage", "message": "Usage: validate-draft.py <draft_file.json>"}],
            "warnings": []
        }))
        sys.exit(1)

    draft_path = Path(sys.argv[1])
    if not draft_path.exists():
        print(json.dumps({
            "status": "FAILED",
            "checked": 0,
            "errors": [{"field": "input", "rule": "file_not_found", "message": f"File not found: {draft_path}"}],
            "warnings": []
        }))
        sys.exit(1)

    data = json.loads(draft_path.read_text())

    # Support both single item and array of items (drafts list)
    items = data.get("drafts", [data]) if isinstance(data, dict) else data
    all_errors = []
    all_warnings = []

    for i, item in enumerate(items):
        errs, warns = validate_item(item)
        prefix = f"drafts[{i}]." if len(items) > 1 else ""
        for e in errs:
            e["field"] = f"{prefix}{e['field']}"
            all_errors.append(e)
        for w in warns:
            w["field"] = f"{prefix}{w['field']}"
            all_warnings.append(w)

    if all_errors:
        status = "FAILED"
        exit_code = 1
    elif all_warnings:
        status = "WARNINGS"
        exit_code = 2
    else:
        status = "PASSED"
        exit_code = 0

    print(json.dumps({
        "status": status,
        "checked": len(items),
        "errors": all_errors,
        "warnings": all_warnings
    }, indent=2))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
