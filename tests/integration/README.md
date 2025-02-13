# Integration Tests

Integration tests validate component interactions. These tests should:
- Test multiple components working together
- Use test doubles sparingly
- Validate end-to-end flows
- May require external services

## Structure
Each major subsystem has its own directory:
- api/: API integration tests
- agent/: Agent system tests
- tools/: Tool integration tests
