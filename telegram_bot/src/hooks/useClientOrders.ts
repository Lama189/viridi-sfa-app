import { useQuery } from '@tanstack/react-query'
import { getClientRetailPointOrders } from '../api/orders'
import type { OrderResponse } from '../types/api'

export function useClientOrders(clientId: string, statuses?: string[]) {
  return useQuery<OrderResponse[], Error>({
    queryKey: ['client-retail-point-orders', clientId, statuses],
    queryFn: () => getClientRetailPointOrders(clientId, statuses),
    enabled: Boolean(clientId),
  })
}
