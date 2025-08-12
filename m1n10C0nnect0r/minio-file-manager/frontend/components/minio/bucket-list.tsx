"use client"

import { useEffect, useState } from 'react'
import { Folder, Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useMinioStore } from '@/store/minio-store'
import { bucketApi } from '@/lib/api'
import { format } from 'date-fns'

export function BucketList() {
  const { buckets, currentBucket, setBuckets, setCurrentBucket, setLoading, setError } = useMinioStore()
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [newBucketName, setNewBucketName] = useState('')

  useEffect(() => {
    loadBuckets()
  }, [])

  const loadBuckets = async () => {
    try {
      setLoading(true)
      const data = await bucketApi.list()
      setBuckets(data)
    } catch (error: any) {
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  const createBucket = async () => {
    try {
      await bucketApi.create(newBucketName)
      await loadBuckets()
      setIsCreateDialogOpen(false)
      setNewBucketName('')
    } catch (error: any) {
      setError(error.message)
    }
  }

  const deleteBucket = async (bucketName: string) => {
    if (!confirm(`Are you sure you want to delete bucket "${bucketName}"?`)) return

    try {
      await bucketApi.delete(bucketName)
      if (currentBucket === bucketName) {
        setCurrentBucket(null)
      }
      await loadBuckets()
    } catch (error: any) {
      setError(error.message)
    }
  }

  return (
    <div className="w-64 border-r bg-muted/10 p-4">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Buckets</h2>
        <Button
          size="sm"
          variant="outline"
          onClick={() => setIsCreateDialogOpen(true)}
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      <div className="space-y-2">
        {buckets.map((bucket) => (
          <div
            key={bucket.name}
            className={`flex items-center justify-between rounded-lg p-2 hover:bg-muted/50 cursor-pointer ${
              currentBucket === bucket.name ? 'bg-muted' : ''
            }`}
            onClick={() => setCurrentBucket(bucket.name)}
          >
            <div className="flex items-center space-x-2">
              <Folder className="h-4 w-4" />
              <div>
                <p className="text-sm font-medium">{bucket.name}</p>
                {bucket.creation_date && (
                  <p className="text-xs text-muted-foreground">
                    {format(new Date(bucket.creation_date), 'MMM d, yyyy')}
                  </p>
                )}
              </div>
            </div>
            <Button
              size="sm"
              variant="ghost"
              onClick={(e) => {
                e.stopPropagation()
                deleteBucket(bucket.name)
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>

      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Bucket</DialogTitle>
            <DialogDescription>
              Enter a name for the new bucket. Names must be 3-63 characters long and contain only lowercase letters, numbers, and hyphens.
            </DialogDescription>
          </DialogHeader>
          <Input
            value={newBucketName}
            onChange={(e) => setNewBucketName(e.target.value)}
            placeholder="bucket-name"
            pattern="^[a-z0-9][a-z0-9.-]*[a-z0-9]$"
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={createBucket} disabled={newBucketName.length < 3}>
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}