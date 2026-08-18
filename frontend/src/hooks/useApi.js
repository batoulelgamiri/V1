import { useEffect, useState } from 'react'
import { apiGet } from '../services/api'

export function useApi(path, dependencies = []) {
  const [state, setState] = useState({ data: null, loading: Boolean(path), error: null })

  useEffect(() => {
    if (!path) return undefined
    const controller = new AbortController()
    apiGet(path, controller.signal)
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((error) => {
        if (error.name !== 'AbortError') setState({ data: null, loading: false, error })
      })
    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, ...dependencies])

  return state
}
