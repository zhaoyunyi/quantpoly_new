## MODIFIED Requirements

### Requirement: Frontend Framework Baseline
The frontend application in `apps/frontend_web/` SHALL use the official Vite integration provided by its committed TanStack Start version family and keep a reproducible dependency strategy for stable builds.

#### Scenario: Frontend build uses supported Start runtime pipeline
- **WHEN** engineers inspect the frontend workspace configuration
- **THEN** `apps/frontend_web/package.json` uses the supported TanStack Start runtime toolchain for `dev`, `build`, and `start`
- **AND** the workspace no longer depends on a Vinxi-only runtime path to boot the application

#### Scenario: Production build avoids Start runtime browser externalization warnings
- **WHEN** engineers run `npm run build` in `apps/frontend_web/`
- **THEN** the build succeeds
- **AND** the output does not include `node:fs` or `node:path` being externalized for browser compatibility from TanStack Start runtime internals

#### Scenario: TanStack dependency family is aligned
- **WHEN** engineers inspect `apps/frontend_web/package.json` and the committed lockfile
- **THEN** TanStack Start and Router packages resolve to a compatible version family
- **AND** the workspace does not rely on obsolete overrides for old Start client/server internal packages

#### Scenario: Remaining third-party build warnings are documented
- **WHEN** engineers review the frontend runtime documentation after migration
- **THEN** any remaining non-blocking build warnings that are not caused by TanStack Start runtime internals are documented with their source
- **AND** the documentation states whether each warning is accepted as-is or requires follow-up work
