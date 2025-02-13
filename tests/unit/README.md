# Unit Tests

Unit tests validate individual components in isolation. These tests should:
- Test a single unit of code
- Mock external dependencies
- Run quickly
- Not require external services

## Structure
Each module has its own directory:
- api/: API endpoint and middleware tests
- agent/: Agent component tests
- config/: Configuration system tests
- tools/: Tool implementation tests
