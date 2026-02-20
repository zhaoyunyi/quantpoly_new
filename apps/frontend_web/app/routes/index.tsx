import { createFileRoute } from "@tanstack/react-router";

import { LandingPage } from "../widgets/landing/LandingContent";

export { LandingPage };

export const Route = createFileRoute("/")({
  component: LandingPage,
});
