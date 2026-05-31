'use client'

import { getApiUrl } from '@/lib/api'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { Volume2, Check, AlertCircle } from 'lucide-react'

interface VoiceClip {
  id: string
  filename: string
  url: string
  speaker_estimated: string
  timestamp_start: string
  duration_seconds: number
  note: string
  speaker_verified?: string
  verified_by_user?: boolean
}

const STUDENT_OPTIONS = ['Aryang', 'Grace', 'Chilaka', 'Sthepen', 'Mega', 'Unknown']

export default function VoiceVerificationPage() {
  const params = useParams()
  const sessionId = params?.sessionId as string
  const [clips, setClips] = useState<VoiceClip[]>([])
  const [loading, setLoading] = useState(true)
  const [currentClipIndex, setCurrentClipIndex] = useState(0)
  const [verifications, setVerifications] = useState<Record<string, string>>({})
  const [notes, setNotes] = useState<Record<string, string>>({})

  useEffect(() => {
    const fetchClips = async () => {
      try {
        const res = await fetch(getApiUrl(`/api/clases/${sessionId}/voice_training_clips`))
        const data = await res.json()
        setClips(data.clips || [])

        // Initialize with estimated speakers
        const initialVerifications: Record<string, string> = {}
        data.clips?.forEach((clip: VoiceClip) => {
          initialVerifications[clip.id] = clip.speaker_estimated || 'Unknown'
        })
        setVerifications(initialVerifications)
      } catch (err) {
        console.error('Error fetching voice clips:', err)
      } finally {
        setLoading(false)
      }
    }

    if (sessionId) fetchClips()
  }, [sessionId])

  const handleVerify = async (clipId: string) => {
    try {
      await fetch(getApiUrl(`/api/clases/${sessionId}/voice_training_clips/${clipId}/verify`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          speaker_verified: verifications[clipId],
          note: notes[clipId] || ''
        })
      })

      // Move to next clip
      if (currentClipIndex < clips.length - 1) {
        setCurrentClipIndex(currentClipIndex + 1)
      }
    } catch (err) {
      console.error('Error verifying clip:', err)
      alert('Error saving verification')
    }
  }

  if (loading) {
    return <div className="p-8">Cargando clips de voz...</div>
  }

  if (clips.length === 0) {
    return (
      <div className="p-8">
        <div className="text-center py-12 bg-white rounded-lg border border-slate-200">
          <AlertCircle className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <p className="text-slate-500">No hay clips de entrenamiento de voz disponibles</p>
        </div>
      </div>
    )
  }

  const currentClip = clips[currentClipIndex]
  const isVerified = currentClip?.verified_by_user

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-slate-900">Verificación de Voces</h1>
        <p className="text-slate-600 mt-2">
          Confirma la identidad de cada estudiante escuchando los clips
        </p>
      </div>

      {/* Progress Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 mb-8">
        <div className="flex justify-between items-center mb-4">
          <span className="text-sm font-medium text-slate-700">
            Clip {currentClipIndex + 1} de {clips.length}
          </span>
          <span className="text-sm text-slate-500">
            {Math.round(((currentClipIndex + 1) / clips.length) * 100)}%
          </span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${((currentClipIndex + 1) / clips.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Audio Player Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-8 mb-8">
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-slate-900 mb-2">
            {currentClip?.filename}
          </h2>
          <p className="text-sm text-slate-600">
            📍 Timestamp: {currentClip?.timestamp_start} | ⏱️ Duración: {currentClip?.duration_seconds}s
          </p>
          <p className="text-sm text-slate-500 mt-2">{currentClip?.note}</p>
        </div>

        {/* Audio Player */}
        <div className="bg-slate-50 rounded-lg p-6 mb-6">
          {currentClip?.url ? (
            <div className="space-y-4">
              <p className="text-sm text-slate-600 mb-3">
                🎙️ Presiona el botón de reproducción para escuchar:
              </p>
              <audio
                controls
                className="w-full h-12"
                controlsList="nodownload"
                preload="auto"
              >
                <source src={getApiUrl(currentClip.url)} type="audio/aac" />
                <source src={getApiUrl(currentClip.url)} type="audio/mp4" />
                Tu navegador no soporta reproducción de audio.
                <a
                  href={getApiUrl(currentClip.url)}
                  download
                  className="text-blue-600 underline"
                >
                  Descarga el archivo aquí
                </a>
              </audio>
              <p className="text-xs text-slate-500 mt-2">
                Si no funciona la reproducción, intenta descargar el archivo
              </p>
            </div>
          ) : (
            <p className="text-slate-500">Cargando clip...</p>
          )}
        </div>

        {/* Verification Options */}
        <div className="space-y-4 mb-6">
          <label className="block text-sm font-medium text-slate-700">
            ¿Quién es esta voz?
          </label>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {STUDENT_OPTIONS.map((student) => (
              <button
                key={student}
                onClick={() => setVerifications({ ...verifications, [currentClip.id]: student })}
                className={`px-4 py-3 rounded-lg font-medium transition ${
                  verifications[currentClip.id] === student
                    ? 'bg-blue-600 text-white ring-2 ring-blue-400'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {student}
              </button>
            ))}
          </div>

          {/* Current Selection Badge */}
          {verifications[currentClip.id] && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-2">
              <Check className="w-5 h-5 text-blue-600" />
              <span className="text-sm text-blue-700">
                Seleccionaste: <strong>{verifications[currentClip.id]}</strong>
              </span>
            </div>
          )}
        </div>

        {/* Notes Field */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Notas (opcional)
          </label>
          <textarea
            value={notes[currentClip.id] || ''}
            onChange={(e) => setNotes({ ...notes, [currentClip.id]: e.target.value })}
            placeholder="Ej: 'Suena como Aryang por el acento', 'Muchos ruidos de fondo'..."
            className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={() => handleVerify(currentClip.id)}
            disabled={!verifications[currentClip.id]}
            className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition disabled:bg-slate-300"
          >
            Confirmar {verifications[currentClip.id] ? `como ${verifications[currentClip.id]}` : ''}
          </button>

          {currentClipIndex > 0 && (
            <button
              onClick={() => setCurrentClipIndex(currentClipIndex - 1)}
              className="px-6 py-3 border border-slate-200 rounded-lg font-medium hover:bg-slate-50 transition"
            >
              ← Anterior
            </button>
          )}

          {currentClipIndex < clips.length - 1 && (
            <button
              onClick={() => setCurrentClipIndex(currentClipIndex + 1)}
              className="px-6 py-3 border border-slate-200 rounded-lg font-medium hover:bg-slate-50 transition"
            >
              Siguiente →
            </button>
          )}
        </div>
      </div>

      {/* Clips List Sidebar */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Todos los clips</h3>
        <div className="space-y-2">
          {clips.map((clip, idx) => (
            <button
              key={clip.id}
              onClick={() => setCurrentClipIndex(idx)}
              className={`w-full text-left px-4 py-3 rounded-lg transition ${
                currentClipIndex === idx
                  ? 'bg-blue-100 text-blue-900 border border-blue-300'
                  : 'bg-slate-50 text-slate-700 hover:bg-slate-100'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium">
                  {idx + 1}. {clip.speaker_estimated}
                </span>
                {clip.verified_by_user && (
                  <Check className="w-4 h-4 text-green-600" />
                )}
              </div>
              <span className="text-xs text-slate-500 mt-1 block">
                {clip.timestamp_start} • {clip.duration_seconds}s
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
