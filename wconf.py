#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess

## read config file json
def readWconf(filepath: str) -> dict:
  fh = os.open(filepath, os.O_RDONLY)
  fcontent = os.read(fh, 100000)
  os.close(fh)
  json1 = json.loads(fcontent)
  return json1

## Write config file json
## on default dense, but human readable
## default fmt: indent=2, sort_keys=True
## Python is unable to figure out that OS supports utf-8, so use io module instead
## Could be that the libstd code is broken and there is merely no exception thrown
#  fh = os.open(filepath, os.O_TRUNC|os.O_WRONLY|os.O_CREAT)
#  json1 = json.dumps(conf, indent=fmt['indent'], sort_keys=fmt['sort_keys'], ensure_ascii=fmt['ensure_ascii']).encode('utf-8')
def writeWconf(conf: dict, filepath, **fmt) -> int:
  defaultFmt = { 'indent': 2, 'sort_keys': True, 'ensure_ascii': False }
  fmt = { **defaultFmt, **fmt }
  with open(filepath, 'w+', encoding='utf-8') as fph:
      json.dump(conf, fph, ensure_ascii=fmt['ensure_ascii'], indent=fmt['indent'], sort_keys=fmt['sort_keys'])
  return 0

## Returns 0 for true, 1 for regular false and 2 on failure
## assume structure:
## root_dir
## root_dir/.bare
## root_dir/worktree
def isBareRepo(cwd: str, filepath: str) -> int:
  # GITDIRR=$(git rev-parse --git-dir)
  # GITCOMMDIRR=$(git rev-parse --git-common-dir)
  # return $GITDIR == $GITCOMMDIR
  gitdir = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=filepath, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  if (gitdir.returncode != 0): return 3
  gitcommdir = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=filepath, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  if (gitcommdir.returncode != 0): return 3
  result: bool = gitdir.stdout.decode("utf-8").splitlines()[0] == gitcommdir.stdout.decode("utf-8").splitlines()[0]
  if result == True:
    return 0
  else:
    return 1

## Returns 0 for true, 1 for regular false and 2 on failure
## assume structure:
## root_dir
## root_dir/.bare
## root_dir/worktree
## assume filepath is absolute path
def isGitRootDir(cwd: str, filepath: str) -> bool:
  # WORKTREE=$(git rev-parse --show-toplevel)
  # GITDIR=$(git rev-parse --git-dir)
  # GITCOMMDIR=$(git rev-parse --git-common-dir)
  # ROOT=$(dirname "${GITCOMMDIR}")
  # PWD=$(pwd)
  # return $PWD == $ROOT
  gitcommdir = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=filepath, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  if (gitcommdir.returncode != 0): return 3
  root = os.path.dirname(gitcommdir.stdout.decode("utf-8").splitlines()[0])
  result: bool = filepath == root
  if result == True:
    return 0
  else:
    return 1

## Returns 0 for true, 1 for regular false and 2 on failure
## assume structure:
## root_dir
## root_dir/.bare
## root_dir/worktree
def isGitWorktreeDir(cwd: str, filepath: str) -> bool:
  worktree = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=filepath, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  if (worktree.returncode != 0): return 3
  # WORKTREE=$(git rev-parse --show-toplevel)
  # return $CWD == $WORKTREE
  result: bool = filepath == worktree.stdout.decode("utf-8").splitlines()[0]
  if result == True:
    return 0
  else:
    return 1

def chdir(path: str) -> int:
  try:
    os.chdir(path)
  except OSError:
    sys.stderr.write("os.chdir(", path, ") failed")
    return 1
  return 0

def mkdir(path: str) -> int:
  try:
      os.mkdir(path)
  except OSError:
    sys.stderr.write("os.mkdir(", path, ") failed")
    return 1
  return 0

## Inserts or updates field with "paths" containing tuples with
## 1. path to root bare dir, 2. path to worktree
## assume: 1. cwd is root dir of git, 2. config was created from cwd
## Note: 1. can be checked with isGitWorktreeDir() and isGitRootDir()
def writePaths(cwd: str, wconf: dict) -> dict:
  pathlist = []
  for gititem in wconf["git"]:
    # print(gititem["server"])
    # print(gititem["name"])
    # print(gititem["git"])
    # print(gititem["dir"])
    # print(gititem["branch"])
    gituri: str = "git@" + gititem["server"] + ":" + gititem["git"] + ".git"
    abspath_rootbare = os.path.join(cwd, gititem["dir"])
    abspath_branch = os.path.join(cwd, gititem["dir"], gititem["branch"])
    # git requires upstream branch = downstream branch for pushing
    upstream_branch = os.path.join(gititem["name"], gititem["branch"])

    pathlist.append({"gituri":gituri,"bare":abspath_rootbare,"branch":abspath_branch,"upbranch":upstream_branch})
  wconf["paths"] = pathlist
  return wconf

## assume: 1. cwd is root dir of git, 2. config was created from cwd
## Note: 1. can be checked with isGitWorktreeDir() and isGitRootDir()
def setupBareOrWorktrees(wconf: dict) -> int:
  loc_cwd = os.getcwd()
  assert(len(wconf["paths"]) == 2)
  for pi in range(0, len(wconf["paths"]), 1):
    path = wconf["paths"][pi]
    git = wconf["git"][pi]
    if (os.path.isdir(path["bare"]) == False or os.path.isdir(path["bare"] + "/.bare") == False):
      print("bare not existing")
      if os.path.isdir(path["bare"]) == False:
        if mkdir(path["bare"]) == 1:
          return 1
      if chdir(path["bare"]) == 1:
        return 1
      cmdexec = subprocess.run(["git", "clone", "--bare", path["gituri"], ".bare"])
      if (cmdexec.returncode != 0): return 3
      try:
        with open(".git", "w") as gitlinkfile:
          gitlinkfile.write("gitdir: ./.bare")
      except OSError:
        sys.stderr.write("could not write gitdir")
        return 1
      cmdexec = subprocess.run(["git", "remote", "rm", "origin"])
      if (cmdexec.returncode != 0): return 3
      cmdexec = subprocess.run(["git", "remote", "add", git["name"], path["gituri"]])
      if (cmdexec.returncode != 0): return 3
      cmdexec = subprocess.run(["git", "fetch", "--all"])
      if (cmdexec.returncode != 0): return 3
      cmdexec = subprocess.run(["git", "worktree", "add", git["branch"]])
      if (cmdexec.returncode != 0): return 3
      if chdir(path["branch"]) == 1:
        return 1
      cmdexec = subprocess.run(["git", "branch", "--set-upstream-to="+git["name"]+"/"+git["branch"], git["branch"]])
      if (cmdexec.returncode != 0): return 3
    else:
      if (os.path.isdir(path["branch"]) == False):
        if chdir(path["bare"]) == 1:
          return 1
        cmdexec = subprocess.run(["git", "fetch", "--all"])
        if (cmdexec.returncode != 0): return 3
        cmdexec = subprocess.run(["git", "worktree", "add", git["branch"]])
        if (cmdexec.returncode != 0): return 3
      if chdir(path["branch"]) == 1:
        return 1
      cmdexec = subprocess.run(["git", "branch", "--set-upstream-to="+git["name"]+"/"+git["branch"], git["branch"]])
      if (cmdexec.returncode != 0): return 3
    if chdir(loc_cwd) == 1:
      return 1
  return 0

## path is one of {bare, branch, gituri, upbranch}
## This is a convenience workaround of python not supporting dict field access
## via . like https://github.com/fubark/cyber
def getPath(wconf: dict, index, path: str) -> str:
  return wconf["paths"][index][path]


def _runUnitTest1():
  cwd = os.getcwd()
  wconf = readWconf("wconf_def.json")
  res = writeWconf(wconf, "wconf_def_copy.json")
  wconf = writePaths(cwd, wconf)
  res = writeWconf(wconf, "wconf_def_ext.json")
  assert res == 0

def _runUnitTest2():
  cwd = os.getcwd()
  wconf = readWconf("wconf_def.json")
  wconf = writePaths(cwd, wconf)
  print(wconf)
  assert(len(getPath(wconf, 0, "bare")) > 0)
  assert(len(getPath(wconf, 0, "branch")) > 0)
  assert(getPath(wconf, 0, "gituri") == "git@github.com:matu3ba/testing.git")
  assert(getPath(wconf, 0, "upbranch") == "downstream/master")
  assert(len(wconf["paths"][0]["bare"]) > 0)
  assert(len(wconf["paths"][0]["branch"]) > 0)
  assert(wconf["paths"][0]["gituri"] == "git@github.com:matu3ba/testing.git")
  assert(wconf["paths"][0]["upbranch"] == "downstream/master")

  assert(len(getPath(wconf, 1, "bare")) > 0)
  assert(len(getPath(wconf, 1, "branch")) > 0)
  print(getPath(wconf, 1, "gituri"))
  assert(getPath(wconf, 1, "gituri") == "git@github.com:matu3ba/testing.git")
  assert(getPath(wconf, 1, "upbranch") == "downstream/master")
  assert(len(wconf["paths"][1]["bare"]) > 0)
  assert(len(wconf["paths"][1]["branch"]) > 0)
  assert(wconf["paths"][1]["gituri"] == "git@github.com:matu3ba/testing.git")
  assert(wconf["paths"][1]["upbranch"] == "downstream/master")
  assert(len(wconf["paths"]) == 2)

def _runUnitTest3():
  cwd = os.getcwd()
  wconf = readWconf("wconf_def.json")
  wconf = writePaths(cwd, wconf)
  # remove everything
  import shutil
  shutil.rmtree("testing")
  res = setupBareOrWorktrees(wconf)
  assert res == 0
  # setup again to test other code path
  res = setupBareOrWorktrees(wconf)
  assert res == 0

def _runUnitTest4():
  # test requires bare repo to be setup before
  cwd = os.getcwd()
  wconf = readWconf("wconf_def_ext.json")
  print(getPath(wconf, 0, "bare"))
  print(getPath(wconf, 0, "branch"))
  assert(isBareRepo(cwd, getPath(wconf, 0, "bare")) == 0)
  assert(isGitRootDir(cwd, getPath(wconf, 0, "bare")) == 0)
  assert(isGitWorktreeDir(cwd, getPath(wconf, 0, "branch")) == 0)

  print(getPath(wconf, 1, "bare"))
  print(getPath(wconf, 1, "branch"))

_runUnitTest1()
_runUnitTest2()
_runUnitTest3()
_runUnitTest4()
