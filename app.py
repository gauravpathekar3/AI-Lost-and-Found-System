"""Interactive AI-assisted lost-and-found application."""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

import streamlit as st

from image_utils import check_secret, make_secret_hash, save_uploaded_image
from matcher import find_matches

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "items.json"
CLAIMS_PATH = ROOT / "data" / "pending_claims.json"
IMAGE_DIR = ROOT / "data" / "images"
CATEGORIES = ["Bag", "Bottle", "Clothing", "Electronics", "ID card", "Keys", "Wallet", "Umbrella", "Other"]


def load_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        records = json.load(file)
    return records if isinstance(records, list) else []


def save_list(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def image_file(relative_path: str) -> Path | None:
    if not relative_path:
        return None
    candidate = (ROOT / relative_path).resolve()
    if not candidate.is_relative_to(ROOT.resolve()) or not candidate.exists():
        return None
    return candidate


def report_label(item: dict[str, Any]) -> str:
    return f"{item.get('item_name', 'Item')} · {item.get('category', 'Other')} · {item.get('location', 'Location not specified')}"


def show_match(match: dict[str, Any], rank: int) -> None:
    with st.container(border=True):
        st.markdown(f"**{rank}. {match.get('item_name', 'Item')} · {match['match_score']:.0%} match score**")
        st.caption(f"{match.get('status', '').title()} · {match.get('category', 'Other')} · {match.get('location', 'Location not specified')} · {match.get('date', 'Date not specified')}")
        photo = image_file(str(match.get("image_path", "")))
        if photo:
            st.image(str(photo), width=180, caption="Submitted item photo")
        st.write(match.get("description", "No description provided."))
        st.write("**Why it matched:** " + " · ".join(match.get("reasons", [])))
        st.caption("A match score ranks similar reports; it is not proof of ownership.")


st.set_page_config(page_title="AI Lost & Found", page_icon="🔎", layout="centered")
st.title("🔎 AI-Based Lost & Found System")
st.write("Report an item and compare it with opposite-type reports using text, item details, and optional photos.")

try:
    reports = load_list(DATA_PATH)
    claims = load_list(CLAIMS_PATH)
except (OSError, json.JSONDecodeError) as error:
    st.error(f"Could not read the local project records: {error}")
    st.stop()

active = [item for item in reports if not item.get("resolved", False)]
lost_count = sum(item.get("status") == "lost" for item in active)
found_count = sum(item.get("status") == "found" for item in active)
cols = st.columns(3)
cols[0].metric("Open reports", len(active))
cols[1].metric("Lost", lost_count)
cols[2].metric("Found", found_count)

demo = next((item for item in reports if item.get("id") == "demo-lost-blue-bottle"), None)
if demo:
    found = find_matches(demo, reports, limit=1)
    with st.expander("See a sample AI match", expanded=True):
        st.caption("These sample reports are fictional.")
        left, right = st.columns(2)
        with left:
            st.markdown("**Lost report**")
            st.write(f"{demo.get('item_name')} · {demo.get('color')}")
            photo = image_file(str(demo.get("image_path", "")))
            if photo:
                st.image(str(photo), width=180, caption="Sample item photo")
            st.write(demo.get("description"))
            st.caption(f"Location: {demo.get('location')}")
        with right:
            st.markdown("**Top matching found report**")
            if found:
                match = found[0]
                st.write(f"{match.get('item_name')} · {match['match_score']:.0%} match score")
                photo = image_file(str(match.get("image_path", "")))
                if photo:
                    st.image(str(photo), width=180, caption="Sample item photo")
                st.write(match.get("description"))
                st.caption(f"Category: {match.get('category')} · Location: {match.get('location')}")
                if match.get("visual_similarity") is not None:
                    st.caption(f"Image similarity signal: {match['visual_similarity']:.0%}")
            else:
                st.info("No matching sample report is available.")
        st.caption("A similarity score suggests a candidate; it does not confirm ownership.")

st.subheader("1. Report an item and find potential matches")
st.caption("Reports and sanitized photos are saved locally. Do not include faces, ID numbers, serial numbers, or private contact details.")
with st.form("item_report_form", clear_on_submit=False):
    status_label = st.radio("What are you reporting?", ["I lost an item", "I found an item"], horizontal=True)
    status = "lost" if status_label.startswith("I lost") else "found"
    item_name = st.text_input("Item name", placeholder="e.g., Blue water bottle")
    category = st.selectbox("Category", CATEGORIES)
    color = st.text_input("Color or identifying feature", placeholder="e.g., Blue with a white sticker")
    location = st.text_input("General location", placeholder="e.g., Main Library")
    item_date = st.date_input("Date lost or found", value=date.today())
    description = st.text_area("Public description", placeholder="Describe the item without sharing a unique secret or personal details.", max_chars=700)
    uploaded = st.file_uploader(
        "Optional item photo",
        type=["jpg", "jpeg", "png"],
        help="Up to 5 MB. The image is re-encoded to remove EXIF metadata before saving.",
    )
    photo_consent = st.checkbox("I confirm the photo shows the item only and does not expose faces, IDs, addresses, or other sensitive information.")
    clue = st.text_input(
        "Private owner verification clue (required for lost items)",
        type="password",
        help="Use a unique detail only the owner knows. It is stored as a salted hash and never shown in reports. Do not use a password, PIN, serial number, or public fact.",
    )
    submitted = st.form_submit_button("Save report and find matches", type="primary", use_container_width=True)

if submitted:
    if not item_name.strip() or not description.strip():
        st.error("Please enter an item name and public description.")
    elif status == "lost" and len(clue.strip()) < 8:
        st.error("For lost items, enter a private verification clue of at least 8 characters.")
    elif uploaded is not None and not photo_consent:
        st.error("Confirm the photo privacy note or remove the photo.")
    else:
        report_id = uuid.uuid4().hex[:10]
        record: dict[str, Any] = {
            "id": report_id,
            "status": status,
            "item_name": item_name.strip(),
            "category": category,
            "color": color.strip(),
            "location": location.strip(),
            "date": item_date.isoformat(),
            "description": description.strip(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "resolved": False,
            "sample": False,
        }
        if status == "lost":
            record.update(make_secret_hash(clue))
        if uploaded is not None:
            try:
                record.update(save_uploaded_image(
                    uploaded,
                    IMAGE_DIR / f"{report_id}.jpg",
                    f"data/images/{report_id}.jpg",
                ))
            except ValueError as error:
                st.error(str(error))
                st.stop()
        reports.append(record)
        save_list(DATA_PATH, reports)
        matches = find_matches(record, reports)
        st.success("Report saved locally.")
        if matches:
            st.subheader("Potential matches")
            for index, match in enumerate(matches, start=1):
                show_match(match, index)
        else:
            st.info("No opposite-type reports are available yet. A later report can be matched to this one.")

st.subheader("2. Request a return")
st.caption("A correct private clue creates only a pending request. Staff must verify the claimant and item in person before any return.")
lost_reports = [item for item in active if item.get("status") == "lost" and item.get("verification_hash")]
found_reports = [item for item in active if item.get("status") == "found"]
if not lost_reports or not found_reports:
    st.info("A return request is available when there is at least one open lost report and one open found report.")
else:
    with st.form("claim_form"):
        lost_item = st.selectbox("Select the lost-item report", lost_reports, format_func=report_label)
        found_item = st.selectbox("Select the found-item report", found_reports, format_func=report_label)
        claim_clue = st.text_input("Private owner verification clue", type="password")
        claim_submitted = st.form_submit_button("Verify clue and request staff review", use_container_width=True)
    if claim_submitted:
        ranked = find_matches(lost_item, reports, limit=len(reports))
        candidate = next((item for item in ranked if item.get("id") == found_item.get("id")), None)
        if not claim_clue.strip():
            st.error("Enter the private clue set in the lost-item report.")
        elif not candidate or candidate["match_score"] < 0.20:
            st.error("These reports are not similar enough for an automated request. Ask staff to review them manually.")
        elif not check_secret(claim_clue, str(lost_item.get("verification_salt", "")), str(lost_item.get("verification_hash", ""))):
            st.error("The private clue did not match. No request was created.")
        elif any(c.get("lost_report_id") == lost_item["id"] and c.get("found_report_id") == found_item["id"] and c.get("status") == "pending_staff_review" for c in claims):
            st.info("A request for this pair is already waiting for staff review.")
        else:
            reference = uuid.uuid4().hex[:8].upper()
            claims.append({
                "reference": reference,
                "lost_report_id": lost_item["id"],
                "found_report_id": found_item["id"],
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "status": "pending_staff_review",
            })
            save_list(CLAIMS_PATH, claims)
            st.success(f"Clue accepted. Request {reference} is pending staff review. Bring this reference to the campus lost-property desk. No item was marked returned and no private details were revealed.")

with st.expander("Browse open reports"):
    for kind in ("lost", "found"):
        subset = [item for item in active if item.get("status") == kind]
        st.markdown(f"**{kind.title()} items ({len(subset)})**")
        for item in subset:
            with st.container(border=True):
                st.write(f"**{item.get('item_name', 'Item')}** · {item.get('category', 'Other')}")
                st.caption(f"{item.get('color', 'Color not specified')} · {item.get('location', 'Location not specified')} · {item.get('date', 'Date not specified')}")
                photo = image_file(str(item.get("image_path", "")))
                if photo:
                    st.image(str(photo), width=140, caption="Item photo")
                st.write(item.get("description", ""))
        if not subset:
            st.caption("No open reports.")

with st.expander("How matching and privacy work"):
    st.write("TF-IDF and cosine similarity compare the report text. Category, color, location overlap, and optional image descriptors add signals. Photos are re-encoded to remove EXIF metadata. Lost-item clues are stored as salted hashes. A valid clue only creates a pending staff-review request; the app never releases an item automatically.")
