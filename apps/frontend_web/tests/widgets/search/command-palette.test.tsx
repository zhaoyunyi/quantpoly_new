import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CommandPalette } from '../../../app/widgets/search/CommandPalette'

const navigateMock = vi.fn()

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-router')>(
    '@tanstack/react-router',
  )
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

describe('CommandPalette', () => {
  beforeEach(() => {
    navigateMock.mockReset()
  })

  it('given_open_palette_when_rendered_then_shows_nav_items', () => {
    render(<CommandPalette open={true} onOpenChange={vi.fn()} />)
    expect(screen.getByPlaceholderText('搜索页面...')).toBeInTheDocument()
    // Should show at least one nav item
    expect(screen.getByText('仪表盘')).toBeInTheDocument()
  })

  it('given_search_query_when_typing_then_filters_results', async () => {
    const user = userEvent.setup()
    render(<CommandPalette open={true} onOpenChange={vi.fn()} />)

    await user.type(screen.getByPlaceholderText('搜索页面...'), '交易')

    expect(screen.getByText('交易账户')).toBeInTheDocument()
    // Other non-matching items should be filtered out
  })

  it('given_no_match_when_searching_then_shows_empty_message', async () => {
    const user = userEvent.setup()
    render(<CommandPalette open={true} onOpenChange={vi.fn()} />)

    await user.type(screen.getByPlaceholderText('搜索页面...'), 'zzzzzzz')

    expect(screen.getByText('未找到匹配页面')).toBeInTheDocument()
  })

  it('given_selected_result_when_click_then_uses_client_navigation', async () => {
    const user = userEvent.setup()
    const onOpenChange = vi.fn()

    render(<CommandPalette open={true} onOpenChange={onOpenChange} />)

    await user.click(screen.getByRole('button', { name: /仪表盘/i }))

    expect(onOpenChange).toHaveBeenCalledWith(false)
    expect(navigateMock).toHaveBeenCalledWith({ to: '/dashboard' })
  })
})
