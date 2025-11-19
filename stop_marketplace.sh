#!/bin/bash

echo "🛑 Stopping AI Marketplace..."

lsof -ti :8000 | xargs kill -9 2>/dev/null && echo "   ✅ Registry stopped"
lsof -ti :8001 | xargs kill -9 2>/dev/null && echo "   ✅ Project Manager stopped"
lsof -ti :8002 | xargs kill -9 2>/dev/null && echo "   ✅ Summarizer stopped"
lsof -ti :8003 | xargs kill -9 2>/dev/null && echo "   ✅ ChartBot Pro stopped"
lsof -ti :8004 | xargs kill -9 2>/dev/null && echo "   ✅ ChartBot Budget stopped"

echo ""
echo "✅ All services stopped!"
