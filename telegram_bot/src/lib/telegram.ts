import {
  backButton,
  init,
  miniApp,
  retrieveLaunchParams,
  retrieveRawInitData,
  themeParams,
  viewport,
  type User,
} from '@telegram-apps/sdk'

let isInitialized = false

export interface TelegramLaunchData {
  initData: string | undefined
  user: User | undefined
}

export function initializeTelegram(): TelegramLaunchData {
  if (!isInitialized) {
    try {
      init()
      mountTelegramComponents()
    } catch (err) {
      console.warn('[Telegram SDK] init() warning:', err)
    }

    isInitialized = true
  }

  try {
    const launchParams = retrieveLaunchParams()
    const initData = retrieveRawInitData()
    return {
      initData,
      user: launchParams.tgWebAppData?.user,
    }
  } catch (err) {
    console.error('[Telegram SDK] retrieveLaunchParams failed:', err)
    console.error('[Telegram SDK] Current location.href:', window.location.href)
    console.error('[Telegram SDK] Current location.hash:', window.location.hash)

    const legacyWebApp = (
      window as unknown as {
        Telegram?: {
          WebApp?: {
            initData?: string
            initDataUnsafe?: { user?: User }
          }
        }
      }
    )?.Telegram?.WebApp

    if (legacyWebApp?.initData) {
      console.log('[Telegram SDK] Recovered initData from legacy window.Telegram.WebApp')
      return {
        initData: legacyWebApp.initData,
        user: legacyWebApp.initDataUnsafe?.user,
      }
    }

    return { initData: undefined, user: undefined }
  }
}

function mountTelegramComponents(): void {
  if (miniApp.mountSync.isAvailable()) {
    miniApp.mountSync()
  }
  if (themeParams.mountSync.isAvailable()) {
    themeParams.mountSync()
  }
  if (viewport.mount.isAvailable()) {
    void viewport.mount()
  }
  if (miniApp.ready.isAvailable()) {
    miniApp.ready()
  }
}

export function setTelegramBackButton(onBack: (() => void) | undefined): () => void {
  if (!backButton.mount.isAvailable() || !backButton.show.isAvailable()) {
    return () => undefined
  }

  backButton.mount()

  if (!onBack) {
    if (backButton.hide.isAvailable()) {
      backButton.hide()
    }
    return () => undefined
  }

  backButton.show()
  const removeListener = backButton.onClick.isAvailable()
    ? backButton.onClick(onBack)
    : () => undefined

  return () => {
    removeListener()
    if (backButton.hide.isAvailable()) {
      backButton.hide()
    }
  }
}

export function closeTelegramMiniApp(): void {
  try {
    if (miniApp.close.isAvailable()) {
      miniApp.close()
      return
    }
  } catch {
  }

  try {
    const webApp = (window as unknown as { Telegram?: { WebApp?: { close?: () => void } } })
      ?.Telegram?.WebApp
    if (typeof webApp?.close === 'function') {
      webApp.close()
    }
  } catch {
  }
}
