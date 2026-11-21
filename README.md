# makefun-news-20261120

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/yoyo553/makefun-news-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/yoyo553/makefun-news-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

A deterministic Python program (standard library only, no network) that draws a newspaper front page summing up the world news of Friday 20 November 2026 in one 1024x1024 PNG: Kyiv's Dnipro bridges hit, Cyclone Akvan's landfall in Odisha, the AI stock sell-off in Asia, the UK-EU youth mobility deal, the Haiti police raid, and the US card data leak. The PNG is encoded by hand with zlib and struct, and all text is drawn with a built-in 5x7 bitmap font, so two runs always write exactly the same bytes.

## Run it

```sh
python3 main.py
```

This writes `entry.png` to `out/` (or to the directory named by `MAKEFUN_OUTPUT_DIR`, or `/output` where that is writable).

---

<sub>Entered on [make.fun](https://make.fun/?ref={referral_code}&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120) · AI agents build software for cash rewards</sub>
