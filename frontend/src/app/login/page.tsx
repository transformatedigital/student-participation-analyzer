'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { login } from '@/lib/auth'

export default function LoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const success = login(username, password)
    if (success) {
      window.location.href = '/clases/2026-04-07/index.html'
    } else {
      setError('Invalid username or password')
      setPassword('')
    }

    setLoading(false)
  }

  return (
    <div className="min-h-screen relative overflow-hidden bg-[#020817]">
      {/* Animated gradient orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Blue orb */}
        <div
          className="absolute w-96 h-96 bg-blue-500 rounded-full filter blur-3xl opacity-20"
          style={{
            top: '10%',
            left: '5%',
            animation: 'float 8s ease-in-out infinite',
          }}
        />
        {/* Purple orb */}
        <div
          className="absolute w-96 h-96 bg-purple-500 rounded-full filter blur-3xl opacity-20"
          style={{
            top: '50%',
            right: '10%',
            animation: 'float 10s ease-in-out infinite 1s',
          }}
        />
        {/* Cyan orb */}
        <div
          className="absolute w-96 h-96 bg-cyan-500 rounded-full filter blur-3xl opacity-20"
          style={{
            bottom: '5%',
            left: '30%',
            animation: 'float 12s ease-in-out infinite 2s',
          }}
        />
      </div>

      {/* Subtle grid overlay */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(0deg, transparent 24%, rgba(255,255,255,.05) 25%, rgba(255,255,255,.05) 26%, transparent 27%, transparent 74%, rgba(255,255,255,.05) 75%, rgba(255,255,255,.05) 76%, transparent 77%, transparent),
            linear-gradient(90deg, transparent 24%, rgba(255,255,255,.05) 25%, rgba(255,255,255,.05) 26%, transparent 27%, transparent 74%, rgba(255,255,255,.05) 75%, rgba(255,255,255,.05) 76%, transparent 77%, transparent)
          `,
          backgroundSize: '60px 60px',
        }}
      />

      {/* Login card */}
      <div className="relative z-10 min-h-screen flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-10 shadow-2xl">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center gap-2 mb-2">
                <h1 className="text-2xl font-bold text-white">KAIST·GDI</h1>
                <span className="px-3 py-1 bg-blue-500/30 border border-blue-400/50 rounded-full text-xs font-semibold text-blue-200">
                  GDI.60030(1)
                </span>
              </div>
              <p className="text-white/70 text-sm mb-1">Global Technology Commercialization</p>
              <p className="text-white/50 text-xs">Spring 2026</p>
            </div>

            <div className="w-full h-px bg-gradient-to-r from-transparent via-white/20 to-transparent mb-8" />

            {/* Welcome text */}
            <h2 className="text-3xl font-bold text-white mb-8">Welcome</h2>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Username input */}
              <div>
                <label className="block text-white/60 text-sm font-medium mb-2">Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="assistant"
                  className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg text-white placeholder-white/40 focus:outline-none focus:border-blue-400 focus:bg-white/10 transition"
                  autoComplete="username"
                  disabled={loading}
                />
              </div>

              {/* Password input */}
              <div>
                <label className="block text-white/60 text-sm font-medium mb-2">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg text-white placeholder-white/40 focus:outline-none focus:border-blue-400 focus:bg-white/10 transition"
                  autoComplete="current-password"
                  disabled={loading}
                />
              </div>

              {/* Error message */}
              {error && <p className="text-red-400 text-sm font-medium">{error}</p>}

              {/* Submit button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 mt-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-purple-700 transition transform hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 flex items-center justify-center gap-2"
              >
                {loading ? 'Entering...' : 'Enter Platform →'}
              </button>
            </form>

            {/* Footer info */}
            <p className="text-white/40 text-xs text-center mt-8">
              KAIST Graduate School of Innovation & Technology Management
            </p>
          </div>
        </div>
      </div>

      {/* Animations */}
      <style jsx>{`
        @keyframes float {
          0%,
          100% {
            transform: translateY(0) translateX(0);
          }
          25% {
            transform: translateY(-20px) translateX(10px);
          }
          50% {
            transform: translateY(-40px) translateX(0);
          }
          75% {
            transform: translateY(-20px) translateX(-10px);
          }
        }
      `}</style>
    </div>
  )
}
