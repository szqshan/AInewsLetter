"use client"

import { useState, useCallback } from 'react'
import { Upload, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useMinioStore } from '@/store/minio-store'
import { objectApi } from '@/lib/api'

export function FileUpload() {
  const { currentBucket } = useMinioStore()
  const [isDragging, setIsDragging] = useState(false)
  const [uploadingFiles, setUploadingFiles] = useState<Set<string>>(new Set())

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)

      if (!currentBucket) return

      const files = Array.from(e.dataTransfer.files)
      await uploadFiles(files)
    },
    [currentBucket]
  )

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      if (!currentBucket || !e.target.files) return

      const files = Array.from(e.target.files)
      await uploadFiles(files)
    },
    [currentBucket]
  )

  const uploadFiles = async (files: File[]) => {
    if (!currentBucket) return

    for (const file of files) {
      const fileName = file.name
      setUploadingFiles((prev) => new Set(prev).add(fileName))

      try {
        await objectApi.upload(currentBucket, file)
        window.location.reload()
      } catch (error: any) {
        console.error(`Failed to upload ${fileName}:`, error)
      } finally {
        setUploadingFiles((prev) => {
          const newSet = new Set(prev)
          newSet.delete(fileName)
          return newSet
        })
      }
    }
  }

  if (!currentBucket) return null

  return (
    <div className="p-4 border-b">
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging ? 'border-primary bg-primary/10' : 'border-muted-foreground/25'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
        <p className="mt-2 text-sm text-muted-foreground">
          Drag and drop files here, or click to select files
        </p>
        <input
          type="file"
          multiple
          className="hidden"
          id="file-upload"
          onChange={handleFileSelect}
        />
        <label htmlFor="file-upload">
          <Button className="mt-4" asChild>
            <span>Select Files</span>
          </Button>
        </label>
      </div>

      {uploadingFiles.size > 0 && (
        <div className="mt-4 space-y-2">
          <p className="text-sm font-medium">Uploading:</p>
          {Array.from(uploadingFiles).map((fileName) => (
            <div key={fileName} className="flex items-center space-x-2 text-sm">
              <div className="h-2 w-2 bg-blue-500 rounded-full animate-pulse" />
              <span>{fileName}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}