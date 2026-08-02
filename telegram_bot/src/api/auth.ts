import { apiClient, saveAuthResponse } from './client'
import type { ClientAuthResponse } from '../types/api'

export async function telegramLogin(initData: string): Promise<ClientAuthResponse> {
  const { data } = await apiClient.post<ClientAuthResponse>('/clients/telegram-login', {
    init_data: initData,
  })

  saveAuthResponse(data)
  return data
}
