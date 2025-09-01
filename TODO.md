# TODO List for Dooms Deal Clock

## Failed Tests (After 3+ Fix Attempts)

### Database Connection Issues
**Status**: Failed after multiple attempts  
**Problem**: Tests in `tests/unit/utils/test_database.py` failing with SQLite connection errors  
**Error**: `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file`  
**Root Cause**: Conflict between test database setup and app database initialization  
**Next Steps**: Needs complete database testing strategy redesign with proper isolation

### Background Tasks Service Tests
**Status**: Failed after multiple attempts  
**Problem**: Tests in `tests/unit/services/test_background_tasks.py` failing with async/mock issues  
**Error**: Various async mock configuration problems and attribute errors  
**Root Cause**: Complex async service with multiple dependencies hard to mock properly  
**Next Steps**: Simplify service design or use different testing approach

### Telegram Client Tests  
**Status**: Failed after multiple attempts
**Problem**: Tests in `tests/unit/telegram_api/test_client.py` failing with async iterator issues
**Error**: `TypeError: 'list' object cannot be interpreted as an integer` and async mock problems
**Root Cause**: Complex external API client with async generators difficult to mock
**Next Steps**: Use real Telegram client in integration tests or simplify client interface

### Clock Service Tests
**Status**: Failed after multiple attempts  
**Problem**: Tests in `tests/unit/services/test_clock_service.py` failing with database session issues
**Error**: Database integrity errors and session management problems  
**Root Cause**: Service has tight coupling with database and external services
**Next Steps**: Refactor service to be more testable with dependency injection

### Integration Tests
**Status**: Failed after multiple attempts
**Problem**: Tests in `tests/integration/test_api_workflow.py` failing with FastAPI test client issues
**Error**: Database session conflicts and dependency override problems
**Root Cause**: Complex integration between FastAPI, database, and external services
**Next Steps**: Use separate test database configuration or mock all external dependencies

## Current Test Coverage Status
- **Total Coverage**: 59.49%
- **Working Tests**: 52 passing tests
- **Core Modules**: Excellent coverage (config: 91.67%, main: 96.15%, parser: 96.25%, logging: 100%)
- **Problematic Modules**: Services and utilities with external dependencies

## Next Actions
1. Focus on modules with highest coverage potential that don't require complex database/async mocking
2. Consider architectural changes to improve testability
3. Implement integration tests with real database for complex services
4. Document testing limitations and workarounds for future development

## Frontend Layout Notes (to remind later)

- Completed: message pane split into fixed `time-header` (top) and scrollable `message-content` (bottom). Header aligned with image top; scroll constrained to lower pane.
- Suggestion: consider setting explicit min/max height for `time-header` to stabilize layout across varying header content.
  - Option A: `.time-header { min-height: 56px; max-height: 120px; overflow: hidden; }`
  - Option B: responsive size via media queries and clamp() for font-size.
  - Decision pending — revisit after visual QA on multiple messages.
