#!/bin/bash

echo "🎯 AI MARKETPLACE FINAL REPORT"
echo "=============================="
echo "Generated: $(date)"
echo ""

echo "📊 AGENT STATISTICS:"
curl -s http://127.0.0.1:8000/agents | jq '.[] | select(.capability == "generate_charts") | {
  name, 
  price, 
  rating, 
  total_jobs, 
  successful_jobs, 
  success_rate, 
  total_earned
}'

echo ""
echo "💰 REVENUE ANALYSIS:"
curl -s http://127.0.0.1:8000/transactions | jq '
  [.[] | select(.capability == "generate_charts")] | 
  group_by(.seller_name) | 
  map({
    agent: .[0].seller_name,
    jobs: length,
    revenue: ([.[].price] | add),
    avg_price: (([.[].price] | add) / length),
    market_share_pct: (length * 100 / 65)
  })
'

echo ""
echo "🎰 PM STRATEGY EFFECTIVENESS:"
curl -s http://127.0.0.1:8000/transactions | jq '
  [.[] | select(.capability == "generate_charts")] | 
  group_by(.buyer_id) | 
  map({
    pm: .[0].buyer_id,
    total_jobs: length,
    budget_pct: (([.[] | select(.seller_name == "ChartBot_Budget_v1")] | length) * 100 / length),
    pro_pct: (([.[] | select(.seller_name == "ChartBot_Pro_v1")] | length) * 100 / length)
  })
'

echo ""
echo "✅ MARKETPLACE HEALTH:"
echo "  Total Transactions: $(curl -s http://127.0.0.1:8000/transactions | jq 'length')"
echo "  Total Revenue: \$$(curl -s http://127.0.0.1:8000/transactions | jq '[.[] | .price] | add')"
echo "  Agents Earning: $(curl -s http://127.0.0.1:8000/agents | jq '[.[] | select(.total_earned > 0)] | length')"
echo "  Success Rate: $(curl -s http://127.0.0.1:8000/agents | jq '[.[] | .success_rate] | add / length')%"
