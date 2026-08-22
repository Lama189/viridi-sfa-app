import {
  Box,
  Calendar,
  Check,
  Clock,
  Loader2,
  MapPin,
  Package,
  PackageCheck,
  Truck,
  UserRound,
  X,
  XCircle,
} from 'lucide-react'
import { useState } from 'react'
import axios from 'axios'

import { useCancelOrder } from '../hooks/useCancelOrder'
import { useDeliverOrder } from '../hooks/useDeliverOrder'
import { useOrderDetails } from '../hooks/useOrderDetails'
import { formatPrice, formatVolume } from '../lib/format'
import { formatDeliveryDate, formatOrderFullDate, getOrderStatusInfo } from '../lib/order-status'
import type { OrderResponse } from '../types/api'


interface OrderDetailSheetProps {
  initialOrder: OrderResponse
  onClose: () => void
}

export function OrderDetailSheet({ initialOrder, onClose }: OrderDetailSheetProps) {
  const { data: freshOrder } = useOrderDetails(initialOrder.id)
  const order = freshOrder ?? initialOrder

  const cancelOrderMutation = useCancelOrder()
  const deliverOrderMutation = useDeliverOrder()

  const [isConfirmingCancel, setIsConfirmingCancel] = useState(false)
  const [isConfirmingDeliver, setIsConfirmingDeliver] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const statusInfo = getOrderStatusInfo(order.status)
  const orderShortId = order.id.slice(0, 8).toUpperCase()
  const totalItemsCount = order.items.reduce((acc, item) => acc + item.quantity, 0)

  const normalizedStatus = order.status.toLowerCase().trim()
  const isDelivered = normalizedStatus === 'delivered'
  const canDeliver = ['shipped', 'delivering', 'taken_by_agent'].includes(normalizedStatus)
  const canCancel = ['pending', 'confirmed'].includes(normalizedStatus)

  const handleCancelOrder = async () => {
    setActionError(null)
    try {
      await cancelOrderMutation.mutateAsync(order.id)
      setIsConfirmingCancel(false)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail
        if (typeof detail === 'string') {
          setActionError(detail)
          return
        }
      }
      if (err instanceof Error) {
        setActionError(err.message)
        return
      }
      setActionError('Не удалось отменить заказ. Попробуйте позже.')
    }
  }

  const handleDeliverOrder = async () => {
    setActionError(null)
    try {
      await deliverOrderMutation.mutateAsync(order.id)
      setIsConfirmingDeliver(false)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail
        if (typeof detail === 'string') {
          setActionError(detail)
          return
        }
      }
      if (err instanceof Error) {
        setActionError(err.message)
        return
      }
      setActionError('Не удалось подтвердить получение заказа. Попробуйте позже.')
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
        <button
          className="product-sheet__close"
          type="button"
          aria-label="Закрыть детали заказа"
          onClick={(e) => {
            e.stopPropagation()
            onClose()
          }}
        >
          <X size={22} aria-hidden="true" />
        </button>

        <div className="order-detail-sheet__header">
          <div className="order-detail-sheet__top-row">
            <span className="brand-mark">Viridi market</span>
          </div>
          <div className="order-detail-sheet__title-row">
            <h2>Заказ #{orderShortId}</h2>
            <span className={`status-badge ${statusInfo.className}`}>
              {statusInfo.label}
            </span>
          </div>
          <p className="order-detail-sheet__date">
            <Calendar size={14} />
            <span>{formatOrderFullDate(order.created_at)}</span>
          </p>
        </div>

        <div className="order-detail-sheet__body">
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

            <div className="order-detail-meta-item">
              <span className="order-detail-meta-icon" aria-hidden="true">
                <Truck size={18} />
              </span>
              <div className="order-detail-meta-text">
                <strong>Дата доставки</strong>
                <span>
                  {formatDeliveryDate(order.planned_delivery_date)}
                  {order.delivery_agent_name ? ` · ${order.delivery_agent_name}` : ''}
                </span>
              </div>
            </div>


            {order.created_by && (
              <div className="order-detail-meta-item">
                <span className="order-detail-meta-icon" aria-hidden="true">
                  <UserRound size={18} />
                </span>
                <div className="order-detail-meta-text">
                  <strong>Создал заказ</strong>
                  <span>{order.created_by.full_name}</span>
                </div>
              </div>
            )}
          </div>


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

          {actionError && (
            <div className="checkout-error-banner" role="alert">
              <span>{actionError}</span>
            </div>
          )}

          {isDelivered && (
            <div className="order-detail-delivered-banner">
              <Check size={18} strokeWidth={2.5} />
              <span>Заказ успешно доставлен и принят</span>
            </div>
          )}

          {canDeliver && (
            <div className="order-detail-actions-section">
              {isConfirmingDeliver ? (
                <div className="order-deliver-confirm-box">
                  <p className="order-deliver-confirm-text">
                    Подтвердить получение заказа? Товар доставлен и проверен.
                  </p>
                  <div className="order-deliver-confirm-actions">
                    <button
                      className="order-deliver-confirm-yes-btn"
                      type="button"
                      disabled={deliverOrderMutation.isPending}
                      onClick={handleDeliverOrder}
                    >
                      {deliverOrderMutation.isPending ? (
                        <>
                          <Loader2 className="spinner-icon" size={17} />
                          <span>Принимаем…</span>
                        </>
                      ) : (
                        <>
                          <Check size={17} strokeWidth={2.5} />
                          <span>Да, заказ получен</span>
                        </>
                      )}
                    </button>
                    <button
                      className="order-deliver-confirm-no-btn"
                      type="button"
                      disabled={deliverOrderMutation.isPending}
                      onClick={() => setIsConfirmingDeliver(false)}
                    >
                      Отмена
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  className="order-detail-deliver-btn"
                  type="button"
                  onClick={() => {
                    setIsConfirmingCancel(false)
                    setIsConfirmingDeliver(true)
                  }}
                >
                  <PackageCheck size={19} />
                  <span>Подтвердить получение</span>
                </button>
              )}
            </div>
          )}

          {canCancel && !isConfirmingDeliver && (
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
                  onClick={() => {
                    setIsConfirmingDeliver(false)
                    setIsConfirmingCancel(true)
                  }}
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
