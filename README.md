# AI-Based Lost & Found System

A local web app for matching campus lost and found reports. It ranks candidates using TF-IDF text similarity, item details, and optional image similarity.

## Run it

Requirements: Python 3.10 or newer.

### Windows

~~~powershell
cd AI_Lost_and_Found_System
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python evaluate_matching.py
streamlit run app.py
~~~

### macOS / Linux

~~~bash
cd AI_Lost_and_Found_System
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python evaluate_matching.py
streamlit run app.py
~~~

Streamlit prints a local address to open in your browser. Fictional starter reports make a sample text match visible immediately. Add a report with the form; reports and sanitized photos are stored locally under data/.

## Project files

- app.py — interactive reporting, matching, browsing, and return-request workflow.
- matcher.py — TF-IDF, cosine similarity, structured detail scoring, and optional image scoring.
- image_utils.py — image metadata removal and salted owner-clue hashing.
- evaluate_matching.py — small reproducible ranking demonstration.
- data/items.json — fictional starter reports; new reports are appended here.
- data/pending_claims.json — pending staff-review requests without private clues.
- artifacts/matching_evaluation.json — results from the bundled example run.
- PROJECT_REPORT.md — brief academic report.

## Photo matching and privacy

An optional JPG or PNG photo is limited to 5 MB. The app re-encodes it to remove EXIF metadata and compares compact visual descriptors for coarse shape and color. It uses this image signal only when both reports have photos. This is an approximate visual feature, not a deep-learning image model; backgrounds, lighting, and camera angle can affect it.

Lost-item reports require a private owner clue. The app stores a salted PBKDF2 hash instead of the clue. A correct clue creates only a pending request; staff must verify the claimant and item in person before returning anything. Do not use a password, PIN, serial number, or public fact as the clue.

This classroom prototype uses local JSON files and has no accounts or protected shared server. It reduces casual false claims but cannot guarantee identity or prevent someone with file access from editing local records. Use fictional information for class demonstrations. A real deployment needs authenticated accounts, role-based access, protected storage, audit logs, and staff verification. Do not upload faces, IDs, addresses, phone numbers, or sensitive item contents.
