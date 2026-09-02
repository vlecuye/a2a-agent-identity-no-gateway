# Project Guidelines and Rules

## Version Control & Commits
- **Automatic Commits**: Always generate a new Git commit when a new feature, bug fix, configuration change, or deployment milestone is completed.
- **Commit Messages**: Write clear, descriptive, Conventional Commit style messages (e.g., `feat: ...`, `fix: ...`, `chore: ...`).

## Architecture & Conventions
- **Code Scope**: Never change or patch underlying installed ADK or third-party library code. Focus exclusively on project application code.
- **Model Selection**: Always use `gemini-3.7-flash` for all agents. Never revert to `gemini-2.5`.
- **Agent Identity & A2A**: Remote A2A agent communications use `AdcAuth` and `mtls_context()` for SPIFFE certificate authentication to prevent HTTP 401 unauthenticated errors.
- **Agent Architecture**: Agent A is a pure ADK agent (native Gemini Enterprise / Vertex AI Agent Engine) coordinating specialist agents (like Agent B) via A2A client tools.
- **Agent Runtime Scaling**: Maintain `minInstances: 1` on production Agent Runtime deployments to prevent cold start latency.
