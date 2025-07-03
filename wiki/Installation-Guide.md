# Installation Guide

Complete setup instructions for the Library of Babel system. Choose your installation path based on your intended use.

## 🎯 Installation Paths

### 📚 **Educational Path** - Experience Borges' Infinite Library
Perfect for students, educators, and literary enthusiasts who want to explore procedural content generation.

### 🔬 **Research Path** - Complete Ebook Research System  
Ideal for researchers, data scientists, and bibliophiles who want to analyze real book collections.

### 💻 **Developer Path** - Full Development Environment
For contributors and developers who want to extend the system.

---

## 📚 Educational Path (Quickest Start)

Experience the infinite library concept with minimal setup.

### Prerequisites
- **Node.js** 18+ (Download from [nodejs.org](https://nodejs.org/))
- **Git** (Usually pre-installed on macOS/Linux)
- **5GB free disk space**

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone [repository-url]
   cd LibraryOfBabel
   ```

2. **Setup Backend**
   ```bash
   cd babel-backend
   npm install
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env file:
   # PORT=5570
   # LIBRARY_MODE=educational
   # ENHANCED_MODE=false
   ```

4. **Start the System**
   ```bash
   npm start
   ```

5. **Explore the Library**
   - Open browser to `http://localhost:5570`
   - Try searching for "infinity and paradox"
   - Navigate to specific books using coordinates

### ✅ Verification
```bash
# Test the API
curl http://localhost:5570/api/library/info

# Expected response:
{
  "name": "Library of Babel",
  "mode": "educational",
  "features": {
    "proceduralGeneration": true,
    "infiniteSpace": true
  }
}
```

---

## 🔬 Research Path (Complete System)

Full ebook processing and AI agent system for serious research.

### Prerequisites

#### System Requirements
- **Operating System**: macOS 10.15+, Ubuntu 18.04+, or Windows 10+ with WSL
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB free space (more for large ebook collections)
- **Python**: 3.8+ with pip
- **PostgreSQL**: 12+ 
- **Node.js**: 18+ (for web interface)

#### Package Managers
```bash
# macOS (install Homebrew first)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# Windows (install WSL2 and Ubuntu first)
wsl --install -d Ubuntu
```

### Installation Steps

#### 1. **Clone Repository**
```bash
git clone [repository-url]
cd LibraryOfBabel
```

#### 2. **Install System Dependencies**

**macOS:**
```bash
# Install PostgreSQL
brew install postgresql@14
brew services start postgresql@14

# Install Python dependencies
brew install python@3.11

# Install Node.js
brew install node@18
```

**Ubuntu/Debian:**
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib python3-psycopg2

# Install Python and Node.js
sudo apt install python3.11 python3-pip nodejs npm

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 3. **Setup PostgreSQL Database**
```bash
# Create database user (if needed)
sudo -u postgres createuser --interactive librarybabel

# Setup database schema
cd database/schema
chmod +x setup.sh
./setup.sh
```

#### 4. **Install Python Dependencies**
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

#### 5. **Install AI Agent Dependencies**
```bash
# Install EPUB and analysis libraries
pip install EbookLib beautifulsoup4 networkx matplotlib
pip install numpy pandas scipy scikit-learn

# Install optional PDF support
pip install PyPDF2
```

#### 6. **Configure Environment**
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings:
nano .env
```

**Required Environment Variables:**
```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost/librarybabel
DB_HOST=localhost
DB_PORT=5432
DB_NAME=librarybabel
DB_USER=your_username
DB_PASSWORD=your_password

# Library Configuration  
LIBRARY_MODE=research
ENHANCED_MODE=true
EBOOKS_PATH=/path/to/your/ebooks

# AI Agent Configuration
REDDIT_AGENT_ENABLED=true
QA_AGENT_ENABLED=true
SEEDING_MONITOR_ENABLED=true

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Optional: MAM Integration (for automated ebook discovery)
MAM_USERNAME=your_mam_username
MAM_PASSWORD=your_mam_password
MAM_ENABLED=false  # Set to true only if you have MAM access
```

#### 7. **Setup Ebook Processing**
```bash
# Create ebook directories
mkdir -p ebooks/{downloads,processed,torrents,analysis}

# Test EPUB processing with sample files
python3 src/epub_processor.py --input ebooks/downloads/ --test
```

#### 8. **Initialize AI Agents**
```bash
# Setup Reddit Bibliophile Agent
cd agents/reddit_bibliophile
python3 reddit_bibliophile_agent.py --config ../../config/agent_configs/reddit_config.json

# Setup QA Agent
cd ../qa_system  
python3 qa_agent.py --initialize

# Setup Seeding Monitor (if using torrents)
cd ../seeding_monitor
python3 seeding_monitor.py --setup
```

#### 9. **Start the Complete System**
```bash
# Start database (if not running)
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Start the search API
python3 src/api/search_api.py &

# Start the backend server
cd babel-backend
npm start &

# Start the frontend (optional)
cd ../frontend
npm install
npm start &

# Start AI agents
python3 agents/reddit_bibliophile/reddit_bibliophile_agent.py --daemon &
```

### ✅ Research Path Verification

1. **Test Database Connection**
   ```bash
   python3 -c "
   import psycopg2
   conn = psycopg2.connect('postgresql://localhost/librarybabel')
   print('Database connection successful!')
   conn.close()
   "
   ```

2. **Test EPUB Processing**
   ```bash
   # Process a sample EPUB
   python3 src/epub_processor.py --input path/to/sample.epub --verbose
   ```

3. **Test AI Agents**
   ```bash
   # Run Reddit Bibliophile Agent
   python3 agents/reddit_bibliophile/reddit_bibliophile_agent.py --books 1
   ```

4. **Test Search API**
   ```bash
   curl -X POST http://localhost:5560/search \
     -H "Content-Type: application/json" \
     -d '{"query": "machine learning"}'
   ```

---

## 💻 Developer Path (Full Environment)

Complete development setup for contributing to the project.

### Additional Prerequisites
- **Git LFS** (for large files)
- **Docker** (optional, for containerized development)
- **Playwright** (for automated testing)
- **ESLint/Prettier** (for code formatting)

### Development Setup

#### 1. **Fork and Clone**
```bash
# Fork the repository on GitHub first
git clone https://github.com/YOUR_USERNAME/LibraryOfBabel.git
cd LibraryOfBabel

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_USERNAME/LibraryOfBabel.git
```

#### 2. **Install Development Tools**
```bash
# Install Git LFS
git lfs install
git lfs pull

# Install Docker (optional)
# macOS: Download Docker Desktop
# Ubuntu: sudo apt install docker.io docker-compose

# Install Playwright for testing
npm install -g playwright
playwright install
```

#### 3. **Setup Development Environment**
```bash
# Install all dependencies
npm install
cd frontend && npm install && cd ..
cd babel-backend && npm install && cd ..
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 4. **Configure Development Settings**
```bash
# Copy development environment
cp .env.dev.example .env.dev

# Edit development settings
nano .env.dev
```

**Development Environment Variables:**
```bash
# Development Mode
NODE_ENV=development
DEBUG_MODE=true
HOT_RELOAD=true

# Testing
PLAYWRIGHT_TEST_MODE=true
TEST_DATABASE_URL=postgresql://localhost/librarybabel_test

# Development Ports
BACKEND_PORT=5570
FRONTEND_PORT=3000
API_PORT=5560

# Logging
LOG_LEVEL=debug
LOG_FILE=logs/development.log
```

#### 5. **Setup Testing**
```bash
# Create test database
createdb librarybabel_test

# Run initial tests
npm test
python3 -m pytest tests/
playwright test
```

#### 6. **Development Workflow**
```bash
# Start development servers
npm run dev          # Starts all services with hot reload
# OR start individually:
npm run dev:backend   # Backend only
npm run dev:frontend  # Frontend only
npm run dev:api      # API only

# Run tests continuously
npm run test:watch
python3 -m pytest tests/ --watch
```

### Development Tools

#### Code Quality
```bash
# ESLint (JavaScript/TypeScript)
npm run lint
npm run lint:fix

# Black (Python formatting)
black src/ tests/ agents/

# Type checking
npm run type-check
mypy src/ agents/
```

#### Testing
```bash
# Unit tests
npm test
python3 -m pytest tests/unit/

# Integration tests  
npm run test:integration
python3 -m pytest tests/integration/

# End-to-end tests
playwright test

# Performance tests
npm run test:performance
```

#### Git Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Manual hook run
pre-commit run --all-files
```

---

## 🚨 Troubleshooting

### Common Issues

#### PostgreSQL Connection Issues
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # macOS

# Reset PostgreSQL password
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'newpassword';"
```

#### Python Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall packages
pip install --force-reinstall -r requirements.txt
```

#### Node.js Version Issues
```bash
# Install Node Version Manager
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install and use correct Node version
nvm install 18
nvm use 18
```

#### Permission Issues (macOS)
```bash
# Fix npm permissions
sudo chown -R $(whoami) $(npm config get prefix)/{lib/node_modules,bin,share}

# Fix PostgreSQL permissions
sudo chown -R $(whoami) /usr/local/var/postgres/
```

#### Port Conflicts
```bash
# Find what's using a port
lsof -i :5570
lsof -i :3000

# Kill process using port
kill -9 $(lsof -t -i :5570)
```

### Getting Help

1. **Check the [Troubleshooting](Troubleshooting)** page for specific issues
2. **Review logs** in `logs/` directory
3. **Run diagnostic script** `scripts/diagnose.sh`
4. **Open an issue** on GitHub with logs and system info

---

## 🎯 Next Steps

### Educational Path
- Explore the **[API Reference](API-Reference)** to understand available endpoints
- Read about **[Procedural Generation Algorithm](Procedural-Generation-Algorithm)** 
- Try the **[Quick Start Tutorial](Quick-Start-Tutorial)**

### Research Path  
- Process your first ebook collection
- Run the **Reddit Bibliophile Agent** analysis
- Explore **[AI Agents Guide](AI-Agents-Guide)**

### Developer Path
- Read the **[Development Guide](Development-Guide)**
- Review the **[Architecture Overview](Architecture-Overview)**
- Check out open issues on GitHub

---

*Installation complete! Welcome to the Library of Babel. Every possible book awaits your discovery.*