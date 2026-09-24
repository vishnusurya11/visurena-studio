#!/usr/bin/env sh
# ep11 grids: faces one to a 1x1 (a 1x1 holds its framing and count), the
# faceless wides and inserts grouped (ep10's split). Runs from the worktree.
B=20260827135508_the-war-of-the-worlds
g() { uv run python scripts/episode/grids.py "$B" 11 "$@" 2>&1 | tail -1; }
g study 2 1 room --shots=0,7
g study 1 1 doorway --shots=1
g study 1 1 chair --shots=6
g valley 3 1 valley --shots=2,3,5
g valley 2 1 details --shots=4,8
g garden 1 1 fence --shots=9
g garden 1 1 lean --shots=10
g garden 1 1 under --shots=11
g garden 1 1 ask --shots=12
g garden 1 1 answer --shots=13
g garden 1 1 beckon --shots=14
g dining 1 1 pour --shots=15
g dining 1 1 weep --shots=16
g dining 1 1 wiped --shots=17
g dining 1 1 listen --shots=18
g dining 1 1 bread --shots=19
g dawn 1 1 sill --shots=20
g dawn 1 1 parade --shots=21
g dawn 1 1 ashes --shots=22
