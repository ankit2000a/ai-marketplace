#!/bin/bash

echo "📊 AI Marketplace Status Check"
echo "=============================="
echo ""

# Check services
echo "🔍 Running Services:"
lsof -i :8000 | grep LISTEN > /dev/null && echo "   ✅ Registry (8000)" || echo "   ❌ Registry (8000) NOT RUNNING"
lsof -i :8001 | grep LISTEN > /dev/null && echo "   ✅ Project Manager (8001)" || echo "   ❌ Project Manager (8001) NOT RUNNING"
lsof -i :8002 | grep LISTEN > /dev/null && echo "   ✅ Summarizer (8002)" || echo "   ❌ Summarizer (8002) NOT RUNNING"
lsof -i :8003 | grep LISTEN > /dev/null && echo "   ✅ ChartBot Pro (8003)" || echo "   ❌ ChartBot Pro (8003) NOT RUNNING"
lsof -i :8004 | grep LISTEN > /dev/null && echo "   ✅ ChartBot Budget (8004)" || echo "   ❌ ChartBot Budget (8004) NOT RUNNING"

echo ""
echo "🤖 Registered Agents:"
curl -s "http://127.0.0.1:8000/agents" 2>/dev/null | jq -r '.[] | "   ✅ \(.name) - \(.capability) ($\(.price)) - Rating: \(.rating)⭐"' 2>/dev/null || echo "   ❌ Cannot connect to registry"

echo ""
echo "💰 Recent Transactions:"
curl -s "http://127.0.0.1:8000/transactions" 2>/dev/null | jq -r '.[-5:] | .[] | "   \(.buyer_id) → \(.seller_name): $\(.price)"' 2>/dev/null || echo "   No transactions yet"
