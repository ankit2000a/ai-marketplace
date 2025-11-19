#!/bin/bash

# Change to project directory
cd ~/Build/Sanre/ai_marketplace

echo "🚀 Starting AI Marketplace..."
echo "📂 Working directory: $(pwd)"

# Kill existing processes (macOS compatible)
echo "🛑 Stopping existing services..."
lsof -ti :8000 | xargs kill -9 2>/dev/null
lsof -ti :8001 | xargs kill -9 2>/dev/null
lsof -ti :8002 | xargs kill -9 2>/dev/null
lsof -ti :8003 | xargs kill -9 2>/dev/null
lsof -ti :8004 | xargs kill -9 2>/dev/null
sleep 1

# Start registry
echo "📍 Starting Registry..."
python registry.py > logs/registry.log 2>&1 &
sleep 3

# Verify registry started
if lsof -ti :8000 > /dev/null; then
    echo "   ✅ Registry running on port 8000"
else
    echo "   ❌ Registry failed to start!"
    exit 1
fi

# Start agents
echo "🤖 Starting Summarizer..."
python summarizer_agent.py > logs/summarizer.log 2>&1 &
sleep 2

echo "🤖 Starting ChartBot Budget..."
python chartbot_budget_agent.py > logs/chartbot_budget.log 2>&1 &
sleep 2

echo "🤖 Starting ChartBot Pro..."
python chartbot_pro_agent.py > logs/chartbot_pro.log 2>&1 &
sleep 2

echo "🤖 Starting Project Manager..."
python project_manager_agent.py > logs/project_manager.log 2>&1 &
sleep 2

# Check status
echo ""
echo "✅ All services started!"
echo ""
echo "📊 Running Services:"
lsof -i :8000 | grep LISTEN && echo "   ✅ Registry (8000)"
lsof -i :8001 | grep LISTEN && echo "   ✅ Project Manager (8001)"
lsof -i :8002 | grep LISTEN && echo "   ✅ Summarizer (8002)"
lsof -i :8003 | grep LISTEN && echo "   ✅ ChartBot Pro (8003)"
lsof -i :8004 | grep LISTEN && echo "   ✅ ChartBot Budget (8004)"

echo ""
echo "📋 Checking agent registration..."
sleep 2
curl -s "http://127.0.0.1:8000/agents" | jq -r '.[] | "   ✅ \(.name) - \(.capability) ($\(.price))"'

echo ""
echo "🎯 Test the system:"
echo "   curl -X POST http://127.0.0.1:8001/execute_task -H 'Content-Type: application/json' -d '{\"task_data\": {\"text_to_summarize\": \"Test\"}}' | jq ."
echo ""
echo "📄 View logs: tail -f logs/*.log"
