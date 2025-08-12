"use client"

import { useEffect, useState } from 'react'
import { File, Folder, Download, Trash2, Copy, Link } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useMinioStore } from '@/store/minio-store'
import { objectApi } from '@/lib/api'
import { format } from 'date-fns'

export function ObjectList() {
  const { currentBucket, objects, setObjects, setLoading, setError } = useMinioStore()
  const [selectedObject, setSelectedObject] = useState<string | null>(null)

  useEffect(() => {
    if (currentBucket) {
      loadObjects()
    }
  }, [currentBucket])

  const loadObjects = async () => {
    if (!currentBucket) return

    try {
      setLoading(true)
      const data = await objectApi.list(currentBucket)
      setObjects(data)
    } catch (error: any) {
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  const downloadObject = async (objectName: string) => {
    if (!currentBucket) return

    try {
      const response = await objectApi.download(currentBucket, objectName)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', objectName.split('/').pop() || objectName)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error: any) {
      setError(error.message)
    }
  }

  const deleteObject = async (objectName: string) => {
    if (!currentBucket) return
    if (!confirm(`Are you sure you want to delete "${objectName}"?`)) return

    try {
      await objectApi.delete(currentBucket, objectName)
      await loadObjects()
    } catch (error: any) {
      setError(error.message)
    }
  }

  const getPresignedUrl = async (objectName: string) => {
    if (!currentBucket) return

    try {
      const { url } = await objectApi.getPresignedUrl(currentBucket, objectName)
      await navigator.clipboard.writeText(url)
      alert('Presigned URL copied to clipboard!')
    } catch (error: any) {
      setError(error.message)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  if (!currentBucket) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-muted-foreground">Select a bucket to view objects</p>
      </div>
    )
  }

  return (
    <div className="flex-1 p-4">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Objects in {currentBucket}</h2>
      </div>

      <div className="space-y-2">
        {objects.length === 0 ? (
          <p className="text-muted-foreground">No objects in this bucket</p>
        ) : (
          objects.map((object) => (
            <div
              key={object.name}
              className={`flex items-center justify-between rounded-lg border p-3 hover:bg-muted/10 ${
                selectedObject === object.name ? 'bg-muted/20' : ''
              }`}
              onClick={() => setSelectedObject(object.name)}
            >
              <div className="flex items-center space-x-3">
                {object.is_dir ? (
                  <Folder className="h-5 w-5 text-blue-500" />
                ) : (
                  <File className="h-5 w-5 text-gray-500" />
                )}
                <div>
                  <p className="font-medium">{object.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatFileSize(object.size)} •{' '}
                    {object.last_modified &&
                      format(new Date(object.last_modified), 'MMM d, yyyy HH:mm')}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-1">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation()
                    downloadObject(object.name)
                  }}
                >
                  <Download className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation()
                    getPresignedUrl(object.name)
                  }}
                >
                  <Link className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation()
                    deleteObject(object.name)
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}