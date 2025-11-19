#!/bin/bash

# Change to project directory
cd ~/Build/Sanre/ai_marketplace

echo "🚀 Starting AI Marketplace (Smart Selection Demo)..."

# Kill existing processes
echo "🛑 Stopping existing services..."
lsof -ti :8000 | xargs kill -9 2>/dev/null
lsof -ti :8001 | xargs kill -9 2>/dev/null
lsof -ti :8002 | xargs kill -9 2>/dev/null
lsof -ti :8003 | xargs kill -9 2>/dev/null
lsof -ti :8004 | xargs kill -9 2>/dev/null
lsof -ti :8005 | xargs kill -9 2>/dev/null
lsof -ti :8006 | xargs kill -9 2>/dev/null
sleep 1

# Start registry
echo "📍 Starting Registry..."
python registry.py > logs/registry.log 2>&1 &
sleep 2

# Start agents
echo "🤖 Starting Summarizer..."
python summarizer_agent.py > logs/summarizer.log 2>&1 &
sleep 1

echo "🤖 Starting ChartBot Budget..."
python chartbot_budget_agent.py > logs/chartbot_budget.log 2>&1 &
sleep 1

echo "🤖 Starting ChartBot Pro..."
python chartbot_pro_agent.py > logs/chartbot_pro.log 2>&1 &
sleep 1

# Start PM Variants
echo "🤖 Starting PM Budget (Port 8001)..."
python pm_budget.py --port 8001 > logs/pm_budget.log 2>&1 &

echo "🤖 Starting PM Quality (Port 8005)..."
python pm_quality.py --port 8005 > logs/pm_quality.log 2>&1 &

echo "🤖 Starting PM Balanced (Port 8006)..."
python pm_balanced.py --port 8006 > logs/pm_balanced.log 2>&1 &

sleep 5

echo ""
echo "✅ All services started!"
echo "📊 Running Services:"
lsof -i :8000 | grep LISTEN && echo "   ✅ Registry (8000)"
lsof -i :8001 | grep LISTEN && echo "   ✅ PM Budget (8001)"
lsof -i :8005 | grep LISTEN && echo "   ✅ PM Quality (8005)"
lsof -i :8006 | grep LISTEN && echo "   ✅ PM Balanced (8006)"

echo ""
echo "📋 Registered Agents:"
curl -s "http://127.0.0.1:8000/agents" | jq -r '.[] | "   ✅ \(.name) - \(.capability) ($\(.price))"'

echo ""
echo "🎯 Ready to test!"
