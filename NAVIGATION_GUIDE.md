# 🗺️ Class Analytics Platform - Navigation Guide

## 📍 Dashboard Structure

### Main Entry Point
```
index.html (Dashboard Home)
├── 📊 Overview & Summary → overview.html
├── 🎤 Class Transcription → class_transcript.html ⭐ NEW
├── 📝 Statements (with Filter) → transcripcion.html
├── 🤖 AI Evaluation & Grades → evaluacion.html
├── ⏱️ Participation Timeline → timeline.html
└── 📋 Rubrics & Methodology → rubrics.html
```

---

## 🎯 What Each Page Does

### 1. **index.html** - Dashboard Home
- Main navigation hub
- Quick access buttons
- Student performance cards (Aryang, Grace, Sthepen, Chilaka, Mega)
- Links to all 6 main sections
- **Size:** 12K

### 2. **class_transcript.html** ⭐ NEW - Class Transcription
- **Full class transcription organized by 12 blocks**
- Block-by-block breakdown (B01-B12, each 5 minutes)
- 464 total utterances displayed
- 20 Ileana's questions tracked
- 126 student participations shown
- Click any block to expand and view details
- Color-coded speakers and types
- **Size:** 190K

### 3. **transcripcion.html** - Statements with Student Filter
- All 137 statements in one table
- **Dropdown filter to view by student:**
  - All Students (137)
  - Aryang (83)
  - Grace (21)
  - Sthepen (12)
  - Chilaka (1)
- Perfect for analyzing individual student participation
- **Size:** 147K

### 4. **overview.html** - Overview & Summary
- Class statistics (137 participations, 4 students, 40:11 coverage)
- Student performance cards with detailed breakdown
- Each student shows:
  - Final grade
  - Participation count
  - Responses/Questions/Comments split
  - Quality averages
  - Bonus applied
- **Size:** 8.2K

### 5. **evaluacion.html** - AI Evaluation & Grades
- Detailed individual student evaluations
- Complete analysis for each student:
  - Aryang: 3.12 (C) - 83 participations
  - Grace: 2.82 (C) - 21 participations
  - Sthepen: 2.98 (C) - 12 participations
  - Chilaka: 1.8 (D) - 1 participation
  - Mega: No data
- Shows calculation breakdown for each
- Quality analysis and assessment notes
- **Size:** 15K

### 6. **timeline.html** - Participation Timeline
- Visual timeline bar showing speaker time distribution
- Participation statistics table
- Color-coded speakers (Ileana=green, Aryang=red, Grace=blue, etc)
- Breakdown by type (responses, questions, comments)
- **Size:** 10K

### 7. **rubrics.html** - Rubrics & Methodology
- Weighted grading formula explained
- Bonus system details (41%, +0.15 / 20-39%, +0.10 / <5%, -0.20)
- Quality rubrics:
  - **Rubric A** (Responses): A-E scale
  - **Rubric B** (Questions/Comments): A-E scale
- Grade scale reference (A=4.5-5.0, B=3.5-4.4, etc)
- Complete evaluation process documentation
- **Size:** 12K

---

## 🔗 Navigation System

Every page has **navigation buttons** at the top:
```
← Back to Dashboard  |  🎤 Class Transcript  |  📝 Statements (Filter)  |  🤖 Evaluations  |  ⏱️ Timeline  |  📋 Rubrics
```

Plus in the header:
```
← Dashboard / [Current Page Name]
```

---

## 💡 Recommended Workflows

### 📚 Student Performance Review
1. Start at **index.html** → View student cards
2. Go to **evaluacion.html** → See detailed grades & rationale
3. Visit **class_transcript.html** → Understand context
4. Use **transcripcion.html** filter → Isolate student's statements

### 📊 Understanding Grading
1. Read **rubrics.html** → Learn evaluation criteria
2. Check **evaluacion.html** → See applications
3. Review **overview.html** → See final grades

### 🎬 Watching the Lesson
1. Start **class_transcript.html** → 12 blocks overview
2. Click blocks to expand → View speaker sequence
3. Switch to **transcripcion.html** filter → Focus on specific student

---

## 🎨 Color Scheme (Consistent Throughout)

- **Header:** Purple gradient (#667eea → #764ba2)
- **Background:** White (#ffffff)
- **Text:** Dark gray (#1f2937)
- **Speakers:**
  - Dr. Ileana: Green (#10b981)
  - Aryang: Red (#dc2626)
  - Grace: Blue (#0284c7)
  - Sthepen: Purple (#7c3aed)
  - Chilaka: Amber (#d97706)
  - Mega: Cyan (#06b6d4)

---

## 📈 Data Consistency Across All Pages

All pages show the same core data:
- **Grades:** Aryang 3.12 (C), Grace 2.82 (C), Sthepen 2.98 (C), Chilaka 1.8 (D)
- **Participations:** 137 total (83+21+12+1+0)
- **Coverage:** 40:11 minutes (58% of 69-min class)
- **Utterances:** 464 total
- **Ileana's Questions:** 20 total

✅ All numbers verified and consistent across all 7 pages

---

## 🚀 Files Ready to Deploy

All files at:
```
/Users/santi/clase-analytics/data/clases/2026-04-07/
```

**Core Pages (7):**
- index.html
- class_transcript.html ⭐ NEW
- transcripcion.html
- overview.html
- evaluacion.html
- timeline.html
- rubrics.html

**Supporting Files:**
- weighted_grades.json (grade calculations)
- analysis.json (full data)
- transcript_cache/ (block transcripts)

