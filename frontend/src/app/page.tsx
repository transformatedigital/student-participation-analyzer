'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { isAuthenticated } from '@/lib/auth'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    const authenticated = isAuthenticated()
    if (authenticated) {
      router.push('/clases')
    } else {
      router.push('/login')
    }
  }, [router])

  return (
    <div className="min-h-screen bg-[#020817] flex items-center justify-center">
      <div className="text-center">
        <div className="text-4xl mb-4">📊</div>
        <p className="text-white/50">Loading Clase Analytics...</p>
      </div>
    </div>
  )
}
