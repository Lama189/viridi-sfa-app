import { apiClient } from './client'
import type { Category, Product } from '../types/api'

export async function getCategories(): Promise<Category[]> {
  const { data } = await apiClient.get<Category[]>('/categories', {
    params: { only_active: true },
  })
  return data
}

export async function getProducts(): Promise<Product[]> {
  const { data } = await apiClient.get<Product[]>('/products', {
    params: { only_active: true },
  })
  return data
}
