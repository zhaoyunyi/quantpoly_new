import '@testing-library/jest-dom/vitest'
import { createElement } from 'react'
import { vi } from 'vitest'

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-router')>(
    '@tanstack/react-router',
  )

  return {
    ...actual,
    Link: ({ children, to, ...props }: Record<string, unknown>) =>
      createElement(
        'a',
        {
          href: String(to ?? ''),
          ...(props as Record<string, unknown>),
        },
        children as any,
      ),
    useNavigate: () => vi.fn(),
  }
})
