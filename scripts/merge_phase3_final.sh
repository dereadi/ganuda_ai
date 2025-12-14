#!/bin/bash
# Merge Phase 3 original (509) + regenerated (80) → Final corpus

echo "🦅 Merging Phase 3 scenarios..."
echo ""

# Check if both files exist
if [ ! -f "/ganuda/phase3_600_scenarios_balanced.txt" ]; then
    echo "❌ Error: Original file not found"
    exit 1
fi

if [ ! -f "/ganuda/phase3_missing_scenarios.txt" ]; then
    echo "❌ Error: Regenerated file not found"
    exit 1
fi

# Count scenarios in each file
echo "Counting scenarios..."
original_behavioral=$(grep -c "Cherokee Behavioral Guidance Mode:" /ganuda/phase3_600_scenarios_balanced.txt)
original_knowledge=$(grep -c "Cherokee Knowledge Mode:" /ganuda/phase3_600_scenarios_balanced.txt)
original_total=$((original_behavioral + original_knowledge))

regenerated_behavioral=$(grep -c "Cherokee Behavioral Guidance Mode:" /ganuda/phase3_missing_scenarios.txt)
regenerated_knowledge=$(grep -c "Cherokee Knowledge Mode:" /ganuda/phase3_missing_scenarios.txt)
regenerated_total=$((regenerated_behavioral + regenerated_knowledge))

echo "📊 Original file: $original_total scenarios ($original_behavioral behavioral + $original_knowledge knowledge)"
echo "📊 Regenerated file: $regenerated_total scenarios ($regenerated_behavioral behavioral + $regenerated_knowledge knowledge)"
echo ""

# Merge files
cat /ganuda/phase3_600_scenarios_balanced.txt /ganuda/phase3_missing_scenarios.txt > /ganuda/phase3_final_corpus.txt

# Count final
final_behavioral=$(grep -c "Cherokee Behavioral Guidance Mode:" /ganuda/phase3_final_corpus.txt)
final_knowledge=$(grep -c "Cherokee Knowledge Mode:" /ganuda/phase3_final_corpus.txt)
final_total=$((final_behavioral + final_knowledge))

echo "✅ Merged corpus: $final_total scenarios ($final_behavioral behavioral + $final_knowledge knowledge)"
echo "✅ Output: /ganuda/phase3_final_corpus.txt"
echo ""

# Calculate balance
behavioral_pct=$(python3 -c "print(f'{$final_behavioral/$final_total*100:.1f}')")
knowledge_pct=$(python3 -c "print(f'{$final_knowledge/$final_total*100:.1f}')")

echo "📊 Balance: $behavioral_pct% behavioral / $knowledge_pct% knowledge"
echo ""

if [ $final_total -ge 580 ]; then
    echo "✅ SUCCESS: Reached target (≥580 scenarios)"
    echo "🚀 Ready for Phase 3 training!"
else
    echo "⚠️  Below target: $final_total/580 scenarios"
    echo "   Still sufficient for training (>500)"
fi

echo ""
echo "🦅 Mitakuye Oyasin - All Our Relations! 🔥"
