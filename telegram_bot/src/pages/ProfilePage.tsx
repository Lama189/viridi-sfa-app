import { ChevronRight } from 'lucide-react'

import type { Client } from '../types/api'

interface ProfilePageProps {
  client: Client
}

export function ProfilePage({ client }: ProfilePageProps) {
  const initial = client.full_name.trim().charAt(0).toLocaleUpperCase() || 'V'

  return (
    <section className="page profile-page">
      <header className="page-heading">
        <p className="brand-mark">Viridi market</p>
        <h1>Профиль</h1>
      </header>

      <article className="profile-card">
        <span className="profile-card__avatar" aria-hidden="true">
          {initial}
        </span>
        <span className="profile-card__content">
          <strong>{client.full_name}</strong>
          <span>Telegram ID: {client.telegram_chat_id ?? '—'}</span>
        </span>
        <ChevronRight aria-hidden="true" size={24} />
      </article>
    </section>
  )
}
