import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { AddSourcePage } from '../AddSource'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('AddSourcePage', () => {
  it('renders form fields', () => {
    render(<AddSourcePage />, { wrapper })
    expect(screen.getByLabelText(/source name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/workspace/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/path/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/include patterns/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/exclude patterns/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument()
  })

  it('shows cancel button', () => {
    render(<AddSourcePage />, { wrapper })
    const cancel = screen.getAllByRole('button', { name: /cancel/i })
    expect(cancel.length).toBeGreaterThanOrEqual(1)
  })

  it('has back link to sources', () => {
    render(<AddSourcePage />, { wrapper })
    expect(screen.getAllByText(/back to sources/i)[0]).toBeInTheDocument()
  })
})
