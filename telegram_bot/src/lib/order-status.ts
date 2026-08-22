export interface OrderStatusInfo {
  label: string
  className: string
}

export function getOrderStatusInfo(status: string): OrderStatusInfo {
  const normalized = status.toLowerCase().trim()

  switch (normalized) {
    case 'pending':
      return { label: 'В обработке', className: 'status-badge--pending' }
    case 'confirmed':
      return { label: 'Подтверждён', className: 'status-badge--confirmed' }
    case 'assembly_started':
    case 'assembling':
      return { label: 'Собирается', className: 'status-badge--assembling' }
    case 'assembled':
      return { label: 'Собран', className: 'status-badge--assembled' }
    case 'shipped':
      return { label: 'Отгружен', className: 'status-badge--shipped' }
    case 'taken_by_agent':
    case 'delivering':
      return { label: 'В пути', className: 'status-badge--delivering' }
    case 'delivered':
      return { label: 'Доставлен', className: 'status-badge--delivered' }
    case 'cancelled':
    case 'canceled':
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

export function formatDeliveryDate(dateString?: string | null): string {
  if (!dateString) return '—'
  try {
    const cleanDateStr = dateString.split('T')[0]
    const parts = cleanDateStr.split('-')
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10)
      const month = parseInt(parts[1], 10) - 1
      const day = parseInt(parts[2], 10)
      const date = new Date(year, month, day)
      if (!isNaN(date.getTime())) {
        return new Intl.DateTimeFormat('ru-RU', {
          day: 'numeric',
          month: 'long',
          year: 'numeric',
        }).format(date)
      }
    }

    const date = new Date(dateString)
    if (isNaN(date.getTime())) return '—'

    return new Intl.DateTimeFormat('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    }).format(date)
  } catch {
    return '—'
  }
}

