import type { Product } from './api'

export interface CartItem {
  product: Product
  quantity: number
}

export interface CartSummary {
  totalItems: number
  totalUniqueItems: number
  totalPrice: number
  totalWeight: number
  totalVolume: number
}
