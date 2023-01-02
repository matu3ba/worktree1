## worktree1 - Git worktree 1 structure.

Idea: Root is configuration and test runner, children git worktrees. 1-level nested git repo.

```
Root as configuration + build and test runner
               │
      ┌─────┬──┴───┬───────┐   ....
      ▼     ▼      ▼       ▼
     ch1   ch2    ch3     ch4     children: git bare repos (+ worktree/helper scripts)
      │
    ┌─┴─┐  ....
    ▼   ▼
   wt1 wt2                       worktrees: branches
```

Advantage: Fast swapping of branches, simpler for (decentralized) experimentation
on multiple parts. Biggest advantage from my point of view: Helper scripts for
a git repo have a home.

Disadvantage: Git worktree shennanigans, less tight coupling than monorepo.
More effort to setup and maintain. Paths become longer, so one should have the
root in $HOME for faster access. Otherwise, the same properties as a monorepo apply.

#### Usage

- Copy-paste the code and use it.
- Adjust as you want.

#### Goals

- Minimal example to allow fast hacking worktrees with the various git features.
- Non-goals: More than worktree setup and lookup of current config paths.

#### Overview

- wconf.py | wconf.zig
- only git uris, ie `git@github.com:neovim/neovim.git`, but simple to extend

#### Setup of Worktrees and Git path access commands

Manual setup (better use setupBareOrWorktree):
```sh
mkdir -p ROOTDIR_for_worktrees
cd ROOTDIR_for_worktrees
git clone --bare gitrepo .bare
echo "gitdir: ./.bare" > .git
git worktree add master
```

Git has the following cli commands for worktree detection:
```sh
WORKTREE=$(git rev-parse --show-toplevel) # alternative: ROOT/LOCAL_BRANCH
GITDIR=$(git rev-parse --git-dir)
GITCOMMDIR=$(git rev-parse --git-common-dir)
ROOT=$(dirname "${GITCOMMDIR}")
LOCAL_BRANCH=$(git branch --show-current)
PWD=$(pwd)
```
