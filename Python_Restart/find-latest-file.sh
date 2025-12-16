#!/bin/bash
echo "================================================"
echo "   MQL5 Latest File Finder"
echo "================================================"
echo ""
echo "📁 Searching for MQL5 files (sorted by newest first)..."
echo ""

# Find all MQL5 files and sort by modification time
find . -type f \( -name "*.mq5" -o -name "*.mq4" -o -name "*.mqh" \) -print0 | xargs -0 ls -lth | head -n 20

echo ""
echo "================================================"
echo "✅ The file at the TOP is your LATEST version"
echo "================================================"
