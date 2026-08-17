import { Box, Minus, Package, Plus, ShoppingBag, Trash2, X } from 'lucide-react'
import { useState } from 'react'

import { useCart } from '../hooks/useCart'
import { formatPrice } from '../lib/format'
import type { Product } from '../types/api'

interface ProductSheetProps {
  product: Product
  onClose: () => void
}

export function ProductSheet({ product, onClose }: ProductSheetProps) {
  const { getItemQuantity, updateQuantity, addItem, removeItem } = useCart()
  const inCartQty = getItemQuantity(product.id)

  const [quantity, setQuantity] = useState<number>(() => (inCartQty > 0 ? inCartQty : 1))

  const handleIncrement = () => {
    setQuantity((q) => q + 1)
  }

  const handleDecrement = () => {
    setQuantity((q) => Math.max(1, q - 1))
  }

  const handleAddToCart = () => {
    if (inCartQty > 0) {
      updateQuantity(product.id, quantity)
    } else {
      addItem(product, quantity)
    }
    onClose()
  }

  const handleRemove = () => {
    removeItem(product.id)
    onClose()
  }

  const numericPrice = Number(product.price || 0)
  const totalItemPrice = numericPrice * quantity

  return (
    <div className="product-sheet-backdrop" role="presentation" onClick={onClose}>
      <section
        aria-label={`Информация о товаре ${product.name}`}
        className="product-sheet"
        role="dialog"
        aria-modal="true"
        onClick={(event) => event.stopPropagation()}
      >
        <button className="product-sheet__close" type="button" onClick={onClose}>
          <X size={22} aria-label="Закрыть" />
        </button>
        <span className="product-sheet__visual" aria-hidden="true">
          <Box size={44} strokeWidth={1.4} />
        </span>
        <h2>{product.name}</h2>
        <p className="product-sheet__price">{formatPrice(product.price)}</p>

        <dl className="product-sheet__attributes">
          {product.weight && product.weight !== '0.000' && (
            <div>
              <dt>Вес</dt>
              <dd>{product.weight} кг</dd>
            </div>
          )}
          {product.volume && product.volume !== '0.000' && (
            <div>
              <dt>Объём</dt>
              <dd>{product.volume} м³</dd>
            </div>
          )}
          {product.items_in_box > 1 && (
            <div>
              <dt>В коробке</dt>
              <dd>
                <Package size={15} aria-hidden="true" /> {product.items_in_box} шт.
              </dd>
            </div>
          )}
        </dl>

        <div className="product-sheet__cart-section">
          <div className="product-sheet__quantity-selector">
            <span className="product-sheet__quantity-label">Количество</span>
            <div className="quantity-controls">
              <button
                className="quantity-btn"
                type="button"
                onClick={handleDecrement}
                disabled={quantity <= 1}
                aria-label="Уменьшить количество"
              >
                <Minus size={18} />
              </button>
              <span className="quantity-value">{quantity}</span>
              <button
                className="quantity-btn"
                type="button"
                onClick={handleIncrement}
                aria-label="Увеличить количество"
              >
                <Plus size={18} />
              </button>
            </div>
          </div>

          <button className="product-sheet__add-btn" type="button" onClick={handleAddToCart}>
            <ShoppingBag size={20} strokeWidth={2} />
            <span>
              {inCartQty > 0 ? 'Сохранить' : 'В корзину'} · {formatPrice(totalItemPrice)}
            </span>
          </button>

          {inCartQty > 0 && (
            <button
              className="product-sheet__remove-btn"
              type="button"
              onClick={handleRemove}
              aria-label="Удалить из корзины"
            >
              <Trash2 size={16} />
              <span>Удалить из корзины</span>
            </button>
          )}
        </div>
      </section>
    </div>
  )
}
