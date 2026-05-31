'use client'

import { getApiUrl } from '@/lib/api'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'

interface Row {
  timestamp: string
  nombre: string
  contenido: string
  ai: string
  manual: string
  id: number
  tipo?: string
  pregunta?: string
}

export default function ParticipacionPage() {
  const params = useParams()
  const sessionId = params?.sessionId as string
  const [rows, setRows] = useState<Row[]>([])
  const [manualCalifs, setManualCalifs] = useState<Record<number, string>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(getApiUrl(`/api/clases/${sessionId}/participacion`))
        const data = await res.json()

        const allRows: Row[] = []
        let id = 0

        // Agregar respuestas a preguntas
        (data.teacher_questions || []).forEach((q: any) => {
          if (q.student_response) {
            allRows.push({
              timestamp: q.timestamp || q.timestamp_start || '',
              nombre: q.student_response.student,
              contenido: q.student_response.response,
              ai: q.student_response.quality_score || '',
              manual: '',
              id: id++
            })
          }
        })

        // Agregar contribuciones voluntarias
        (data.student_contributions || []).forEach((c: any) => {
          allRows.push({
            timestamp: c.timestamp || c.timestamp_start || '',
            nombre: c.student,
            contenido: c.content,
            ai: c.quality_score || '',
            manual: '',
            id: id++
          })
        })

        // Ordenar por timestamp
        allRows.sort((a, b) => a.timestamp.localeCompare(b.timestamp))

        setRows(allRows)
      } catch (err) {
        console.error('Error:', err)
      } finally {
        setLoading(false)
      }
    }

    if (sessionId) fetchData()
  }, [sessionId])

  const exportCSV = () => {
    const headers = 'Timestamp,Nombre,Comentario o Pregunta,Calificación AI,Calificación Manual'
    const lines = rows.map(r => {
      const content = `"${r.contenido.replace(/"/g, '""')}"`
      return `${r.timestamp},${r.nombre},${content},${r.ai},${manualCalifs[r.id] || ''}`
    })

    const csv = [headers, ...lines].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `participacion-${sessionId}.csv`)
    link.click()
  }

  if (loading) return <div className="p-8">Cargando...</div>

  const statsData = {
    totalParticipations: rows.length,
    teacherQuestions: rows.filter(r => r.tipo === 'question_response').length,
    studentContributions: rows.filter(r => r.tipo === 'contribution').length,
    uniqueStudents: new Set(rows.filter(r => r.nombre !== 'Dr. Ileana').map(r => r.nombre)).size,
  }

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-2 text-gray-800">📊 Análisis de Participación</h1>
        <p className="text-gray-600 mb-6">Seminario de Posgrado - 7 de Abril de 2026</p>

        {/* Statistics Cards */}
        {rows.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
              <div className="text-sm text-gray-600">Total Participaciones</div>
              <div className="text-2xl font-bold text-gray-800">{statsData.totalParticipations}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border-l-4 border-purple-500">
              <div className="text-sm text-gray-600">Preguntas</div>
              <div className="text-2xl font-bold text-gray-800">{statsData.teacherQuestions}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border-l-4 border-cyan-500">
              <div className="text-sm text-gray-600">Contribuciones</div>
              <div className="text-2xl font-bold text-gray-800">{statsData.studentContributions}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border-l-4 border-green-500">
              <div className="text-sm text-gray-600">Estudiantes</div>
              <div className="text-2xl font-bold text-gray-800">{statsData.uniqueStudents}</div>
            </div>
          </div>
        )}

        {rows.length > 0 && (
          <button
            onClick={exportCSV}
            className="mb-6 px-6 py-3 bg-green-600 text-white font-bold rounded-lg hover:bg-green-700 transition"
          >
            📥 Descargar CSV
          </button>
        )}

      {rows.length > 0 ? (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-800 text-white">
                  <th className="px-4 py-3 text-left text-sm font-semibold w-20">#</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold w-24">Timestamp</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold w-32">Nombre</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">Comentario o Pregunta</th>
                  <th className="px-4 py-3 text-center text-sm font-semibold w-20">Calificación AI</th>
                  <th className="px-4 py-3 text-center text-sm font-semibold w-28">Calificación Manual</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, idx) => {
                  const qualityColor = {
                    'A': 'bg-green-100 text-green-800 font-bold',
                    'B': 'bg-blue-100 text-blue-800 font-bold',
                    'C': 'bg-amber-100 text-amber-800 font-bold',
                    'D': 'bg-orange-100 text-orange-800 font-bold',
                    'E': 'bg-red-100 text-red-800 font-bold',
                  }[row.ai] || 'bg-gray-100 text-gray-800'

                  const rowBg = row.nombre === 'Dr. Ileana' ? 'bg-yellow-50' : 'bg-blue-50'

                  return (
                    <tr key={row.id} className={`${rowBg} border-b border-gray-200 hover:bg-opacity-75 transition`}>
                      <td className="px-4 py-3 text-sm text-gray-600 font-mono">{idx + 1}</td>
                      <td className="px-4 py-3 text-sm text-gray-700 font-mono">{row.timestamp}</td>
                      <td className="px-4 py-3 text-sm font-semibold text-gray-900">{row.nombre}</td>
                      <td className="px-4 py-3 text-sm text-gray-700 max-w-2xl truncate">{row.contenido}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-block px-3 py-1 rounded text-sm ${qualityColor}`}>
                          {row.ai || '—'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <input
                          type="text"
                          maxLength={1}
                          value={manualCalifs[row.id] || ''}
                          onChange={(e) =>
                            setManualCalifs({ ...manualCalifs, [row.id]: e.target.value.toUpperCase() })
                          }
                          placeholder="A-E"
                          className="w-16 px-2 py-2 border border-gray-300 rounded text-center font-bold text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <p className="text-gray-500">No hay participaciones</p>
      )}

      {rows.length > 0 && (
        <div className="mt-8 space-y-4">
          <div className="bg-blue-50 border-l-4 border-blue-500 p-6 rounded">
            <h3 className="font-semibold text-gray-800 mb-2">📋 Escala de Calificación</h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
              <div><span className="inline-block bg-green-100 px-3 py-1 rounded font-bold text-green-800">A</span> Excelente</div>
              <div><span className="inline-block bg-blue-100 px-3 py-1 rounded font-bold text-blue-800">B</span> Bueno</div>
              <div><span className="inline-block bg-amber-100 px-3 py-1 rounded font-bold text-amber-800">C</span> Satisfactorio</div>
              <div><span className="inline-block bg-orange-100 px-3 py-1 rounded font-bold text-orange-800">D</span> Insuficiente</div>
              <div><span className="inline-block bg-red-100 px-3 py-1 rounded font-bold text-red-800">E</span> Deficiente</div>
            </div>
          </div>

          <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded text-sm text-gray-700">
            <strong>💡 Consejo:</strong> Puedes ingresar tus calificaciones manuales en la columna "Calificación Manual" y luego descargar todo como CSV.
          </div>

          <div className="bg-gray-50 border border-gray-300 p-4 rounded text-xs text-gray-600">
            <p><strong>Nota:</strong> Los datos mostrados corresponden al análisis de la clase del 7 de Abril de 2026. Filas amarillas = preguntas y respuestas de profesora. Filas azules = contribuciones de estudiantes.</p>
          </div>
        </div>
      )}
      </div>
    </div>
  )
}
