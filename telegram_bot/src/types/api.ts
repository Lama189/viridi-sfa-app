export interface Client {
  id: string
  phone: string
  full_name: string
  telegram_chat_id: number | null
  is_active: boolean
}

export interface ClientAuthResponse {
  access_token: string
  refresh_token: string
  client: Client
}

export interface Category {
  id: string
  name: string
  is_active: boolean
}

export interface Product {
  id: string
  name: string
  price: string
  category_id: string
  volume: string
  weight: string
  items_in_box: number
  photo_url: string | null
}
