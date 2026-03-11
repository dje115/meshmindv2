import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { WebCitationCard } from '../WebCitationCard'

describe('WebCitationCard', () => {
  it('renders title and source', () => {
    render(
      <WebCitationCard
        citation={{
          title: 'Test Article',
          source: 'example.com',
          url: 'https://example.com/article',
          snippet: 'A brief excerpt.',
        }}
      />
    )
    expect(screen.getByText('Test Article')).toBeInTheDocument()
    expect(screen.getByText('example.com')).toBeInTheDocument()
    expect(screen.getByText('A brief excerpt.')).toBeInTheDocument()
  })

  it('renders Open link with correct href', () => {
    render(
      <WebCitationCard
        citation={{
          title: 'X',
          source: '',
          url: 'https://example.com/foo',
          snippet: '',
        }}
      />
    )
    const links = screen.getAllByRole('link', { name: /open/i })
    const link = links.find((l) => l.getAttribute('href') === 'https://example.com/foo')
    expect(link).toBeDefined()
  })
})
