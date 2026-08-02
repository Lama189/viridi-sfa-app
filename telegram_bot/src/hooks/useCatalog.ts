import { useQuery } from '@tanstack/react-query'

import { getCategories, getProducts } from '../api/catalog'

export function useCatalog() {
  const categoriesQuery = useQuery({
    queryKey: ['categories'],
    queryFn: getCategories,
    staleTime: 5 * 60 * 1000,
  })
  const productsQuery = useQuery({
    queryKey: ['products'],
    queryFn: getProducts,
    staleTime: 5 * 60 * 1000,
  })

  return {
    categories: categoriesQuery.data ?? [],
    products: productsQuery.data ?? [],
    isLoading: categoriesQuery.isLoading || productsQuery.isLoading,
    error: categoriesQuery.error ?? productsQuery.error,
  }
}
