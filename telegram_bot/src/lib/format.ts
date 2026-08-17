export function formatPrice(price: string | number): string {
  const numericPrice = typeof price === 'string' ? Number(price) : price
  return `${new Intl.NumberFormat('ru-RU').format(numericPrice)} сум`
}

export function formatWeight(weight: string | number): string {
  const numericWeight = typeof weight === 'string' ? Number(weight) : weight
  return `${numericWeight.toFixed(3).replace(/\.?0+$/, '')} кг`
}

export function formatVolume(volume: string | number): string {
  const numericVolume = typeof volume === 'string' ? Number(volume) : volume
  return `${numericVolume.toFixed(3).replace(/\.?0+$/, '')} м³`
}
