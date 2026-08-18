import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createOrder } from '../api/orders'
import type { CreateOrderPayload, OrderResponse } from '../types/api'

export function useCreateOrder() {
  const queryClient = useQueryClient()

  return useMutation<OrderResponse, Error, CreateOrderPayload>({
    mutationFn: (payload) => createOrder(payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['client-orders'] }),
        queryClient.invalidateQueries({ queryKey: ['client-retail-point-orders'] }),
      ])
    },
  })
}
