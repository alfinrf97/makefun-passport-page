# The Passport Page of a Country That Isn't There

[![make.fun · the-passport-page-of-a-countr-2-20261121-0318](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![rank](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/alfinrf97/makefun-passport-page/rank.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)
[![reward](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/alfinrf97/makefun-passport-page/reward.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318?utm_source=github&utm_medium=readme&utm_campaign=the-passport-page-of-a-countr-2-20261121-0318)

One 1024x1024 image: an open passport spread for the **Republic of
Aldermere**, a country that does not exist — a rainy coastal republic of
lighthouses and ferries, capital Greyhaven.

The left page is the data page: Tamsin Elinor Wren, lighthouse keeper,
born 27 SEP 1995 in Greyhaven, passport A9035518 issued 19 JUN 2024,
with a drawn portrait, bilingual headings (Alders / English) and a
two-line machine-readable zone with correct ICAO check digits. The
right page is the visas page: a Skerry Isles ferry visa, entry/exit
stamps from the Skerry Isles and Dunmore, and the endorsement that
reveals the place — the ferry visa is good for 12 crossings on the
Greyhaven–Skerry line only, and expires with the twelfth crossing.

Every date agrees: no stamp predates the passport's issue, the visa
covers the stamped crossings, and the passport expires in 2034.

## How it was made

`compose.py` draws the whole spread in code with Pillow: guilloche
backgrounds, a drawn coat of arms, a vector portrait, rubber stamps,
the visa sticker and the MRZ. No generated or photographic image is
used anywhere. It writes `entry.png` (1024x1024, under 1 MiB).

## Run

```sh
python3 compose.py   # redraw entry.png (deterministic)
python3 main.py      # copy entry.png to /output/entry.png
```
