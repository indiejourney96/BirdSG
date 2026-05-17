"""
build_species_mapping.py — Robust eBird ↔ dataset mapper

Fixes:
- Safe fuzzy matching (no .iloc crash)
- Normalized lookup table (no mismatch bug)
- Rejects generic taxa (sp., spp.)
- Deterministic mapping output
"""

import os
import json
import re
from pathlib import Path

import pandas as pd
from rapidfuzz import process, fuzz


# -------------------------------------------------------------------
# PATHS
# -------------------------------------------------------------------

DATASET_PATH = Path(r"C:\Users\Admin\Daryl\SD Projects\BirdSG\dataset")
EBIRD_FILE = Path(r"C:\Users\Admin\Daryl\SD Projects\BirdSG\ebird.xlsx")

OUTPUT_JSON = Path("species_mapping.json")
OUTPUT_PY = Path("species_mapping.py")

FUZZY_THRESHOLD = 88


# -------------------------------------------------------------------
# 1. LOAD DATASET LABELS
# -------------------------------------------------------------------

def load_dataset_labels():
    return [
        d for d in os.listdir(DATASET_PATH)
        if (DATASET_PATH / d).is_dir()
    ]


# -------------------------------------------------------------------
# 2. LOAD EBIRD DATA
# -------------------------------------------------------------------

def load_ebird_data():
    df = pd.read_excel(EBIRD_FILE)

    # Column B = COMMON NAME
    # Column C = SPECIES_CODE
    df = df.iloc[:, [1, 2]]
    df.columns = ["common_name", "species_code"]

    df = df.dropna()

    df["common_name"] = df["common_name"].astype(str).str.strip()
    df["species_code"] = df["species_code"].astype(str).str.strip()

    # Remove generic taxa (VERY IMPORTANT)
    df = df[~df["common_name"].str.contains(r"\bsp\b|\bspp\b|species", case=False)]

    return df


# -------------------------------------------------------------------
# 3. NORMALIZATION
# -------------------------------------------------------------------

def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"[^a-z\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# -------------------------------------------------------------------
# 4. BUILD FAST LOOKUP INDEX
# -------------------------------------------------------------------

def build_lookup(df):
    """
    Creates:
    normalized_name -> row
    """
    lookup = {}

    for _, row in df.iterrows():
        key = normalize(row["common_name"])
        lookup[key] = row

    return lookup, list(lookup.keys())


# -------------------------------------------------------------------
# 5. FUZZY MATCH
# -------------------------------------------------------------------

def match(label, choices):
    label_norm = normalize(label)

    match_name, score, _ = process.extractOne(
        label_norm,
        choices,
        scorer=fuzz.token_set_ratio
    )

    return match_name, score


# -------------------------------------------------------------------
# 6. BUILD MAPPING
# -------------------------------------------------------------------

def build_mapping(df):
    dataset_labels = load_dataset_labels()

    lookup, choices = build_lookup(df)

    mapping = {}
    unmatched = []

    print(f"Dataset labels: {len(dataset_labels)}")
    print(f"eBird entries: {len(df)}")

    for label in dataset_labels:
        match_name, score = match(label, choices)

        if score < FUZZY_THRESHOLD:
            unmatched.append({
                "label": label,
                "match": match_name,
                "score": score
            })
            continue

        row = lookup.get(match_name)

        if row is None:
            unmatched.append({
                "label": label,
                "match": match_name,
                "score": score,
                "reason": "lookup_failed"
            })
            continue

        mapping[label] = {
            "common_name": row["common_name"],
            "ebird_code": row["species_code"],
            "match_score": score
        }

    return mapping, unmatched


# -------------------------------------------------------------------
# 7. SAVE OUTPUTS
# -------------------------------------------------------------------

def save_outputs(mapping, unmatched):
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)

    with open(OUTPUT_PY, "w", encoding="utf-8") as f:
        f.write("# AUTO-GENERATED FILE — DO NOT EDIT\n\n")
        f.write("SPECIES_MAP = ")
        f.write(json.dumps(mapping, indent=2))

    with open("unmatched_species.json", "w", encoding="utf-8") as f:
        json.dump(unmatched, f, indent=2)


# -------------------------------------------------------------------
# 8. MAIN
# -------------------------------------------------------------------

def print_unmatched_summary(unmatched):
    print("\nUNMATCHED SPECIES REPORT")
    print("-" * 60)

    # sort worst matches first
    sorted_unmatched = sorted(unmatched, key=lambda x: x.get("score", 0))

    for item in sorted_unmatched:
        label = item["label"]
        match = item.get("match", "None")
        score = item.get("score", 0)

        print(f"{label:40} → {match:30} ({score:.2f})")

    print("-" * 60)
    print(f"Total unmatched: {len(unmatched)}\n")

def main():
    print("Loading dataset...")
    labels = load_dataset_labels()
    print(f"Dataset folders: {len(labels)}")

    print("Loading eBird Excel...")
    df = load_ebird_data()

    print("Building mapping...")
    mapping, unmatched = build_mapping(df)

    print(f"Mapped: {len(mapping)}")
    print(f"Unmatched: {len(unmatched)}")

    # NEW: console report
    print_unmatched_summary(unmatched)

    save_outputs(mapping, unmatched)

    print("Done.")


if __name__ == "__main__":
    main()