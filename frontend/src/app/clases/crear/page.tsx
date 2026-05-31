'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ChevronLeft, ChevronRight, Upload } from 'lucide-react'

interface Participant {
  name: string
  degree: string
  nationality: string
  email: string
}

export default function CreateClassPage() {
  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState({
    date: '',
    courseName: '',
    courseCode: '',
    instructor: '',
    duration: '',
    audioFiles: [] as File[],
    participants: [
      { name: '', degree: 'PhD', nationality: '', email: '' }
    ]
  })

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    setFormData(prev => ({ ...prev, audioFiles: [...prev.audioFiles, ...files] }))
  }

  const handleRemoveFile = (idx: number) => {
    setFormData(prev => ({
      ...prev,
      audioFiles: prev.audioFiles.filter((_, i) => i !== idx)
    }))
  }

  const handleParticipantChange = (idx: number, field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      participants: prev.participants.map((p, i) =>
        i === idx ? { ...p, [field]: value } : p
      )
    }))
  }

  const handleAddParticipant = () => {
    setFormData(prev => ({
      ...prev,
      participants: [...prev.participants, { name: '', degree: 'PhD', nationality: '', email: '' }]
    }))
  }

  const handleRemoveParticipant = (idx: number) => {
    setFormData(prev => ({
      ...prev,
      participants: prev.participants.filter((_, i) => i !== idx)
    }))
  }

  const canProceed = () => {
    if (step === 1) return formData.date && formData.courseName && formData.courseCode && formData.instructor
    if (step === 2) return formData.audioFiles.length > 0
    if (step === 3) return formData.participants.some(p => p.name && p.email)
    return true
  }

  const handleCreate = async () => {
    // This would typically send data to backend
    console.log('Creating class with data:', formData)
    alert('Class created successfully! (Note: This is a demo - full implementation pending)')
  }

  return (
    <div className="min-h-screen bg-slate-50 py-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/clases" className="flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-4">
            <ChevronLeft size={20} />
            Back to Classes
          </Link>
          <h1 className="text-3xl font-semibold text-slate-900">Create New Class</h1>
        </div>

        {/* Progress Bar */}
        <div className="bg-white rounded-lg border border-slate-200 p-4 mb-8">
          <div className="flex justify-between mb-4">
            {[1, 2, 3, 4].map(s => (
              <div
                key={s}
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                  s <= step
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-200 text-slate-400'
                }`}
              >
                {s}
              </div>
            ))}
          </div>
          <div className="w-full bg-slate-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${(step / 4) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Form Content */}
        <div className="bg-white rounded-lg border border-slate-200 p-8 mb-8">
          {/* Step 1: Session Info */}
          {step === 1 && (
            <div>
              <h2 className="text-2xl font-semibold text-slate-900 mb-6">
                Step 1: Session Information
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Class Date *
                  </label>
                  <input
                    type="date"
                    name="date"
                    value={formData.date}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Class Name *
                  </label>
                  <input
                    type="text"
                    name="courseName"
                    placeholder="e.g., Advanced Machine Learning"
                    value={formData.courseName}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Course Code *
                  </label>
                  <input
                    type="text"
                    name="courseCode"
                    placeholder="e.g., CS 502"
                    value={formData.courseCode}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Instructor *
                  </label>
                  <input
                    type="text"
                    name="instructor"
                    placeholder="e.g., Dr. Jane Doe"
                    value={formData.instructor}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Approximate Duration (minutes)
                  </label>
                  <input
                    type="number"
                    name="duration"
                    placeholder="e.g., 180"
                    value={formData.duration}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Audio Upload */}
          {step === 2 && (
            <div>
              <h2 className="text-2xl font-semibold text-slate-900 mb-6">
                Step 2: Upload Audio Files
              </h2>

              {/* Drop Zone */}
              <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center mb-6 hover:border-blue-400 hover:bg-blue-50 transition cursor-pointer">
                <Upload size={32} className="mx-auto text-slate-400 mb-2" />
                <p className="text-slate-600 font-medium">Drop files here or click to select</p>
                <p className="text-xs text-slate-500 mt-1">
                  Supported: MP3, WAV, M4A, OGG (Max 500MB each)
                </p>
                <input
                  type="file"
                  multiple
                  accept="audio/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="fileInput"
                />
                <label htmlFor="fileInput" className="block mt-4">
                  <button
                    type="button"
                    onClick={() => document.getElementById('fileInput')?.click()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition inline-block"
                  >
                    Select Files
                  </button>
                </label>
              </div>

              {/* File List */}
              {formData.audioFiles.length > 0 && (
                <div className="bg-slate-50 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-slate-900 mb-3">
                    Files to merge ({formData.audioFiles.length}):
                  </h3>
                  <div className="space-y-2">
                    {formData.audioFiles.map((file, idx) => (
                      <div key={idx} className="flex items-center justify-between bg-white p-3 rounded-lg border border-slate-200">
                        <span className="text-sm text-slate-700">{file.name}</span>
                        <button
                          onClick={() => handleRemoveFile(idx)}
                          className="text-red-600 hover:text-red-700"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-slate-600 mt-3">
                    Total: {(formData.audioFiles.reduce((sum, f) => sum + f.size, 0) / 1024 / 1024).toFixed(1)} MB
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Step 3: Participants */}
          {step === 3 && (
            <div>
              <h2 className="text-2xl font-semibold text-slate-900 mb-6">
                Step 3: Add Participants
              </h2>

              <div className="space-y-4 mb-4">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-200">
                        <th className="text-left px-4 py-2 font-semibold text-slate-700">Name</th>
                        <th className="text-left px-4 py-2 font-semibold text-slate-700">Degree</th>
                        <th className="text-left px-4 py-2 font-semibold text-slate-700">Nationality</th>
                        <th className="text-left px-4 py-2 font-semibold text-slate-700">Email</th>
                        <th className="px-4 py-2 w-10"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {formData.participants.map((p, idx) => (
                        <tr key={idx}>
                          <td className="px-4 py-2">
                            <input
                              type="text"
                              placeholder="Full name"
                              value={p.name}
                              onChange={(e) => handleParticipantChange(idx, 'name', e.target.value)}
                              className="w-full px-2 py-1 border border-slate-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </td>
                          <td className="px-4 py-2">
                            <select
                              value={p.degree}
                              onChange={(e) => handleParticipantChange(idx, 'degree', e.target.value)}
                              className="w-full px-2 py-1 border border-slate-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                              <option value="PhD">PhD</option>
                              <option value="Master">Master</option>
                              <option value="Other">Other</option>
                            </select>
                          </td>
                          <td className="px-4 py-2">
                            <input
                              type="text"
                              placeholder="Nationality"
                              value={p.nationality}
                              onChange={(e) => handleParticipantChange(idx, 'nationality', e.target.value)}
                              className="w-full px-2 py-1 border border-slate-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </td>
                          <td className="px-4 py-2">
                            <input
                              type="email"
                              placeholder="Email"
                              value={p.email}
                              onChange={(e) => handleParticipantChange(idx, 'email', e.target.value)}
                              className="w-full px-2 py-1 border border-slate-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </td>
                          <td className="px-4 py-2 text-center">
                            {formData.participants.length > 1 && (
                              <button
                                onClick={() => handleRemoveParticipant(idx)}
                                className="text-red-600 hover:text-red-700"
                              >
                                ×
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <button
                  onClick={handleAddParticipant}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  + Add Participant
                </button>
              </div>
            </div>
          )}

          {/* Step 4: Review */}
          {step === 4 && (
            <div>
              <h2 className="text-2xl font-semibold text-slate-900 mb-6">
                Step 4: Review & Process
              </h2>

              <div className="space-y-6 mb-6">
                <div className="border border-slate-200 rounded-lg p-4">
                  <h3 className="font-semibold text-slate-900 mb-2">Session Info</h3>
                  <p className="text-sm text-slate-600">
                    📅 {formData.date} | {formData.courseName} ({formData.courseCode})
                  </p>
                  <p className="text-sm text-slate-600">
                    👨‍🏫 {formData.instructor}
                  </p>
                </div>

                <div className="border border-slate-200 rounded-lg p-4">
                  <h3 className="font-semibold text-slate-900 mb-2">Audio Files</h3>
                  <p className="text-sm text-slate-600">
                    📁 {formData.audioFiles.length} files to merge
                  </p>
                </div>

                <div className="border border-slate-200 rounded-lg p-4">
                  <h3 className="font-semibold text-slate-900 mb-2">Participants</h3>
                  <p className="text-sm text-slate-600">
                    👥 {formData.participants.filter(p => p.name).length} registered
                  </p>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-semibold text-blue-900 mb-2">Processing Pipeline</h3>
                  <ol className="text-sm text-blue-800 space-y-1">
                    <li>1️⃣ Merge audio files</li>
                    <li>2️⃣ Diarization (speaker identification)</li>
                    <li>3️⃣ Transcription (Whisper)</li>
                    <li>4️⃣ Analysis (Questions, Responses, Quality)</li>
                    <li>5️⃣ Generate Report</li>
                  </ol>
                  <p className="text-xs text-blue-700 mt-2">⏱️ Estimated time: 10-15 minutes</p>
                </div>

                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="w-4 h-4 rounded border border-slate-300"
                  />
                  <span className="text-sm text-slate-600">
                    I confirm the information is correct
                  </span>
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={() => setStep(Math.max(1, step - 1))}
            disabled={step === 1}
            className="flex items-center gap-2 px-6 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft size={20} />
            Back
          </button>

          {step < 4 ? (
            <button
              onClick={() => setStep(Math.min(4, step + 1))}
              disabled={!canProceed()}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
              <ChevronRight size={20} />
            </button>
          ) : (
            <button
              onClick={handleCreate}
              className="px-8 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition font-semibold"
            >
              ✨ Create & Process Class
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
