import { Box, Package, X } from 'lucide-react'

import type { Product } from '../types/api'

interface ProductSheetProps {
  product: Product
  onClose: () => void
}

function formatPrice(price: string): string {
  return `${new Intl.NumberFormat('ru-RU').format(Number(price))} сум`
}

export function ProductSheet({ product, onClose }: ProductSheetProps) {
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
          <div>
            <dt>Вес</dt>
            <dd>{product.weight} кг</dd>
          </div>
          <div>
            <dt>Объём</dt>
            <dd>{product.volume} м³</dd>
          </div>
          <div>
            <dt>В коробке</dt>
            <dd>
              <Package size={15} aria-hidden="true" /> {product.items_in_box} шт.
            </dd>
          </div>
        </dl>
      </section>
    </div>
  )
}
