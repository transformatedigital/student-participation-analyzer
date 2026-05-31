'use client'

import { getApiUrl } from '@/lib/api'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { Users, Volume2 } from 'lucide-react'

interface Speaker {
  id: string
  role: string
  name: string
  segments_count: number
  percentage: number
  color: string
  degree?: string | null
  nationality?: string | null
  email?: string | null
}

interface AudioClip {
  id: string
  filename: string
  url: string
  speaker?: string
  note?: string
  is_student?: boolean
  is_unknown?: boolean
}

export default function SpeakersPage() {
  const params = useParams()
  const sessionId = params?.sessionId as string
  const [speakers, setSpeakers] = useState<Speaker[]>([])
  const [audioClips, setAudioClips] = useState<AudioClip[]>([])
  const [editingId, setEditingId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)
  const [playingClip, setPlayingClip] = useState<string | null>(null)
  const [labelingClip, setLabelingClip] = useState<string | null>(null)
  const [labelValue, setLabelValue] = useState<string>('')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [speakersRes, clipsRes] = await Promise.all([
          fetch(getApiUrl(`/api/clases/${sessionId}/hablantes`)),
          fetch(getApiUrl(`/api/clases/${sessionId}/audio_clips`))
        ])
        const speakersData = await speakersRes.json()
        const clipsData = await clipsRes.json()
        setSpeakers(speakersData.speakers)
        setAudioClips(clipsData.clips || [])
      } catch (err) {
        console.error('Error fetching data:', err)
      } finally {
        setLoading(false)
      }
    }

    if (sessionId) fetchData()
  }, [sessionId])

  const handleUpdate = async (speakerId: string, updatedData: Partial<Speaker>) => {
    setUpdating(true)
    try {
      const res = await fetch(
        getApiUrl(`/api/clases/${sessionId}/hablantes/${speakerId}`),
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updatedData)
        }
      )

      if (res.ok) {
        const data = await res.json()
        setSpeakers(data.speakers)
        setEditingId(null)
      }
    } catch (err) {
      console.error('Error updating speaker:', err)
    } finally {
      setUpdating(false)
    }
  }

  if (loading) {
    return <div className="p-8">Loading speaker data...</div>
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-slate-900">Speaker Profiles</h1>
        <p className="text-slate-600 mt-2">{speakers.length} speakers identified</p>
      </div>

      {/* Audio Clips Section - Listen to identify speakers */}
      {audioClips.length > 0 && (
        <div className="mb-8 space-y-6">
          {/* Teacher Clips */}
          <div className="bg-slate-50 rounded-xl border border-slate-200 p-6">
            <div className="flex items-center gap-2 mb-4">
              <Volume2 size={24} className="text-slate-600" />
              <h3 className="text-lg font-semibold text-slate-900">Teacher (Ileana) - Reference Clips</h3>
            </div>
            <p className="text-slate-600 text-sm mb-4">
              These clips are mostly the teacher. Listen to establish a baseline of the teacher's voice.
            </p>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-6">
              {audioClips.filter(c => !c.is_student).map((clip) => (
                <div
                  key={clip.id}
                  className="bg-white rounded-lg border border-slate-200 p-3 hover:shadow-md transition"
                >
                  <p className="text-xs font-medium text-slate-600 mb-2 truncate">
                    {clip.id}
                  </p>
                  <audio
                    controls
                    className="w-full mb-2 h-7 text-xs"
                    src={getApiUrl(clip.url)}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Student Clips */}
          {audioClips.filter(c => c.is_student && !c.is_unknown).length > 0 && (
            <div className="bg-gradient-to-r from-emerald-50 to-blue-50 rounded-xl border-2 border-emerald-300 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Volume2 size={24} className="text-emerald-600" />
                <h3 className="text-lg font-semibold text-slate-900">⭐ STUDENT VOICES - Key Clips</h3>
              </div>
              <p className="text-slate-700 text-sm mb-4 font-medium">
                🎯 Listen to these clips to identify student names. These contain actual student voices!
              </p>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {audioClips.filter(c => c.is_student && !c.is_unknown).map((clip) => (
                  <div
                    key={clip.id}
                    className="bg-white rounded-lg border-2 border-emerald-300 p-4 shadow-sm hover:shadow-lg transition"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">⭐</span>
                      <p className="text-sm font-bold text-emerald-700">
                        {clip.speaker}
                      </p>
                    </div>
                    <p className="text-xs text-slate-600 mb-3">
                      {clip.note}
                    </p>
                    <audio
                      controls
                      className="w-full mb-2 h-8"
                      onPlay={() => setPlayingClip(clip.id)}
                      onPause={() => setPlayingClip(null)}
                      src={getApiUrl(clip.url)}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Unknown Clips - Need Identification */}
          {audioClips.filter(c => c.is_unknown).length > 0 && (
            <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl border-2 border-amber-300 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Volume2 size={24} className="text-amber-600" />
                <h3 className="text-lg font-semibold text-slate-900">❓ UNIDENTIFIED CLIPS - Need Labeling</h3>
              </div>
              <p className="text-slate-700 text-sm mb-4 font-medium">
                🎧 Listen to each clip, then select which student it belongs to and click "Assign Speaker"
              </p>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                {audioClips.filter(c => c.is_unknown).map((clip, idx) => {
                  const clipNumber = idx + 1;
                  return (
                    <div
                      key={clip.id}
                      className="bg-white rounded-lg border-2 border-amber-300 p-4 shadow-md hover:shadow-lg transition relative"
                    >
                      {/* CLIP NUMBER - TOP RIGHT - VERY LARGE */}
                      <div className="absolute top-2 right-2 bg-amber-600 text-white rounded-full w-12 h-12 flex items-center justify-center font-bold text-xl flex-shrink-0">
                        {clipNumber}
                      </div>

                      {/* Clip Info with Number Suffix */}
                      <div className="mb-3 text-sm space-y-2">
                        <p className="text-amber-700 font-bold text-base">
                          {clip.speaker} {clipNumber}
                        </p>
                        <p className="text-slate-500 italic text-xs">
                          {clip.note}
                        </p>
                      </div>

                      {/* Audio Player */}
                      <audio
                        controls
                        className="w-full mb-4 h-9 rounded"
                        onPlay={() => setPlayingClip(clip.id)}
                        onPause={() => setPlayingClip(null)}
                        src={getApiUrl(clip.url)}
                      />

                      {/* Label Form */}
                      {labelingClip === clip.id ? (
                        <div className="space-y-2">
                          <select
                            value={labelValue}
                            onChange={(e) => setLabelValue(e.target.value)}
                            className="w-full px-3 py-2 border border-amber-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                          >
                            <option value="">Select student...</option>
                            <option value="Student 1">Student 1</option>
                            <option value="Student 2">Student 2</option>
                            <option value="Student 3">Student 3</option>
                            <option value="Student 4">Student 4</option>
                            <option value="Aryang">Aryang</option>
                            <option value="Other">Other/Unknown</option>
                          </select>
                          <div className="flex gap-2">
                            <button
                              onClick={() => {
                                if (labelValue) {
                                  console.log(`✅ Labeled ${clip.id} as: ${labelValue}`);
                                  alert(`You told me: "Clip ${clipNumber}" = "${labelValue}"\n\nI've noted this. Tell me all clips and I'll update them.`);
                                  setLabelingClip(null);
                                  setLabelValue('');
                                }
                              }}
                              className="flex-1 px-3 py-2 bg-emerald-600 text-white text-xs font-medium rounded-lg hover:bg-emerald-700 transition"
                            >
                              ✅ Assign
                            </button>
                            <button
                              onClick={() => {
                                setLabelingClip(null);
                                setLabelValue('');
                              }}
                              className="flex-1 px-3 py-2 bg-slate-300 text-slate-700 text-xs font-medium rounded-lg hover:bg-slate-400 transition"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() => setLabelingClip(clip.id)}
                          className="w-full px-4 py-3 bg-amber-600 text-white text-sm font-semibold rounded-lg hover:bg-amber-700 transition flex items-center justify-center gap-2"
                        >
                          <span>🏷️</span>
                          Label This Clip
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Instructions */}
              <div className="mt-6 bg-amber-100 border border-amber-300 rounded-lg p-4">
                <p className="text-sm text-amber-900 font-medium">💡 How to Identify Clips:</p>
                <div className="text-xs text-amber-800 mt-3 space-y-2">
                  <p className="font-semibold">Option A - Tell me here in chat:</p>
                  <div className="bg-white rounded p-2 font-mono text-amber-900 text-xs ml-2">
                    Clip 1 = Student 2<br/>
                    Clip 2 = Student 2<br/>
                    Clip 3 = Student 1<br/>
                    Clip 4 = Student 2<br/>
                    ... (continue for all clips)
                  </div>

                  <p className="font-semibold mt-3">Option B - Web interface:</p>
                  <ol className="ml-4 list-decimal space-y-1">
                    <li>Click audio player to listen</li>
                    <li>Click "Label This Clip"</li>
                    <li>Select student → "Assign"</li>
                  </ol>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Speakers Grid */}
      <div className="space-y-6">
        {speakers.map((speaker) => (
          <div
            key={speaker.id}
            className="bg-white rounded-xl border border-slate-200 p-6"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-6 pb-6 border-b border-slate-200">
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
                  {speaker.role === 'Teacher' ? '👩‍🏫' : '👤'} {speaker.name}
                </h2>
                <p className="text-sm text-slate-500 mt-1">{speaker.role}</p>
              </div>
              <div className="text-right">
                <p className="text-3xl font-bold text-slate-900">
                  {speaker.segments_count}
                </p>
                <p className="text-xs text-slate-500">
                  {speaker.percentage}% of session
                </p>
              </div>
            </div>

            {/* Details */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {speaker.role !== 'Teacher' && (
                <>
                  <div>
                    <label className="text-xs font-semibold text-slate-500 uppercase block mb-2">
                      Name
                    </label>
                    {editingId === speaker.id ? (
                      <input
                        type="text"
                        defaultValue={speaker.name}
                        onChange={(e) => handleUpdate(speaker.id, { name: e.target.value })}
                        className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Enter student name"
                      />
                    ) : (
                      <p className="text-slate-700">{speaker.name}</p>
                    )}
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-500 uppercase block mb-2">
                      Degree
                    </label>
                    {editingId === speaker.id ? (
                      <select
                        defaultValue={speaker.degree || ''}
                        onChange={(e) => handleUpdate(speaker.id, { degree: e.target.value || null })}
                        className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">Select degree...</option>
                        <option value="PhD">PhD</option>
                        <option value="Master">Master</option>
                        <option value="Other">Other</option>
                      </select>
                    ) : (
                      <p className="text-slate-700">{speaker.degree || '—'}</p>
                    )}
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-500 uppercase block mb-2">
                      Nationality
                    </label>
                    {editingId === speaker.id ? (
                      <input
                        type="text"
                        defaultValue={speaker.nationality || ''}
                        onChange={(e) => handleUpdate(speaker.id, { nationality: e.target.value || null })}
                        className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g., Colombian"
                      />
                    ) : (
                      <p className="text-slate-700">{speaker.nationality || '—'}</p>
                    )}
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-500 uppercase block mb-2">
                      Email
                    </label>
                    {editingId === speaker.id ? (
                      <input
                        type="email"
                        defaultValue={speaker.email || ''}
                        onChange={(e) => handleUpdate(speaker.id, { email: e.target.value || null })}
                        className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="example@example.com"
                      />
                    ) : (
                      <p className="text-slate-700 text-sm truncate">{speaker.email || '—'}</p>
                    )}
                  </div>
                </>
              )}
            </div>

            {/* Participation Bar */}
            <div className="mt-6">
              <div className="text-xs font-medium text-slate-600 mb-2">
                Participation Share
              </div>
              <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-3 transition-all ${
                    speaker.role === 'Teacher'
                      ? 'bg-emerald-600'
                      : 'bg-blue-600'
                  }`}
                  style={{ width: `${speaker.percentage}%` }}
                ></div>
              </div>
            </div>

            {/* Edit Button */}
            {speaker.role !== 'Teacher' && (
              <div className="mt-4 flex gap-2">
                {editingId === speaker.id ? (
                  <>
                    <button
                      onClick={() => setEditingId(null)}
                      disabled={updating}
                      className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition text-sm font-medium disabled:opacity-50"
                    >
                      Done
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 transition text-sm font-medium"
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setEditingId(speaker.id)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm font-medium"
                  >
                    Edit Info
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
