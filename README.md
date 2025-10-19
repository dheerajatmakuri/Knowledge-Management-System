# Intelligent Knowledge Management System

## Overview
An advanced knowledge management system that demonstrates intelligent data collection, storage optimization, semantic search, and scope-aware AI interactions.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Web Scraping    │────▶│ Knowledge       │────▶│ Query Engine    │
│ Engine          │     │ Storage         │     │                 │
│ • Profile Pages │     │ • SQLite/JSON   │     │ • Semantic      │
│ • Structured    │     │ • Indexing      │     │   Search        │
│ • Auto-Discovery│     │ • Categories    │     │ • Scope Check   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
             ┌──────▼──────┐      ┌──────▼──────┐
             │ Streamlit UI│      │ AI Assistant│
             │             │      │             │
             │ • Chat      │      │ • Context   │
             │ • Browse    │      │ • Scoped    │
             │ • Data Mgmt │      │ • Helpful   │
             └─────────────┘      └─────────────┘
```

## Features

### 1. Web Scraping Engine
- Extract profile pages with structured data
- Auto-discover linked pages
- Rate limiting and respectful scraping
- Error handling and retry logic

### 2. Knowledge Storage
- SQLite database with optimized schema
- JSON export/import functionality
- Full-text search indexing
- Category-based organization

### 3. Query Engine
- Semantic search using sentence transformers
- Vector embeddings for similarity matching
- Scope checking for relevant results
- Ranking and filtering

### 4. Streamlit UI
- Interactive chat interface
- Profile browsing and search
- Data management dashboard
- Visualization of knowledge graph

### 5. AI Assistant
- Context-aware responses
- Scope-limited queries
- Integration with OpenAI or local LLMs
- Helpful error messages

## Installation

### Prerequisites
- Python 3.9+
- pip

### Setup

1. Clone the repository or navigate to project directory

2. Create and activate virtual environment:
```powershell
# Windows PowerShell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install dependencies:
```powershell
pip install -r requirements.txt
```

4. Configure environment variables:
```powershell
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Initialize the database:
```powershell
python -m src.storage.database init
```

## Usage

### Run the Streamlit App
```powershell
streamlit run src/ui/app.py
```

### Scrape a Website
```powershell
python -m src.scraper.scraper --url https://example.com/leadership-team/
```

### Query the Knowledge Base
```powershell
python -m src.query.search "Who is the CEO?"
```

## Project Structure

```
knowledge-management-system/
├── src/
│   ├── scraper/          # Web scraping engine
│   │   ├── __init__.py
│   │   ├── scraper.py    # Main scraper
│   │   ├── parser.py     # HTML parser
│   │   └── discovery.py  # Link discovery
│   ├── storage/          # Database and storage
│   │   ├── __init__.py
│   │   ├── database.py   # Database operations
│   │   ├── models.py     # Data models
│   │   └── exporter.py   # Export functionality
│   ├── query/            # Search and retrieval
│   │   ├── __init__.py
│   │   ├── search.py     # Search engine
│   │   ├── embeddings.py # Vector embeddings
│   │   └── ranking.py    # Result ranking
│   ├── assistant/        # AI assistant
│   │   ├── __init__.py
│   │   ├── chatbot.py    # Chat interface
│   │   ├── context.py    # Context management
│   │   └── prompts.py    # Prompt templates
│   └── ui/               # User interface
│       ├── __init__.py
│       ├── app.py        # Main Streamlit app
│       ├── components/   # UI components
│       └── utils.py      # UI utilities
├── data/                 # Data storage
│   ├── database.db
│   ├── embeddings/
│   ├── cache/
│   └── backups/
├── tests/                # Tests
│   ├── unit/
│   └── integration/
├── config/               # Configuration
├── logs/                 # Application logs
├── requirements.txt      # Dependencies
├── .env.example          # Environment template
├── .gitignore
└── README.md
```

## Configuration

Edit `.env` file with your settings:

```env
# OpenAI API Key (optional)
OPENAI_API_KEY=your_key_here

# Database path
DATABASE_PATH=data/database.db

# Scraper settings
RATE_LIMIT_DELAY=1.0
MAX_RETRIES=3

# Embeddings model
EMBEDDINGS_MODEL=all-MiniLM-L6-v2
```

## Development

### Running Tests
```powershell
pytest tests/
```

### Code Formatting
```powershell
black src/ tests/
```

## Roadmap

- [x] Project structure and setup
- [ ] Web scraping engine
- [ ] Knowledge storage system
- [ ] Semantic search implementation
- [ ] Streamlit UI
- [ ] AI assistant integration
- [ ] Testing and documentation

## License

MIT License

## Contact

For questions or support, please open an issue on GitHub.

---

Built with ❤️ using Python, Streamlit, and modern NLP technologies.
