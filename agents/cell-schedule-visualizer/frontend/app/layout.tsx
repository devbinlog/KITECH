import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Manufacturing Schedule Visualizer',
  description: 'Interactive visualization for manufacturing schedules',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  )
}
