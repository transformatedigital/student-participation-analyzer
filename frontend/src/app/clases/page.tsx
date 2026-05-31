'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Plus, Calendar, Mic, Clock, CheckCircle } from 'lucide-react'
import { getApiUrl } from '@/lib/api'

interface ClassSession {
  session_id: string
  date: string
  course_name: string
  instructor: string
  duration_minutes: number
  status: string
  speakers_count: number
  total_segments: number
}

export default function ClassesPage() {
  const [classes, setClasses] = useState<ClassSession[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchClasses = async () => {
      try {
        const res = await fetch(getApiUrl('/api/clases'))
        const data = await res.json()
        setClasses(data.classes)
      } catch (err) {
        setError('Failed to load classes')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchClasses()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-slate-500">Loading classes...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-semibold text-slate-900">
                📋 Class Analysis Platform
              </h1>
              <p className="text-slate-500 mt-2">
                Classroom Participation Evaluation & Analysis
              </p>
            </div>
            <Link
              href="/clases/crear"
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              <Plus size={20} />
              New Class
            </Link>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {classes.length === 0 ? (
          <div className="text-center py-12">
            <Calendar size={48} className="mx-auto text-slate-300 mb-4" />
            <h2 className="text-xl font-medium text-slate-600">No classes yet</h2>
            <p className="text-slate-500 mt-2">Create a new class to get started</p>
            <Link
              href="/clases/crear"
              className="inline-block mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              Create First Class
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {classes.map((cls) => (
              <Link
                key={cls.session_id}
                href={`/clases/${cls.session_id}`}
                className="group"
              >
                <div className="bg-white rounded-xl border border-slate-200 p-6 hover:shadow-lg hover:border-blue-200 hover:ring-1 hover:ring-blue-100 transition cursor-pointer">
                  {/* Status Badge */}
                  <div className="flex items-center gap-2 mb-4">
                    {cls.status === 'analyzed' && (
                      <>
                        <CheckCircle size={16} className="text-emerald-600" />
                        <span className="text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-1 rounded">
                          ✅ Analyzed
                        </span>
                      </>
                    )}
                  </div>

                  {/* Date and Course */}
                  <div className="mb-4">
                    <h3 className="text-lg font-semibold text-slate-900 group-hover:text-blue-600 transition">
                      📅 {new Date(cls.date).toLocaleDateString('en-US', {
                        month: 'long',
                        day: 'numeric',
                        year: 'numeric'
                      })}
                    </h3>
                    <p className="text-sm text-slate-600 mt-1">{cls.course_name}</p>
                  </div>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
                    <div className="flex items-center gap-2 text-slate-600">
                      <Mic size={16} />
                      <span>{cls.speakers_count} speakers</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-600">
                      <Clock size={16} />
                      <span>{Math.round(cls.duration_minutes / 60)}h {cls.duration_minutes % 60}m</span>
                    </div>
                  </div>

                  {/* Segments */}
                  <div className="text-xs text-slate-500">
                    📝 {cls.total_segments} segments
                  </div>

                  {/* CTA */}
                  <div className="mt-4 pt-4 border-t border-slate-100">
                    <div className="text-sm font-medium text-blue-600 group-hover:text-blue-700">
                      View Analysis →
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
