#!/bin/bash
# wiki 批量抽取 runner(并发安全版,2026-08-26)
#
# 与旧 /tmp/hrf_runner_v3.sh 的区别:
#   1. 持久化在 .skill/scripts/(不再放 /tmp 被清)
#   2. 每篇抽取完成 → 立即 git commit(untracked 窗口从几十分钟缩到零,reset/stash 伤不到)
#   3. 运行期间在 .git/wiki-locks/ 持有本篇锁(不污染 git status);
#      破坏性 git 操作前应跑 wiki_git_guard.sh,看到锁就必须等待
#
# 用法: wiki_run_extract.sh [--engine pi|codex|zcode] [--provider zhipu|cce-minimax3] [--model M] ck1 ck2 ...
#   引擎(2026-09-04 解耦 + 2026-10-08 zcode headless 解禁,详见 .skill/INVOKE.md):
#     pi    默认;--provider/--model 按 AGENTS.md §0.5(批量默认 cce-minimax3/MiniMax-M3)
#     codex codex exec 子进程;模型默认走 ~/.codex/config.toml,--model 可透传
#           (--provider 对 codex 无效,自动忽略)
#     zcode zcode -p --cwd 子进程(2026-10-08 起 headless 可用);模型=zcode 客户端当前配置
#           (无 CLI --model 透传;首选 GLM-5.3-Flash,2026-09-17 用户指令),--provider/--model 自动忽略
set -u
cd "$(dirname "$0")/../.." || exit 1
ENGINE="pi"
PROVIDER="zhipu"
MODEL=""
# flag 解析(2026-10-08 顺序无关化:旧版单遍 if 对 "--model X --provider Y" 顺序敏感,
# --provider 会被误当 citekey 发动垃圾抽取;任何顺序均可)
while :; do
  case "${1:-}" in
    --engine)   ENGINE="$2";   shift 2 ;;
    --provider) PROVIDER="$2"; shift 2 ;;
    --model)    MODEL="$2";    shift 2 ;;
    *) break ;;
  esac
done
[ $# -ge 1 ] || { echo "用法: $0 [--engine pi|codex|zcode] [--provider P] [--model M] ck1 ck2 ..."; exit 1; }
case "$ENGINE" in
  pi|codex|zcode) ;;
  *) echo "[engine-error] 未知引擎: $ENGINE(可选 pi|codex|zcode)"; exit 1 ;;
esac
if [ "$ENGINE" = "codex" ] && [ "$PROVIDER" != "zhipu" ]; then
  echo "[engine-note] --provider 仅对 pi 引擎有效,codex 引擎已忽略(provider=$PROVIDER)"
fi
if [ "$ENGINE" = "zcode" ]; then
  [ "$PROVIDER" != "zhipu" ] && echo "[engine-note] --provider 仅对 pi 引擎有效,zcode 引擎已忽略(provider=$PROVIDER)"
  [ -n "$MODEL" ] && echo "[engine-note] zcode 无 CLI 模型透传,--model 已忽略(模型=zcode 客户端当前配置;首选 GLM-5.3-Flash)"
fi

MODEL_ARGS=()
[ -n "$MODEL" ] && MODEL_ARGS=(--model "$MODEL")
# codex 用 -m 传模型;默认不传 = 走 ~/.codex/config.toml 的 model
CODEX_MODEL_ARGS=()
[ -n "$MODEL" ] && CODEX_MODEL_ARGS=(-m "$MODEL")
# 超时:codex 高推理档默认放宽到 3600s
case "$ENGINE" in
  pi)    ENGINE_TIMEOUT=1800 ;;
  codex) ENGINE_TIMEOUT=3600 ;;
  zcode) ENGINE_TIMEOUT=3600 ;;
esac

PREFIX=$(cat .skill/INVOKE-PREFIX.txt)
LOCKDIR=.git/wiki-locks
# 目录名沿用 pi_logs_runner(历史兼容:wiki_batch_feed.py / batch.md 等多处引用),对 pi/codex 引擎通用
LOGDIR=/tmp/pi_logs_runner
mkdir -p "$LOCKDIR" "$LOGDIR"

for ck in "$@"; do
  # citekey 守卫(2026-10-08):拦截被误传的 flag/空参(否则会以垃圾 ck 发动真实抽取);
  # raw 缺失仅警告不拦截(保留"引擎登记 NO_KNOWLEDGE/缺陷"的既有流程)
  case "$ck" in
    -*|'') echo "[ck-invalid] '$ck' 疑似误传 flag/空参,跳过"; continue ;;
  esac
  [ -d "raw/$ck" ] || echo "[ck-warn] raw/$ck 不存在(无抽取物料,引擎大概率拒抽/登记缺陷)"
  lock="$LOCKDIR/$ck.$$"
  if ls "$LOCKDIR/$ck."* >/dev/null 2>&1; then
    echo "[skip-locked] $ck (已有会话在抽: $(ls "$LOCKDIR/$ck."* 2>/dev/null | head -1))"
    continue
  fi
  if [ -s "00-pending/$ck/$ck.md" ] && git cat-file -e "HEAD:00-pending/$ck/$ck.md" 2>/dev/null; then
    echo "[skip-done] $ck"
    continue
  fi
  echo "$ck extract-runner pid=$$" > "$lock"

  if [ "$ENGINE" = "codex" ]; then
    echo "[start $(date +%H:%M:%S)] $ck (engine=codex model=${MODEL:-codex-config-default})"
  elif [ "$ENGINE" = "zcode" ]; then
    echo "[start $(date +%H:%M:%S)] $ck (engine=zcode model=zcode-client-config${MODEL:+ (--model 忽略)})"
  else
    echo "[start $(date +%H:%M:%S)] $ck (engine=pi provider=$PROVIDER model=${MODEL:-provider-default})"
  fi
  # 声明自持锁:防引擎把 runner 为本调用挂的锁误读为他站冲突而拒抽(2026-08-27 tang_m/bressler 事故)
  if [ "$ENGINE" = "codex" ]; then
    timeout "$ENGINE_TIMEOUT" codex exec -C "$(pwd)" --sandbox workspace-write "${CODEX_MODEL_ARGS[@]}" \
      "$PREFIX 处理 $ck(注:.git/wiki-locks/$ck.$$ 即本次调用的自持锁,非并发冲突,直接执行抽取)" \
      > "$LOGDIR/$ck.log" 2>&1
  elif [ "$ENGINE" = "zcode" ]; then
    # zcode headless:-p 默认 yolo 模式(可写);cwd 下 AGENTS.md 自动加载 + ~/.zcode/skills/ 微 skill 自动发现
    timeout "$ENGINE_TIMEOUT" zcode -p "$PREFIX 处理 $ck(注:.git/wiki-locks/$ck.$$ 即本次调用的自持锁,非并发冲突,直接执行抽取)" --cwd "$(pwd)" \
      > "$LOGDIR/$ck.log" 2>&1
  else
    timeout "$ENGINE_TIMEOUT" pi -p "$PREFIX 处理 $ck(注:.git/wiki-locks/$ck.$$ 即本次调用的自持锁,非并发冲突,直接执行抽取)" --provider "$PROVIDER" "${MODEL_ARGS[@]}" > "$LOGDIR/$ck.log" 2>&1
  fi

  if [ -s "00-pending/$ck/$ck.md" ]; then
    # 落盘即提交(铁律:绝不让抽取产物停留在 untracked 状态)
    git add "00-pending/$ck" "raw/$ck"
    # 路径限定提交:并发会话留在暂存区的在途工作不被扫进本提交
    case "$ENGINE" in
      pi)    COMMIT_TAG="engine=pi provider=$PROVIDER${MODEL:+ model=$MODEL}" ;;
      codex) COMMIT_TAG="engine=codex${MODEL:+ model=$MODEL}" ;;
      zcode) COMMIT_TAG="engine=zcode(model=client-config)" ;;
    esac
    git commit -q -m "extract(auto): $ck ($COMMIT_TAG, by runner)" -- "00-pending/$ck" "raw/$ck" \
      && echo "[end   $(date +%H:%M:%S)] $ck OK+committed $(git rev-parse --short HEAD)" \
      || echo "[end   $(date +%H:%M:%S)] $ck OK 但 commit 失败,产物在暂存区,请手动 commit"
  else
    echo "[end   $(date +%H:%M:%S)] $ck FAIL(无 $ck.md),日志: $LOGDIR/$ck.log"
  fi
  rm -f "$lock"
done
echo "=== ALL DONE $(date +%H:%M:%S) ==="
