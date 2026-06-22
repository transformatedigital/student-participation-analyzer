# GDI.60030 — Next Semester Guide (V2 · Fall 2026)

This guide explains how to run the grading platform for the **next semester** using the
data-driven dashboard **`docs/dashboard-v2.html`** and a **Google Sheet** as the single
source of truth. The Spring 2026 dashboard (`docs/dashboard.html`) stays untouched as the archive.

- **Live page:** `https://transformatedigital.github.io/student-participation-analyzer/dashboard-v2.html`
- **Period:** Fall 2026 (Sep–Dec), Tuesdays, class time **TBD**
- **Roster placeholders:** `Alumni1 … Alumni10` (rename freely via the `Name` column in the Sheet)

---

## 1. One-time setup — connect the Google Sheet

1. Open the template: `docs/GDI60030_V2_Fall2026_GradingSheet_TEMPLATE.xlsx`.
2. Upload it to Google Drive and **Open with → Google Sheets** (or recreate the tabs manually).
3. **Share → General access → "Anyone with the link" → Viewer.**
4. Copy the link. Open `dashboard-v2.html`, paste the link into the **🔗 Google Sheet** bar at the top, press **Load**.
   - The link is remembered in your browser (localStorage). Press **↻ Refresh** any time to pull the latest edits.

> The page reads the Sheet through Google's public `gviz` JSON endpoint. No server is needed — it works on plain GitHub Pages. Google caches sheet reads for up to ~1 minute, so edits can take a moment to appear; press **Refresh**.

### Sheet structure — ONE general table `Grades` (one row per student, fill across)
The page reads a single tab named **`Grades`** (and falls back to the first sheet if a CSV import named it differently). Header row (do not rename):

| Group | Columns | Meaning |
|-------|---------|---------|
| Identity | `Student`, `Name` | `Student` = stable key (Alumni1…). `Name` = real display name (e.g. Cesar Fonseca). |
| **A** (20%) | `A1_prep` (/7.5), `A2_part` (/7.5), `A3_att` (/5), `A_adjust` | A_total = A1+A2+A3 + bonus. A1/A2/A3 come from the audio pipeline or are typed manually. |
| **B** (25%) | `B1_q1..B1_q3` (/100), `B2` (/10), `Team` | Pop-up quizzes + team score + team label. |
| **C** (20%) | `C1_1`, `C1_2`, `C2_v1..C2_v4` (/100) | Assignments + ICP V1–V4. |
| **D** (15%) | `D_format,D_ref,D_problem,D_root,D_logical` (0–3), `D_ai_appendix` (5/0/−5), `D_override` (optional /100) | D1 rubric + AI appendix; override wins if set. |
| **E** (20%) | `E_format,E_ref,E_problem,E_root,E_logical` (0–4) | E1 pitch rubric. |

Optional second tab **`Attendance`**: `Student`, `W1..W16` (Tuesdays Sep 1 – Dec 15 2026; `1` = present, blank = absent).

**Grade math (computed in the page):** Final = A(/20) + B(/25) + C(/20) + D(/15) + E(/20) = /100.
**KAIST scale:** A+ 95–100 → adjusted to A0 (no A+ awarded) · A0 90–95 · A- 85–90 · B+ 80–85 · B0 75–80 …

---

## 2. Component A from class audio (per class)

Component A (Preparation 7.5 + Participation 7.5 + Attendance 5 = /20) is produced by the existing
AI pipeline. Requires `GEMINI_API_KEY` set in the environment.

```bash
# 1) Process one class (audio → transcript → Component A)
python3 backend/process_class.py /path/to/class_audio.m4a 2026-09-01

# 2) Re-aggregate across all classes of the semester
python3 backend/aggregate_all.py
```

This writes `data/clases/2026-09-01/component_a.json` and updates `docs/all_classes.json` /
`docs/Component_A_Aggregated.xlsx` with each student's **A total (/20)**.

**Then:** copy each student's A total into the `ComponentA → A_total` column of the Google Sheet
(and set `A_adjust` if you grant a participation bonus). Press **Refresh** in the page.

### Roster for the pipeline
If you run the audio pipeline, set the student names in these three constants so the transcript
speaker labels match your roster (replace the Spring names with `Alumni1..Alumni10`, or the real names):

- `backend/process_class.py` → `DEFAULT_STUDENTS`
- `backend/build_component_a.py` → `STUDENTS`
- `backend/aggregate_all.py` → `STUDENTS`

> Use the **same key** in the Sheet's `Student` column as the page expects (`Alumni1`…). Put real
> names only in the `Name` column so they show up without breaking the data mapping.

---

## 3. Components B–E (manual via the Sheet)

Just type the scores into the matching tab. The page recomputes weighted contributions, the /100
total, and the KAIST letter on **Refresh**. Cells stay **Pending (—)** until their inputs exist.

- **B2 Team Discussion** is a team score: give every member of a team the same `B2` value.
- **D AI Appendix:** `+5` if the ICP v.6 includes the AI-use appendix/statement, `−5` if missing, `0` to ignore.
- **D override:** if you want to set D's /100 directly (e.g. a manual adjustment), fill `D_override`.

---

## 4. Attendance calendar

The 16 Tuesdays of Fall 2026 are pre-loaded (`Sep 1, 8, 15, 22, 29 · Oct 6, 13, 20, 27 · Nov 3, 10, 17, 24 · Dec 1, 8, 15`).
Korean holidays (Chuseok Sep 24–26, National Foundation Day Oct 3, Hangeul Day Oct 9) do **not** fall on a
Tuesday, so no class day is cancelled. Final exams: mid-December. Mark attendance in the `Attendance` tab (`W1..W16`).

---

## 5. Publishing

`dashboard-v2.html` and the template live under `docs/`, which is served by GitHub Pages.
Commit and push to `main`; the new page is live at the URL above within ~1 minute.
The teacher only edits the Google Sheet afterward — no code changes or redeploys needed.

---

## 6. Notes & limits
- **Privacy:** "Anyone with the link: Viewer" means anyone with the link can read the Sheet (not indexed, but not private). For real privacy, switch to a Google Apps Script endpoint with a token (future enhancement).
- **Caching:** Google may serve a cached read for up to ~1 minute; press **Refresh**.
- **Validation:** the page's grade math was regression-tested against the Spring 2026 results (e.g. Arya = 94.36 → A0) and matches exactly.
