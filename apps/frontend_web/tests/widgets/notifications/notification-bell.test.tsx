import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NotificationBell } from '../../../app/widgets/notifications/NotificationBell'

describe('NotificationBell', () => {
  it('given_count_5_when_rendered_then_shows_badge', () => {
    render(<NotificationBell count={5} onClick={vi.fn()} />)
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('given_count_0_when_rendered_then_hides_badge', () => {
    render(<NotificationBell count={0} onClick={vi.fn()} />)
    expect(screen.queryByText('0')).not.toBeInTheDocument()
  })

  it('given_count_100_when_rendered_then_shows_99_plus', () => {
    render(<NotificationBell count={100} onClick={vi.fn()} />)
    expect(screen.getByText('99+')).toBeInTheDocument()
  })

  it('given_bell_when_clicked_then_calls_onClick', async () => {
    const onClick = vi.fn()
    const user = userEvent.setup()
    render(<NotificationBell count={3} onClick={onClick} />)
    await user.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalledOnce()
  })
})
