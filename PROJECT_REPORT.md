# AI Lab Project Report: AI-Based Lost & Found System

**Student name(s):** Gaurav Pathekar , Harsh Rao
**Class / roll number(s):** 0808AL251105, 0808AL251115
**Submission date:** 25/10/2026

## 1. Project title and problem statement

**Title:** AI-Based Lost & Found System

Students can have difficulty reconnecting lost belongings with items handed in by someone else. Manual notices are hard to search when people describe the same item in different words. This project records lost and found items and ranks possible matches using text, item details, and optional photos.

## 2. Objectives

- Create an interface for reporting lost and found belongings.
- Compare report descriptions with natural language processing.
- Add optional image similarity for item photos.
- Rank candidates using category, color, and location details.
- Reduce false claims with a private owner clue and staff review before return.
- Demonstrate the workflow using fictional sample reports.

## 3. AI/ML technique used

TF-IDF vectorization turns names and descriptions into numeric word and phrase features. Cosine similarity compares those text vectors. Category, color, and location signals add to the ranking. When both reports include photos, compact computer-vision descriptors compare coarse shape and color. This is an information-retrieval and similarity-ranking approach, not a trained deep-learning image model. Scores rank candidates; they are not probabilities or proof of ownership.

## 4. Dataset

Starter data contains fictional item reports for demonstration. It has no real names, phone numbers, or personal records. New reports and sanitized photos are saved locally. The example evaluation is small and hand-written, so it is not a real-world performance estimate.

## 5. Methodology / workflow

1. Record item type, name, category, color, general location, date, and description.
2. Optionally upload a JPG or PNG. The app re-encodes it to remove EXIF metadata and creates a compact shape/color descriptor.
3. Compare the new report only with open reports of the opposite type.
4. Use TF-IDF and cosine similarity for text; include available category, color, location, and image signals in a weighted score.
5. Rank candidate reports and show the reasons for each suggestion.
6. For a lost item, store a private owner clue as a salted PBKDF2 hash. A matching clue creates a pending staff-review request; the app never marks an item returned or reveals private details automatically.
7. Require staff to verify the claimant and item in person before handover.

## 6. Working code / implementation

- app.py — Streamlit interface for reports, matches, and return requests.
- matcher.py — text, detail, and optional image similarity ranking.
- image_utils.py — EXIF removal, visual descriptors, and private clue hashing.
- evaluate_matching.py — reproducible ranking demonstration.
- data/items.json — fictional sample reports.
- data/pending_claims.json — pending staff-review requests.

See README.md for installation and run instructions.

## 7. Results and screenshots

### Screenshot 1: Sample AI match

![Sample AI match](screenshots/samplematch.png)

### Screenshot 2: Lost and found item match

![Item match](screenshots/_item_match.png)

### Screenshot 3: Protected return request

![Pending staff review](screenshots/_pending_review.png)

The demonstration script ranked the expected found report first in **4 of 4 fictional sample cases (top-1 match rate: 100%)**. This result only checks the workflow on its four hand-written examples; it is not a statistically meaningful real-world accuracy estimate. Full per-case scores are in artifacts/matching_evaluation.json.

Add screenshots of the running app here:

1. The sample match shown when the app opens.
2. A report submitted with photos attached to both sides, showing the image similarity signal.
3. A return request after the private clue is accepted, showing that the request stays pending staff review.

## 8. Conclusion and future scope

The project demonstrates an AI-assisted workflow for finding possible matches from text and optional photos. The private clue and pending-review process makes casual false claims harder and prevents automatic release. The local demo does not provide authentication or secure shared hosting, so it cannot guarantee identity on its own. Future work could add verified campus accounts, protected database storage, audit logs, image embeddings from a trained vision model, multilingual text matching, and evaluation on confirmed reports. Staff should confirm ownership before returning belongings.
