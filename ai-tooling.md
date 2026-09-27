# AI Tooling and Development Process

## Tools used

The project used AI-assisted development workflows to accelerate requirement translation, tool design, and implementation quality. In practice this included:

- GitHub Copilot for code generation, refactoring, and test-driven iteration
- Kiro/Antigravity-style planning workflows for requirement decomposition and architecture mapping
- manual engineering review to validate logic, guardrails, and output quality

## What worked well

- AI tools were strong at generating the initial structure for policy tooling and workflow scaffolding
- they accelerated the creation of the mock HR data model and the tool schemas
- they reduced the time needed to draft the evaluation and test set
- they were helpful for quickly iterating on endpoint design and agent routing logic

## What was less effective

- AI-generated workflow logic needed strong manual validation to ensure policy grounding and action safety
- tool traces and guardrails required careful engineering because simulated HR workflows can become overconfident if not constrained
- some generated responses were too generic unless explicit policy and identity logic were enforced in code

## Human review and validation

The final application was validated by:

- running the project test suite with `pytest`
- validating /health and /chat behavior through endpoint checks
- checking tool discovery and tool execution against the mock database
- reviewing policy behavior to ensure out-of-scope requests were refused

## Final assessment

AI tooling was valuable for speed and structure, but the final correctness came from explicit project requirements, consistent validation, and human supervision. The project demonstrates a realistic “AI-assisted engineering” workflow rather than a fully autonomous build.
