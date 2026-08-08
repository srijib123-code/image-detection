# image-detection
for ciii
# Duplicate Image Detector

Detects **exact duplicates** (byte-identical files, via MD5) and **near-duplicates**
(visually similar but not identical — resized, recompressed, watermarked, slightly
cropped, etc., via perceptual hashing) among a set of uploaded images.

## How it works

1. **Upload** — each image is saved and three hashes are computed:
   - `MD5` — catches exact byte-for-byte duplicates.
   - `pHash` (perceptual hash) — the main similarity signal. It's robust to resizing,
     re-encoding, minor color/brightness changes.
   - `dHash` / `aHash` — computed and stored too, useful if you want to extend the
     grouping logic.
2. **Analyze** — every pair of images is compared:
   - If MD5 matches → exact duplicate.
   - Else if the Hamming distance between pHashes is under a threshold (adjustable
     via the slider, default 8 out of 64 bits) → near-duplicate.
   - Images are grouped with a union-find (disjoint set), so duplicate *clusters*
     (not just pairs) are detected correctly.
3. **Frontend** shows each cluster as a card (red badge = exact, yellow badge =
   near-duplicate with a similarity %), plus a section for images with no duplicates.

## Project structure

```
duplicate-image-detector/
├── backend/
│   ├── app.py            # Flask API
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

## Running it

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Runs on `http://localhost:5000`.

### 2. Frontend

No build step needed — it's plain HTML/CSS/JS. Just open `frontend/index.html`
in a browser, or serve it:

```bash
cd frontend
python -m http.server 8080
```

Then visit `http://localhost:8080`. (Opening the file directly also works since
the frontend talks to the backend via `http://localhost:5000` with CORS enabled.)

## API reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/upload` | multipart form, field `images` (multiple files) |
| GET | `/api/images` | list all uploaded images + hashes |
| GET | `/api/analyze?threshold=8` | run duplicate detection, return groups |
| GET | `/uploads/<filename>` | serves the stored image file |
| POST | `/api/reset` | clears all uploaded images |
| GET | `/api/health` | health check |

## Demo tips for judges

- Upload the **same image twice** → shows up as "Exact Duplicate" (100% similar).
- Upload the same image **resized or re-saved as a different format** → shows up
  as "Near Duplicate" with a high similarity % (pHash survives resize/recompression).
- Drag the **sensitivity slider** and re-run analyze to show how the threshold
  trades off precision vs. recall — good talking point for judges about the
  algorithm design.

## Ideas to extend (if you have extra time)

- Swap the in-memory list for SQLite so uploads persist across restarts.
- Add a "delete duplicate" button per thumbnail to actually clean up storage.
- Add CNN-embedding-based similarity (e.g. via a pretrained ResNet) for
  duplicates that are perceptually different but semantically the same image
  (different crop/angle) — perceptual hashing alone won't catch those.
- Add a progress bar for large batch uploads.
