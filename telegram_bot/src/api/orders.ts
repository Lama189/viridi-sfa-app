import { apiClient } from './client'
import type { CreateOrderPayload, OrderResponse } from '../types/api'

export async function createOrder(payload: CreateOrderPayload): Promise<OrderResponse> {
  const { data } = await apiClient.post<OrderResponse>('/orders', payload)
  return data
}

export async function getClientOrders(
  clientId: string,
  statuses?: string[],
): Promise<OrderResponse[]> {
  const { data } = await apiClient.get<OrderResponse[]>(`/clients/${clientId}/orders`, {
    params: statuses && statuses.length > 0 ? { statuses } : undefined,
  })
  return data
}

export async function getOrderById(orderId: string): Promise<OrderResponse> {
  const { data } = await apiClient.get<OrderResponse>(`/orders/${orderId}`)
  return data
}

export async function cancelOrder(orderId: string): Promise<void> {
  await apiClient.delete(`/orders/${orderId}`)
}
