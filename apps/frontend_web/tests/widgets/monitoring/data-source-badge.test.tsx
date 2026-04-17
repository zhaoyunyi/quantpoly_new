import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DataSourceBadge } from '../../../app/widgets/monitoring/DataSourceBadge'

describe('DataSourceBadge', () => {
  it('given_ws_source_when_rendered_then_shows_websocket', () => {
    render(<DataSourceBadge source="ws" />)
    expect(screen.getByText('WebSocket')).toBeInTheDocument()
  })

  it('given_rest_source_when_rendered_then_shows_rest', () => {
    render(<DataSourceBadge source="rest" />)
    expect(screen.getByText('REST')).toBeInTheDocument()
  })
})
