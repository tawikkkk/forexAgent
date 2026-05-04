import { useEffect, useState } from 'react'

const API_URL = 'http://localhost:8000/'

function TrainingStatus() {
  const [isOnline, setIsOnline] = useState(false)

  useEffect(() => {
    let isMounted = true

    async function checkStatus() {
      try {
        const response = await fetch(API_URL)
        const data = await response.json()

        if (isMounted) {
          setIsOnline(response.ok && data.status === 'online')
        }
      } catch {
        if (isMounted) {
          setIsOnline(false)
        }
      }
    }

    checkStatus()
    const intervalId = window.setInterval(checkStatus, 30000)

    return () => {
      isMounted = false
      window.clearInterval(intervalId)
    }
  }, [])

  return (
    <div className={`status-badge ${isOnline ? 'online' : 'offline'}`}>
      <span aria-hidden="true">{isOnline ? '🟢' : '🔴'}</span>
      <span>{isOnline ? 'Model Online' : 'Model Offline'}</span>
    </div>
  )
}

export default TrainingStatus
