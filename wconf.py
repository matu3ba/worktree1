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

## write config file json
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

def isGitRootDir(filepath: str) -> bool:
  pass

def isGitBareRootDir(filepath: str) -> bool:
  pass

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

## inserts or updates field with "paths" containing tuples with
## 1. path to root bare dir, 2. path to worktree
## assume: 1. cwd is root dir of git, 2. config was created from cwd
## Note: 1. can be checked with TODO
def writePaths(cwd: str, wconf: dict) -> dict:
  pathlist = []
  for gititem in wconf["git"]:
    print(gititem["server"])
    print(gititem["name"])
    print(gititem["git"])
    print(gititem["dir"])
    print(gititem["branch"])
    gituri = "git@" + gititem["server"] + gititem["git"]
    abspath_rootbare = os.path.join(cwd, gititem["dir"])
    abspath_branch = os.path.join(cwd, gititem["dir"], gititem["branch"])
    # git requires upstream branch = downstream branch for pushing
    upstream_branch = os.path.join(gititem["name"], gititem["branch"])

    pathlist.append({"gituri":gituri,"bare":abspath_rootbare,"branch":abspath_branch,"upbranch":upstream_branch})
  wconf["paths"] = pathlist
  return wconf

## assume: 1. cwd is root dir of git, 2. config was created from cwd
## Note: 1. can be checked with TODO
def setupBareOrWorktree(wconf: dict) -> int:
  loc_cwd = os.getcwd()
  for pi in range(0,len(wconf["paths"])):
    path = wconf["paths"][pi]
    git = wconf["git"][pi]
    if (os.path.isdir(path["bare"]) == False or os.path.isdir(path["bare"] + "/.bare") == False):
      if os.path.isdir(path["bare"]) == False:
        if mkdir(path["bare"]) == 1:
          return 1
      if chdir(path["bare"]) == 1:
        return 1
      subprocess.run(["git", "clone", "--bare", path["gituri"], ".bare"], check=True)
      try:
        with open(".git", "w") as gitlinkfile:
          gitlinkfile.write("gitdir: ./.bare")
      except OSError:
        sys.stderr.write("could not write gitdir")
        return 1
      subprocess.run(["git", "remote", "rm", "origin"], check=True)
      subprocess.run(["git", "remote", "add", git["name"], path["gituri"]], check=True)
      subprocess.run(["git", "fetch", "--all"], check=True)
      subprocess.run(["git", "worktree", "add", git["branch"]], check=True)
      if chdir(path["branch"]) == 1:
        return 1
      subprocess.run(["git", "branch", "--set-upstream-to="+git["name"]+"/"+git["branch"], git["branch"]], check=True)
    else:
      if (os.path.isdir(path["branch"]) == False):
        if chdir(path["bare"]) == 1:
          return 1
        subprocess.run(["git", "fetch", "--all"], check=True)
        subprocess.run(["git", "worktree", "add", git["branch"]], check=True)
      if chdir(path["branch"]) == 1:
        return 1
      subprocess.run(["git", "branch", "--set-upstream-to="+git["name"]+"/"+git["branch"], git["branch"]], check=True)
    if chdir(loc_cwd) == 1:
      return 1
    return 0


## path is one of {bare, branch, gituri, upbranch}
def getPath(wconf: dict, index, path: str) -> str:
  return wconf["paths"][0][path]

def runUnitTest1():
  cwd = os.getcwd()
  wconf = readWconf("wconf_def.json")
  wconf = writePaths(cwd, wconf)
  res = setupBareOrWorktree(wconf)
  assert res == 0

def runUnitTest2():
  cwd = os.getcwd()
  wconf = readWconf("wconf_def.json")
  res = writeWconf(wconf, "wconf_def_copy.json")
  wconf = writePaths(cwd, wconf)
  res = writeWconf(wconf, "wconf_def_ext.json")
  assert res == 0

def runUnitTest3():
  cwd = os.getcwd()
  wconf = readWconf("wconf_def.json")
  wconf = writePaths(cwd, wconf)
  print(wconf)
  assert(len(getPath(wconf, 0, "bare")) > 0)
  assert(len(getPath(wconf, 0, "branch")) > 0)
  assert(getPath(wconf,0,"gituri") == "git@github.com:matu3ba/testing.git")
  assert(getPath(wconf,0,"upbranch") == "downstream/master")
  assert(len(wconf["paths"][0]["bare"]) > 0)
  assert(len(wconf["paths"][0]["branch"]) > 0)
  assert(wconf["paths"][0]["gituri"] == "git@github.com:matu3ba/testing.git")
  assert(wconf["paths"][0]["upbranch"] == "downstream/master")

runUnitTest1()
runUnitTest2()
runUnitTest3()
