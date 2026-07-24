# PoroPilot — Design Brief

A self-contained brief for designing PoroPilot's UI. Paste this into a design tool
(e.g. Claude.ai Artifacts) to generate or iterate on the interface. It describes
what the app is, who it's for, every screen/state, the data available, the current
look, and the design goals.

---

## What it is

**PoroPilot** is a companion web app for the game **League of Legends**. A player
enters their region and Riot ID and gets their profile, ranked standing, champion
pool with recent win-rates, and an AI **draft assistant** that recommends champion
picks. It's a single-page web app (works on desktop and mobile browsers).

## Who it's for

League of Legends players — mostly younger, game-literate users who are used to
polished gaming tools (op.gg, mobalytics, loldle). They expect champion icons, fast
search, and a snappy, confident feel — not a corporate dashboard.

## Tone / vibe

Clean and modern, lightly game-flavoured, icon-rich. Think "a good esports stats
tool": legible, fast, a bit of personality (the mascot is a **poro** 🐾), but not
cluttered or gamer-cliché (avoid neon-on-black, dragons, heavy skeuomorphism).
Accessibility matters — good contrast, keyboard-friendly.

---

## Screens, components and states

It's currently one page with these sections top-to-bottom.

### 1. Header
- App name **"PoroPilot"** + poro emoji, and a one-line tagline:
  *"Your League of Legends companion — profile, champ pool & AI draft help."*

### 2. Summoner search
- A **region dropdown** (EUW, NA, KR, …) + a **text input** for the Riot ID (`name#tag`).
- States: idle, loading, error (e.g. "Failed to fetch" / "Enter your Riot ID as name#tag").

### 3. Profile (after a successful lookup)
- **Header:** Riot ID (e.g. `PilotSheep#EUW`), region, summoner level.
- **Ranked:** per queue — tier, rank, LP, W/L (e.g. "Solo/Duo: GOLD II — 6 LP (73W/60L)").
  Empty state: "Unranked".
- **Top champions (mastery):** list of champions with **icon**, name, mastery points, mastery level.
- **Recent form:** the player's strongest recent champions from match history — **icon**,
  name, win-rate %, games played, and a "form" score (0–1).

### 4. AI draft assistant (only shown when AI is enabled)
- A **role selector** (TOP/JUNGLE/MID/BOT/SUPPORT).
- Four **champion pickers**: "Your champion pool", "Allied picks", "Enemy bans",
  "Enemy picks". Each is a **search-as-you-type** control: type → a dropdown of
  matching champions with **icons** → pick one → it becomes a removable **chip**
  (with icon). Keyboard: ↑/↓ to highlight, Enter to select.
- A **"Suggest a pick"** button (loading state: "Thinking…").
- **Suggestions:** an ordered list; each item = champion name, a **tag** ("your pool"
  vs "meta pick"), a confidence level (low/medium/high), and a one-line reason.

---

## Data available (for realistic mockups)

Champion icons come from Riot's Data Dragon CDN, e.g.
`https://ddragon.leagueoflegends.com/cdn/<version>/img/champion/Aatrox.png`.

Example shapes the UI renders:

```json
// Profile
{ "riot_id": "PilotSheep#EUW", "region": "EUW", "level": 128, "profile_icon_id": 773,
  "ranked": [{ "queueType": "RANKED_SOLO_5x5", "tier": "GOLD", "rank": "II",
               "leaguePoints": 6, "wins": 73, "losses": 60 }],
  "top_masteries": [{ "champion_id": 134, "points": 246443, "level": 25 }] }

// Champion pool "recent form" entry
{ "champion_id": 266, "champion_name": "Aatrox", "games": 12, "wins": 7,
  "win_rate": 0.58, "avg_kda": 3.1, "avg_cs_per_min": 7.4, "form_score": 0.44 }

// Draft suggestion
{ "champion": "Ahri", "reason": "Strong into the enemy mid pick; safe laning.",
  "confidence": "high", "in_pool": true }
```

---

## Current visual style (to match or evolve)

The current UI is deliberately plain (function first). Design tokens in use:

| Token | Value | Use |
|---|---|---|
| Ink (text) | `#1c2430` | Body text |
| Muted | `#5b6674` | Secondary text |
| Accent | `#1f4e79` | Headings, primary button, links |
| Line | `#d9e0e8` | Borders |
| Chip bg | `#eef3f8` | Chips, hover, tags |
| Error | `#b00020` | Error text |
| Radius | `6px` | Corners |
| Font | system-ui sans-serif | Everything |

The layout is a single centred column, max-width ~640px. It's tidy but flat — there's
lots of room to make it feel like a proper gaming tool.

---

## What I'd like from a redesign

1. **Elevate the visual design** into something that feels like a polished LoL
   companion — stronger hierarchy, tasteful use of champion art/icons, a confident
   accent, subtle depth (cards, spacing), maybe a light/dark option.
2. **Make champion-heavy areas shine** — the champion pool, recent form, and the draft
   suggestions should feel visual and scannable (icons, win-rate bars, tags).
3. **Keep it fast and legible** — accessible contrast, clear states (loading/empty/error),
   responsive down to mobile.
4. **Draft assistant as the hero feature** — the search pickers and the suggestion cards
   (with the in-pool / meta-pick tags and confidence) should be the standout.

Constraints: single-page web app, champion images are external URLs (Data Dragon),
no login. Not affiliated with Riot Games (small disclaimer in the footer is fine).

## Suggested prompt to kick off a design

> "Design a modern, responsive UI for a League of Legends companion web app called
> PoroPilot. Sections: summoner search, a profile card (rank, mastery, recent-form
> champions with icons and win-rates), and an AI draft assistant with search pickers
> and suggestion cards tagged 'your pool' / 'meta pick' with a confidence level. Clean,
> icon-rich, game-flavoured but not cliché; strong hierarchy; light and dark themes;
> accessible contrast. Use champion-icon placeholders."
