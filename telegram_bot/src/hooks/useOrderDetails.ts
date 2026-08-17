import { useQuery } from '@tanstack/react-query'
import { getOrderById } from '../api/orders'
import type { OrderResponse } from '../types/api'

export function useOrderDetails(orderId: string | null) {
  return useQuery<OrderResponse, Error>({
    queryKey: ['order-details', orderId],
    queryFn: () => getOrderById(orderId!),
    enabled: Boolean(orderId),
  })
}
