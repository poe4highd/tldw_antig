#!/bin/bash
VIDEOS=(
    "2OdqjtDG0jA|川普拼了！2000亿美元砸房产"
    "UBE4vkQrSb8|川普强买格陵兰真相"
    "0C2lF8pKwlI|高市早苗剛透露了未來 3 年發財的方法"
    "z4pZHh2aut4|【越哥】2026顶级科幻惊悚片《弗兰肯斯坦》"
)

# 修复 OpenMP 多重初始化导致的崩溃
export KMP_DUPLICATE_LIB_OK=TRUE

cd backend
source venv/bin/activate

for entry in "${VIDEOS[@]}"; do
    IFS='|' read -r vid title <<< "$entry"
    echo "=========================================================="
    echo "开始处理视频: $vid - $title"
    echo "=========================================================="
    python tests/reprocess_from_cache.py "$vid" "$title" --detect-hallucination --iterations 2
    echo "完成视频: $vid"
    echo ""
done
