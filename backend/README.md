# FastAPI Minimal MVP Template

A lightweight FastAPI template for rapid prototyping and MVPs.

## Features

- **FastAPI** with automatic OpenAPI docs
- **Virtual environment** for isolated dependencies
- **Environment configuration** with .env support
- **CORS enabled** for frontend integration
- **In-memory storage** for quick development
- **Pydantic models** for type safety
- **Health check endpoints**

## Quick Start

```bash
# Initialize environment
./init.sh

# Start development server
./run.sh
```

## Endpoints

- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Items API**: http://localhost:8000/api/v1/items

## Project Structure

```
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── .env.template       # Environment variables template
├── .env                # Your environment variables (created by init.sh)
├── init.sh             # Setup script
├── run.sh              # Development server script
└── venv/               # Virtual environment (created by init.sh)
```

## Environment Variables

Copy `.env.template` to `.env` and customize:

- `APP_NAME`: Application name
- `DEBUG`: Debug mode (true/false)
- `PORT`: Server port (default: 8000)
- `DATABASE_URL`: Database connection (SQLite for MVP)

## Next Steps

For production deployment:
1. Replace in-memory storage with proper database
2. Add authentication and authorization
3. Implement proper error handling
4. Add logging and monitoring
5. Configure CORS for specific origins