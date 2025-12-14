#!/bin/bash
################################################################################
# Archive Jr. - Dream Cycle File Organization
# Moves older documentation to dated archives to reduce context bloat
# Cherokee Constitutional AI
################################################################################

echo "🦅 Archive Jr. organizing old knowledge..."
echo ""

# Create archive directories
mkdir -p /ganuda/archive/{2025-10-13,2025-10-14,2025-10-15,2025-10-16,2025-10-17,2025-10-18,2025-10-19}

# Archive Oct 13-14 files (older than 6 days)
echo "Archiving Oct 13-14 files..."
find /ganuda -maxdepth 1 -name "*.md" -mtime +5 -exec sh -c '
  for file; do
    date=$(stat -c %y "$file" | cut -d" " -f1)
    dest="/ganuda/archive/$date/$(basename "$file")"
    mkdir -p "/ganuda/archive/$date"
    mv "$file" "$dest"
    echo "  → Moved $(basename "$file") to archive/$date/"
  done
' sh {} +

# Archive Oct 15-17 files (3-5 days old)
echo ""
echo "Archiving Oct 15-17 files..."
find /ganuda -maxdepth 1 -name "*.md" -mtime +2 -mtime -6 -exec sh -c '
  for file; do
    date=$(stat -c %y "$file" | cut -d" " -f1)
    dest="/ganuda/archive/$date/$(basename "$file")"
    mkdir -p "/ganuda/archive/$date"
    mv "$file" "$dest"
    echo "  → Moved $(basename "$file") to archive/$date/"
  done
' sh {} +

echo ""
echo "✅ Archiving complete!"
echo ""
echo "Current /ganuda/*.md files (recent only):"
ls -1 /ganuda/*.md 2>/dev/null | wc -l
echo ""
echo "Archived files by date:"
du -sh /ganuda/archive/* 2>/dev/null

echo ""
echo "🔥 Knowledge preserved, context optimized - Mitakuye Oyasin!"
