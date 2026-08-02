import { Search } from 'lucide-react'
import { useMemo, useState } from 'react'

import { ProductCard } from '../components/ProductCard'
import { useCatalog } from '../hooks/useCatalog'
import type { Product } from '../types/api'

interface CatalogPageProps {
  onProductSelect: (product: Product) => void
}

export function CatalogPage({ onProductSelect }: CatalogPageProps) {
  const { categories, products, isLoading, error } = useCatalog()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategoryId, setSelectedCategoryId] = useState('all')

  const normalizedSearchQuery = searchQuery.trim().toLocaleLowerCase()
  const filteredProducts = useMemo(
    () =>
      products.filter((product) => {
        const matchesCategory =
          selectedCategoryId === 'all' || product.category_id === selectedCategoryId
        const matchesSearch = product.name.toLocaleLowerCase().includes(normalizedSearchQuery)

        return matchesCategory && matchesSearch
      }),
    [normalizedSearchQuery, products, selectedCategoryId],
  )

  const visibleCategories = categories.filter((category) =>
    filteredProducts.some((product) => product.category_id === category.id),
  )

  return (
    <section className="page catalog-page">
      <header className="page-heading">
        <p className="brand-mark">Viridi market</p>
        <h1>Каталог</h1>
      </header>

      <label className="search-field">
        <Search aria-hidden="true" size={27} />
        <input
          type="search"
          placeholder="Поиск по названию товара..."
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
        />
      </label>

      <div className="category-tabs" role="tablist" aria-label="Категории товаров">
        <button
          className={`category-tab ${selectedCategoryId === 'all' ? 'category-tab--active' : ''}`}
          type="button"
          role="tab"
          aria-selected={selectedCategoryId === 'all'}
          onClick={() => setSelectedCategoryId('all')}
        >
          Все
        </button>
        {categories.map((category) => (
          <button
            className={`category-tab ${
              selectedCategoryId === category.id ? 'category-tab--active' : ''
            }`}
            key={category.id}
            type="button"
            role="tab"
            aria-selected={selectedCategoryId === category.id}
            onClick={() => setSelectedCategoryId(category.id)}
          >
            {category.name}
          </button>
        ))}
      </div>

      {isLoading && <div className="page-state">Загружаем каталог…</div>}
      {error && <div className="page-state page-state--error">Не удалось загрузить каталог.</div>}
      {!isLoading && !error && filteredProducts.length === 0 && (
        <div className="page-state">Товары не найдены.</div>
      )}

      <div className="catalog-sections">
        {visibleCategories.map((category) => {
          const categoryProducts = filteredProducts.filter(
            (product) => product.category_id === category.id,
          )

          return (
            <section className="catalog-section" key={category.id}>
              <h2>{category.name}</h2>
              <div className="product-list">
                {categoryProducts.map((product) => (
                  <ProductCard key={product.id} product={product} onClick={onProductSelect} />
                ))}
              </div>
            </section>
          )
        })}
      </div>
    </section>
  )
}
