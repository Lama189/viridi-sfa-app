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

export interface OrderItemCreate {
  product_id: string
  quantity: number
}

export interface CreateOrderPayload {
  warehouse_id?: string
  retail_point_id?: string
  visit_id?: string
  items: OrderItemCreate[]
}

export interface UserShort {
  id: string
  full_name: string
}

export interface RetailPointShort {
  id: string
  name: string
  address: string
}

export interface WarehouseShort {
  id: string
  name: string
}

export interface OrderItemResponse {
  id: string
  order_id: string
  product: {
    id: string
    name: string
    code?: string | null
    unit_of_measure?: string | null
  }
  quantity: number
  price_at_order: string
  total_volume: string
}

export interface OrderResponse {
  id: string
  status: string
  total_amount: string
  total_volume: string
  created_at?: string | null
  updated_at?: string | null
  retail_point?: RetailPointShort | null
  warehouse?: WarehouseShort | null
  created_by?: UserShort | null
  items: OrderItemResponse[]
}
