import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type DocumentStatus = 'READY' | 'INDEXING' | 'QUEUED' | 'ERROR'

export interface Document {
  id: string
  filename: string
  status: DocumentStatus
  size: number
  uploadTime: Date
  chunk_count?: number
  error?: string
}

export const useDocumentStore = defineStore('document', () => {
  const documents = ref<Document[]>([])
  const totalCount = computed(() => documents.value.length)
  const readyCount = computed(() => documents.value.filter(d => d.status === 'READY').length)

  function setDocuments(docs: Document[]) {
    documents.value = docs
  }

  function addDocument(doc: Document) {
    documents.value.unshift(doc)
  }

  function updateDocument(id: string, updates: Partial<Document>) {
    const index = documents.value.findIndex(d => d.id === id)
    if (index !== -1) {
      documents.value[index] = { ...documents.value[index], ...updates }
    }
  }

  function removeDocument(id: string) {
    const index = documents.value.findIndex(d => d.id === id)
    if (index !== -1) {
      documents.value.splice(index, 1)
    }
  }

  return {
    documents,
    totalCount,
    readyCount,
    setDocuments,
    addDocument,
    updateDocument,
    removeDocument
  }
})
