#!/bin/bash

# 強制Dockerボリューム削除スクリプト
# Force Docker volume cleanup script

echo "🗑️  Force volume cleanup utility:"
echo ""
echo "📊 Current volume usage:"
docker system df | grep -E "(TYPE|Local Volumes)"
echo ""
echo "🔍 Analyzing volumes..."

# danglingボリュームを取得
unused_volumes=$(docker volume ls -q --filter dangling=true)

# どのコンテナからも参照されていないボリュームを取得
orphaned_volumes=$(docker volume ls -q | while read vol; do
    if [ $(docker ps -a --filter volume=$vol --format '{{.Names}}' | wc -l) -eq 0 ]; then
        echo $vol
    fi
done)

# 削除可能なボリュームをまとめる（重複を除去）
all_removable=$(echo "$unused_volumes $orphaned_volumes" | tr ' ' '\n' | sort -u | tr '\n' ' ')

if [ -n "$all_removable" ]; then
    echo "📋 Volumes that will be removed:"
    for vol in $all_removable; do
        if [ -n "$vol" ]; then
            mountpoint=$(docker volume inspect $vol --format '{{.Mountpoint}}' 2>/dev/null || echo "N/A")
            if [ "$mountpoint" != "N/A" ] && [ -d "$mountpoint" ]; then
                size=$(du -sh "$mountpoint" 2>/dev/null | cut -f1 || echo "N/A")
            else
                size="N/A"
            fi
            printf "  - %-40s (Size: %s)\n" "$vol" "$size"
        fi
    done
    echo ""
    echo "⚠️  WARNING: This will permanently delete these volumes!"
    echo "⚠️  Make sure no important data is stored in these volumes."
    echo ""
    read -p "Continue with volume cleanup? (y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        echo "🗑️  Removing volumes..."
        removed_count=0
        for vol in $all_removable; do
            if [ -n "$vol" ]; then
                if docker volume rm "$vol" 2>/dev/null; then
                    echo "  ✅ Removed: $vol"
                    removed_count=$((removed_count + 1))
                else
                    echo "  ❌ Failed to remove: $vol (may be in use)"
                fi
            fi
        done
        echo ""
        echo "✅ Volume cleanup completed ($removed_count volumes removed)"
        echo ""
        echo "📊 Updated volume usage:"
        docker system df | grep -E "(TYPE|Local Volumes)"
    else
        echo "❌ Volume cleanup cancelled"
    fi
else
    echo "  No removable volumes found"
    echo "✅ All volumes are clean"
fi