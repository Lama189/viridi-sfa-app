import {
  Calendar,
  ChevronRight,
  Loader2,
  Package,
  ShoppingBag,
} from 'lucide-react'
import { useMemo, useState } from 'react'

import { OrderDetailSheet } from '../components/OrderDetailSheet'
import { useClientOrders } from '../hooks/useClientOrders'
import { formatPrice } from '../lib/format'
import { formatOrderDate, getOrderStatusInfo } from '../lib/order-status'
import type { Client, OrderResponse } from '../types/api'

interface ProfilePageProps {
  client: Client
  selectedOrder?: OrderResponse | null
  onSelectOrder?: (order: OrderResponse | null) => void
}

type OrderFilter = 'all' | 'active' | 'completed'

export function ProfilePage({
  client,
  selectedOrder: externalSelectedOrder,
  onSelectOrder: externalOnSelectOrder,
}: ProfilePageProps) {
  const { data: orders = [], isLoading, isError } = useClientOrders(client.id)
  const [internalSelectedOrder, setInternalSelectedOrder] = useState<OrderResponse | null>(null)
  const [activeFilter, setActiveFilter] = useState<OrderFilter>('all')

  const selectedOrder = externalSelectedOrder !== undefined ? externalSelectedOrder : internalSelectedOrder
  const handleSelectOrder = (order: OrderResponse | null) => {
    if (externalOnSelectOrder) {
      externalOnSelectOrder(order)
    } else {
      setInternalSelectedOrder(order)
    }
  }

  const initial = client.full_name.trim().charAt(0).toLocaleUpperCase() || 'V'

  const filteredOrders = useMemo(() => {
    if (activeFilter === 'all') return orders

    return orders.filter((order) => {
      const st = order.status.toLowerCase().trim()
      if (activeFilter === 'active') {
        return [
          'pending',
          'confirmed',
          'assembly_started',
          'assembling',
          'assembled',
          'shipped',
          'taken_by_agent',
          'delivering',
        ].includes(st)
      }
      if (activeFilter === 'completed') {
        return st === 'delivered'
      }
      return true
    })
  }, [orders, activeFilter])

  return (
    <section className="page profile-page">
      <header className="page-heading">
        <p className="brand-mark">Viridi market</p>
        <h1>Профиль</h1>
      </header>

      <article className="profile-card">
        <span className="profile-card__avatar" aria-hidden="true">
          {initial}
        </span>
        <span className="profile-card__content">
          <strong>{client.full_name}</strong>
          <span>{client.phone}</span>
          <span className="profile-card__tg-id">ID: {client.telegram_chat_id ?? '—'}</span>
        </span>
      </article>

      <div className="profile-orders-section">
        <div className="profile-orders-section__header">
          <h2>Мои заказы</h2>
          <span className="profile-orders-count">{orders.length}</span>
        </div>

        {orders.length > 0 && (
          <div className="category-tabs profile-order-tabs" role="tablist">
            <button
              className={`category-tab ${activeFilter === 'all' ? 'category-tab--active' : ''}`}
              type="button"
              onClick={() => setActiveFilter('all')}
            >
              Все ({orders.length})
            </button>
            <button
              className={`category-tab ${activeFilter === 'active' ? 'category-tab--active' : ''}`}
              type="button"
              onClick={() => setActiveFilter('active')}
            >
              Активные
            </button>
            <button
              className={`category-tab ${activeFilter === 'completed' ? 'category-tab--active' : ''}`}
              type="button"
              onClick={() => setActiveFilter('completed')}
            >
              Доставленные
            </button>
          </div>
        )}

        {isLoading && (
          <div className="page-state">
            <Loader2 className="spinner-icon" size={24} style={{ margin: '0 auto 12px' }} />
            <span>Загружаем историю заказов…</span>
          </div>
        )}

        {isError && (
          <div className="page-state page-state--error">
            <span>Не удалось загрузить историю заказов.</span>
          </div>
        )}

        {!isLoading && !isError && filteredOrders.length === 0 && (
          <div className="profile-orders-empty">
            <div className="profile-orders-empty__icon" aria-hidden="true">
              <ShoppingBag size={38} strokeWidth={1.5} />
            </div>
            <strong>
              {orders.length === 0 ? 'У вас пока нет заказов' : 'Нет заказов в этой категории'}
            </strong>
            <p>Оформленные заказы будут отображаться здесь с подробными статусами.</p>
          </div>
        )}

        <div className="orders-list">
          {filteredOrders.map((order) => {
            const statusInfo = getOrderStatusInfo(order.status)
            const orderShortId = order.id.slice(0, 8).toUpperCase()
            const itemsCount = order.items.reduce((sum, item) => sum + item.quantity, 0)

            return (
              <article
                className="order-card"
                key={order.id}
                role="button"
                tabIndex={0}
                onClick={() => handleSelectOrder(order)}
              >
                <div className="order-card__header">
                  <span className="order-card__id">#{orderShortId}</span>
                  <span className={`status-badge ${statusInfo.className}`}>
                    {statusInfo.label}
                  </span>
                </div>

                <div className="order-card__body">
                  <div className="order-card__meta">
                    <span className="order-card__date">
                      <Calendar size={13} />
                      {formatOrderDate(order.created_at)}
                    </span>
                    <span className="order-card__items-count">
                      <Package size={13} />
                      {order.items.length} поз. · {itemsCount} шт.
                    </span>
                  </div>

                  <div className="order-card__footer">
                    <strong className="order-card__total">{formatPrice(order.total_amount)}</strong>
                    <ChevronRight className="order-card__arrow" size={18} />
                  </div>
                </div>
              </article>
            )
          })}
        </div>
      </div>

      {selectedOrder && (
        <OrderDetailSheet
          initialOrder={selectedOrder}
          onClose={() => handleSelectOrder(null)}
        />
      )}
    </section>
  )
}
