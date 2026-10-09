#!/bin/bash
# 破坏性 git 操作前的清场检查(AGENTS.md §8 铁律配套,2026-08-26)
#
# 用法:
#   wiki_git_guard.sh            # 只检查,不安全则 exit 1 并列出风险
#   wiki_git_guard.sh --wip      # 检查 + 把在途工作先替它打成 wip- 前缀 commit,再放行
#
# 适用操作: git reset --hard / git stash(-u) / git clean / cherry-pick 冲突手术 / rebase
# 原则: commit 永远可回退,stash 和 reset 不是。
set -u
cd "$(dirname "$0")/../.." || exit 1

rc=0

# 检查 1: 活跃抽取锁
if ls .git/wiki-locks/*.pid .git/wiki-locks/* 2>/dev/null | grep -q .; then
  echo "✗ 有活跃抽取锁(其他 runner 在写):"
  cat .git/wiki-locks/* 2>/dev/null | sed 's/^/    /'
  rc=1
fi

# 检查 2: 别的会话的 LLM 抽取进程(pi / codex,2026-09-04 引擎解耦)
runners=$(ps aux | grep -E "timeout [0-9]+ (pi -p|codex exec)" | grep -v grep | awk '{print $2, $9}')
if [ -n "$runners" ]; then
  echo "✗ 有 LLM 抽取进程在跑(pi/codex,pid 启动时间):"
  echo "$runners" | sed 's/^/    /'
  echo "  (要嘛等它跑完——runner 现在每篇落盘即 commit;要嘛 kill 后立即做 wip commit)"
  rc=1
fi

# 检查 3: untracked / 未提交内容(不属于本会话的在途工作)
dirty=$(git -c core.quotepath=false status --porcelain | grep -vE '^\?\? \.git' | head -20)
if [ -n "$dirty" ]; then
  echo "⚠ 工作区有未提交内容(可能是其他会话的在途工作,reset --hard / stash -u 会破坏它):"
  echo "$dirty" | sed 's/^/    /'
  if [ "${1:-}" = "--wip" ]; then
    git add -A
    git commit -q -m "wip: 破坏性 git 操作前自动保存工作区在途内容(by wiki_git_guard)" \
      && echo "✓ 已打成 wip commit $(git rev-parse --short HEAD),可安全手术;事后可 revert/reset 此 commit" \
      && rc=0
  else
    echo "  → 加 --wip 参数可先自动保存为 wip commit 再放行"
    rc=1
  fi
fi

[ $rc -eq 0 ] && echo "✓ 清场检查通过,可执行破坏性操作"
exit $rc
