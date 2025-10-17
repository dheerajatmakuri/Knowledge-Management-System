# Knowledge Management System

A modern, production-ready platform for scraping, extracting, searching, and chatting with organizational knowledge—built for leadership discovery, hybrid search, and AI-powered Q&A.

## 🚀 Features

- **URL Leadership Extraction**: Scrape any company website, auto-navigate to leadership/team pages, and extract names, roles, and images.
- **Universal Extraction Engine**: Multiple strategies to handle WordPress, custom, and enterprise sites.
- **Beautiful Streamlit UI**: Responsive, dark-mode friendly, with card grids, chat, and export features.
- **Hybrid Search Engine**: Combines full-text, vector, and metadata search for best-in-class relevance.
- **AI Chat Service**: Ask questions about extracted knowledge, get direct answers (e.g., "Who is the CEO?"), and see source citations.
- **Database Integration**: Store and manage profiles with SQLAlchemy and repository pattern.
- **Configurable & Extensible**: YAML/ENV config, modular services, and easy to extend for new domains.

## 🏗️ Project Structure

```
knowledge-management-system/
├── src/
│   ├── ui/                # Streamlit interfaces
│   ├── scrapers/          # Web scraping logic
│   ├── services/          # Chat, search, and business logic
│   ├── database/          # Models, repositories, migrations
│   └── ...
├── data/                  # Backups, cache, embeddings
├── config/                # YAML and environment configs
├── tests/                 # Unit and integration tests
├── requirements.txt       # Python dependencies
└── README.md
```

## ⚡ Quick Start

1. **Clone the repo:**
   ```sh
   git clone https://github.com/dheerajatmakuri/Knowledge-Management-System.git
   cd Knowledge-Management-System
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Configure environment:**
   - Copy `.env.example` to `.env` and fill in your keys (OpenAI, etc.)
   - Edit `config/config.yaml` as needed
4. **Run the app:**
   ```sh
   streamlit run src/ui/url_chat_interface.py --server.port 8503
   ```
5. **Open in browser:**
   - Go to [http://localhost:8503](http://localhost:8503)

## 🧠 How It Works

- **Leadership Extraction:**
  - Enter a company URL, the system auto-navigates to the leadership/team page, and extracts all leaders with names, roles, and images.
  - Handles WordPress, Elementor, and custom layouts.
- **Hybrid Search & AI Chat:**
  - Search and chat with the extracted knowledge using advanced hybrid search and GPT-4.
  - Ask direct questions ("Who is the CEO?"), get precise answers with citations.
- **Database & Export:**
  - Save extracted profiles to SQLite, export as JSON, and manage your knowledge base.

## 🛡️ Security & Privacy
- No sensitive data is stored by default.
- API keys and credentials are managed via `.env` and never committed.

## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📄 License
MIT License. See [LICENSE](LICENSE) for details.

---

**Built with ❤️ by Dheeraj Atmakuri and contributors.**
