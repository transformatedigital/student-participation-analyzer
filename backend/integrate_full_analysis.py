#!/usr/bin/env python3
"""
Integra el análisis completo de 60 minutos en el analysis.json
y actualiza la tabla HTML con todos los datos.
"""

import json
from pathlib import Path

def integrate_analysis():
    """Combine full blocks analysis with existing data"""

    # Load the new full analysis
    full_analysis_file = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/analysis_full_blocks.json")
    existing_analysis_file = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/analysis.json")

    if not full_analysis_file.exists():
        print("❌ Archivo de análisis completo no encontrado")
        return False

    with open(full_analysis_file, 'r') as f:
        full_data = json.load(f)

    with open(existing_analysis_file, 'r') as f:
        existing_data = json.load(f)

    # Merge data
    print("🔄 Integrando análisis completo...")

    # Update teacher questions
    existing_data['teacher_questions'] = full_data.get('teacher_questions', [])
    print(f"  ✓ {len(existing_data['teacher_questions'])} preguntas de profesora")

    # Update student contributions
    existing_data['student_contributions'] = full_data.get('student_contributions', [])
    print(f"  ✓ {len(existing_data['student_contributions'])} contribuciones de estudiantes")

    # Update per_student_summary
    per_student = {}

    # Profesora
    per_student['Dr. Ileana'] = {
        'questions_asked': len(existing_data['teacher_questions']),
        'responses_to_students': sum(1 for q in existing_data['teacher_questions']
                                     if q.get('student_response', {}).get('student') == 'Dr. Ileana'),
        'participation_segments': 342,
        'percentage': 85
    }

    # Students
    for student in ['Aryang', 'Grace']:
        responses = sum(1 for q in existing_data['teacher_questions']
                       if q.get('student_response', {}).get('student') == student)
        contributions = sum(1 for c in existing_data['student_contributions']
                           if c.get('student') == student)

        per_student[student] = {
            'responses_count': responses,
            'voluntary_contributions': contributions,
            'total_participations': responses + contributions,
            'quality_distribution': {}
        }

    existing_data['per_student_summary'] = per_student

    # Save updated analysis
    with open(existing_analysis_file, 'w') as f:
        json.dump(existing_data, f, indent=2)

    print(f"✅ Análisis integrado en analysis.json")
    return True

def generate_html_table():
    """Generate updated HTML table with all participations"""

    analysis_file = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/analysis.json")
    html_file = Path("/Users/santi/clase-analytics/data/clases/2026-04-07/Case_7_de_abril.html")

    with open(analysis_file, 'r') as f:
        data = json.load(f)

    # Combine participations
    rows = []

    # Add teacher questions
    for q in data.get('teacher_questions', []):
        resp = q.get('student_response', {})
        rows.append({
            'id': q.get('id', 0),
            'timestamp': q.get('timestamp', ''),
            'nombre': resp.get('student', ''),
            'tipo': 'response',
            'contenido': resp.get('response', ''),
            'ai': resp.get('quality_score', ''),
            'manual': ''
        })

    # Add student contributions
    for c in data.get('student_contributions', []):
        rows.append({
            'id': c.get('id', 0),
            'timestamp': c.get('timestamp', ''),
            'nombre': c.get('student', ''),
            'tipo': 'contribution',
            'contenido': c.get('content', ''),
            'ai': c.get('quality_score', ''),
            'manual': ''
        })

    # Sort by timestamp
    def parse_time(ts):
        try:
            p = ts.split(':')
            return int(p[0]) * 60 + int(p[1])
        except:
            return 0

    rows.sort(key=lambda x: parse_time(x['timestamp']))

    # Generate HTML
    rows_json = json.dumps(rows)

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clase del 7 de Abril (60 min) - Análisis de Participación</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; color: #333; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; margin-bottom: 10px; font-size: 28px; }}
        .metadata {{ background: #f0f8ff; padding: 15px; border-left: 4px solid #2196F3; margin-bottom: 20px; border-radius: 4px; }}
        .metadata p {{ margin: 5px 0; font-size: 14px; }}
        .controls {{ display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; align-items: center; }}
        button {{ padding: 10px 20px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; transition: background 0.3s; }}
        button:hover {{ background: #1976D2; }}
        button.export {{ background: #4CAF50; }}
        button.export:hover {{ background: #45a049; }}
        .search-box {{ flex: 1; min-width: 250px; }}
        .search-box input {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }}
        .table-wrapper {{ overflow-x: auto; border: 1px solid #ddd; border-radius: 4px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        thead {{ background: #2c3e50; color: white; position: sticky; top: 0; }}
        th {{ padding: 15px; text-align: left; font-weight: 600; border-right: 1px solid #34495e; }}
        th:last-child {{ border-right: none; }}
        td {{ padding: 12px 15px; border-bottom: 1px solid #eee; }}
        tbody tr:hover {{ background: #f9f9f9; }}
        tbody tr.response {{ background: #fffbea; }}
        tbody tr.contribution {{ background: #f0f8ff; }}
        .timestamp {{ font-family: monospace; color: #666; font-size: 13px; font-weight: 500; }}
        .student-name {{ font-weight: 600; color: #2c3e50; white-space: nowrap; }}
        .content {{ font-size: 13px; line-height: 1.5; max-height: 150px; overflow-y: auto; color: #555; }}
        .quality-badge {{ display: inline-block; padding: 4px 8px; border-radius: 3px; font-weight: 600; text-align: center; min-width: 40px; font-size: 12px; color: white; }}
        .quality-a {{ background: #4CAF50; }}
        .quality-b {{ background: #2196F3; }}
        .quality-c {{ background: #FF9800; }}
        .quality-d {{ background: #FF5722; }}
        .quality-e {{ background: #f44336; }}
        .quality-empty {{ background: #ccc; }}
        .manual-input {{ width: 50px; padding: 6px; border: 1px solid #ddd; border-radius: 3px; text-align: center; font-weight: 600; font-size: 14px; text-transform: uppercase; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 13px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 4px; text-align: center; }}
        .stat-card.questions {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .stat-card.contributions {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
        .stat-number {{ font-size: 32px; font-weight: bold; margin: 10px 0; }}
        .stat-label {{ font-size: 13px; opacity: 0.9; }}
        .alert {{ background: #fff3cd; border: 1px solid #ffc107; padding: 12px; border-radius: 4px; margin-bottom: 15px; color: #856404; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Análisis de Participación (60 Minutos Completos)</h1>

        <div class="alert">
            <strong>✨ NOVEDAD:</strong> Análisis ahora incluye los 60 minutos completos de la clase usando bloques de 10 minutos procesados con Google Gemini AI
        </div>

        <div class="metadata">
            <p><strong>Fecha:</strong> 7 de Abril de 2026</p>
            <p><strong>Instructor:</strong> Dra. Ileana</p>
            <p><strong>Duración:</strong> 69 minutos 24 segundos</p>
            <p><strong>Participantes:</strong> Dra. Ileana (Instructora), Aryang (Indonesia), Grace (Congo)</p>
        </div>

        <div class="stats">
            <div class="stat-card questions">
                <div class="stat-label">Preguntas de Profesora</div>
                <div class="stat-number" id="totalQuestions">{len(data.get('teacher_questions', []))}</div>
            </div>
            <div class="stat-card contributions">
                <div class="stat-label">Contribuciones de Estudiantes</div>
                <div class="stat-number" id="totalContributions">{len(data.get('student_contributions', []))}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total de Participaciones</div>
                <div class="stat-number" id="totalRows">{len(rows)}</div>
            </div>
        </div>

        <div class="controls">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="🔍 Buscar por nombre, contenido o timestamp...">
            </div>
            <button class="export" onclick="exportToCSV()">📥 Descargar CSV</button>
        </div>

        <div class="table-wrapper">
            <table id="dataTable">
                <thead>
                    <tr>
                        <th style="width: 50px;">#</th>
                        <th style="width: 100px;">Timestamp</th>
                        <th style="width: 120px;">Nombre</th>
                        <th>Comentario o Pregunta</th>
                        <th style="width: 80px; text-align: center;">Calificación AI</th>
                        <th style="width: 100px; text-align: center;">Calificación Manual</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p><strong>Escala:</strong> A (Excelente) | B (Bueno) | C (Satisfactorio) | D (Insuficiente) | E (Deficiente)</p>
            <p style="margin-top: 10px; opacity: 0.7;">Generado automáticamente | Análisis completo de 60 minutos | Google Gemini API</p>
        </div>
    </div>

    <script>
        const participations = {rows_json};

        function renderTable(data = participations) {{
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';

            data.forEach((row, idx) => {{
                const tr = document.createElement('tr');
                tr.className = row.tipo;

                const qualityClass = row.ai ? `quality-${{row.ai.toLowerCase()}}` : 'quality-empty';
                const aiText = row.ai || '—';

                tr.innerHTML = `
                    <td>${{idx + 1}}</td>
                    <td class="timestamp">${{row.timestamp}}</td>
                    <td class="student-name">${{row.nombre}}</td>
                    <td class="content">${{escapeHtml(row.contenido)}}</td>
                    <td style="text-align: center;">
                        <span class="quality-badge ${{qualityClass}}">${{aiText}}</span>
                    </td>
                    <td style="text-align: center;">
                        <input type="text" class="manual-input" maxlength="1"
                            value="${{row.manual}}"
                            placeholder="A-E">
                    </td>
                `;
                tbody.appendChild(tr);
            }});

            document.getElementById('totalRows').textContent = data.length;
        }}

        function escapeHtml(text) {{
            const map = {{'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'}};
            return text.replace(/[&<>"']/g, m => map[m]);
        }}

        function exportToCSV() {{
            const rows = [];
            rows.push('Timestamp,Nombre,Comentario o Pregunta,Calificación AI,Calificación Manual');

            document.querySelectorAll('#tableBody tr').forEach(tr => {{
                const cells = tr.querySelectorAll('td');
                const timestamp = cells[1].textContent.trim();
                const nombre = cells[2].textContent.trim();
                const contenido = cells[3].textContent.trim().replace(/"/g, '""');
                const ai = cells[4].textContent.trim();
                const manual = cells[5].querySelector('input').value.trim();

                rows.push(`${{timestamp}},"${{nombre}}","${{contenido}}",${{ai}},${{manual}}`);
            }});

            const csv = rows.join('\\n');
            const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `participacion-2026-04-07-completo.csv`);
            link.click();
        }}

        function setupSearch() {{
            const searchInput = document.getElementById('searchInput');
            searchInput.addEventListener('input', (e) => {{
                const query = e.target.value.toLowerCase();
                if (!query) {{
                    renderTable(participations);
                    return;
                }}

                const filtered = participations.filter(row =>
                    row.timestamp.includes(query) ||
                    row.nombre.toLowerCase().includes(query) ||
                    row.contenido.toLowerCase().includes(query)
                );
                renderTable(filtered);
            }});
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            renderTable();
            setupSearch();
        }});
    </script>
</body>
</html>
'''

    with open(html_file, 'w') as f:
        f.write(html)

    print(f"✅ HTML actualizado con {len(rows)} participaciones")
    return True

if __name__ == '__main__':
    print("🔄 Integrando análisis completo...\n")

    if integrate_analysis():
        if generate_html_table():
            print("\n✅ ¡Integración completada exitosamente!")
            print("\nArchivos actualizados:")
            print("  - analysis.json")
            print("  - Case_7_de_abril.html")
        else:
            print("\n⚠️  Error generando HTML")
    else:
        print("\n❌ Error en integración")
