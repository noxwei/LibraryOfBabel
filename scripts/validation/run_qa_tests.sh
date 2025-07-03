#!/bin/bash

# LibraryOfBabel Essay QA Test Runner
# Comprehensive testing before any commits

echo "🚀 LibraryOfBabel Essay Generation QA Pipeline"
echo "================================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "essay_qa_system.py" ]; then
    echo -e "${RED}❌ Error: Must be run from LibraryOfBabel root directory${NC}"
    exit 1
fi

# Create test directories
echo -e "${BLUE}📁 Setting up test directories...${NC}"
mkdir -p tests/essays
mkdir -p tests/reports

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${BLUE}🐍 Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Check if PostgreSQL is running
echo -e "${BLUE}🗄️ Checking PostgreSQL connection...${NC}"
if ! psql -h localhost -U weixiangzhang -d knowledge_base -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${RED}❌ PostgreSQL not accessible. Please start PostgreSQL and ensure knowledge_base exists.${NC}"
    exit 1
fi

# Check if Ollama is running
echo -e "${BLUE}🤖 Checking Ollama connection...${NC}"
if ! curl -s http://localhost:11434/api/version > /dev/null; then
    echo -e "${RED}❌ Ollama not accessible. Please start Ollama service.${NC}"
    echo -e "${YELLOW}   Run: ollama serve${NC}"
    exit 1
fi

# Start the essay API in background if not running
echo -e "${BLUE}🌐 Checking essay API...${NC}"
if ! curl -s http://localhost:5571/api/health > /dev/null; then
    echo -e "${YELLOW}⚠️ Essay API not running. Starting it...${NC}"
    python3 high_quality_essay_api.py &
    API_PID=$!
    
    # Wait for API to start
    echo -e "${BLUE}⏳ Waiting for API to start...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:5571/api/health > /dev/null; then
            echo -e "${GREEN}✅ API started successfully${NC}"
            break
        fi
        sleep 2
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ API failed to start within 60 seconds${NC}"
            kill $API_PID 2>/dev/null
            exit 1
        fi
    done
else
    echo -e "${GREEN}✅ Essay API already running${NC}"
    API_PID=""
fi

# Run the QA tests
echo -e "\n${BLUE}🔍 Running comprehensive QA tests...${NC}"
python3 essay_qa_system.py
QA_EXIT_CODE=$?

# Stop API if we started it
if [ ! -z "$API_PID" ]; then
    echo -e "\n${BLUE}🛑 Stopping API...${NC}"
    kill $API_PID 2>/dev/null
fi

# Interpret results
echo -e "\n${BLUE}📊 QA Results:${NC}"
case $QA_EXIT_CODE in
    0)
        echo -e "${GREEN}🎉 ALL TESTS PASSED - System ready for commit!${NC}"
        echo -e "${GREEN}✅ Essay generation quality validated${NC}"
        echo -e "${GREEN}✅ All components functioning correctly${NC}"
        ;;
    1)
        echo -e "${YELLOW}⚠️ Tests passed with warnings - Review before commit${NC}"
        echo -e "${YELLOW}📝 Check generated essays and QA report for details${NC}"
        ;;
    2)
        echo -e "${RED}❌ Tests failed - Do not commit until issues resolved${NC}"
        echo -e "${RED}🔧 Fix reported issues before attempting commit${NC}"
        ;;
    *)
        echo -e "${RED}❌ Unexpected error in QA system${NC}"
        ;;
esac

# Show generated files
echo -e "\n${BLUE}📁 Generated files:${NC}"
if [ -d "tests/essays" ] && [ "$(ls -A tests/essays)" ]; then
    echo -e "${GREEN}📝 Essays:${NC}"
    ls -la tests/essays/
fi

if [ -d "tests" ] && [ "$(ls -A tests/*.json 2>/dev/null)" ]; then
    echo -e "${GREEN}📊 Reports:${NC}"
    ls -la tests/qa_report_*.json 2>/dev/null || true
fi

echo -e "\n${BLUE}🔍 Next steps:${NC}"
if [ $QA_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}1. Review generated essays for quality${NC}"
    echo -e "${GREEN}2. Commit changes to repository${NC}"
    echo -e "${GREEN}3. Push to remote if satisfied${NC}"
elif [ $QA_EXIT_CODE -eq 1 ]; then
    echo -e "${YELLOW}1. Review warnings in QA report${NC}"
    echo -e "${YELLOW}2. Check generated essays${NC}"
    echo -e "${YELLOW}3. Decide if acceptable for commit${NC}"
else
    echo -e "${RED}1. Review failed tests in QA report${NC}"
    echo -e "${RED}2. Fix identified issues${NC}"
    echo -e "${RED}3. Re-run QA tests${NC}"
fi

exit $QA_EXIT_CODE