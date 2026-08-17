import {
  Box,
  Building2,
  Calendar,
  Clock,
  Loader2,
  MapPin,
  Package,
  X,
  XCircle,
} from 'lucide-react'
import { useState } from 'react'
import axios from 'axios'

import { useCancelOrder } from '../hooks/useCancelOrder'
import { useOrderDetails } from '../hooks/useOrderDetails'
import { formatPrice, formatVolume } from '../lib/format'
import { formatOrderFullDate, getOrderStatusInfo } from '../lib/order-status'
import type { OrderResponse } from '../types/api'

interface OrderDetailSheetProps {
  initialOrder: OrderResponse
  onClose: () => void
}

export function OrderDetailSheet({ initialOrder, onClose }: OrderDetailSheetProps) {
  const { data: freshOrder } = useOrderDetails(initialOrder.id)
  const order = freshOrder ?? initialOrder

  const cancelOrderMutation = useCancelOrder()
  const [isConfirmingCancel, setIsConfirmingCancel] = useState(false)
  const [cancelError, setCancelError] = useState<string | null>(null)

  const statusInfo = getOrderStatusInfo(order.status)
  const orderShortId = order.id.slice(0, 8).toUpperCase()
  const totalItemsCount = order.items.reduce((acc, item) => acc + item.quantity, 0)

  const normalizedStatus = order.status.toLowerCase()
  const canCancel = ['pending', 'confirmed'].includes(normalizedStatus)

  const handleCancelOrder = async () => {
    setCancelError(null)
    try {
      await cancelOrderMutation.mutateAsync(order.id)
      setIsConfirmingCancel(false)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail
        if (typeof detail === 'string') {
          setCancelError(detail)
          return
        }
      }
      if (err instanceof Error) {
        setCancelError(err.message)
        return
      }
      setCancelError('Не удалось отменить заказ. Попробуйте позже.')
    }
  }

  return (
    <div className="product-sheet-backdrop" role="presentation" onClick={onClose}>
      <section
        aria-label={`Детали заказа #${orderShortId}`}
        className="product-sheet order-detail-sheet"
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <button className="product-sheet__close" type="button" onClick={onClose}>
          <X size={22} aria-label="Закрыть" />
        </button>

        <div className="order-detail-sheet__header">
          <div className="order-detail-sheet__id-row">
            <span className="brand-mark">Viridi market</span>
            <span className={`status-badge ${statusInfo.className}`}>
              {statusInfo.label}
            </span>
          </div>
          <h2>Заказ #{orderShortId}</h2>
          <p className="order-detail-sheet__date">
            <Calendar size={14} />
            <span>{formatOrderFullDate(order.created_at)}</span>
          </p>
        </div>

        <div className="order-detail-sheet__body">
          {(order.retail_point || order.warehouse) && (
            <div className="order-detail-meta-card">
              {order.retail_point && (
                <div className="order-detail-meta-item">
                  <span className="order-detail-meta-icon" aria-hidden="true">
                    <MapPin size={18} />
                  </span>
                  <div className="order-detail-meta-text">
                    <strong>{order.retail_point.name}</strong>
                    <span>{order.retail_point.address}</span>
                  </div>
                </div>
              )}

              {order.warehouse && (
                <div className="order-detail-meta-item">
                  <span className="order-detail-meta-icon" aria-hidden="true">
                    <Building2 size={18} />
                  </span>
                  <div className="order-detail-meta-text">
                    <strong>Склад отгрузки</strong>
                    <span>{order.warehouse.name}</span>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="order-detail-section">
            <div className="order-detail-section__title">
              <Package size={17} />
              <span>Состав заказа ({order.items.length})</span>
            </div>

            <div className="order-detail-items">
              {order.items.map((item) => {
                const itemTotal = Number(item.price_at_order || 0) * item.quantity
                return (
                  <article className="order-detail-item-card" key={item.id}>
                    <span className="order-detail-item-card__visual" aria-hidden="true">
                      <Box size={22} strokeWidth={1.5} />
                    </span>
                    <div className="order-detail-item-card__info">
                      <strong className="order-detail-item-card__name">
                        {item.product?.name || 'Товар'}
                      </strong>
                      <span className="order-detail-item-card__meta">
                        {item.quantity} шт. × {formatPrice(item.price_at_order)}
                      </span>
                    </div>
                    <strong className="order-detail-item-card__price">
                      {formatPrice(itemTotal)}
                    </strong>
                  </article>
                )
              })}
            </div>
          </div>

          <div className="order-detail-summary-card">
            <div className="cart-summary-row">
              <span>Количество наименований</span>
              <strong>{order.items.length}</strong>
            </div>
            <div className="cart-summary-row">
              <span>Всего единиц</span>
              <strong>{totalItemsCount} шт.</strong>
            </div>
            {Number(order.total_volume) > 0 && (
              <div className="cart-summary-row">
                <span>Общий объём</span>
                <strong>{formatVolume(order.total_volume)}</strong>
              </div>
            )}
            {order.updated_at && order.updated_at !== order.created_at && (
              <div className="cart-summary-row">
                <span>Обновлено</span>
                <span className="order-detail-updated-at">
                  <Clock size={13} />
                  {formatOrderFullDate(order.updated_at)}
                </span>
              </div>
            )}
            <div className="cart-summary-divider" />
            <div className="cart-summary-row cart-summary-row--total">
              <span>Итоговая сумма</span>
              <strong className="cart-summary-total-amount">
                {formatPrice(order.total_amount)}
              </strong>
            </div>
          </div>

          {cancelError && (
            <div className="checkout-error-banner" role="alert">
              <span>{cancelError}</span>
            </div>
          )}

          {canCancel && (
            <div className="order-detail-cancel-section">
              {isConfirmingCancel ? (
                <div className="order-cancel-confirm-box">
                  <p className="order-cancel-confirm-text">
                    Вы уверены, что хотите отменить этот заказ?
                  </p>
                  <div className="order-cancel-confirm-actions">
                    <button
                      className="order-cancel-confirm-yes-btn"
                      type="button"
                      disabled={cancelOrderMutation.isPending}
                      onClick={handleCancelOrder}
                    >
                      {cancelOrderMutation.isPending ? (
                        <>
                          <Loader2 className="spinner-icon" size={17} />
                          <span>Отменяем…</span>
                        </>
                      ) : (
                        <span>Да, отменить</span>
                      )}
                    </button>
                    <button
                      className="order-cancel-confirm-no-btn"
                      type="button"
                      disabled={cancelOrderMutation.isPending}
                      onClick={() => setIsConfirmingCancel(false)}
                    >
                      Не отменять
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  className="order-detail-cancel-btn"
                  type="button"
                  onClick={() => setIsConfirmingCancel(true)}
                >
                  <XCircle size={18} />
                  <span>Отменить заказ</span>
                </button>
              )}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
