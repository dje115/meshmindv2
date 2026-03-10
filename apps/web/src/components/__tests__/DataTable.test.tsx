import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DataTable } from '../DataTable'

describe('DataTable', () => {
  it('renders empty message when no data', () => {
    render(
      <DataTable
        columns={[{ key: 'name', header: 'Name' }]}
        data={[]}
        keyExtractor={() => ''}
        emptyMessage="No items"
      />
    )
    expect(screen.getByText('No items')).toBeInTheDocument()
  })

  it('renders rows when data provided', () => {
    const data = [{ id: '1', name: 'Alice' }, { id: '2', name: 'Bob' }]
    render(
      <DataTable
        columns={[{ key: 'name', header: 'Name' }]}
        data={data}
        keyExtractor={(r) => r.id}
      />
    )
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
  })

  it('uses custom render when provided', () => {
    const data = [{ id: '1', score: 0.9 }]
    render(
      <DataTable
        columns={[
          { key: 'score', header: 'Score', render: (r) => `${(r.score * 100).toFixed(0)}%` },
        ]}
        data={data}
        keyExtractor={(r) => r.id}
      />
    )
    expect(screen.getByText('90%')).toBeInTheDocument()
  })
})
