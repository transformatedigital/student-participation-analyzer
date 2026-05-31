'use client'

import { getApiUrl } from '@/lib/api'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'

interface Framework {
  level: string
  solo: string
  blooms: string
  characteristics: string[]
  examples: string
}

export default function EvaluationPage() {
  const params = useParams()
  const sessionId = params?.sessionId as string
  const [frameworks, setFrameworks] = useState<Record<string, Record<string, Framework>>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(
          getApiUrl(`/api/clases/${sessionId}/evaluacion`)
        )
        const data = await res.json()
        setFrameworks(data.evaluation_frameworks)
      } catch (err) {
        console.error('Error fetching evaluation data:', err)
      } finally {
        setLoading(false)
      }
    }

    if (sessionId) fetchData()
  }, [sessionId])

  if (loading) {
    return <div className="p-8">Loading evaluation frameworks...</div>
  }

  const levels = ['A', 'B', 'C', 'D', 'E']
  const colors: Record<string, string> = {
    'A': 'emerald',
    'B': 'blue',
    'C': 'amber',
    'D': 'orange',
    'E': 'red'
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-slate-900">Evaluation Framework</h1>
        <p className="text-slate-600 mt-2">
          A-E Scale (Based on SOLO Taxonomy + Bloom's + Socratic Criteria)
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 mb-8 border-b border-slate-200">
        <div className="px-4 py-3 border-b-2 border-blue-600 text-blue-600 font-medium cursor-pointer">
          Student Questions
        </div>
      </div>

      {/* Framework Grid */}
      <div className="space-y-6">
        {levels.map((level) => {
          const framework = frameworks?.student_questions?.[level]
          if (!framework) return null

          const color = colors[level]
          const bgColor = {
            'emerald': 'bg-emerald-50',
            'blue': 'bg-blue-50',
            'amber': 'bg-amber-50',
            'orange': 'bg-orange-50',
            'red': 'bg-red-50'
          }[color]

          const borderColor = {
            'emerald': 'border-emerald-200 border-l-4 border-l-emerald-600',
            'blue': 'border-blue-200 border-l-4 border-l-blue-600',
            'amber': 'border-amber-200 border-l-4 border-l-amber-600',
            'orange': 'border-orange-200 border-l-4 border-l-orange-600',
            'red': 'border-red-200 border-l-4 border-l-red-600'
          }[color]

          const textColor = {
            'emerald': 'text-emerald-700',
            'blue': 'text-blue-700',
            'amber': 'text-amber-700',
            'orange': 'text-orange-700',
            'red': 'text-red-700'
          }[color]

          return (
            <div
              key={level}
              className={`${bgColor} border ${borderColor} rounded-lg p-6`}
            >
              {/* Title */}
              <div className="flex items-center justify-between mb-4">
                <h2 className={`text-xl font-semibold ${textColor}`}>
                  {framework.level}
                </h2>
                <div className="flex gap-4 text-sm">
                  <span className="font-medium text-slate-600">
                    SOLO: <span className="font-semibold">{framework.solo}</span>
                  </span>
                  <span className="font-medium text-slate-600">
                    Bloom's: <span className="font-semibold">{framework.blooms}</span>
                  </span>
                </div>
              </div>

              {/* Characteristics */}
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-slate-700 mb-2">
                  Characteristics:
                </h3>
                <ul className="space-y-1">
                  {framework.characteristics.map((char, idx) => (
                    <li key={idx} className="text-sm text-slate-700 flex items-start gap-2">
                      <span className="text-slate-400 flex-shrink-0">•</span>
                      <span>{char}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Example */}
              <div>
                <h3 className="text-sm font-semibold text-slate-700 mb-2">Example:</h3>
                <p className="text-sm text-slate-700 italic">"{framework.examples}"</p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="mt-12 bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Scale Legend</h3>
        <div className="grid grid-cols-5 gap-4">
          {[
            { level: 'A', label: 'Excellent', desc: 'Extended Abstract' },
            { level: 'B', label: 'Very Good', desc: 'Relational' },
            { level: 'C', label: 'Good', desc: 'Multistructural' },
            { level: 'D', label: 'Acceptable', desc: 'Unistructural' },
            { level: 'E', label: 'Weak', desc: 'Prestructural' }
          ].map((item) => {
            const color = colors[item.level]
            const textColor = {
              'emerald': 'text-emerald-700',
              'blue': 'text-blue-700',
              'amber': 'text-amber-700',
              'orange': 'text-orange-700',
              'red': 'text-red-700'
            }[color]

            return (
              <div key={item.level} className="text-center">
                <div className={`text-2xl font-bold ${textColor} mb-1`}>
                  {item.level}
                </div>
                <p className="text-xs font-medium text-slate-700">{item.label}</p>
                <p className="text-xs text-slate-500">{item.desc}</p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
