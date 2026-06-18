#!/bin/bash
# 医学文献综述报告格式验证脚本
# 用法: bash validate.sh <综述报告.md>

set -e

REPORT="$1"

if [ -z "$REPORT" ]; then
    echo "用法: bash validate.sh <综述报告.md>"
    exit 1
fi

if [ ! -f "$REPORT" ]; then
    echo "错误: 文件 '$REPORT' 不存在"
    exit 1
fi

ERRORS=0
WARNINGS=0

echo "=========================================="
echo "  医学文献综述报告格式验证"
echo "  目标文件: $REPORT"
echo "=========================================="

# 1. 必要章节检查
echo ""
echo "[1/10] 必要章节检查..."
REQUIRED_SECTIONS=(
    "摘要"
    "背景与目的"
    "方法"
    "检索策略"
    "纳入与排除标准"
    "结果"
    "讨论"
    "结论"
    "参考文献"
)

for section in "${REQUIRED_SECTIONS[@]}"; do
    if grep -q "$section" "$REPORT"; then
        echo "  ✅ $section"
    else
        echo "  ❌ 缺少章节: $section"
        ERRORS=$((ERRORS + 1))
    fi
done

# 2. PICO框架检查
echo ""
echo "[2/10] PICO框架检查..."
PICO_ITEMS=("Population\|目标人群" "Intervention\|干预" "Comparison\|对照" "Outcome\|结局")
for item in "${PICO_ITEMS[@]}"; do
    if grep -q "$item" "$REPORT"; then
        echo "  ✅ $item"
    else
        echo "  ⚠️  未明确找到: $item"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# 3. PRISMA流程图检查
echo ""
echo "[3/10] PRISMA流程图检查..."
if grep -q "PRISMA\|筛选流程\|流程图" "$REPORT"; then
    echo "  ✅ 包含PRISMA/筛选流程描述"
else
    echo "  ⚠️  未找到PRISMA流程图相关描述"
    WARNINGS=$((WARNINGS + 1))
fi

# 4. 证据等级标注检查
echo ""
echo "[4/10] GRADE证据等级标注检查..."
GRADE_COUNT=$(grep -c "GRADE\|证据等级\|高⭫\|中⭬\|低⭭\|极低⭯\|证据质量" "$REPORT" || true)
if [ "$GRADE_COUNT" -ge 1 ]; then
    echo "  ✅ 包含GRADE证据等级标注 ($GRADE_COUNT 处)"
else
    echo "  ❌ 未找到GRADE证据等级标注"
    ERRORS=$((ERRORS + 1))
fi

# 5. 纳入研究特征表检查
echo ""
echo "[5/10] 纳入研究特征表检查..."
if grep -q "研究.*设计.*样本量\|Author.*Year.*RCT\|研究特征" "$REPORT"; then
    echo "  ✅ 包含纳入研究特征表"
else
    echo "  ⚠️  未找到标准格式的纳入研究特征表"
    WARNINGS=$((WARNINGS + 1))
fi

# 6. 检索日期/数据库检查
echo ""
echo "[6/10] 检索信息完整性检查..."
if grep -q "检索日期\|检索时间\|检索截止" "$REPORT"; then
    echo "  ✅ 包含检索日期"
else
    echo "  ❌ 缺少检索日期"
    ERRORS=$((ERRORS + 1))
fi

DB_COUNT=$(grep -c "PubMed\|MEDLINE\|Embase\|Cochrane\|Web of Science\|CNKI\|万方" "$REPORT" || true)
if [ "$DB_COUNT" -ge 1 ]; then
    echo "  ✅ 明确提及检索数据库 ($DB_COUNT 个)"
else
    echo "  ❌ 未明确提及检索数据库"
    ERRORS=$((ERRORS + 1))
fi

# 7. 偏倚风险评估检查
echo ""
echo "[7/10] 偏倚风险评估检查..."
if grep -q "偏倚\|RoB\|NOS\|QUADAS\|AMSTAR\|质量评价" "$REPORT"; then
    echo "  ✅ 包含偏倚风险/质量评价"
else
    echo "  ❌ 缺少偏倚风险评估"
    ERRORS=$((ERRORS + 1))
fi

# 8. 效应量报告检查
echo ""
echo "[8/10] 效应量报告检查..."
if grep -q "RR\|OR\|HR\|MD\|SMD\|95%CI\|置信区间\|效应量" "$REPORT"; then
    echo "  ✅ 包含效应量/置信区间报告"
else
    echo "  ⚠️  未找到效应量/置信区间，可能为定性综述"
    WARNINGS=$((WARNINGS + 1))
fi

# 9. 局限性讨论检查
echo ""
echo "[9/10] 局限性讨论检查..."
if grep -q "局限\|不足\|限制\|偏倚风险" "$REPORT"; then
    echo "  ✅ 包含局限性讨论"
else
    echo "  ❌ 缺少局限性讨论"
    ERRORS=$((ERRORS + 1))
fi

# 10. 利益冲突声明检查
echo ""
echo "[10/10] 利益冲突/资金来源声明检查..."
if grep -q "利益冲突\|资金.*来源\|资助\|conflict" "$REPORT"; then
    echo "  ✅ 包含利益冲突/资金来源声明"
else
    echo "  ⚠️  未找到利益冲突声明"
    WARNINGS=$((WARNINGS + 1))
fi

# 汇总
echo ""
echo "=========================================="
echo "  验证结果汇总"
echo "=========================================="
echo "  错误: $ERRORS"
echo "  警告: $WARNINGS"

if [ "$ERRORS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo "  状态: ✅ 通过"
    exit 0
elif [ "$ERRORS" -eq 0 ]; then
    echo "  状态: ⚠️  通过（有 $WARNINGS 个建议改进项）"
    exit 0
else
    echo "  状态: ❌ 不通过（$ERRORS 个错误需修复）"
    exit 1
fi
