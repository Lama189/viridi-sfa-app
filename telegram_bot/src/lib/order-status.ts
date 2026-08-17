export interface OrderStatusInfo {
  label: string
  className: string
}

export function getOrderStatusInfo(status: string): OrderStatusInfo {
  const normalized = status.toLowerCase()

  switch (normalized) {
    case 'pending':
      return { label: 'В обработке', className: 'status-badge--pending' }
    case 'confirmed':
      return { label: 'Подтверждён', className: 'status-badge--confirmed' }
    case 'assembling':
      return { label: 'Сборка', className: 'status-badge--assembling' }
    case 'assembled':
      return { label: 'Собран', className: 'status-badge--assembled' }
    case 'shipped':
      return { label: 'Отправлен', className: 'status-badge--shipped' }
    case 'delivering':
      return { label: 'В пути', className: 'status-badge--delivering' }
    case 'delivered':
      return { label: 'Доставлен', className: 'status-badge--delivered' }
    case 'cancelled':
      return { label: 'Отменён', className: 'status-badge--cancelled' }
    default:
      return { label: status, className: 'status-badge--default' }
  }
}

export function formatOrderDate(dateString?: string | null): string {
  if (!dateString) return '—'
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return '—'

    return new Intl.DateTimeFormat('ru-RU', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  } catch {
    return '—'
  }
}

export function formatOrderFullDate(dateString?: string | null): string {
  if (!dateString) return '—'
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return '—'

    return new Intl.DateTimeFormat('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  } catch {
    return '—'
  }
}
