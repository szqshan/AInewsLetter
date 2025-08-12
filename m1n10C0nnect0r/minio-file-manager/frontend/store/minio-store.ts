import { create } from 'zustand'
import { Bucket, MinioObject } from '@/lib/api'

interface MinioStore {
  buckets: Bucket[]
  currentBucket: string | null
  objects: MinioObject[]
  loading: boolean
  error: string | null

  setBuckets: (buckets: Bucket[]) => void
  setCurrentBucket: (bucket: string | null) => void
  setObjects: (objects: MinioObject[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  reset: () => void
}

export const useMinioStore = create<MinioStore>((set) => ({
  buckets: [],
  currentBucket: null,
  objects: [],
  loading: false,
  error: null,

  setBuckets: (buckets) => set({ buckets }),
  setCurrentBucket: (bucket) => set({ currentBucket: bucket }),
  setObjects: (objects) => set({ objects }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  reset: () => set({
    buckets: [],
    currentBucket: null,
    objects: [],
    loading: false,
    error: null,
  }),
}))