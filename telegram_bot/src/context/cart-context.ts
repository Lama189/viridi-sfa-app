import { createContext } from 'react'

import type { Product } from '../types/api'
import type { CartItem, CartSummary } from '../types/cart'

export interface CartContextValue {
  items: CartItem[]
  summary: CartSummary
  addItem: (product: Product, quantity?: number) => void
  removeItem: (productId: string) => void
  updateQuantity: (productId: string, quantity: number) => void
  incrementQuantity: (productId: string) => void
  decrementQuantity: (productId: string) => void
  clearCart: () => void
  getItemQuantity: (productId: string) => number
}

export const CartContext = createContext<CartContextValue | null>(null)
