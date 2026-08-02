import { Box, ChevronRight, Package } from 'lucide-react'

import type { Product } from '../types/api'

interface ProductCardProps {
  product: Product
  onClick: (product: Product) => void
}

function formatPrice(price: string): string {
  return `${new Intl.NumberFormat('ru-RU').format(Number(price))} сум`
}

export function ProductCard({ product, onClick }: ProductCardProps) {
  const productDetails = [
    product.weight !== '0.000' ? `${product.weight} кг` : null,
    product.items_in_box > 1 ? `${product.items_in_box} шт.` : null,
  ].filter(Boolean)

  return (
    <button className="product-card" type="button" onClick={() => onClick(product)}>
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
      <ChevronRight className="product-card__arrow" size={20} aria-hidden="true" />
    </button>
  )
}
