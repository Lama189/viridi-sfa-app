import {
  ArrowRight,
  Box,
  Minus,
  Package,
  Plus,
  ShoppingBag,
  Trash2,
} from 'lucide-react'

import { useCart } from '../hooks/useCart'
import { formatPrice, formatVolume, formatWeight } from '../lib/format'
import type { Product } from '../types/api'

interface CartPageProps {
  onNavigateToCatalog: () => void
  onProductSelect?: (product: Product) => void
}

export function CartPage({ onNavigateToCatalog, onProductSelect }: CartPageProps) {
  const {
    items,
    summary,
    incrementQuantity,
    decrementQuantity,
    removeItem,
    clearCart,
  } = useCart()

  if (items.length === 0) {
    return (
      <section className="page cart-page">
        <header className="page-heading">
          <p className="brand-mark">Viridi market</p>
          <h1>Корзина</h1>
        </header>

        <div className="cart-empty-state">
          <div className="cart-empty-state__icon" aria-hidden="true">
            <ShoppingBag size={48} strokeWidth={1.4} />
          </div>
          <h2>Корзина пуста</h2>
          <p>Выберите товары в каталоге, чтобы сформировать заказ.</p>
          <button
            className="cart-empty-state__action"
            type="button"
            onClick={onNavigateToCatalog}
          >
            <span>Перейти в каталог</span>
            <ArrowRight size={18} />
          </button>
        </div>
      </section>
    )
  }

  return (
    <section className="page cart-page">
      <header className="page-heading">
        <div className="cart-page__header-top">
          <p className="brand-mark">Viridi market</p>
          <button
            className="cart-page__clear-btn"
            type="button"
            onClick={clearCart}
            title="Очистить всю корзину"
          >
            <Trash2 size={16} />
            <span>Очистить</span>
          </button>
        </div>
        <h1>Корзина</h1>
        <p className="page-heading__subtitle">
          {summary.totalUniqueItems === 1
            ? '1 позиция'
            : `${summary.totalUniqueItems} позиций`}
          {' · '}
          {summary.totalItems} шт.
        </p>
      </header>

      <div className="cart-items-list">
        {items.map(({ product, quantity }) => {
          const itemTotal = Number(product.price || 0) * quantity
          const productDetails = [
            product.weight !== '0.000' && product.weight ? `${product.weight} кг` : null,
            product.items_in_box > 1 ? `${product.items_in_box} шт./упак.` : null,
          ].filter(Boolean)

          return (
            <article className="cart-item-card" key={product.id}>
              <div
                className="cart-item-card__header"
                role="button"
                tabIndex={0}
                onClick={() => onProductSelect?.(product)}
              >
                <span className="cart-item-card__visual" aria-hidden="true">
                  <Box size={24} strokeWidth={1.5} />
                </span>
                <div className="cart-item-card__info">
                  <strong className="cart-item-card__name">{product.name}</strong>
                  {productDetails.length > 0 && (
                    <span className="cart-item-card__details">
                      <Package size={13} aria-hidden="true" />
                      {productDetails.join(' · ')}
                    </span>
                  )}
                  <span className="cart-item-card__unit-price">
                    {formatPrice(product.price)} / шт.
                  </span>
                </div>
                <button
                  className="cart-item-card__remove-btn"
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    removeItem(product.id)
                  }}
                  title="Удалить товар"
                  aria-label={`Удалить ${product.name}`}
                >
                  <Trash2 size={18} />
                </button>
              </div>

              <div className="cart-item-card__footer">
                <div className="quantity-controls quantity-controls--compact">
                  <button
                    className="quantity-btn quantity-btn--compact"
                    type="button"
                    onClick={() => decrementQuantity(product.id)}
                    aria-label="Уменьшить количество"
                  >
                    <Minus size={16} />
                  </button>
                  <span className="quantity-value quantity-value--compact">{quantity}</span>
                  <button
                    className="quantity-btn quantity-btn--compact"
                    type="button"
                    onClick={() => incrementQuantity(product.id)}
                    aria-label="Увеличить количество"
                  >
                    <Plus size={16} />
                  </button>
                </div>
                <div className="cart-item-card__total-price">
                  {formatPrice(itemTotal)}
                </div>
              </div>
            </article>
          )
        })}
      </div>

      <div className="cart-summary-section">
        <h2>Итоги заказа</h2>
        <div className="cart-summary-card">
          <div className="cart-summary-row">
            <span>Позиций в заказе</span>
            <strong>{summary.totalUniqueItems}</strong>
          </div>
          <div className="cart-summary-row">
            <span>Количество единиц</span>
            <strong>{summary.totalItems} шт.</strong>
          </div>
          {summary.totalWeight > 0 && (
            <div className="cart-summary-row">
              <span>Общий вес</span>
              <strong>{formatWeight(summary.totalWeight)}</strong>
            </div>
          )}
          {summary.totalVolume > 0 && (
            <div className="cart-summary-row">
              <span>Общий объём</span>
              <strong>{formatVolume(summary.totalVolume)}</strong>
            </div>
          )}
          <div className="cart-summary-divider" />
          <div className="cart-summary-row cart-summary-row--total">
            <span>Итого к оплате</span>
            <strong className="cart-summary-total-amount">
              {formatPrice(summary.totalPrice)}
            </strong>
          </div>
        </div>

        <div className="cart-page__actions">
          <button className="cart-submit-btn" type="button">
            <span>Оформить заказ</span>
            <ArrowRight size={20} />
          </button>
        </div>
      </div>
    </section>
  )
}
