import { Grid2X2, Settings, UserRound } from 'lucide-react'

export type AppPage = 'catalog' | 'profile' | 'settings'

interface BottomNavigationProps {
  activePage: AppPage
  onChange: (page: AppPage) => void
}

const items = [
  { id: 'catalog', label: 'Каталог', icon: Grid2X2 },
  { id: 'profile', label: 'Профиль', icon: UserRound },
  { id: 'settings', label: 'Настройки', icon: Settings },
] as const

export function BottomNavigation({ activePage, onChange }: BottomNavigationProps) {
  return (
    <nav className="bottom-navigation" aria-label="Основная навигация">
      {items.map(({ id, label, icon: Icon }) => {
        const isActive = activePage === id

        return (
          <button
            className={`navigation-item ${isActive ? 'navigation-item--active' : ''}`}
            key={id}
            type="button"
            onClick={() => onChange(id)}
          >
            <Icon aria-hidden="true" size={24} strokeWidth={isActive ? 2.1 : 1.8} />
            <span>{label}</span>
          </button>
        )
      })}
    </nav>
  )
}
