#!/bin/bash
# 🔒 Privacy Protection Check Script
# Ensures no personal data is accidentally committed to git

echo "🔒 LibraryOfBabel Privacy Protection Check"
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "="

# Check for personal data files in git staging
echo "📋 Checking git staging area for personal data..."

PERSONAL_PATTERNS=(
    "*wei*"
    "*zhang*" 
    "*linda*"
    "*personal*"
    "*user_profile*"
    "*interaction*"
    "*performance*"
    "*workforce*"
    "*hr_analytics*"
    "*agent_memory*"
    "*conversation*"
    "*session*"
)

FOUND_ISSUES=0

for pattern in "${PERSONAL_PATTERNS[@]}"; do
    if git diff --cached --name-only | grep -i "$pattern" > /dev/null; then
        echo "⚠️  WARNING: Personal data pattern '$pattern' found in staging!"
        git diff --cached --name-only | grep -i "$pattern"
        FOUND_ISSUES=1
    fi
done

# Check for specific file types that might contain personal data
echo ""
echo "📂 Checking for sensitive file types..."

SENSITIVE_EXTENSIONS=(
    "*.json"
    "*.log" 
    "*.sql"
    "*.csv"
)

for ext in "${SENSITIVE_EXTENSIONS[@]}"; do
    staged_files=$(git diff --cached --name-only | grep "$ext" | grep -E "(hr|personal|user|agent|workforce)" || true)
    if [ ! -z "$staged_files" ]; then
        echo "⚠️  WARNING: Potentially sensitive $ext files in staging:"
        echo "$staged_files"
        FOUND_ISSUES=1
    fi
done

# Check if HR analytics directory is properly ignored
echo ""
echo "🛡️  Verifying HR analytics protection..."

if [ -d "reports/hr_analytics" ]; then
    if git check-ignore reports/hr_analytics/ > /dev/null; then
        echo "✅ HR analytics directory properly ignored"
    else
        echo "❌ CRITICAL: HR analytics directory NOT ignored!"
        FOUND_ISSUES=1
    fi
else
    echo "ℹ️  No HR analytics directory found"
fi

# Check for accidentally tracked personal files
echo ""
echo "🔍 Scanning for accidentally tracked personal files..."

TRACKED_PERSONAL=$(git ls-files | grep -E "(wei|zhang|linda|personal|hr_analytics|interaction|workforce)" || true)
if [ ! -z "$TRACKED_PERSONAL" ]; then
    echo "❌ CRITICAL: Personal files found in git tracking:"
    echo "$TRACKED_PERSONAL"
    FOUND_ISSUES=1
else
    echo "✅ No personal files found in git tracking"
fi

# Summary
echo ""
echo "📊 Privacy Check Summary"
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "="

if [ $FOUND_ISSUES -eq 0 ]; then
    echo "🎉 PRIVACY CHECK PASSED!"
    echo "✅ No personal data found in git staging"
    echo "✅ All sensitive files properly protected"
    echo "✅ Ready for safe commit"
    exit 0
else
    echo "🚨 PRIVACY CHECK FAILED!"
    echo "❌ Personal data protection issues found"
    echo "❌ DO NOT COMMIT until issues are resolved"
    echo ""
    echo "🔧 Recommended actions:"
    echo "1. Remove personal files from staging: git reset HEAD <file>"
    echo "2. Add files to .gitignore if needed"
    echo "3. Run privacy check again before committing"
    exit 1
fi