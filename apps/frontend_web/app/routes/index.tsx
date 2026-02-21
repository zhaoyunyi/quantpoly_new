import { createFileRoute } from '@tanstack/react-router'

import { LandingPage } from '../widgets/landing/LandingContent'

export function IndexPage() {
  return <LandingPage />
}

export const Route = createFileRoute('/')({
  component: IndexPage,
})
