import { useQuery } from '@tanstack/react-query'
import { getClientOrders } from '../api/orders'
import type { OrderResponse } from '../types/api'

export function useClientOrders(clientId: string, statuses?: string[]) {
  return useQuery<OrderResponse[], Error>({
    queryKey: ['client-orders', clientId, statuses],
    queryFn: () => getClientOrders(clientId, statuses),
    enabled: Boolean(clientId),
  })
}
