import { useMutation, useQueryClient } from '@tanstack/react-query'
import { cancelOrder } from '../api/orders'

export function useCancelOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (orderId: string) => cancelOrder(orderId),
    onSuccess: async (_, orderId) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['client-orders'] }),
        queryClient.invalidateQueries({ queryKey: ['order-details', orderId] }),
      ])
    },
  })
}
