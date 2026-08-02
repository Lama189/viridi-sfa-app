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
    } catch {
      // The local browser preview is not a Telegram Mini App environment.
    }

    isInitialized = true
  }

  try {
    const launchParams = retrieveLaunchParams()
    return {
      initData: retrieveRawInitData(),
      user: launchParams.tgWebAppData?.user,
    }
  } catch {
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
