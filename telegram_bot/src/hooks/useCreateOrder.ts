import { useMutation } from '@tanstack/react-query'
import { createOrder } from '../api/orders'
import type { CreateOrderPayload, OrderResponse } from '../types/api'

export function useCreateOrder() {
  return useMutation<OrderResponse, Error, CreateOrderPayload>({
    mutationFn: (payload) => createOrder(payload),
  })
}
