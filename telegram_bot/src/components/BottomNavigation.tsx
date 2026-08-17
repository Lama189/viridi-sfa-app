import { Grid2X2, Settings, ShoppingBag, UserRound } from 'lucide-react'

export type AppPage = 'catalog' | 'cart' | 'profile' | 'settings'

interface BottomNavigationProps {
  activePage: AppPage
  cartCount?: number
  onChange: (page: AppPage) => void
}

const items = [
  { id: 'catalog', label: 'Каталог', icon: Grid2X2 },
  { id: 'cart', label: 'Корзина', icon: ShoppingBag },
  { id: 'profile', label: 'Профиль', icon: UserRound },
  { id: 'settings', label: 'Настройки', icon: Settings },
] as const

export function BottomNavigation({ activePage, cartCount = 0, onChange }: BottomNavigationProps) {
  return (
    <nav className="bottom-navigation" aria-label="Основная навигация">
      {items.map(({ id, label, icon: Icon }) => {
        const isActive = activePage === id
        const showBadge = id === 'cart' && cartCount > 0

        return (
          <button
            className={`navigation-item ${isActive ? 'navigation-item--active' : ''}`}
            key={id}
            type="button"
            onClick={() => onChange(id)}
          >
            <span className="navigation-item__icon-wrapper">
              <Icon aria-hidden="true" size={24} strokeWidth={isActive ? 2.1 : 1.8} />
              {showBadge && (
                <span className="navigation-item__badge" aria-label={`Товаров в корзине: ${cartCount}`}>
                  {cartCount > 99 ? '99+' : cartCount}
                </span>
              )}
            </span>
            <span>{label}</span>
          </button>
        )
      })}
    </nav>
  )
}
