# 🛠️ Installation Guide

## 🎯 **Choose Your Installation Path**

The Library of Babel offers three installation options depending on your use case:

### 📚 **Educational Path** - For Classrooms & Learning
Perfect for teachers, students, and educational institutions

### 🔬 **Research Path** - For Academics & Analysis  
Ideal for researchers, digital humanities scholars, and advanced users

### 💻 **Developer Path** - For Contributors & Customization
For developers wanting to contribute or customize the system

---

## 📚 **Educational Installation**

### **Prerequisites**
- **Computer**: Mac, Windows, or Linux
- **Node.js**: Version 18 or higher ([Download here](https://nodejs.org))
- **Memory**: 2GB RAM minimum, 4GB recommended
- **Storage**: 1GB free space

### **Quick Setup (15 minutes)**

1. **Download the Project**
```bash
git clone https://github.com/noxwei/LibraryOfBabel.git
cd LibraryOfBabel
```

2. **Install Everything**
```bash
npm run install-all
```

3. **Start the System**
```bash
npm run start-dev
```

4. **Open Your Browser**
- **Frontend**: http://localhost:3000 (Beautiful mystical interface)
- **Backend**: http://localhost:5570 (API for advanced users)

### **Classroom Network Setup**

For classroom use where students access from multiple devices:

1. **Start Local Network Servers**
```bash
cd babel-backend
npm run start:local
```

2. **Find Your Network IP**
The system will automatically detect your local IP (e.g., 10.0.0.13)

3. **Student Access**
- **Hell Theme**: http://YOUR_IP:5571 (Red/black dramatic theme)
- **Quest Theme**: http://YOUR_IP:5572 (Gold/blue scholarly theme)

### **Educational Features**
- ✅ **Safe Content**: All generated books are educational and appropriate
- ✅ **No Internet Required**: Works completely offline
- ✅ **Multiple Themes**: Choose atmosphere for different lesson types
- ✅ **Seeker Mode**: Hidden advanced features for instructors

---

## 🔬 **Research Installation**

### **Prerequisites** 
- **Academic/Research Environment**: University computer or research lab
- **Node.js**: Version 18+ with npm 8+
- **Memory**: 4GB RAM minimum, 8GB recommended for large collections
- **Storage**: 5GB+ for ebook processing and analysis

### **Advanced Setup (30 minutes)**

1. **Clone and Configure**
```bash
git clone https://github.com/noxwei/LibraryOfBabel.git
cd LibraryOfBabel
npm run install-all
```

2. **Enable Research Features**
```bash
# Copy research configuration
cp babel-backend/.env.production.example babel-backend/.env.local

# Edit configuration for your research needs
nano babel-backend/.env.local
```

3. **Configure Research Settings**
```bash
# In .env.local file:
ENHANCED_MODE=true
REAL_SEARCH_API=http://localhost:5560  # Your existing search system
SEEKER_MODE_ENABLED=true
SEEKER_MODE_KEY=your_unique_research_key
```

4. **Start Research Servers**
```bash
npm run start:research
```

### **Research Capabilities**
- 🤖 **AI Agent Analysis**: Reddit Bibliophile provides intelligent insights
- 📊 **Knowledge Graphs**: Visual concept relationship mapping
- 🔍 **Hybrid Search**: Combine procedural and real content analysis
- 📚 **Ebook Integration**: Process and analyze personal collections
- 🎯 **Seeker Mode**: Enhanced research features and real content access

### **AI Agent Setup**

The Reddit Bibliophile Agent requires additional configuration:

1. **Verify Agent Installation**
```bash
cd agents/reddit_bibliophile
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Test Agent Functionality**
```bash
python test_agent.py
```

3. **Expected Output**
```
🤓 u/DataScientistBookworm's Analysis Results:
- Knowledge graphs generated: ✅
- Chapter outlines extracted: ✅  
- Reddit-style analysis: ✅
- Seeding compliance: ✅
```

---

## 💻 **Developer Installation**

### **Prerequisites**
- **Development Environment**: Code editor (VS Code recommended)
- **Node.js**: Version 18+ with npm 8+
- **Python**: Version 3.8+ (for AI agents)
- **Git**: For version control and contributions
- **Memory**: 8GB RAM recommended
- **Storage**: 10GB+ for full development environment

### **Complete Development Setup (45 minutes)**

1. **Fork and Clone**
```bash
# Fork the repository on GitHub first
git clone https://github.com/YOUR_USERNAME/LibraryOfBabel.git
cd LibraryOfBabel
git remote add upstream https://github.com/noxwei/LibraryOfBabel.git
```

2. **Install All Dependencies**
```bash
# Root dependencies (Playwright testing)
npm install

# Backend dependencies
cd babel-backend && npm install && cd ..

# Frontend dependencies  
cd frontend && npm install && cd ..

# AI agent dependencies
cd agents/reddit_bibliophile
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ../..
```

3. **Development Environment Configuration**
```bash
# Copy all environment templates
cp babel-backend/.env.example babel-backend/.env
cp babel-backend/.env.local.example babel-backend/.env.local
cp babel-backend/.env.production.example babel-backend/.env.production
```

4. **Start Development Servers**
```bash
# Terminal 1: Backend
cd babel-backend && npm run dev

# Terminal 2: Frontend  
cd frontend && npm start

# Terminal 3: Local testing (optional)
cd babel-backend && npm run dev:local
```

### **Development Tools**

1. **Automated Testing**
```bash
# Install Playwright browsers
npx playwright install

# Run complete test suite
npm test

# Run tests with UI (watch the agent explore!)
npm run test:headed
```

2. **Code Quality**
```bash
# Lint backend code
cd babel-backend && npm run lint

# Build frontend
cd frontend && npm run build
```

3. **Testing Endpoints**
```bash
# Health check
curl http://localhost:5570/api/health

# Search test
curl -X POST http://localhost:5570/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "infinity paradox", "maxResults": 3}'

# Network scan (for local testing)
curl http://localhost:5571/api/network/scan
```

### **Development Workflow**

1. **Making Changes**
   - Create feature branch: `git checkout -b feature/your-feature`
   - Make your changes and test thoroughly
   - Run automated tests: `npm test`
   - Commit with descriptive messages

2. **Testing Changes**
   - Test all three installation paths
   - Verify educational applications work
   - Test research features and AI agents
   - Run Playwright automation for validation

3. **Contributing**
   - Push branch: `git push origin feature/your-feature`
   - Create pull request on GitHub
   - Include tests and documentation
   - Follow code review process

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Port Already in Use**
```bash
# Kill processes on specific ports
lsof -ti:5570 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

#### **Node.js Version Issues**
```bash
# Check version
node --version  # Should be 18+

# Install Node Version Manager (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

#### **Frontend Build Errors**
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

#### **Backend API Errors**
```bash
# Check environment configuration
cd babel-backend
cat .env  # Verify configuration

# Restart with debug output
DEBUG=* npm start
```

### **Educational Troubleshooting**

#### **Students Can't Access on Network**
1. **Check Firewall**: Ensure ports 5571-5572 are open
2. **Verify IP**: Use `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
3. **Test Connection**: `ping YOUR_IP` from student device
4. **Alternative**: Use localhost and share screen

#### **Content Not Generating**
1. **Verify Installation**: `npm run health:all`
2. **Check Memory**: System needs 2GB+ available
3. **Restart Services**: Stop and restart all servers
4. **Clear Cache**: Delete temp files and restart

### **Research Troubleshooting**

#### **AI Agent Not Working**
1. **Python Environment**: Verify Python 3.8+ installed
2. **Dependencies**: `pip list` should show required packages
3. **Test Independently**: Run `python test_agent.py`
4. **Check Logs**: Look for error messages in agent output

#### **Enhanced Mode Failing**
1. **API Endpoint**: Verify REAL_SEARCH_API in .env.local
2. **Connection Test**: `curl YOUR_API_ENDPOINT/health`
3. **Fallback Mode**: System should fallback to procedural generation
4. **Debug Mode**: Set DEBUG_MODE=true for detailed logging

### **Developer Troubleshooting**

#### **Playwright Tests Failing**
1. **Browser Installation**: `npx playwright install`
2. **Server Status**: Ensure backend and frontend are running
3. **Port Conflicts**: Check no other services using ports
4. **Update Tests**: Tests may need updates for new features

#### **Git Issues**
1. **Upstream Sync**: `git fetch upstream && git merge upstream/main`
2. **Merge Conflicts**: Use VS Code or your preferred merge tool
3. **Branch Issues**: `git status` and follow Git recommendations
4. **Clean State**: `git stash` to temporarily save changes

---

## 🎯 **Verification**

### **Educational Verification**
- [ ] Can access http://localhost:3000
- [ ] Search returns academic books
- [ ] Multiple themes work (mystical vs infernal)
- [ ] Network access works from other devices
- [ ] No inappropriate content appears

### **Research Verification**  
- [ ] AI agent generates analysis reports
- [ ] Knowledge graphs visualize properly
- [ ] Enhanced mode connects to real search API
- [ ] Seeker mode provides additional features
- [ ] Large collections process efficiently

### **Developer Verification**
- [ ] All automated tests pass
- [ ] Code linting succeeds
- [ ] Both local and production servers start
- [ ] API endpoints return expected responses
- [ ] Frontend builds without errors

---

## 🎊 **Success!**

Once your installation is complete, you're ready to explore the infinite Library of Babel!

### **Next Steps:**
- **Educators**: Check out [Educational Applications](Educational-Applications)
- **Researchers**: Explore [AI Agents Guide](AI-Agents-Guide)  
- **Developers**: Review [Architecture Overview](Architecture-Overview)
- **Everyone**: Browse the [FAQ](FAQ) for tips and tricks

### **Need Help?**
- **Documentation**: This wiki covers all major features
- **Community**: GitHub Discussions for questions
- **Issues**: GitHub Issues for bugs and features
- **Educational Support**: Contact for classroom implementation

**Welcome to the infinite library! Every book that could ever exist awaits your discovery.** 🏛️✨