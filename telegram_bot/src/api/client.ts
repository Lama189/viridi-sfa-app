import axios, { type InternalAxiosRequestConfig } from 'axios'

import type { ClientAuthResponse } from '../types/api'

const AUTH_STORAGE_KEY = 'viridi-market-auth'
const rawBaseUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'
const apiBaseUrl = rawBaseUrl.includes('/api/v1')
  ? rawBaseUrl
  : `${rawBaseUrl.replace(/\/+$/, '')}/api/v1`

export interface AuthTokens {
  accessToken: string
  refreshToken: string
}

export function getMediaThumbnailUrl(photoId: string | null | undefined): string | null {
  if (!photoId) return null
  return `${apiBaseUrl}/media/${photoId}/thumbnail`
}

export function getMediaContentUrl(photoId: string | null | undefined): string | null {
  if (!photoId) return null
  return `${apiBaseUrl}/media/${photoId}/content`
}

interface RetriableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 15_000,
})

export function getAuthTokens(): AuthTokens | null {
  const serializedTokens = localStorage.getItem(AUTH_STORAGE_KEY)
  if (!serializedTokens) {
    return null
  }

  try {
    return JSON.parse(serializedTokens) as AuthTokens
  } catch {
    localStorage.removeItem(AUTH_STORAGE_KEY)
    return null
  }
}

export function saveAuthTokens(tokens: AuthTokens): void {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(tokens))
}

export function clearAuthTokens(): void {
  localStorage.removeItem(AUTH_STORAGE_KEY)
}

export function saveAuthResponse(response: ClientAuthResponse): void {
  saveAuthTokens({
    accessToken: response.access_token,
    refreshToken: response.refresh_token,
  })
}

apiClient.interceptors.request.use((config) => {
  const tokens = getAuthTokens()

  if (tokens && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${tokens.accessToken}`
  }

  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error) || !error.config || error.response?.status !== 401) {
      return Promise.reject(error)
    }

    const request = error.config as RetriableRequestConfig
    const isRefreshRequest = request.url?.endsWith('/clients/refresh')
    if (request._retry || isRefreshRequest) {
      clearAuthTokens()
      return Promise.reject(error)
    }

    const tokens = getAuthTokens()
    if (!tokens) {
      return Promise.reject(error)
    }

    request._retry = true

    try {
      const { data } = await axios.post<{ access_token: string }>(
        `${apiBaseUrl}/clients/refresh`,
        { refresh_token: tokens.refreshToken },
      )
      saveAuthTokens({
        accessToken: data.access_token,
        refreshToken: tokens.refreshToken,
      })
      request.headers.Authorization = `Bearer ${data.access_token}`
      return apiClient(request)
    } catch (refreshError) {
      clearAuthTokens()
      return Promise.reject(refreshError)
    }
  },
)
