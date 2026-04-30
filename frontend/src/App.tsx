import { useEffect, useState } from 'react'
import { fetchHealth } from './api'

export default function App() {
  const [message, setMessage] = useState('Loading backend health...')
  useEffect(() => {
    fetchHealth().then((h) => setMessage(`${h.app}: ${h.status} (${h.version})`)).catch((e) => setMessage(`Backend unavailable: ${e.message}`))
  }, [])
  return <main><h1>Local 3D Room Mapper</h1><p>{message}</p></main>
}
