import { AlertTriangle, KeyRound, Loader2, LogOut, UserCheck, X } from 'lucide-react'
import { useState } from 'react'

import { leaveRetailPoint } from '../api/auth'
import { clearAuthTokens } from '../api/client'
import { closeTelegramMiniApp } from '../lib/telegram'
import type { Client } from '../types/api'

interface LeaveRetailPointSheetProps {
  client?: Client | null
  onClose: () => void
}

export function LeaveRetailPointSheet({ client, onClose }: LeaveRetailPointSheetProps) {
  const [isLeaving, setIsLeaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleConfirmLeave = async () => {
    if (!client) {
      clearAuthTokens()
      closeTelegramMiniApp()
      return
    }

    setIsLeaving(true)
    setError(null)
    try {
      await leaveRetailPoint(client.id)
      clearAuthTokens()
      onClose()
      closeTelegramMiniApp()
    } catch {
      setError('Не удалось выйти из точки. Попробуйте ещё раз.')
      setIsLeaving(false)
    }
  }

  return (
    <div className="product-sheet-backdrop" role="presentation" onClick={onClose}>
      <section
        aria-label="Подтверждение выхода из торговой точки"
        className="product-sheet leave-point-sheet"
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          className="product-sheet__close"
          type="button"
          aria-label="Закрыть"
          onClick={(e) => {
            e.stopPropagation()
            onClose()
          }}
        >
          <X size={22} aria-hidden="true" />
        </button>

        <div className="leave-point-sheet__header">
          <div className="leave-point-sheet__icon-box">
            <LogOut size={30} />
          </div>
          <span className="brand-mark">Viridi market</span>
          <h2>Выйти из торговой точки?</h2>
          <p className="leave-point-sheet__subtitle">
            Вы будете отвязаны от текущей торговой точки
          </p>
        </div>

        <div className="leave-point-sheet__content">
          <div className="leave-point-info-card">
            <div className="leave-point-info-row">
              <span className="leave-point-info-icon leave-point-info-icon--check">
                <UserCheck size={18} />
              </span>
              <div className="leave-point-info-text">
                <strong>Аккаунт сохранится</strong>
                <span>Ваш профиль и номер телефона останутся в системе</span>
              </div>
            </div>

            <div className="leave-point-info-row">
              <span className="leave-point-info-icon leave-point-info-icon--key">
                <KeyRound size={18} />
              </span>
              <div className="leave-point-info-text">
                <strong>Новый код приглашения</strong>
                <span>Для подключения к новой точке нужно будет просто ввести код в боте</span>
              </div>
            </div>
          </div>

          {error && (
            <div className="leave-point-error">
              <AlertTriangle size={16} />
              <span>{error}</span>
            </div>
          )}

          <div className="leave-point-sheet__actions">
            <button
              type="button"
              className="leave-point-btn leave-point-btn--danger"
              disabled={isLeaving}
              onClick={handleConfirmLeave}
            >
              {isLeaving ? (
                <>
                  <Loader2 className="spinner-icon" size={19} />
                  <span>Выходим…</span>
                </>
              ) : (
                <>
                  <LogOut size={19} />
                  <span>Да, выйти из точки</span>
                </>
              )}
            </button>

            <button
              type="button"
              className="leave-point-btn leave-point-btn--cancel"
              disabled={isLeaving}
              onClick={onClose}
            >
              Отмена
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}
