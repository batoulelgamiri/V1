const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export class ApiError extends Error {
  constructor(message, status, code) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

async function parseResponse(response) {
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new ApiError(payload.detail || `Request failed (${response.status})`, response.status, payload.code)
  }
  return response.json()
}

export async function apiGet(path, signal) {
  const response = await fetch(`${API_BASE}${path}`, { signal })
  return parseResponse(response)
}

export function uploadAnalysis(file, onProgress) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest()
    request.open('POST', `${API_BASE}/analyses/upload`)
    request.responseType = 'json'
    request.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress?.(Math.round((event.loaded / event.total) * 100))
    }
    request.onload = () => {
      const payload = request.response || {}
      if (request.status >= 200 && request.status < 300) resolve(payload)
      else reject(new ApiError(payload.detail || 'Upload failed.', request.status, payload.code))
    }
    request.onerror = () => reject(new ApiError('Unable to reach the analysis service.', 0))
    const data = new FormData()
    data.append('file', file)
    request.send(data)
  })
}

export const pdfUrl = (analysisId) => `${API_BASE}/analyses/${analysisId}/report/pdf`
