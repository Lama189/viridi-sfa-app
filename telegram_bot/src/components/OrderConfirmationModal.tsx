import {
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronLeft,
  Loader2,
  Package,
  ShoppingBag,
  UserRound,
  X,
} from 'lucide-react'
import { useState } from 'react'
import axios from 'axios'

import { useCart } from '../hooks/useCart'
import { useCreateOrder } from '../hooks/useCreateOrder'
import { formatPrice, formatVolume, formatWeight } from '../lib/format'
import type { Client, OrderResponse } from '../types/api'

interface OrderConfirmationModalProps {
  client: Client
  onClose: () => void
  onSuccess: () => void
}

export function OrderConfirmationModal({
  client,
  onClose,
  onSuccess,
}: OrderConfirmationModalProps) {
  const { items, summary, clearCart } = useCart()
  const createOrderMutation = useCreateOrder()
  const [createdOrder, setCreatedOrder] = useState<OrderResponse | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleConfirmOrder = async () => {
    setErrorMessage(null)
    try {
      const payload = {
        items: items.map((item) => ({
          product_id: item.product.id,
          quantity: item.quantity,
        })),
      }

      const response = await createOrderMutation.mutateAsync(payload)
      setCreatedOrder(response)
      clearCart()
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail
        if (typeof detail === 'string') {
          setErrorMessage(detail)
          return
        }
      }
      if (err instanceof Error) {
        setErrorMessage(err.message)
        return
      }
      setErrorMessage('Произошла ошибка при создании заказа. Попробуйте снова.')
    }
  }

  const handleFinishSuccess = () => {
    onSuccess()
  }

  if (createdOrder) {
    const orderShortId = createdOrder.id.slice(0, 8).toUpperCase()

    return (
      <div className="product-sheet-backdrop" role="presentation" onClick={handleFinishSuccess}>
        <section
          aria-label="Заказ успешно оформлен"
          className="product-sheet checkout-success-sheet"
          role="dialog"
          aria-modal="true"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="checkout-success-sheet__icon-wrapper">
            <CheckCircle2 size={54} strokeWidth={1.8} />
          </div>

          <h2>Заказ оформлен!</h2>
          <p className="checkout-success-sheet__subtitle">
            Заказ <strong className="checkout-success-sheet__order-id">#{orderShortId}</strong>{' '}
            успешно отправлен в обработку.
          </p>

          <div className="checkout-success-sheet__summary">
            <div className="cart-summary-row">
              <span>Сумма заказа</span>
              <strong>{formatPrice(createdOrder.total_amount || summary.totalPrice)}</strong>
            </div>
            <div className="cart-summary-row">
              <span>Статус</span>
              <strong className="checkout-status-badge">
                <Check size={12} strokeWidth={3} />
                Принят
              </strong>
            </div>
          </div>

          <button
            className="cart-submit-btn checkout-success-sheet__btn"
            type="button"
            onClick={handleFinishSuccess}
          >
            <span>В каталог</span>
            <ArrowRight size={20} />
          </button>
        </section>
      </div>
    )
  }

  const initial = client.full_name.trim().charAt(0).toLocaleUpperCase() || 'V'

  return (
    <div className="product-sheet-backdrop" role="presentation" onClick={onClose}>
      <section
        aria-label="Подтверждение заказа"
        className="product-sheet checkout-sheet"
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          className="product-sheet__close"
          type="button"
          aria-label="Закрыть"
          onClick={(e) => {
            e.stopPropagation()
            onClose()
          }}
        >
          <X size={22} aria-hidden="true" />
        </button>

        <div className="checkout-sheet__header">
          <span className="brand-mark">Viridi market</span>
          <h2>Подтверждение заказа</h2>
          <p className="checkout-sheet__subtitle">
            Проверьте данные получателя и состав перед отправкой
          </p>
        </div>

        <div className="checkout-sheet__body">
          <div className="checkout-section">
            <div className="checkout-section__title">
              <UserRound size={17} />
              <span>Получатель</span>
            </div>
            <div className="checkout-client-card">
              <span className="profile-card__avatar checkout-client-avatar" aria-hidden="true">
                {initial}
              </span>
              <div className="checkout-client-info">
                <strong>{client.full_name}</strong>
                <span>{client.phone}</span>
              </div>
            </div>
          </div>

          <div className="checkout-section">
            <div className="checkout-section__title">
              <ShoppingBag size={17} />
              <span>Позиции ({summary.totalUniqueItems})</span>
            </div>
            <div className="checkout-items-list">
              {items.map(({ product, quantity }) => {
                const itemTotal = Number(product.price || 0) * quantity
                return (
                  <div className="checkout-item-row" key={product.id}>
                    <div className="checkout-item-row__info">
                      <span className="checkout-item-row__name">{product.name}</span>
                      <span className="checkout-item-row__quantity">
                        {quantity} шт. × {formatPrice(product.price)}
                      </span>
                    </div>
                    <strong className="checkout-item-row__price">{formatPrice(itemTotal)}</strong>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="checkout-section">
            <div className="checkout-section__title">
              <Package size={17} />
              <span>Детали и сумма</span>
            </div>
            <div className="checkout-summary-box">
              <div className="cart-summary-row">
                <span>Всего единиц</span>
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
          </div>

          {errorMessage && (
            <div className="checkout-error-banner" role="alert">
              <span>{errorMessage}</span>
            </div>
          )}
        </div>

        <div className="checkout-sheet__footer">
          <button
            className="cart-submit-btn checkout-sheet__confirm-btn"
            type="button"
            disabled={createOrderMutation.isPending}
            onClick={handleConfirmOrder}
          >
            {createOrderMutation.isPending ? (
              <>
                <Loader2 className="spinner-icon" size={20} />
                <span>Отправляем заказ…</span>
              </>
            ) : (
              <>
                <span>Подтвердить заказ</span>
                <ArrowRight size={20} />
              </>
            )}
          </button>

          <button
            className="checkout-sheet__back-btn"
            type="button"
            disabled={createOrderMutation.isPending}
            onClick={onClose}
          >
            <ChevronLeft size={18} />
            <span>Вернуться в корзину</span>
          </button>
        </div>
      </section>
    </div>
  )
}
