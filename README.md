# Dooms Deal Clock

A dynamic web application that automatically fetches updates from the Telegram channel [@dooms_deal_clock](https://t.me/dooms_deal_clock) and displays the real-time "Dooms Deal Clock" countdown.

## Overview

The Dooms Deal Clock is a web application that monitors a specific Telegram channel and displays countdown timers and status updates. The application features a sleek dark interface with pink countdown numbers and an analog clock, replicating the exact visual style from the original Telegram channel.

![Dooms Deal Clock Interface](screenshot.png)

## Features

- **Real-time updates**: Automatically fetches new data from Telegram every 2 minutes
- **Visual design**: Exact replica of the Telegram channel's countdown design
- **Responsive layout**: Works on desktop and mobile devices  
- **Analog clock**: Shows current time with hour and minute hands
- **REST API**: Backend provides JSON endpoints for data access
- **No admin rights required**: Uses Telegram Client API to read public channel

## Architecture

```
Telegram Channel (@dooms_deal_clock)
           ↓
    Telegram Client API
           ↓
   FastAPI Backend (Python)
           ↓
    SQLite Database
           ↓
   Frontend (HTML/CSS/JS)
```

## Project Structure

```
├── app/                    # Backend application
│   ├── main.py            # FastAPI application
│   ├── config.py          # Configuration settings
│   ├── models.py          # Database models
│   ├── services/          # Business logic
│   │   ├── clock_service.py
│   │   ├── parser.py
│   │   └── background_tasks.py
│   ├── telegram_api/      # Telegram integration
│   │   └── client.py
│   └── utils/             # Utilities
│       ├── database.py
│       └── logging.py
├── web/                   # Frontend files
│   ├── index.html         # Main page
│   ├── styles.css         # Styling (dark theme)
│   └── script.js          # JavaScript client
├── docker-compose.yml     # Docker deployment
├── Dockerfile            # Backend container
├── Makefile              # Development commands
└── pyproject.toml        # Python dependencies
```

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- Telegram account for API credentials
- Docker (optional, for deployment)

### 1. Get Telegram API Credentials

1. Visit [https://my.telegram.org/apps](https://my.telegram.org/apps)
2. Log in with your Telegram account
3. Create a new application:
   - **App title**: Dooms Deal Clock
   - **Short name**: dooms_clock
   - **Platform**: Desktop
4. Save your `api_id` and `api_hash`

### 2. Installation

```bash
# Clone repository
git clone <your-repo-url>
cd dooms_deal_clock

# Initialize project
make init-dev

# Create environment file
cp .env.example .env
```

### 3. Configuration

Edit `.env` file with your credentials:

```bash
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here  
TELEGRAM_PHONE=+1234567890
TELEGRAM_CHANNEL_USERNAME=dooms_deal_clock
```

### 4. Run Application

```bash
# Start backend server
make run

# Open web interface
# Navigate to http://localhost:8000/static/index.html
```

On first run, you'll need to authenticate with Telegram:
- Enter the SMS code sent to your phone
- If you have 2FA enabled, enter your password

## API Endpoints

The backend provides the following REST API endpoints:

- `GET /` - API information
- `GET /api/health` - Health check
- `GET /api/clock/latest` - Get current clock data
- `GET /api/clock/history?limit=10` - Get update history
- `POST /api/clock/fetch` - Manually fetch updates (for testing)

### Example Response

```json
{
  "time": "23:56:30",
  "date": "20 августа 2025 года, 1274 день", 
  "currentTime": "23:57:20 (-5) | 160 секунд (+5)",
  "content": "Full message content...",
  "created_at": "2025-08-30T14:30:00Z"
}
```

## Development

### Available Commands

```bash
make help          # Show all available commands
make init-dev      # Initialize development environment  
make run           # Run the application
make tests         # Run all tests with coverage
make format        # Format code with ruff
make lint          # Lint code with ruff  
make check         # Run all checks (format, lint, type check)
make clean         # Clean temporary files
```

### Frontend Development

The frontend uses vanilla JavaScript with automatic API polling:

```javascript
// Force refresh data
fetchClockData()

// Check server status  
checkServerStatus()
```

### Testing Parser

Test message parsing in browser console:

```javascript
// Test parsing a message
testMessageParsing("23:56:30 Time until historic agreement")

// Manual update for testing
manualUpdate("23:55:00", "Critical moment approaching")
```

## Docker Deployment

### Production Deployment

```bash
# Create production environment file
cp .env.example .env
# Edit .env with your credentials

# Start with Docker Compose  
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Services

- **Backend**: FastAPI server on port 8000
- **Frontend**: Served via Nginx on port 80
- **Database**: SQLite file in `data/` directory

## Visual Design

The application replicates the exact visual design from the Telegram channel:

- **Dark background** with subtle gradient effects
- **Pink countdown numbers** (#E85D75) in large font
- **White analog clock** with hour markers and hands
- **Telegram-style header** with channel name and icon
- **Responsive design** for mobile devices

## Monitoring

### Health Checks

- **Application**: `GET /api/health`
- **Telegram Connection**: Check logs for "Telegram Client initialized"  
- **Database**: Automatic table creation on startup

### Logs

```bash
# View application logs
docker compose logs backend

# View all service logs
docker compose logs
```

## Troubleshooting

### Telegram Connection Issues

**Problem**: Client can't connect to Telegram API

**Solution**:
1. Verify `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and `TELEGRAM_PHONE` in `.env`
2. Ensure phone number is in international format (+1234567890)
3. Check that you can receive SMS for verification
4. Look for authentication prompts in application logs

### Frontend Not Loading Data

**Problem**: Interface shows default values, not updating

**Solution**:
1. Check backend is running: `http://localhost:8000/api/health`
2. Verify API endpoints are accessible
3. Check browser console for CORS or network errors
4. Ensure frontend is served from correct URL

### Docker Issues

**Problem**: Containers won't start

**Solution**:
1. Ensure `.env` file exists with valid credentials
2. Check ports 80 and 8000 are available
3. Verify Docker and Docker Compose are installed
4. Review container logs: `docker compose logs`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests and linting: `make check`
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Original concept from [@dooms_deal_clock](https://t.me/dooms_deal_clock) Telegram channel
- Built with [FastAPI](https://fastapi.tiangolo.com/) and [Telethon](https://github.com/LonamiWebs/Telethon)
- Uses [uv](https://github.com/astral-sh/uv) for Python dependency management