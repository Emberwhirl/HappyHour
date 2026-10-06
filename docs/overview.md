# Overview

This repository is the invitation for the Barozzi & Tardito Lab happy hour.

## Event

- Day: Friday, October 30, 2026
- Time: 5:00 PM to 7:00 PM, Vienna time (`Europe/Vienna`)
- Place: CCR container
- Host: Barozzi & Tardito Lab

October 30, 2026 is a Friday. Europe switches from summer time to standard time on October 25, 2026, so this evening is CET (UTC+1). 5:00 PM in Vienna is 16:00 UTC. 7:00 PM is 18:00 UTC.

## What lives where

| Path | Role |
| --- | --- |
| `index.html` | The invitation page. Host this file with `assets/`. |
| `assets/fonts/` | Self-hosted Cormorant Garamond and Outfit files. |
| `assets/images/` | Header mark, Vienna terrace picture, and favicon. |
| `docs/` | Event facts, the open plan, and implementation notes. |
| `scripts/` | Local preview server and the invitation check. |
| `drafts_helene/` | Legacy mail drafts. Leave this folder where it is. |

`drafts_helene/mail_happy_hour.py` builds a local preview and, only with `--send`, a plain-text note. `drafts_helene/mail_example_html.py` is an older quiz mailer kept as a reference. Neither file moves into `scripts/`.

## Reading order

1. [plan.md](plan.md) for what is settled and what is still open.
2. [implementation.md](implementation.md) for how the page behaves.
3. [sending.md](sending.md) for preview and the send gate.

The root `README.md` is the short version of the same facts.
