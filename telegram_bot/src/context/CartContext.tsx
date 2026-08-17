import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { CartContext, type CartContextValue } from './cart-context'
import type { Product } from '../types/api'
import type { CartItem, CartSummary } from '../types/cart'

const CART_STORAGE_KEY = 'viridi_cart_items'

function loadInitialCart(): CartItem[] {
  if (typeof window === 'undefined') {
    return []
  }

  try {
    const saved = localStorage.getItem(CART_STORAGE_KEY)
    if (!saved) return []
    const parsed = JSON.parse(saved)
    if (Array.isArray(parsed)) {
      return parsed.filter(
        (item): item is CartItem =>
          Boolean(item?.product?.id) && typeof item?.quantity === 'number' && item.quantity > 0,
      )
    }
  } catch {
  }

  return []
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>(loadInitialCart)

  useEffect(() => {
    try {
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items))
    } catch {
    }
  }, [items])

  const getItemQuantity = useCallback(
    (productId: string): number => {
      const item = items.find((entry) => entry.product.id === productId)
      return item ? item.quantity : 0
    },
    [items],
  )

  const addItem = useCallback((product: Product, quantity = 1) => {
    if (quantity <= 0) return

    setItems((prevItems) => {
      const existingIndex = prevItems.findIndex((entry) => entry.product.id === product.id)
      if (existingIndex > -1) {
        const updated = [...prevItems]
        const current = updated[existingIndex]
        updated[existingIndex] = {
          ...current,
          quantity: current.quantity + quantity,
        }
        return updated
      }

      return [...prevItems, { product, quantity }]
    })
  }, [])

  const updateQuantity = useCallback((productId: string, quantity: number) => {
    setItems((prevItems) => {
      if (quantity <= 0) {
        return prevItems.filter((entry) => entry.product.id !== productId)
      }

      return prevItems.map((entry) =>
        entry.product.id === productId ? { ...entry, quantity } : entry,
      )
    })
  }, [])

  const incrementQuantity = useCallback((productId: string) => {
    setItems((prevItems) =>
      prevItems.map((entry) =>
        entry.product.id === productId ? { ...entry, quantity: entry.quantity + 1 } : entry,
      ),
    )
  }, [])

  const decrementQuantity = useCallback((productId: string) => {
    setItems((prevItems) =>
      prevItems
        .map((entry) => {
          if (entry.product.id === productId) {
            const nextQuantity = entry.quantity - 1
            return nextQuantity > 0 ? { ...entry, quantity: nextQuantity } : null
          }
          return entry
        })
        .filter((entry): entry is CartItem => entry !== null),
    )
  }, [])

  const removeItem = useCallback((productId: string) => {
    setItems((prevItems) => prevItems.filter((entry) => entry.product.id !== productId))
  }, [])

  const clearCart = useCallback(() => {
    setItems([])
  }, [])

  const summary = useMemo<CartSummary>(() => {
    let totalItems = 0
    let totalPrice = 0
    let totalWeight = 0
    let totalVolume = 0

    for (const item of items) {
      const qty = item.quantity
      totalItems += qty
      totalPrice += Number(item.product.price || 0) * qty
      totalWeight += Number(item.product.weight || 0) * qty
      totalVolume += Number(item.product.volume || 0) * qty
    }

    return {
      totalItems,
      totalUniqueItems: items.length,
      totalPrice,
      totalWeight,
      totalVolume,
    }
  }, [items])

  const value = useMemo<CartContextValue>(
    () => ({
      items,
      summary,
      addItem,
      removeItem,
      updateQuantity,
      incrementQuantity,
      decrementQuantity,
      clearCart,
      getItemQuantity,
    }),
    [
      items,
      summary,
      addItem,
      removeItem,
      updateQuantity,
      incrementQuantity,
      decrementQuantity,
      clearCart,
      getItemQuantity,
    ],
  )

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}
