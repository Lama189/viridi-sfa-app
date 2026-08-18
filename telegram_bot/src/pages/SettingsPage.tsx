import { Bell, ChevronRight, Headphones, LogOut } from 'lucide-react'
import { useEffect, useState } from 'react'

import { LeaveRetailPointSheet } from '../components/LeaveRetailPointSheet'
import { setTelegramBackButton } from '../lib/telegram'
import type { Client } from '../types/api'

interface SettingsPageProps {
  client?: Client | null
}

export function SettingsPage({ client }: SettingsPageProps) {
  const [notificationsEnabled, setNotificationsEnabled] = useState(false)
  const [isLeaveSheetOpen, setIsLeaveSheetOpen] = useState(false)

  useEffect(() => {
    if (isLeaveSheetOpen) {
      return setTelegramBackButton(() => setIsLeaveSheetOpen(false))
    }
  }, [isLeaveSheetOpen])

  return (
    <section className="page settings-page">
      <header className="page-heading">
        <p className="brand-mark">Viridi market</p>
        <h1>Настройки</h1>
        <p className="page-heading__subtitle">Уведомления, поддержка и аккаунт</p>
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

        <article
          className="settings-card settings-card--danger"
          role="button"
          tabIndex={0}
          onClick={() => setIsLeaveSheetOpen(true)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              setIsLeaveSheetOpen(true)
            }
          }}
        >
          <span className="settings-card__icon settings-card__icon--danger" aria-hidden="true">
            <LogOut size={27} strokeWidth={1.8} />
          </span>
          <span className="settings-card__content">
            <strong>Выйти из торговой точки</strong>
            <span>Отвязать аккаунт от текущей точки</span>
          </span>
          <ChevronRight aria-hidden="true" size={25} />
        </article>
      </div>

      {isLeaveSheetOpen && (
        <LeaveRetailPointSheet
          client={client}
          onClose={() => setIsLeaveSheetOpen(false)}
        />
      )}
    </section>
  )
}
