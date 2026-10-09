#!/usr/bin/env bash
# wiki_dedup_papers.sh · 00-pending + raw 目录去重工具
#
# 用途:zotero 同步同一论文产生多个不同大小写/后缀的目录时,合并到 paperinfo 节点名(canonical)
#
# 设计原则(plan §1.2 铁律 + 用户原话):
#   1. paperinfo 节点名是 canonical citekey (BBT citekey)
#   2. 同一论文只 1 个 00-pending 目录 + 1 个 raw 目录
#   3. 增量更新:只补缺失内容, 不重建已有
#   4. 不创建多个 paper.md / 多个空目录
#
# 用法:
#   ./wiki_dedup_papers.sh --scan                    # 扫描重复(不修改)
#   ./wiki_dedup_papers.sh --scan --execute          # 扫描 + 合并 + 删
#   ./wiki_dedup_papers.sh --canonical <ck> <dir1> <dir2>   # 手动指定 canonical
#
# 算法:
#   1. 列出 00-pending/ 全部目录
#   2. 对每个目录,提取 citekey 前缀(<author>_<year>)
#   3. 查找 paperinfo/<BBT-citekey>.md 找 canonical
#   4. 用 paperinfo 节点名做 canonical,合并 重复
#   5. 合并 paper.md(选最大)+ claims/ + evidence/(rsync)
#   6. 合并 raw/(rsync full.md + images/)
#   7. 删非 canonical 目录

set -euo pipefail

WIKI_ROOT="${WIKI_ROOT:-$(pwd)}"
PENDING_DIR="$WIKI_ROOT/00-pending"
RAW_DIR="$WIKI_ROOT/raw"
PAPERINFO_DIR="$WIKI_ROOT/paperinfo"
LOG="/tmp/wiki_dedup_papers_$(date +%Y%m%d_%H%M%S).log"

SCAN_ONLY=true
MANUAL_CANONICAL=""

usage() {
    cat << 'EOF'
用法: ./wiki_dedup_papers.sh [选项]

选项:
    --scan                  扫描重复目录(默认, 只报告不修改)
    --execute               扫描 + 合并 + 删除重复
    --canonical <ck> <dirs...>   手动指定 canonical + 多个重复目录合并
    --wiki-root <dir>       wiki 根目录(默认 $PWD)
    --dry-run               模拟执行, 不实际修改
    --help                  显示帮助

示例:
    # 只看哪些重复
    ./wiki_dedup_papers.sh --scan

    # 自动合并所有重复
    ./wiki_dedup_papers.sh --scan --execute

    # 手动指定 schirner 3 个目录合并到 schirner_2022_neuroimage
    ./wiki_dedup_papers.sh --canonical schirner_2022_neuroimage \
        schirner_2022_neuroimage_Brain_simulation_as_a_cloud_service_The_virtual_brain_on_EBRAINS \
        schirner_2022_neuroimage_Brain_simulation_as_a_cloud_service_The_Virtual_Brain_on_EBRAINS
EOF
}

# 解析参数
TARGET_DIRS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --scan) SCAN_ONLY=true; shift;;
        --execute) SCAN_ONLY=false; shift;;
        --canonical) MANUAL_CANONICAL="$2"; shift 2; while [[ $# -gt 0 && ! "$1" =~ ^-- ]]; do TARGET_DIRS+=("$1"); shift; done;;
        --wiki-root) WIKI_ROOT="$2"; shift 2;;
        --dry-run) DRY_RUN="echo [DRY-RUN]"; shift;;
        --help|-h) usage; exit 0;;
        *) echo "未知选项: $1"; usage; exit 1;;
    esac
done

echo "[$(date +%H:%M:%S)] wiki_dedup_papers.sh 开始" | tee -a "$LOG"
echo "  WIKI_ROOT: $WIKI_ROOT" | tee -a "$LOG"
echo "  SCAN_ONLY: $SCAN_ONLY" | tee -a "$LOG"
echo "  MANUAL_CANONICAL: ${MANUAL_CANONICAL:-<auto>}" | tee -a "$LOG"

# 提取目录的 citekey 前缀(author + year)
extract_citekey_prefix() {
    local dir="$1"
    # 提取目录名(去掉路径)
    local name=$(basename "$dir")
    # 找第一个 4 位数字(year)
    if [[ "$name" =~ ^([^_]+_[^_]+_[0-9]{4}) ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        echo "$name" | awk -F'_' '{print $1 "_" $2 "_" $3}'
    fi
}

# 找匹配的 paperinfo 节点
find_paperinfo_canonical() {
    local prefix="$1"
    local author=$(echo "$prefix" | cut -d_ -f1 | tr '[:upper:]' '[:lower:]')
    local year=$(echo "$prefix" | cut -d_ -f3)
    # 在 paperinfo 找匹配的(author + year)
    for f in "$PAPERINFO_DIR"/*.md; do
        [ -f "$f" ] || continue
        local base=$(basename "$f" .md)
        local a=$(echo "$base" | cut -d_ -f1 | tr '[:upper:]' '[:lower:]')
        local y=$(echo "$base" | grep -oE "[0-9]{4}" | head -1)
        if [[ "${a,,}" == "${author,,}" && "$y" == "$year" ]]; then
            echo "$base"
            return
        fi
    done
    echo ""
}

# 合并一个目录到 canonical
merge_dir_to_canonical() {
    local src="$1"
    local canonical="$2"
    local base=$(basename "$src")
    local canonical_full="$PENDING_DIR/$canonical"
    
    # 如果 src 就是 canonical,跳过
    if [[ "$base" == "$canonical" ]]; then
        echo "  ⏭ $base 已经是 canonical, 跳过" | tee -a "$LOG"
        return
    fi
    
    # 合并 paper.md(选最大的)
    if [ -f "$src/$canonical.md" ] && [ ! -f "$canonical_full/$canonical.md" ]; then
        echo "  → 复制 paper.md(从 $base)" | tee -a "$LOG"
        ${DRY_RUN:-:} cp "$src/$canonical.md" "$canonical_full/$canonical.md"
    elif [ -f "$src/$base.md" ]; then
        # 选最大的
        local src_size=$(stat -c%s "$src/$base.md" 2>/dev/null || echo 0)
        local dst_size=$(stat -c%s "$canonical_full/$canonical.md" 2>/dev/null || echo 0)
        if [[ $src_size -gt $dst_size ]]; then
            echo "  → 复制 paper.md(从 $base, ${src_size}B > ${dst_size}B)" | tee -a "$LOG"
            ${DRY_RUN:-:} cp "$src/$base.md" "$canonical_full/$canonical.md"
        fi
    fi
    
    # 合并 claims/
    if [ -d "$src/claims" ]; then
        echo "  → 合并 claims/($(ls "$src/claims" 2>/dev/null | wc -l) 文件)" | tee -a "$LOG"
        mkdir -p "$canonical_full/claims"
        ${DRY_RUN:-:} rsync -a --ignore-existing "$src/claims/" "$canonical_full/claims/" 2>&1 | head -3
    fi
    
    # 合并 evidence/
    if [ -d "$src/evidence" ]; then
        echo "  → 合并 evidence/($(ls "$src/evidence" 2>/dev/null | wc -l) 文件)" | tee -a "$LOG"
        mkdir -p "$canonical_full/evidence"
        ${DRY_RUN:-:} rsync -a --ignore-existing "$src/evidence/" "$canonical_full/evidence/" 2>&1 | head -3
    fi
    
    # 合并 raw/(rsync full.md + images)
    if [ -d "$RAW_DIR/$base" ]; then
        echo "  → 合并 raw/($base → $canonical)" | tee -a "$LOG"
        mkdir -p "$RAW_DIR/$canonical"
        ${DRY_RUN:-:} rsync -a "$RAW_DIR/$base/" "$RAW_DIR/$canonical/" 2>&1 | head -3
    fi
    
    # 删除非 canonical 目录
    echo "  ✗ 删除 $base" | tee -a "$LOG"
    ${DRY_RUN:-:} rm -rf "$PENDING_DIR/$base"
    if [ -d "$RAW_DIR/$base" ]; then
        ${DRY_RUN:-:} rm -rf "$RAW_DIR/$base"
    fi
}

# 扫描 00-pending/ + raw/ 找重复
scan_duplicates() {
    echo "" | tee -a "$LOG"
    echo "[扫描] 00-pending/ 全部目录 + paperinfo/ 匹配" | tee -a "$LOG"
    
    declare -A groups
    for d in "$PENDING_DIR"/*/; do
        [ -d "$d" ] || continue
        local name=$(basename "$d")
        local prefix=$(extract_citekey_prefix "$name")
        local canonical=$(find_paperinfo_canonical "$prefix")
        if [ -z "$canonical" ]; then
            echo "  ⚠ $name (无 paperinfo canonical)" | tee -a "$LOG"
        else
            groups["$canonical"]+="$name "
        fi
    done
    
    echo "" | tee -a "$LOG"
    echo "[结果] 重复组:" | tee -a "$LOG"
    for ck in "${!groups[@]}"; do
        local dirs="${groups[$ck]}"
        local count=$(echo $dirs | wc -w)
        if [[ $count -gt 1 ]]; then
            echo "  🔁 canonical=$ck | $count 个目录:" | tee -a "$LOG"
            for d in $dirs; do
                echo "      - $d" | tee -a "$LOG"
            done
        fi
    done
}

# 自动合并
auto_merge() {
    declare -A groups
    for d in "$PENDING_DIR"/*/; do
        [ -d "$d" ] || continue
        local name=$(basename "$d")
        local prefix=$(extract_citekey_prefix "$name")
        local canonical=$(find_paperinfo_canonical "$prefix")
        if [ -n "$canonical" ]; then
            groups["$canonical"]+="$name "
        fi
    done
    
    local merged_count=0
    for ck in "${!groups[@]}"; do
        local dirs="${groups[$ck]}"
        local count=$(echo $dirs | wc -w)
        if [[ $count -gt 1 ]]; then
            echo "" | tee -a "$LOG"
            echo "[合并] canonical=$ck | $count 个目录:" | tee -a "$LOG"
            for d in $dirs; do
                if [[ "$d" != "$ck" ]]; then
                    merge_dir_to_canonical "$PENDING_DIR/$d" "$ck"
                fi
            done
            merged_count=$((merged_count + count - 1))
        fi
    done
    
    echo "" | tee -a "$LOG"
    echo "[完成] 合并 $merged_count 个重复目录" | tee -a "$LOG"
}

# 手动指定 canonical 合并
manual_merge() {
    local canonical="$MANUAL_CANONICAL"
    echo "" | tee -a "$LOG"
    echo "[手动合并] canonical=$canonical | ${#TARGET_DIRS[@]} 个目录" | tee -a "$LOG"
    
    mkdir -p "$PENDING_DIR/$canonical"
    for d in "${TARGET_DIRS[@]}"; do
        merge_dir_to_canonical "$PENDING_DIR/$d" "$canonical"
    done
}

# 主流程
if [ -n "$MANUAL_CANONICAL" ]; then
    manual_merge
elif [ "$SCAN_ONLY" = true ]; then
    scan_duplicates
else
    scan_duplicates
    echo "" | tee -a "$LOG"
    read -p "执行合并? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        auto_merge
    else
        echo "取消"
    fi
fi

echo "" | tee -a "$LOG"
echo "[$(date +%H:%M:%S)] 完成 — 日志 $LOG" | tee -a "$LOG