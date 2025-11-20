#!/bin/bash
echo "🔍 PRE-SAVE CHECKLIST"
echo "===================="
echo ""

# 1. Test PM cost tracking
echo "1. Testing PM cost tracking..."
response=$(curl -s -X POST http://127.0.0.1:8001/execute_task \
  -H "Content-Type: application/json" \
  -d '{"task_data": "Cost test"}')

cost=$(echo "$response" | jq -r '.total_cost_incurred')
if [ "$cost" != "0.0" ] && [ "$cost" != "0" ] && [ "$cost" != "" ] && [ "$cost" != "null" ]; then
  echo "   ✅ Cost tracking works: \$$cost"
else
  echo "   ❌ BUG: Cost is '$cost' (should be >0)"
  echo "   Response: $response"
fi

# 2. Test Quality PM
echo ""
echo "2. Testing Quality PM cost..."
response=$(curl -s -X POST http://127.0.0.1:8005/execute_task \
  -H "Content-Type: application/json" \
  -d '{"task_data": "Quality test"}')

cost=$(echo "$response" | jq -r '.total_cost_incurred')
if [ "$cost" != "0.0" ] && [ "$cost" != "0" ]; then
  echo "   ✅ Quality PM cost: \$$cost"
else
  echo "   ❌ BUG: Quality PM cost is $cost"
  echo "   Response: $response"
fi

# 3. Check earnings
echo ""
echo "3. Testing earnings tracking..."
earnings=$(curl -s http://127.0.0.1:8000/agents | jq '.[] | select(.name == "ChartBot_Budget_v1") | .total_earned')

if [ "$earnings" != "null" ]; then
  echo "   ✅ Earnings tracked: \$$earnings"
else
  echo "   ❌ BUG: Earnings is null"
fi

# 4. Check decimal precision
echo ""
echo "4. Testing decimal precision..."
python3 -c "from escrow_manager import EscrowManager; escrow = EscrowManager(); print(f'Initial: {escrow.agent_wallets.get(\"PM_Budget\", 0)}')"

echo ""
echo "===================="
echo "CHECKLIST COMPLETE"
