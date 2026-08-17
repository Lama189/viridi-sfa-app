import { apiClient } from './client'
import type { CreateOrderPayload, OrderResponse } from '../types/api'

export async function createOrder(payload: CreateOrderPayload): Promise<OrderResponse> {
  const { data } = await apiClient.post<OrderResponse>('/orders', payload)
  return data
}
