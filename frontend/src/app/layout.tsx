import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Clase Analytics',
  description: 'Classroom Participation Analysis Platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
