'use client'

import { getApiUrl } from '@/lib/api'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { Mic, HelpCircle, MessageSquare, Star, ChevronRight } from 'lucide-react'

interface SessionData {
  metadata: {
    session_id: string
    date: string
    course_name: string
    instructor: string
    duration_minutes: number
    total_segments: number
    speakers_count: number
    questions_identified: number
  }
  speakers: any[]
}

interface PerStudentSummary {
  [student: string]: {
    responses_to_teacher: number
    voluntary_contributions: number
    quality_distribution: Record<string, number>
    avg_quality: string
  }
}

export default function SessionOverviewPage() {
  const params = useParams()
  const sessionId = params?.sessionId as string
  const [data, setData] = useState<SessionData | null>(null)
  const [qualityDistribution, setQualityDistribution] = useState<Record<string, number>>({
    A: 0,
    B: 0,
    C: 0,
    D: 0,
    E: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [resSession, resParticipation] = await Promise.all([
          fetch(getApiUrl(`/api/clases/${sessionId}`)),
          fetch(getApiUrl(`/api/clases/${sessionId}/participacion`)),
        ])

        const sessionData = await resSession.json()
        const participationData = await resParticipation.json()

        setData(sessionData)

        // Aggregate quality distribution from per_student_summary
        const summary = participationData.per_student_summary || {}
        const aggregated: Record<string, number> = { A: 0, B: 0, C: 0, D: 0, E: 0 }

        Object.values(summary).forEach((student: any) => {
          const dist = student.quality_distribution || {}
          Object.entries(dist).forEach(([grade, count]: [string, any]) => {
            aggregated[grade] = (aggregated[grade] || 0) + (count || 0)
          })
        })

        setQualityDistribution(aggregated)
      } catch (err) {
        console.error('Error fetching data:', err)
      } finally {
        setLoading(false)
      }
    }

    if (sessionId) fetchData()
  }, [sessionId])

  if (loading) {
    return <div className="p-8">Loading...</div>
  }

  if (!data) {
    return <div className="p-8">Session not found</div>
  }

  const meta = data.metadata
  const speakers = data.speakers

  // Calculate participation percentages
  const teacherSegments = speakers[0]?.segments_count || 0
  const totalSegments = meta.total_segments || 1

  // Calculate total quality responses
  const totalQualityResponses = Object.values(qualityDistribution).reduce((a, b) => a + (b || 0), 0)

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-slate-900">Session Overview</h1>
        <p className="text-slate-600 mt-2">
          {new Date(meta.date).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })} • {meta.duration_minutes} min • {meta.speakers_count} speakers
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-slate-200 p-6 border-l-4 border-l-emerald-600">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500 uppercase">Speakers</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">{meta.speakers_count}</p>
            </div>
            <Mic size={24} className="text-emerald-600" />
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 border-l-4 border-l-blue-600">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500 uppercase">Questions</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">{meta.questions_identified}</p>
            </div>
            <HelpCircle size={24} className="text-blue-600" />
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 border-l-4 border-l-amber-600">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500 uppercase">Segments</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">{meta.total_segments}</p>
            </div>
            <MessageSquare size={24} className="text-amber-600" />
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 border-l-4 border-l-blue-600">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500 uppercase">Avg Quality</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">
                {totalQualityResponses > 0
                  ? ['A', 'B', 'C', 'D', 'E'].find(
                      (grade) => qualityDistribution[grade] === Math.max(...Object.values(qualityDistribution))
                    ) || 'B'
                  : 'B'}
              </p>
            </div>
            <Star size={24} className="text-blue-600" />
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-2 gap-8">
        {/* Participation Distribution */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-6">
            Participation Distribution
          </h2>
          <div className="space-y-3">
            {speakers.map((speaker, idx) => {
              const percentage = speaker.segments_count
                ? Math.round((speaker.segments_count / totalSegments) * 100)
                : 0
              return (
                <div key={idx}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium text-slate-700">
                      {speaker.name}
                    </span>
                    <span className="text-xs text-slate-500">
                      {speaker.segments_count} ({percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        idx === 0 ? 'bg-emerald-600' : 'bg-blue-600'
                      }`}
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Quality Distribution */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-6">
            Question Quality Levels (A-E)
          </h2>
          <div className="flex items-end justify-around h-48 gap-2">
            {['A', 'B', 'C', 'D', 'E'].map((level) => {
              const count = qualityDistribution[level] || 0
              const maxCount = Math.max(...Object.values(qualityDistribution), 1)
              const height = maxCount > 0 ? (count / maxCount) * 100 : 0
              const colors = {
                A: 'bg-emerald-600',
                B: 'bg-blue-600',
                C: 'bg-amber-600',
                D: 'bg-orange-600',
                E: 'bg-red-600'
              }
              return (
                <div key={level} className="flex flex-col items-center">
                  <div
                    className={`w-12 ${colors[level as keyof typeof colors]} rounded-lg transition-all`}
                    style={{ height: `${Math.max(height * 2, 8)}px` }}
                    title={`${level}: ${count} responses`}
                  ></div>
                  <span className="text-xs font-medium text-slate-600 mt-2">{level}</span>
                  <span className="text-xs text-slate-500">{count}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-8 grid grid-cols-3 gap-4">
        {[
          {
            icon: <FileText size={20} />,
            title: 'View Transcription',
            href: `/clases/${sessionId}/transcripcion`
          },
          {
            icon: <MessageSquare size={20} />,
            title: 'Participation Analysis',
            href: `/clases/${sessionId}/participacion`
          },
          {
            icon: <Star size={20} />,
            title: 'Evaluation Report',
            href: `/clases/${sessionId}/evaluacion`
          }
        ].map((action, idx) => (
          <Link
            key={idx}
            href={action.href}
            className="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-lg hover:border-blue-200 transition group"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-slate-600 group-hover:text-blue-600 transition">
                  {action.icon}
                </div>
                <p className="text-sm font-medium text-slate-900 mt-2">
                  {action.title}
                </p>
              </div>
              <ChevronRight size={20} className="text-slate-300 group-hover:text-blue-400 transition" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

const FileText = ({ size }: { size: number }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="11" x2="12" y2="17"></line><line x1="9" y1="14" x2="15" y2="14"></line></svg>
)
