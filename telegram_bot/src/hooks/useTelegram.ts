import { useMemo } from 'react'

import { initializeTelegram } from '../lib/telegram'

export function useTelegram() {
  return useMemo(() => initializeTelegram(), [])
}
