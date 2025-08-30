# Python Project Development Guidelines

## Environment Setup
- Python version: >=3.11 (specified in pyproject.toml)
- Python version management: Uses `uv` for Python version and dependency management
- Dependencies are managed with `uv` and defined in pyproject.toml
- Development installation: `uv pip install -e .`
- Install development dependencies: `uv pip install -e ".[dev]"`

## Commands
- Run application: `python run.py`
- Run with Docker: `docker-compose up -d`
- Run all unit tests: `uv run pytest`
- Run tests with coverage: `uv run pytest --cov=back --cov-report=term-missing`
- Type check: `uv run mypy .`
- Lint code with Ruff: `uv run ruff check .`
- Format code: `uv run ruff format .`
- Lint code with wemake-python-styleguide: `uv run flake8 . --select=WPS`
- Complete linting: `uv run ruff check && uv run ruff format && uv run flake8 . --select=WPS`

## Project Structure

### Frontend (`web/`)
- `index.html`: Main page with circular clock display
- `styles.css`: Dark theme with red accents and animations
- `script.js`: API client with auto-refresh and error handling

### Backend (`app/`)
- `main.py`: FastAPI application with REST API endpoints
- `config.py`: Application configuration with environment variables
- `telegram_api/client.py`: Telegram Client API integration
- `services/parser.py`: Message parsing service (regex patterns)
- `utils/database.py`: SQLAlchemy models for SQLite database
- `utils/logging.py`: Loguru logging configuration

### Configuration
- `pyproject.toml`: Project dependencies and development setup
- `docker-compose.yml`: Full stack deployment (backend + nginx)
- `Dockerfile`: Backend container configuration
- `nginx.conf`: Reverse proxy for API + static files

## Development Workflow
- **Creating Tests**: When creating tests for existing code, never modify the code itself
- **New Feature Development**: First write the code, then run existing tests, fix issues if needed, and finally create tests for the new code
- **Code Refactoring**: Always run tests after changes to ensure the functionality remains intact
- **Task-Driven Development**: For complex tasks, first create a TODO_*.md file with a step-by-step plan, then follow this plan working on each step sequentially
- Run tests and linter after making significant changes to verify functionality
- After important functionality is added, update README.md accordingly
- Maintain minimum test coverage of 85%

## Code Style
- **Imports**: Standard lib → Third-party → Local (alphabetical within groups)
- **Types**: Use type annotations for all functions and variables
- **Naming**: snake_case for variables/functions, UPPER_CASE for constants
- **Error handling**: Use try/except with specific exceptions, log errors with loguru
- **Docstrings**: Google style docstrings for all modules, classes, and functions
- **Async**: Use async/await for I/O bound operations (DB, network)
- **Formatting**: 4 spaces indentation, max 120 char line length, one empty line at end of file
- **File Structure**: Each file should have one and only one blank line at the end
- **Logging**: Use loguru with appropriate levels (debug, info, error)
- **Language**: Always use English for ALL code, comments, and docstrings

## Linting
The project uses two linting tools that complement each other:

1. **Ruff**: Fast Python linter for basic checks and formatting
   - Configuration: In pyproject.toml under [tool.ruff]
   - Command: `uv run ruff check .`
   - Format: `uv run ruff format .`

2. **wemake-python-styleguide**: Strict linter for enforcing best practices
   - Configuration: In .flake8 file
   - Command: `uv run flake8 . --select=WPS` (WPS only checks)
   - No automatic fixes - requires manual corrections

**Recommended workflow**:
1. Run `uv run ruff check && uv run ruff format && uv run flake8 . --select=WPS`
2. Fix any issues reported by both linters
3. Run tests to verify functionality

## Testing Guidelines
- **Testing Framework**: pytest with pytest-asyncio for async tests, pytest-mock for mocking
- NEVER change code and tests simultaneously
- When adding tests for existing code, do not modify the code itself
- When writing new code, run existing tests and create new tests afterward
- When refactoring code, always run existing tests to verify functionality
- Maintain minimum test coverage of 85%

## API Endpoints

- `GET /` - API information
- `GET /api/health` - Health check
- `GET /api/clock/latest` - Get current clock data
- `GET /api/clock/history?limit=10` - Get update history  
- `POST /api/clock/fetch` - Manually fetch updates (for testing)

## Telegram Client API Setup

**IMPORTANT**: Uses official Client API, no channel admin rights required.

1. Get API credentials at https://my.telegram.org/apps
2. Add to .env: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`
3. First run will ask for SMS confirmation code
4. Start backend - client will automatically begin monitoring

## Message Parsing Logic

Parser searches for:
- **Time**: regex patterns for HH:MM:SS, HH:MM, H.MM.SS formats
- **Keywords**: "час", "время", "договор", "соглашение", "судного"  
- **Description**: message text without time (max 200 chars)

Adapt regex patterns in `app/services/parser.py` for specific channel format.

## Database Schema

### ClockUpdate
- time (STRING): time in HH:MM:SS format
- description (TEXT): situation description
- raw_message (TEXT): original Telegram message
- message_id (INT): Telegram message ID
- is_active (BOOL): active record (only one)
- created_at/updated_at (DATETIME)

### ParsedMessage
- message_id (INT): processed message ID
- raw_text (TEXT): original text
- parsed_successfully (BOOL): parsing success status
- error_message (TEXT): parsing error details

## Docker Deployment

```bash
# Create .env with API credentials
echo "TELEGRAM_API_ID=your_id" > .env
echo "TELEGRAM_API_HASH=your_hash" >> .env
echo "TELEGRAM_PHONE=+1234567890" >> .env

# Run full stack
docker-compose up -d

# Check logs
docker-compose logs dooms-deal-clock
```

## Frontend State Management

Frontend maintains:
- `appState.clockData`: current clock data
- `appState.isConnected`: API connection status
- `appState.retryCount`: retry attempt counter

Auto-refresh every 2 minutes + retry logic with exponential backoff.

## Debugging Tools

Browser console:
```javascript
checkServerStatus()        // API status check
fetchClockData()          // force data reload
testMessageParsing("text") // test parser
manualUpdate("23:55:00", "desc") // manual update
```

## Claude Interaction Guidelines

### Communication Rules

1. **Language**:
   - All project artifacts (code, comments, documentation, commit messages) must be in English
   - Use Russian when communicating with user

2. **Project-Specific Rules**:
   - All changes to project files must be saved to git after developer confirmation
   - Do not commit changes automatically without explicit approval
   - Don't add "Generated with Claude Code" or "Co-Authored-By: Claude" to commit messages
   - Do not include "Test plan" sections in PR descriptions

3. **Code Generation Rules**:
   - Never start working with code until explicit approval from the developer
   - Do not write code directly in chat without a specific request
   - Do not add comments that describe changes, progress, or historical modifications
   - Comments should only describe the current state and purpose of the code, not its history
   - If unable to fix a linting error after 3 attempts, stop and discuss with developer
   - If fixing code requires modifying tests, stop and explain the situation

## Security Considerations

- API credentials stored in .env file (local development only)
- Docker containers run as non-root user
- Future: implement secrets management for production deployment
- Future: add rate limiting and authentication for API endpoints
- Future: implement HTTPS with proper SSL certificates