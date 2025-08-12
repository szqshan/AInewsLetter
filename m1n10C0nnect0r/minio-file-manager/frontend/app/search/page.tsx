"use client"

import { useEffect, useMemo, useState } from 'react'
import { searchApi, type SearchResultItem } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

type TabKey = 'files' | 'documents'

export default function SearchPage() {
  const [tab, setTab] = useState<TabKey>('files')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [fileResults, setFileResults] = useState<SearchResultItem[]>([])
  const [docResults, setDocResults] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)

  const canSearch = useMemo(() => query.trim().length > 0, [query])

  const onSearch = async () => {
    if (!canSearch) return
    setLoading(true)
    setError(null)
    try {
      if (tab === 'files') {
        const res = await searchApi.searchFiles({ query, size: 20 })
        setFileResults(res.results)
      } else {
        const res = await searchApi.searchDocuments({ query, fuzzy: true, size: 20 })
        setDocResults(res.documents)
      }
    } catch (e: any) {
      setError(e?.message || 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // enter to search
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Enter') onSearch()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [tab, query])

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-semibold">Search</h1>

      <div className="flex items-center space-x-2">
        <Input
          placeholder="Type keywords..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button onClick={onSearch} disabled={!canSearch || loading}>
          {loading ? 'Searching...' : 'Search'}
        </Button>
      </div>

      <div className="flex space-x-2">
        <Button variant={tab === 'files' ? 'default' : 'outline'} onClick={() => setTab('files')}>Files</Button>
        <Button variant={tab === 'documents' ? 'default' : 'outline'} onClick={() => setTab('documents')}>Documents</Button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded">{error}</div>
      )}

      {tab === 'files' ? (
        <div className="space-y-2">
          {fileResults.length === 0 && !loading && <p className="text-muted-foreground">No results</p>}
          {fileResults.map((item) => (
            <div key={`${item.bucket}/${item.object_name}`} className="border rounded p-3">
              <div className="font-medium">{item.file_name}</div>
              <div className="text-sm text-muted-foreground">{item.bucket} / {item.object_name}</div>
              {item.highlight?.object_name && (
                <div className="text-xs mt-1" dangerouslySetInnerHTML={{ __html: item.highlight.object_name[0] }} />
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {docResults.length === 0 && !loading && <p className="text-muted-foreground">No results</p>}
          {docResults.map((doc) => (
            <div key={doc._id || doc.content_hash} className="border rounded p-3">
              <div className="font-medium">{doc.title || doc.object_name}</div>
              <div className="text-sm text-muted-foreground">{doc.bucket_name} / {doc.object_name}</div>
              {doc._highlight?.content?.length > 0 && (
                <div className="text-xs mt-1" dangerouslySetInnerHTML={{ __html: doc._highlight.content[0] }} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


