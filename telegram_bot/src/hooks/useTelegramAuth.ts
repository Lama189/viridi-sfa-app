import { useQuery } from '@tanstack/react-query'

import { telegramLogin } from '../api/auth'

export function useTelegramAuth(initData: string | undefined) {
  return useQuery({
    queryKey: ['telegram-auth', initData],
    queryFn: () => telegramLogin(initData ?? ''),
    enabled: Boolean(initData),
    staleTime: 10 * 60 * 1000,
    retry: false,
  })
}
