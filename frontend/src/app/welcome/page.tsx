'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getUser, logout } from '@/lib/auth'
import { LogOut, ArrowRight } from 'lucide-react'

interface User {
  username: string
  name: string
  role: 'TA' | 'Professor'
}

export default function WelcomePage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const currentUser = getUser()
    if (!currentUser) {
      router.push('/login')
    } else {
      setUser(currentUser)
    }
  }, [router])

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  const handleEnterPlatform = () => {
    window.location.href = '/clases/2026-04-07/dashboard.html'
  }

  if (!mounted || !user) {
    return (
      <div className="min-h-screen bg-[#020817] flex items-center justify-center">
        <div className="text-white/50">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen relative overflow-hidden bg-[#020817]">
      {/* Animated gradient orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute w-96 h-96 bg-blue-500 rounded-full filter blur-3xl opacity-20"
          style={{
            top: '5%',
            right: '5%',
            animation: 'float 8s ease-in-out infinite',
          }}
        />
        <div
          className="absolute w-96 h-96 bg-purple-500 rounded-full filter blur-3xl opacity-20"
          style={{
            bottom: '10%',
            left: '10%',
            animation: 'float 10s ease-in-out infinite 1s',
          }}
        />
        <div
          className="absolute w-96 h-96 bg-cyan-500 rounded-full filter blur-3xl opacity-20"
          style={{
            top: '50%',
            right: '20%',
            animation: 'float 12s ease-in-out infinite 2s',
          }}
        />
      </div>

      {/* Grid overlay */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(0deg, transparent 24%, rgba(255,255,255,.03) 25%, rgba(255,255,255,.03) 26%, transparent 27%, transparent 74%, rgba(255,255,255,.03) 75%, rgba(255,255,255,.03) 76%, transparent 77%, transparent),
            linear-gradient(90deg, transparent 24%, rgba(255,255,255,.03) 25%, rgba(255,255,255,.03) 26%, transparent 27%, transparent 74%, rgba(255,255,255,.03) 75%, rgba(255,255,255,.03) 76%, transparent 77%, transparent)
          `,
          backgroundSize: '80px 80px',
        }}
      />

      {/* Content */}
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center p-4">
        {/* Logout button (top right) */}
        <button
          onClick={handleLogout}
          className="absolute top-8 right-8 p-2 text-white/40 hover:text-white/80 transition"
          title="Logout"
        >
          <LogOut size={20} />
        </button>

        {/* Main content */}
        <div className="max-w-2xl w-full">
          {/* Greeting */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-white mb-4">
              Welcome, {user.name}
            </h1>
            <div className="flex items-center justify-center gap-3">
              <span
                className={`px-4 py-2 rounded-full text-sm font-semibold border ${
                  user.role === 'Professor'
                    ? 'bg-emerald-500/20 border-emerald-400/50 text-emerald-200'
                    : 'bg-blue-500/20 border-blue-400/50 text-blue-200'
                }`}
              >
                {user.role === 'Professor' ? '👨‍🏫 Professor' : '👨‍💻 Teaching Assistant'}
              </span>
            </div>
          </div>

          {/* Course card */}
          <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-12 mb-8 shadow-2xl">
            {/* Course code */}
            <div className="flex items-center gap-3 mb-4">
              <div className="w-2 h-2 bg-blue-400 rounded-full" />
              <span className="text-blue-300 text-sm font-semibold">GDI.60030(1)</span>
            </div>

            {/* Course title */}
            <h2 className="text-4xl font-bold text-white mb-2">
              Global Technology Commercialization
            </h2>

            {/* Institution */}
            <p className="text-white/60 mb-8 text-lg">
              KAIST Graduate School of Innovation & Technology Management
            </p>

            {/* Divider */}
            <div className="w-full h-px bg-gradient-to-r from-transparent via-white/20 to-transparent mb-8" />

            {/* Course stats */}
            <div className="grid grid-cols-3 gap-6">
              <div>
                <p className="text-white/50 text-sm mb-2">Semester</p>
                <p className="text-white text-lg font-semibold">Spring 2026</p>
              </div>
              <div>
                <p className="text-white/50 text-sm mb-2">Session</p>
                <p className="text-white text-lg font-semibold">April 7</p>
              </div>
              <div>
                <p className="text-white/50 text-sm mb-2">Students</p>
                <p className="text-white text-lg font-semibold">4 Evaluated</p>
              </div>
            </div>
          </div>

          {/* Primary button */}
          <button
            onClick={handleEnterPlatform}
            className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-purple-700 transition transform hover:scale-105 flex items-center justify-center gap-3 text-lg mb-6"
          >
            Enter Analytics Platform
            <ArrowRight size={20} />
          </button>

          {/* Footer text */}
          <p className="text-white/30 text-center text-sm">
            Classroom Participation Analysis Platform
          </p>
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
