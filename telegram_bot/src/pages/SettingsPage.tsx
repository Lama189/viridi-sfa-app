import { Bell, ChevronRight, Headphones } from 'lucide-react'
import { useState } from 'react'

export function SettingsPage() {
  const [notificationsEnabled, setNotificationsEnabled] = useState(false)

  return (
    <section className="page settings-page">
      <header className="page-heading">
        <p className="brand-mark">Viridi market</p>
        <h1>Настройки</h1>
        <p className="page-heading__subtitle">Уведомления, поддержка</p>
      </header>

      <div className="settings-list">
        <article className="settings-card settings-card--notification">
          <span className="settings-card__icon" aria-hidden="true">
            <Bell size={27} strokeWidth={1.8} />
          </span>
          <span className="settings-card__content">
            <strong>Уведомления</strong>
            <span>Включите, чтобы узнавать о новых поступлениях.</span>
          </span>
          <button
            aria-checked={notificationsEnabled}
            aria-label="Включить уведомления"
            className={`toggle ${notificationsEnabled ? 'toggle--active' : ''}`}
            role="switch"
            type="button"
            onClick={() => setNotificationsEnabled((enabled) => !enabled)}
          >
            <span />
          </button>
        </article>

        <article className="settings-card">
          <span className="settings-card__icon" aria-hidden="true">
            <Headphones size={27} strokeWidth={1.8} />
          </span>
          <span className="settings-card__content">
            <strong>Связь с поддержкой</strong>
            <span>Telegram</span>
          </span>
          <ChevronRight aria-hidden="true" size={25} />
        </article>
      </div>
    </section>
  )
}
