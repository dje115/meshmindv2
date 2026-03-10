import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CitationCard } from '../CitationCard'

describe('CitationCard', () => {
  it('renders filename and page reference', () => {
    render(
      <CitationCard
        citation={{
          chunk_id: 'c1',
          source_item_id: 's1',
          text: 'Sample text',
          page_index: 2,
          filename: 'report.pdf',
        }}
      />
    )
    expect(screen.getByText('report.pdf')).toBeInTheDocument()
    expect(screen.getByText('Page 3')).toBeInTheDocument()
  })

  it('shows open original link when open_target present', () => {
    render(
      <CitationCard
        citation={{
          chunk_id: 'c1',
          source_item_id: 's1',
          text: 'Text',
          open_target: 'file:///path/doc.pdf',
        }}
      />
    )
    const link = screen.getByRole('link', { name: /open original/i })
    expect(link).toHaveAttribute('href', 'file:///path/doc.pdf')
  })
})
