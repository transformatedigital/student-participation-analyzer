#!/usr/bin/env python3
"""
Script to update the exam rendering function to support both formats:
- Format 1 (Exam 1): n_questions + questions[] + answers[]
- Format 2 (Exam 2): n_sections + sections[] + s1_responses[], s2_responses[], etc.
"""

import re

# Read the dashboard file
with open('docs/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the rendering logic for exams
# The current code is between lines ~921-969

old_rendering_code = r'''  // ── Lista de exámenes ──
  let listHtml = '';
  C\.exams\.forEach\(\(exam, idx\) => \{
    const examMax = exam\.n_questions \? exam\.n_questions \* exam\.max_per_question : 100;
    const isCompleted = exam\.status === 'completed';
    const statusBadge = isCompleted
      \? '<span class="status-pill status-rec">✅ Completed</span>'
      : '<span class="status-pill status-pending">⏳ Pending</span>';

    listHtml \+= `<div class="exam-card">
      <h3 class="exam-header collapsible-header" onclick="toggleSection\('exam\$\{exam\.id\}Content', 'exam\$\{exam\.id\}Toggle'\)">
        <span><strong>\$\{exam\.title\}</strong> · \$\{exam\.date_label\} \$\{statusBadge\}</span>
        <span class="toggle-icon" id="exam\$\{exam\.id\}Toggle">▶</span>
      </h3>
      <div id="exam\$\{exam\.id\}Content" class="exam-content" style="display:none;">`;

    if \(\!isCompleted\) \{
      listHtml \+= `<p style="padding:24px; text-align:center; color:#94a3b8; font-style:italic;">
        This exam has not been administered yet\. Once it's done, scores will appear here\.
      </p>`;
    \} else \{
      // Por cada estudiante, mostrar sus respuestas \+ scores
      studentsList\.forEach\(s => \{
        const r = exam\.responses\[s\];
        if \(\!r\) return;
        const totalScore = r\.scores\.reduce\(\(a, b\) => a \+ b, 0\);
        listHtml \+= `<div class="student-block">
          <h4 class="student-header collapsible-header" onclick="toggleSection\('exam\$\{exam\.id\}-\$\{s\}-content', 'exam\$\{exam\.id\}-\$\{s\}-toggle'\)">
            <span>👤 <strong>\$\{s\}</strong> <small style="color:#64748b">\(\$\{r\.full_name\}\)</small> — Total: <strong style="color:#305496">\$\{totalScore\}/\$\{examMax\}</strong></span>
            <span class="toggle-icon" id="exam\$\{exam\.id\}-\$\{s\}-toggle">▶</span>
          </h4>
          <div id="exam\$\{exam\.id\}-\$\{s\}-content" class="student-answers" style="display:none;">`;
        r\.answers\.forEach\(\(ans, qi\) => \{
          const q = exam\.questions\[qi\];
          const score = r\.scores\[qi\];
          listHtml \+= `<div class="answer-block">
            <div class="question-text"><strong>\$\{q\}</strong></div>
            <div class="answer-text">\$\{ans \|\| '<em style="color:#94a3b8">\(No answer\)</em>'\}</div>
            <div class="answer-score">
              <label>Score:</label>
              <input type="number" min="0" max="\$\{exam\.max_per_question\}" value="\$\{score\}" class="score-input" disabled>
              <span class="score-max">/ \$\{exam\.max_per_question\}</span>
            </div>
          </div>`;
        \}\);
        listHtml \+= `</div></div>`;
      \}\);
    \}
    listHtml \+= `</div></div>`;
  \}\);
  document\.getElementById\('c1ExamsList'\)\.innerHTML = listHtml;'''

new_rendering_code = '''  // ── Lista de exámenes ──
  let listHtml = '';
  C.exams.forEach((exam, idx) => {
    const examMax = exam.n_questions ? exam.n_questions * exam.max_per_question : 100;
    const isCompleted = exam.status === 'completed' || exam.status === 'grading';
    const isPending = exam.status === 'pending';
    const isGrading = exam.status === 'grading';

    let statusBadge = '';
    if (exam.status === 'completed') {
      statusBadge = '<span class="status-pill status-rec">✅ Completed</span>';
    } else if (exam.status === 'grading') {
      statusBadge = '<span class="status-pill" style="background:#fef3c7; color:#92400e;">📝 Grading</span>';
    } else {
      statusBadge = '<span class="status-pill status-pending">⏳ Pending</span>';
    }

    listHtml += `<div class="exam-card">
      <h3 class="exam-header collapsible-header" onclick="toggleSection('exam${exam.id}Content', 'exam${exam.id}Toggle')">
        <span><strong>${exam.title}</strong> · ${exam.date_label} ${statusBadge}</span>
        <span class="toggle-icon" id="exam${exam.id}Toggle">▶</span>
      </h3>
      <div id="exam${exam.id}Content" class="exam-content" style="display:none;">`;

    if (isPending) {
      listHtml += `<p style="padding:24px; text-align:center; color:#94a3b8; font-style:italic;">
        This exam has not been administered yet. Once it's done, scores will appear here.
      </p>`;
    } else {
      // Mostrar respuestas para completed o grading
      studentsList.forEach(s => {
        const r = exam.responses[s];
        if (!r) return;

        // Calculate total score (handle null scores)
        const totalScore = r.scores.reduce((a, b) => a + (b || 0), 0);
        const hasScores = r.scores.some(score => score !== null && score !== undefined);
        const scoreDisplay = hasScores ? `${totalScore}/${examMax}` : '— (pending)';

        listHtml += `<div class="student-block">
          <h4 class="student-header collapsible-header" onclick="toggleSection('exam${exam.id}-${s}-content', 'exam${exam.id}-${s}-toggle')">
            <span>👤 <strong>${s}</strong> <small style="color:#64748b">(${r.full_name})</small> — Total: <strong style="color:#305496">${scoreDisplay}</strong></span>
            <span class="toggle-icon" id="exam${exam.id}-${s}-toggle">▶</span>
          </h4>
          <div id="exam${exam.id}-${s}-content" class="student-answers" style="display:none;">`;

        // Check if this is a section-based exam (like Exam 2) or question-based (like Exam 1)
        if (exam.sections && exam.n_sections) {
          // Format 2: Section-based exam (Exam 2)
          exam.sections.forEach((section, si) => {
            const sectionKey = `s${si + 1}_responses`;
            const responses = r[sectionKey] || [];
            const score = r.scores[si];
            const maxScore = section.max_score;

            listHtml += `<div class="answer-block">
              <div class="question-text"><strong>${section.id}: ${section.name}</strong> <small style="color:#64748b">(Max: ${maxScore} pts)</small></div>`;

            // Show subsections if they exist
            if (section.subsections && section.subsections.length > 0) {
              section.subsections.forEach((subsec, ssi) => {
                const response = responses[ssi] || '<em style="color:#94a3b8">(No response)</em>';
                listHtml += `<div style="margin:12px 0 12px 16px; padding-left:12px; border-left:2px solid #e2e8f0;">
                  <div style="font-size:13px; color:#64748b; margin-bottom:4px;"><strong>${subsec}</strong></div>
                  <div class="answer-text">${response}</div>
                </div>`;
              });
            } else {
              // No subsections, just show all responses
              responses.forEach((resp, ri) => {
                listHtml += `<div class="answer-text" style="margin:8px 0;">${resp || '<em style="color:#94a3b8">(No response)</em>'}</div>`;
              });
            }

            listHtml += `<div class="answer-score">
              <label>Score:</label>
              <input type="number" min="0" max="${maxScore}" value="${score !== null ? score : ''}"
                     class="score-input" placeholder="—" ${hasScores ? 'disabled' : ''}>
              <span class="score-max">/ ${maxScore}</span>
            </div>
          </div>`;
          });
        } else {
          // Format 1: Question-based exam (Exam 1)
          r.answers.forEach((ans, qi) => {
            const q = exam.questions[qi];
            const score = r.scores[qi];
            listHtml += `<div class="answer-block">
              <div class="question-text"><strong>${q}</strong></div>
              <div class="answer-text">${ans || '<em style="color:#94a3b8">(No answer)</em>'}</div>
              <div class="answer-score">
                <label>Score:</label>
                <input type="number" min="0" max="${exam.max_per_question}" value="${score}" class="score-input" disabled>
                <span class="score-max">/ ${exam.max_per_question}</span>
              </div>
            </div>`;
          });
        }

        listHtml += `</div></div>`;
      });

      if (isGrading) {
        listHtml += `<p style="padding:16px; margin-top:16px; background:#fef3c7; border-radius:8px; color:#92400e; font-size:13px;">
          ⚠️ <strong>Scores pending:</strong> Professor needs to add scores for each section.
        </p>`;
      }
    }
    listHtml += `</div></div>`;
  });
  document.getElementById('c1ExamsList').innerHTML = listHtml;'''

# Replace the code (need to escape special regex characters carefully)
# Using a simpler approach: find the function and replace specific parts

# First, let's find the exact location and do targeted replacements
content = content.replace(
    "const isCompleted = exam.status === 'completed';",
    "const isCompleted = exam.status === 'completed' || exam.status === 'grading';\n    const isPending = exam.status === 'pending';\n    const isGrading = exam.status === 'grading';"
)

content = content.replace(
    '''const statusBadge = isCompleted
      ? '<span class="status-pill status-rec">✅ Completed</span>'
      : '<span class="status-pill status-pending">⏳ Pending</span>';''',
    '''let statusBadge = '';
    if (exam.status === 'completed') {
      statusBadge = '<span class="status-pill status-rec">✅ Completed</span>';
    } else if (exam.status === 'grading') {
      statusBadge = '<span class="status-pill" style="background:#fef3c7; color:#92400e;">📝 Grading</span>';
    } else {
      statusBadge = '<span class="status-pill status-pending">⏳ Pending</span>';
    }'''
)

content = content.replace(
    "if (!isCompleted) {",
    "if (isPending) {"
)

# Replace the student rendering section
old_student_section = '''      // Por cada estudiante, mostrar sus respuestas + scores
      studentsList.forEach(s => {
        const r = exam.responses[s];
        if (!r) return;
        const totalScore = r.scores.reduce((a, b) => a + b, 0);
        listHtml += `<div class="student-block">
          <h4 class="student-header collapsible-header" onclick="toggleSection('exam${exam.id}-${s}-content', 'exam${exam.id}-${s}-toggle')">
            <span>👤 <strong>${s}</strong> <small style="color:#64748b">(${r.full_name})</small> — Total: <strong style="color:#305496">${totalScore}/${examMax}</strong></span>
            <span class="toggle-icon" id="exam${exam.id}-${s}-toggle">▶</span>
          </h4>
          <div id="exam${exam.id}-${s}-content" class="student-answers" style="display:none;">`;
        r.answers.forEach((ans, qi) => {
          const q = exam.questions[qi];
          const score = r.scores[qi];
          listHtml += `<div class="answer-block">
            <div class="question-text"><strong>${q}</strong></div>
            <div class="answer-text">${ans || '<em style="color:#94a3b8">(No answer)</em>'}</div>
            <div class="answer-score">
              <label>Score:</label>
              <input type="number" min="0" max="${exam.max_per_question}" value="${score}" class="score-input" disabled>
              <span class="score-max">/ ${exam.max_per_question}</span>
            </div>
          </div>`;
        });
        listHtml += `</div></div>`;
      });
    }'''

new_student_section = '''      // Mostrar respuestas para completed o grading
      studentsList.forEach(s => {
        const r = exam.responses[s];
        if (!r) return;

        // Calculate total score (handle null scores)
        const totalScore = r.scores.reduce((a, b) => a + (b || 0), 0);
        const hasScores = r.scores.some(score => score !== null && score !== undefined);
        const scoreDisplay = hasScores ? `${totalScore}/${examMax}` : '— (pending)';

        listHtml += `<div class="student-block">
          <h4 class="student-header collapsible-header" onclick="toggleSection('exam${exam.id}-${s}-content', 'exam${exam.id}-${s}-toggle')">
            <span>👤 <strong>${s}</strong> <small style="color:#64748b">(${r.full_name})</small> — Total: <strong style="color:#305496">${scoreDisplay}</strong></span>
            <span class="toggle-icon" id="exam${exam.id}-${s}-toggle">▶</span>
          </h4>
          <div id="exam${exam.id}-${s}-content" class="student-answers" style="display:none;">`;

        // Check if this is a section-based exam (like Exam 2) or question-based (like Exam 1)
        if (exam.sections && exam.n_sections) {
          // Format 2: Section-based exam (Exam 2)
          exam.sections.forEach((section, si) => {
            const sectionKey = `s${si + 1}_responses`;
            const responses = r[sectionKey] || [];
            const score = r.scores[si];
            const maxScore = section.max_score;

            listHtml += `<div class="answer-block">
              <div class="question-text"><strong>${section.id}: ${section.name}</strong> <small style="color:#64748b">(Max: ${maxScore} pts)</small></div>`;

            // Show subsections if they exist
            if (section.subsections && section.subsections.length > 0) {
              section.subsections.forEach((subsec, ssi) => {
                const response = responses[ssi] || '<em style="color:#94a3b8">(No response)</em>';
                listHtml += `<div style="margin:12px 0 12px 16px; padding-left:12px; border-left:2px solid #e2e8f0;">
                  <div style="font-size:13px; color:#64748b; margin-bottom:4px;"><strong>${subsec}</strong></div>
                  <div class="answer-text">${response}</div>
                </div>`;
              });
            } else {
              // No subsections, just show all responses
              responses.forEach((resp, ri) => {
                listHtml += `<div class="answer-text" style="margin:8px 0;">${resp || '<em style="color:#94a3b8">(No response)</em>'}</div>`;
              });
            }

            listHtml += `<div class="answer-score">
              <label>Score:</label>
              <input type="number" min="0" max="${maxScore}" value="${score !== null ? score : ''}"
                     class="score-input" placeholder="—" ${hasScores ? 'disabled' : ''}>
              <span class="score-max">/ ${maxScore}</span>
            </div>
          </div>`;
          });
        } else {
          // Format 1: Question-based exam (Exam 1)
          r.answers.forEach((ans, qi) => {
            const q = exam.questions[qi];
            const score = r.scores[qi];
            listHtml += `<div class="answer-block">
              <div class="question-text"><strong>${q}</strong></div>
              <div class="answer-text">${ans || '<em style="color:#94a3b8">(No answer)</em>'}</div>
              <div class="answer-score">
                <label>Score:</label>
                <input type="number" min="0" max="${exam.max_per_question}" value="${score}" class="score-input" disabled>
                <span class="score-max">/ ${exam.max_per_question}</span>
              </div>
            </div>`;
          });
        }

        listHtml += `</div></div>`;
      });

      if (isGrading) {
        listHtml += `<p style="padding:16px; margin-top:16px; background:#fef3c7; border-radius:8px; color:#92400e; font-size:13px;">
          ⚠️ <strong>Scores pending:</strong> Professor needs to add scores for each section.
        </p>`;
      }
    }'''

content = content.replace(old_student_section, new_student_section)

# Write back
with open('docs/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Exam rendering function updated successfully!")
print("📊 Dashboard now supports:")
print("   - Format 1: Question-based exams (4 questions × 25 pts)")
print("   - Format 2: Section-based exams (6 sections with variable points)")
print("   - Status 'grading': Shows responses with empty score inputs")
print("   - Status 'completed': Shows responses with filled scores (disabled)")
print("   - Status 'pending': Shows 'not administered yet' message")
