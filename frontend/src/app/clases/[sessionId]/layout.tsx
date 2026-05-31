'use client'

import { useParams, usePathname } from 'next/navigation'
import Link from 'next/link'
import { BarChart3, FileText, Users, MessageSquare, Star, Mic } from 'lucide-react'

interface NavItem {
  icon: React.ReactNode
  label: string
  href: string
}

export default function SessionLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const params = useParams()
  const pathname = usePathname()
  const sessionId = params?.sessionId as string

  const navItems: NavItem[] = [
    {
      icon: <BarChart3 size={20} />,
      label: 'Overview',
      href: `/clases/${sessionId}`
    },
    {
      icon: <FileText size={20} />,
      label: 'Transcription',
      href: `/clases/${sessionId}/transcripcion`
    },
    {
      icon: <MessageSquare size={20} />,
      label: 'Participation',
      href: `/clases/${sessionId}/participacion`
    },
    {
      icon: <Star size={20} />,
      label: 'Evaluation',
      href: `/clases/${sessionId}/evaluacion`
    },
    {
      icon: <Users size={20} />,
      label: 'Speakers',
      href: `/clases/${sessionId}/hablantes`
    },
    {
      icon: <Mic size={20} />,
      label: 'Voice Verify',
      href: `/clases/${sessionId}/verificacion-voces`
    }
  ]

  const isActive = (href: string) => {
    if (href === `/clases/${sessionId}`) {
      return pathname === href || pathname === `${href}/`
    }
    return pathname.startsWith(href)
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="w-56 bg-white border-r border-slate-200 fixed h-screen">
        <div className="p-6">
          <Link href="/clases" className="flex items-center gap-2 mb-8">
            <div className="text-2xl">📊</div>
            <span className="font-semibold text-slate-900">Clase</span>
          </Link>

          {/* Session Info */}
          <div className="mb-8 pb-6 border-b border-slate-200">
            <p className="text-xs font-medium text-slate-500 uppercase">Session</p>
            <p className="text-sm font-medium text-slate-900 mt-2">
              {new Date(sessionId).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric'
              })}
            </p>
          </div>

          {/* Navigation */}
          <nav className="space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-2 rounded-lg transition ${
                  isActive(item.href)
                    ? 'bg-blue-50 text-blue-700 border-l-2 border-l-blue-600'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                {item.icon}
                <span className="text-sm font-medium">{item.label}</span>
              </Link>
            ))}
          </nav>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-56">
        {children}
      </main>
    </div>
  )
}
