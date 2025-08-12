import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Navigation from '@/components/layout/navigation'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: '数据管理平台 - MinIO & Elasticsearch',
  description: 'MinIO 文件管理和 Elasticsearch 查询管理平台',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Navigation />
        <main className="min-h-screen bg-gray-50">
          {children}
        </main>
      </body>
    </html>
  )
}