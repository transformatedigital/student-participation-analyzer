'use client'

import { getApiUrl } from '@/lib/api'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { Download, Search } from 'lucide-react'

interface Segment {
  segment_number?: number
  timestamp_start?: string
  timestamp_end?: string
  timestamp?: string
  speaker: string
  text: string
}

const getSpeakerColor = (speaker: string) => {
  const isTeacher = speaker.toLowerCase().includes('ileana') || speaker === 'Teacher'
  if (isTeacher) return 'border-l-emerald-600 bg-emerald-50'
  return 'border-l-blue-600 bg-slate-50'
}

const getSpeakerBgColor = (speaker: string) => {
  const isTeacher = speaker.toLowerCase().includes('ileana') || speaker === 'Teacher'
  if (isTeacher) return 'bg-emerald-200 text-emerald-800'
  return 'bg-blue-200 text-blue-800'
}

export default function TranscriptionPage() {
  const params = useParams()
  const sessionId = params?.sessionId as string
  const [segments, setSegments] = useState<Segment[]>([])
  const [filteredSegments, setFilteredSegments] = useState<Segment[]>([])
  const [speakers, setSpeakers] = useState<string[]>(['All'])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [speakerFilter, setSpeakerFilter] = useState('All')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(getApiUrl(`/api/clases/${sessionId}/transcripcion`))
        const data = await res.json()
        setSegments(data.segments || [])
        setFilteredSegments(data.segments || [])

        // Extract unique speakers
        const uniqueSpeakers = Array.from(
          new Set((data.segments || []).map((seg: Segment) => seg.speaker))
        ) as string[]
        setSpeakers(['All', ...uniqueSpeakers.sort()])
      } catch (err) {
        console.error('Error fetching transcription:', err)
      } finally {
        setLoading(false)
      }
    }

    if (sessionId) fetchData()
  }, [sessionId])

  useEffect(() => {
    let result = segments

    // Filter by speaker
    if (speakerFilter !== 'All') {
      result = result.filter((seg) => seg.speaker === speakerFilter)
    }

    // Filter by search term
    if (searchTerm) {
      result = result.filter((seg) => seg.text.toLowerCase().includes(searchTerm.toLowerCase()))
    }

    setFilteredSegments(result)
  }, [searchTerm, speakerFilter, segments])

  const handleExport = () => {
    const csv = filteredSegments
      .map((seg) => {
        const timestamp = seg.timestamp || seg.timestamp_start || 'N/A'
        return `${timestamp},${seg.speaker},"${seg.text}"`
      })
      .join('\n')

    const blob = new Blob([`Timestamp,Speaker,Text\n${csv}`], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `transcription-${sessionId}.csv`
    a.click()
  }

  if (loading) {
    return <div className="p-8">Loading transcription...</div>
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-slate-900">Full Transcription</h1>
        <p className="text-slate-600 mt-2">{segments.length} segments</p>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
        <div className="flex gap-4 items-end">
          {/* Search */}
          <div className="flex-1">
            <label className="block text-sm font-medium text-slate-700 mb-2">Search</label>
            <div className="relative">
              <Search size={18} className="absolute left-3 top-3 text-slate-400" />
              <input
                type="text"
                placeholder="Search transcription..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Speaker Filter */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Speaker</label>
            <select
              value={speakerFilter}
              onChange={(e) => setSpeakerFilter(e.target.value)}
              className="px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {speakers.map((speaker) => (
                <option key={speaker} value={speaker}>
                  {speaker}
                </option>
              ))}
            </select>
          </div>

          {/* Export */}
          <button
            onClick={handleExport}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            <Download size={18} />
            Export CSV
          </button>
        </div>
      </div>

      {/* Segments */}
      <div className="space-y-2">
        {filteredSegments.map((segment, idx) => {
          const timestamp = segment.timestamp || segment.timestamp_start || 'N/A'
          const isQuestion = segment.text.includes('?')
          return (
            <div
              key={`${idx}-${timestamp}`}
              className={`border-l-4 p-4 rounded-lg transition hover:shadow-md ${getSpeakerColor(segment.speaker)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-medium text-slate-500 font-mono">{timestamp}</span>
                    <span className={`text-xs font-medium px-2 py-1 rounded ${getSpeakerBgColor(segment.speaker)}`}>
                      {segment.speaker}
                    </span>
                    {isQuestion && <span className="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded">❓ Question</span>}
                  </div>
                  <p className="text-slate-700">"{segment.text}"</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {filteredSegments.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
          <p className="text-slate-500">No segments match your filters</p>
        </div>
      )}
    </div>
  )
}
