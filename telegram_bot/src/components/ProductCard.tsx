import { Box, ChevronRight, Package, Plus, Check } from 'lucide-react'

import { useCart } from '../hooks/useCart'
import { formatPrice } from '../lib/format'
import type { Product } from '../types/api'

interface ProductCardProps {
  product: Product
  onClick: (product: Product) => void
}

export function ProductCard({ product, onClick }: ProductCardProps) {
  const { getItemQuantity, addItem } = useCart()
  const inCartQuantity = getItemQuantity(product.id)

  const productDetails = [
    product.weight !== '0.000' && product.weight ? `${product.weight} кг` : null,
    product.items_in_box > 1 ? `${product.items_in_box} шт.` : null,
  ].filter(Boolean)

  const handleQuickAdd = (event: React.MouseEvent) => {
    event.stopPropagation()
    addItem(product, 1)
  }

  return (
    <div className="product-card" role="button" tabIndex={0} onClick={() => onClick(product)}>
      <span className="product-card__visual" aria-hidden="true">
        <Box size={28} strokeWidth={1.5} />
      </span>
      <span className="product-card__content">
        <span className="product-card__name">{product.name}</span>
        {productDetails.length > 0 && (
          <span className="product-card__details">
            <Package size={14} aria-hidden="true" />
            {productDetails.join(' · ')}
          </span>
        )}
        <span className="product-card__price">{formatPrice(product.price)}</span>
      </span>

      <div className="product-card__actions" onClick={(e) => e.stopPropagation()}>
        {inCartQuantity > 0 ? (
          <button
            className="product-card__cart-indicator"
            type="button"
            onClick={handleQuickAdd}
            title="Добавить ещё 1 шт."
            aria-label={`В корзине ${inCartQuantity} шт. Добавить ещё.`}
          >
            <Check size={14} strokeWidth={2.5} />
            <span>{inCartQuantity}</span>
          </button>
        ) : (
          <button
            className="product-card__add-btn"
            type="button"
            onClick={handleQuickAdd}
            title="Добавить в корзину"
            aria-label={`Добавить ${product.name} в корзину`}
          >
            <Plus size={18} strokeWidth={2.2} />
          </button>
        )}
      </div>

      <ChevronRight className="product-card__arrow" size={20} aria-hidden="true" />
    </div>
  )
}
