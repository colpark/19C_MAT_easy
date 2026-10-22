# vP.1 errors (from VP1-E1)

| label | where | when | what happened | cause | class | fix | check |
|---|---|---|---|---|---|---|---|
| VP1-E1 | the shared git exclude file of the repository's worktrees (`~/Documents/harbor/git/19C_MAT_easy/.git/info/exclude`) | VP1-0 step 3, 2026-10-22 about 13:47Z to 13:49Z | the builder appended `kit/` and `vp1_kit.zip` to the exclude file to keep the working copy's untracked kit out of `git status`; the file is shared by every worktree (v5 to v10), so for that time a `kit/` folder in any worktree would have been ignored | the builder assumed a per-worktree exclude | builder error (operations) | the two lines were removed at once (file back to its previous 7 lines); `vp1/kit` was added with `git add -f` and the commit amended to drop the `__pycache__` files it had picked up | the exclude file holds its 7 original lines; v10 made no commit in that window (its last commit before it was at 13:18Z) |
