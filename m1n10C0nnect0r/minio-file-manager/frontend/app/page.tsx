'use client'

import { BucketList } from '@/components/minio/bucket-list'
import { ObjectList } from '@/components/minio/object-list'
import { FileUpload } from '@/components/minio/file-upload'
import { useMinioStore } from '@/store/minio-store'

export default function Home() {
  const { currentBucket, error } = useMinioStore()

  return (
    <div className="flex h-screen">
      <BucketList />
      <div className="flex-1 flex flex-col">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 m-4 rounded">
            {error}
          </div>
        )}
        {currentBucket && <FileUpload />}
        <ObjectList />
      </div>
    </div>
  )
}