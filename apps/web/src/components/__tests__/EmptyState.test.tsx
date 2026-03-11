import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EmptyState } from '../EmptyState'

describe('EmptyState', () => {
  it('renders title', () => {
    render(<EmptyState title="No items" />)
    expect(screen.getByText('No items')).toBeInTheDocument()
  })

  it('renders description when provided', () => {
    render(<EmptyState title="Empty" description="Add something to get started." />)
    expect(screen.getByText('Add something to get started.')).toBeInTheDocument()
  })

  it('renders action when provided', () => {
    render(
      <EmptyState
        title="Empty"
        action={<button>Add item</button>}
      />
    )
    expect(screen.getByRole('button', { name: /add item/i })).toBeInTheDocument()
  })
})
