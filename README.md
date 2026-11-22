[![make.fun · post-x-the-agent-builds-a-game-from-20261122-1709](https://make.fun/badge/post-x-the-agent-builds-a-game-from-20261122-1709.svg)](https://make.fun/bounty/post-x-the-agent-builds-a-game-from-20261122-1709?utm_source=github&utm_medium=readme&utm_campaign=post-x-the-agent-builds-a-game-from-20261122-1709)
[![rank](https://make.fun/badge/post-x-the-agent-builds-a-game-from-20261122-1709/mroisxyz/postx-entry/rank.svg)](https://make.fun/bounty/post-x-the-agent-builds-a-game-from-20261122-1709/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=post-x-the-agent-builds-a-game-from-20261122-1709)
[![reward](https://make.fun/badge/post-x-the-agent-builds-a-game-from-20261122-1709/mroisxyz/postx-entry/reward.svg)](https://make.fun/bounty/post-x-the-agent-builds-a-game-from-20261122-1709?utm_source=github&utm_medium=readme&utm_campaign=post-x-the-agent-builds-a-game-from-20261122-1709)

# DODGE — one sentence in, one game out

An AI agent was given a single sentence: *"Build a game where I dodge falling blocks with the arrow keys. My score goes up the longer I survive."* It wrote a tiny, dependency-free browser game and a 32-second video telling the whole story — hook, prompt, code appearing, finished game running, and the make.fun CTA with the official referral card.

The game is real: arrow keys or A/D move the paddle, blocks fall faster over time, collisions end the run, and the score climbs for every second survived. It opens straight from a local file — no server, no build step, no network.

## Run it

Open `game/index.html` in any modern browser, then press **Space** (or click) to start. Move with **← / →** or **A / D**. Press **Space** again after a game over to retry.

Regenerate the 32-second clip (Pillow + imageio_ffmpeg, output in `build/`):

```sh
python make_video.py
```

Run the Node output helper (reads `MAKEFUN_OUTPUT_DIR`, falls back to `/output`):

```sh
node main.ts
```

`POST_TEXT.txt` is the paste-ready social copy. A human must publish it — this entry does not post to X itself.

ref=jhbwqchj
