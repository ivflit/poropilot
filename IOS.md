# PoroPilot iOS — build plan

A native iOS client for the existing PoroPilot API, built to support an application for
**BBC Junior Software Engineer (iOS), Corporate Digital & Applications, ref 43346**
(closes **23 August 2026**).

This is a separate deliverable from the web app. It consumes the same FastAPI backend that
already runs at `https://poropilot-api.onrender.com`, so no backend work is required to start.

---

## 1. Why native Swift, and not React Native

React Native would give iOS and Android from one codebase, and for a normal product decision
that would be a reasonable call. It is the wrong call here, because of what this app is *for*.

The BBC role lists five essential criteria. Three of them name the native toolchain directly:

| BBC essential criterion | Native Swift | React Native |
|---|---|---|
| Good experience writing iOS apps using **Xcode** | yes | partly, mostly JS tooling |
| Good experience with **Swift, SwiftUI, SwiftData** and OOP | yes | no |
| Good experience consuming APIs (RESTful or GraphQL) | yes | yes |
| Strong troubleshooting and problem-solving | yes | yes |
| Commitment to own growth, willingness to share knowledge | yes | yes |

Desirable criteria also point the same way: familiarity with **UIKit**, and package managers
such as **CocoaPods or Swift Package Manager**.

BBC applications are scored against those criteria one by one. Turning up to an iOS role with
a JavaScript cross-platform app reads as having avoided the exact skill the job is about, and
it scores zero on the two criteria that matter most. Native Swift turns the single largest gap
on the CV into a demonstrable, testable, shipped thing.

**Android is out of scope.** The role is iOS only. Adding Android doubles the work for zero
marks against the spec, with 13 days on the clock. If PoroPilot iOS is worth continuing after
the application, a Kotlin/Compose Android client is a sensible later project, and it would then
be a second native skill rather than a cross-platform compromise.

**Decision: native Swift 6 + SwiftUI, iOS 17 minimum, no third-party dependencies.**

---

## 2. What the app does

Scope is deliberately a subset of the web app. It has to be finished, polished and tested,
not feature-complete.

1. **Search** — pick a region, enter a Riot ID (`name#tag`), see the profile.
2. **Profile** — summoner level, icon, ranked tier / LP / win-loss.
3. **Champion pool** — mastery-ranked champions with win rates, champion art from Data Dragon.
4. **Match history** — recent games, expandable to per-player KDA, CS and damage.
5. **Recent searches** — persisted locally with SwiftData, so the app is useful on cold launch.
6. **Live game** — if the summoner is in a game, show participants and their ranks.

Deliberately excluded for v1: account signup/login, saved pools, the AI draft assistant, patch
digest and tier list. They are all AI-gated or auth-gated and add risk without adding marks.
If time allows, the AI draft assistant is the first thing to add back, because it is the most
interesting screen to demo in an interview.

---

## 3. API surface already available

All of these exist and are tested on the backend. No new endpoints are needed for v1.

| Screen | Endpoint |
|---|---|
| Region picker | `GET /regions` |
| Feature flags | `GET /config` |
| Champion static data | `GET /champions` |
| Profile | `GET /summoner/{region}/{name}/{tag}` |
| Champion pool | `GET /pool/{region}/{name}/{tag}` |
| Match history | `GET /history/{region}/{name}/{tag}` |
| Live game | `GET /live/{region}/{name}/{tag}` |
| Health check | `GET /health` |

Later, if v1 lands early: `POST /draft`, `GET /patch-digest`, `GET /tier-list` (all AI-gated),
and `/auth/*` plus `/pools` for the signed-in experience.

Two backend facts worth knowing before wiring the client:

- **CORS does not apply.** A native app is not a browser origin, so no `CORS_ORIGINS` change
  is needed. Nothing to configure on Render.
- **Render free tier cold-starts.** The first request after idle can take 30 seconds or more.
  The client needs a generous timeout and a loading state that does not look broken. This is a
  genuine "troubleshooting and problem-solving" story for the application, so document what
  happened rather than just fixing it silently.

---

## 4. Architecture

```
PoroPilotIOS/
  App/                 PoroPilotApp.swift, root navigation
  Models/              Codable structs mirroring the FastAPI response schemas
  Networking/          APIClient (async/await URLSession), APIError, Endpoint
  Persistence/         SwiftData models: RecentSearch, CachedProfile
  Features/
    Search/            SearchView + SearchViewModel
    Profile/           ProfileView + ProfileViewModel
    Pool/              ChampionPoolView
    History/           MatchHistoryView, MatchRowView
    Live/              LiveGameView
  DesignSystem/        Colours, typography, reusable cards
  Resources/           Assets, Data Dragon image caching
PoroPilotIOSTests/     Unit tests, protocol-based mocked APIClient
PoroPilotIOSUITests/   One happy-path UI test
```

**Patterns to use, because they map to the criteria:**

- **MVVM with `@Observable`** view models. This is the OOP evidence: protocols, dependency
  injection of the API client, value-type models.
- **`async`/`await` with `URLSession`**, one generic `request<T: Decodable>` method. No Combine,
  no callbacks.
- **`Codable` structs** matching the backend's Pydantic schemas exactly. Use `CodingKeys` where
  the API uses snake_case.
- **SwiftData** for recent searches and a short-lived profile cache. This is an essential
  criterion, so it must be genuinely used, not bolted on.
- **Swift Package Manager** for anything third-party. Ideally nothing is needed, in which case
  say so and note SPM was the intended route. Do not add a dependency purely to tick the box.
- **Accessibility from the start**: Dynamic Type, VoiceOver labels on every image and stat,
  contrast checked. Mobile accessibility is a desirable criterion and it connects directly to
  the WCAG AAA work already on the CV, so it is cheap marks and an honest story.

---

## 5. Plan, 13 days to the 23 August deadline

Roughly two hours an evening, more at weekends. Ordered so that stopping early still leaves
something shippable.

| Days | Work |
|---|---|
| 1–2 | Xcode project, Swift concurrency setup, `APIClient`, models for `/regions` and `/summoner`, first green unit test against a mocked client |
| 3–4 | Search screen and profile screen, real data end to end, loading and error states including the cold-start case |
| 5–6 | Champion pool with Data Dragon images and an image cache |
| 7–8 | Match history list with expandable per-player detail |
| 9 | SwiftData recent searches, offline cold launch |
| 10 | Live game screen |
| 11 | Accessibility pass: Dynamic Type, VoiceOver, contrast. Dark mode check |
| 12 | Tests: unit coverage on view models and decoding, one UI happy-path test. GitHub Actions job running `xcodebuild test` |
| 13 | README with screenshots, tidy commits, CV and application updated |

**Cut list if it slips**, in order: live game, then match history detail expansion, then
SwiftData cache (keep recent searches). Do not cut the accessibility pass or the tests. They
are each worth more against the criteria than another screen.

---

## 6. Repo workflow

Same rules as the rest of PoroPilot (see `CLAUDE.md`):

- Issue first, then branch `feature/<issue-number>-<short-name>`, then PR, merge on green CI.
- Never commit directly to `main`.
- Tasks tracked in `tasks.md` with acceptance criteria backed by passing tests.

Open question to settle before day 1: **same repo or separate?** A separate `ivflit/poropilot-ios`
repo gives a clean, obviously-iOS project at the top of the GitHub profile, which is what a BBC
reviewer will click. A monorepo `ios/` directory keeps the API and client together and shows the
full-stack story. Recommendation: **separate repo**, cross-linked from both READMEs, because the
audience for this one is a hiring manager scanning for Swift.

---

## 7. What this gives the application

Before: 2 of 5 essential criteria, and the three missing ones are the ones the job is named
after.

After: all 5 essential criteria have real evidence, plus 3 of 4 desirables (UI/UX, mobile
accessibility, SPM). UIKit stays a genuine gap, which is fine to state honestly at interview,
alongside the fact that SwiftUI was the right choice for a greenfield app.

The honest framing for the CV and cover letter is "built and shipped a native SwiftUI client
for an API I wrote myself", not "iOS developer". That is exactly the right claim for a junior
role, and it is verifiable from the repo.
