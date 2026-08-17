import { useMutation, useQueryClient } from '@tanstack/react-query'
import { deliverOrder } from '../api/orders'

export function useDeliverOrder() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (orderId: string) => deliverOrder(orderId),
    onSuccess: async (_, orderId) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['client-orders'] }),
        queryClient.invalidateQueries({ queryKey: ['order-details', orderId] }),
      ])
    },
  })
}
