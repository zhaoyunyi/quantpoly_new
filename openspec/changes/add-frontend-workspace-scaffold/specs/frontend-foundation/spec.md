## ADDED Requirements

### Requirement: Frontend Workspace Layout
The repository SHALL provide a dedicated frontend workspace layout under `apps/` and `libs/` without changing existing backend runtime paths.

#### Scenario: Frontend directories are scaffolded
- **WHEN** engineers inspect the repository layout
- **THEN** they can find `apps/frontend_web/` and frontend-related library directories under `libs/`
- **AND** existing backend directories and entrypoints remain unchanged

### Requirement: Frontend Framework Baseline
The frontend application in `apps/frontend_web/` SHALL use TanStack Start as the framework baseline and keep a reproducible dependency strategy for stable builds.

#### Scenario: TanStack Start app is scaffolded and buildable
- **WHEN** engineers run frontend build command in `apps/frontend_web/`
- **THEN** `npm run build` succeeds with the committed project scaffold
- **AND** dependency resolution remains reproducible through committed lock/override strategy

### Requirement: Frontend UI Baseline Specification
The project SHALL define baseline UI, architecture, and design-token specifications before frontend feature implementation.

#### Scenario: Baseline specs are present
- **WHEN** engineers start frontend implementation
- **THEN** they can reference `spec/UISpec.md`, `spec/FrontendArchitectureSpec.md`, and `spec/DesignTokensSpec.md`
- **AND** all frontend work follows the documented boundaries and testing expectations
