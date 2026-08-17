import { useEffect, useState } from 'react'

import { BottomNavigation, type AppPage } from './components/BottomNavigation'
import { ProductSheet } from './components/ProductSheet'
import { useCart } from './hooks/useCart'
import { useTelegram } from './hooks/useTelegram'
import { useTelegramAuth } from './hooks/useTelegramAuth'
import { setTelegramBackButton } from './lib/telegram'
import { CartPage } from './pages/CartPage'
import { CatalogPage } from './pages/CatalogPage'
import { ProfilePage } from './pages/ProfilePage'
import { SettingsPage } from './pages/SettingsPage'
import type { OrderResponse, Product } from './types/api'
import './App.css'

function App() {
  const telegram = useTelegram()
  const auth = useTelegramAuth(telegram.initData)
  const { summary } = useCart()
  const [activePage, setActivePage] = useState<AppPage>('catalog')
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [selectedOrder, setSelectedOrder] = useState<OrderResponse | null>(null)

  useEffect(() => {
    if (selectedProduct) {
      return setTelegramBackButton(() => setSelectedProduct(null))
    }
    if (selectedOrder) {
      return setTelegramBackButton(() => setSelectedOrder(null))
    }
    if (activePage !== 'catalog') {
      return setTelegramBackButton(() => setActivePage('catalog'))
    }
    return setTelegramBackButton(undefined)
  }, [selectedProduct, selectedOrder, activePage])

  if (!telegram.initData) {
    return <AccessState title="Откройте Viridi market в Telegram" />
  }

  if (auth.isLoading) {
    return <AccessState title="Подключаем Viridi market…" />
  }

  if (auth.isError || !auth.data) {
    return (
      <AccessState
        title="Не удалось подтвердить аккаунт"
        description="Вернитесь в бот и пройдите регистрацию по коду активации."
      />
    )
  }

  return (
    <main className="app-shell">
      {activePage === 'catalog' && <CatalogPage onProductSelect={setSelectedProduct} />}
      {activePage === 'cart' && (
        <CartPage
          client={auth.data.client}
          onNavigateToCatalog={() => setActivePage('catalog')}
          onProductSelect={setSelectedProduct}
        />
      )}
      {activePage === 'profile' && (
        <ProfilePage
          client={auth.data.client}
          selectedOrder={selectedOrder}
          onSelectOrder={setSelectedOrder}
        />
      )}
      {activePage === 'settings' && <SettingsPage />}

      <BottomNavigation
        activePage={activePage}
        cartCount={summary.totalItems}
        onChange={(page) => {
          setSelectedOrder(null)
          setSelectedProduct(null)
          setActivePage(page)
        }}
      />

      {selectedProduct && (
        <ProductSheet product={selectedProduct} onClose={() => setSelectedProduct(null)} />
      )}
    </main>
  )
}

interface AccessStateProps {
  title: string
  description?: string
}

function AccessState({ title, description }: AccessStateProps) {
  return (
    <main className="access-state">
      <p className="brand-mark">Viridi market</p>
      <h1>{title}</h1>
      {description && <p>{description}</p>}
    </main>
  )
}

export default App
