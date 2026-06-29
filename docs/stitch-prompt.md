# Google Stitch Design Brief — Spotify Music Discovery Insights Dashboard

## Project overview

Design a **highly interactive, modern web dashboard** (desktop-first, fully responsive) for **Spotify product teams, executives, and user researchers**.

The product answers **six strategic research questions** about why users struggle with music discovery, using evidence from **~23,000 cleaned public reviews** collected from five sources:

- **App Store**
- **Google Play**
- **Reddit**
- **Community Forums**
- **Social Media**

This is **not** the consumer Spotify app. It is an **internal insights explorer** — a live control panel for user voice, not a static report or wiki page.

**UI is a first-class priority.** The interface should feel as polished and interactive as products like **Linear**, **Vercel Analytics**, or **Stripe Dashboard** — dark, confident, motion-rich, and explorable. Avoid boring text-heavy layouts.

**Tech context (for realism):** Next.js on Vercel, FastAPI on Render, data from Supabase. All content is API-driven.

---

## Design system direction

Use a **hybrid design system**:

| Layer | Reference | Purpose |
|---|---|---|
| **Visual polish & hierarchy** | Apple Human Interface Guidelines | Typography, spacing, calm premium feel, readable long-form text |
| **Components & interaction** | Material Design 3 | Chips, buttons, dialogs, progress, snackbars, data tables, tooltips |
| **Layout energy & density** | Linear / Vercel / Stripe dashboards | Bento grids, animated metrics, master-detail layouts, dark data UI |

### Visual tokens

- **Mode:** Dark mode primary (design light mode optional as secondary)
- **Background:** `#0A0A0B` to `#000000`
- **Surface / cards:** `#1C1C1E`, `#2C2C2E` (layered elevation, not flat gray slabs)
- **Borders:** `rgba(255,255,255,0.08)` — subtle
- **Primary accent:** Spotify green `#1DB954` — CTAs, active states, chart highlights only
- **Secondary accent:** Teal/cyan for charts and secondary data series
- **Warning:** Amber for low-confidence data badges
- **Error:** Soft red for failed synthesis (not alarming)
- **Typography:** SF Pro or **Inter**
  - H1 (question titles): 28–34px, semibold
  - Theme sentences: 17–19px, medium — **hero readable content**
  - Body narrative: 15–17px, line-height 1.5–1.6
  - Metadata / counts: 13px, muted (`#8E8E93` or similar)
- **Radius:** 16–20px on cards; 999px on chips/pills
- **Icons:** Lucide-style line icons (source, status, export, refresh)
- **Hero only:** Very subtle mesh gradient (deep green → black); optional light glass blur on primary CTA card
- **Do not** clone the consumer Spotify app UI. Green is an accent, not the whole brand skin.

### Motion & micro-interactions (spec explicitly)

| Interaction | Behavior |
|---|---|
| Page load | Staggered card fade-up (60–80ms delay per card) |
| Metric numbers | Count-up animation (e.g. 0 → 23,166) |
| Theme bar chart | Bars animate width from 0 on scroll-into-view |
| Card hover | Lift 2px + subtle green glow on border |
| Theme selection | Cross-fade detail panel (~200ms ease) |
| Filter chips | Selected chip fills accent; filtered content cross-fades |
| Chart hover | Tooltip + dim non-hovered segments |
| Synthesize button | Morphs to circular progress ring when running |
| Navigation | Shared-element transition from home question card → question header |
| Quote expand | Full-screen modal with backdrop blur |

**Avoid:** parallax, constant looping animation, neon/cyberpunk, 3D charts, glassmorphism everywhere.

---

## Audience & jobs to be done

**Primary users**

- Product managers — headline answers, ranked themes, copy-paste narratives
- User researchers — quotes, source breakdowns, confidence cues
- Executives — 30-second overview: pain points, opportunities, last updated

**Core jobs**

1. See all **six questions** and top themes at a glance
2. **Click** into any question and explore **5 ranked themes** interactively
3. Filter evidence by **source** and **rating**
4. Read **verbatim anonymised quotes** tied to each theme
5. Trigger **“Synthesize now”** from the home header to refresh with the latest 7 days of feedback
6. **Export Report** as a multi-page PDF for stakeholders
7. Ask **PM Buddy** evidence-backed questions about repetitive listening and discovery strategy
8. Track **synthesis run history** and **live review trends** over time

---

## Information architecture — screens to design

Design **11 screens** (desktop + mobile for key screens) with **interaction notes** on each.

---

### Screen 1: Executive Overview (Home) — `/`

**Layout:** Modern **bento grid** — asymmetric card sizes, not a single scrolling document.

**Header (persistent)**

- Product name: **Music Discovery Insights**
- Subtitle: *Evidence from public user feedback*
- Right side: **Export Report** (secondary) + **Synthesize now** (primary filled button) + run status indicator dot (green/amber/red)
- Metadata strip: `23,166 reviews` · `Last updated: 16 Jun 2026, 14:32 UTC` · `Run: Success`

**Sidebar navigation:** Home · PM Buddy · Trends · History · Q1–Q6

**Bento grid cards:**

**A. Hero metrics row (4 animated tiles)**

- Reviews analyzed (count-up)
- Questions answered: `6/6`
- Themes surfaced: `30`
- Avg rating (discovery-related): `2.5★`

**B. Executive summary card**

- 3–5 sentence narrative (justified text, readable padding)
- **Copy narrative** icon button

**C. Top pain points (interactive)**

- Horizontal **ranked bar chart** (not bullet list)
- Hover bar → tooltip with count + quote preview
- Top 3 pain points

**D. Top opportunities (interactive)**

- Same pattern as pain points
- Action-oriented icons per row

**E. Source mix donut (interactive)**

- 5 segments: App Store, Google Play, Reddit, Community Forum, Social Media
- Hover segment → highlight + count tooltip
- Click segment → preview filtered quote snippet

**F. Six question preview cards (2×3 grid desktop, stack mobile)**

Each card:

- `Q1` badge + short title
- Top theme preview (1 line, truncated)
- Mention count badge (e.g. `1,150`)
- Mini sparkline placeholder (trend)
- Hover: lift + green accent border
- Click: navigate to question detail (shared-element transition)

**Interaction notes:** Home should feel alive on load — metrics count up, bars animate in, cards stagger. No static PDF energy.

---

### Screens 2–7: Question Detail — `/questions/q1` … `/questions/q6`

**Use one consistent template** for all six. This is the **flagship screen** — spend the most design effort here.

**Questions (exact copy):**

| ID | Question |
|---|---|
| Q1 | Why do users struggle to discover new music? |
| Q2 | What are the most common frustrations with recommendations? |
| Q3 | What listening behaviors are users trying to achieve? |
| Q4 | What causes users to repeatedly listen to the same content? |
| Q5 | Which user segments experience different discovery challenges? |
| Q6 | What unmet needs emerge consistently across reviews? |

**Layout: Master-detail split (desktop)**

```
┌──────────────────────────────────────────────────────────────────┐
│ ← Home    Q2 · Recommendation frustrations                       │
│ Stats: 4,805 mentions · 2.5★ avg · 3,200 low ratings (1–3★)      │
├─────────────────────────────┬────────────────────────────────────┤
│ TOP 5 THEMES (clickable)    │ DETAIL PANEL (updates on select) │
│                             │                                    │
│ #1 ████████████████  751  ◀─│ Full theme sentence (layman)      │
│ #2 ██████████████    664    │ Supporting summary                 │
│ #3 ████████          337    │ Example quote card                 │
│ #4 ███               100    │ Mini source breakdown for theme    │
│ #5 ██                 78    │ [Copy theme] [Export]              │
├─────────────────────────────┴────────────────────────────────────┤
│ Answer narrative (collapsible card — expand/collapse)            │
│ 2–4 paragraphs · [Copy narrative]                               │
├──────────────────────────────────────────────────────────────────┤
│ INTERACTIVE CHARTS ROW                                           │
│ [Source donut — mentions by source]  [Rating histogram]        │
├──────────────────────────────────────────────────────────────────┤
│ FILTER CHIPS: All · Google Play · App Store · Reddit · 1–3★ only │
├──────────────────────────────────────────────────────────────────┤
│ QUOTE GALLERY — horizontal scroll, snap cards, live filter sync  │
└──────────────────────────────────────────────────────────────────┘
```

**Top 5 themes component (hero)**

Each theme row:

- Rank `#1–#5`
- **Animated horizontal bar** proportional to mention count
- **Full layman sentence** (12–30 words) — NOT a 3-word label  
  Example: *“Users on the free tier are frustrated with the frequent and intrusive ads that interrupt their music experience.”*
- Mention count badge (e.g. `1,202 mentions`)
- Selected state: green left border + filled background tint

**Click theme row →** detail panel cross-fades with:

- Full theme sentence
- 1-line summary
- Example quote card (source badge + star rating)
- Source mini-chart for that theme
- Copy / Export buttons

**Optional:** “Play through themes” auto-advance button (like a guided walkthrough for execs).

**Answer narrative**

- Collapsible card (default: expanded on desktop, collapsed on mobile)
- **Copy narrative** button

**Charts (interactive, synced with filters)**

- **Source breakdown:** stacked or horizontal bar — hover tooltips, click to filter quotes
- **Rating distribution:** histogram — click 1★ bar → show low-rating quotes only

**Quote gallery**

- Horizontal scroll with snap points (App Store–style card carousel)
- Quote cards: elevated surface, quotation styling, source icon, star rating, date
- Tap card → full-screen quote modal (Screen 9)
- Filters via chips update gallery + charts in real time

**Key findings**

- 3–5 expandable accordion items: finding + evidence line

**Mobile:** Stack master-detail vertically; themes list on top; detail panel below selected theme; charts stack; quote gallery remains horizontal scroll.

---

### Screen 8: Trends — `/trends`

- **Dual-axis chart** (Recharts): net sentiment line (rating-based, −100 to +100) + average rating bars
- **Granularity toggle:** Weekly · Monthly · Yearly — buckets from live `clean.feedback_items` by posting date
- Tooltips show review volume, positive/neutral/negative split, and avg rating per period
- **Empty state:** when no dated reviews exist in the selected range
- **Note:** sentiment is a star-rating proxy (4–5★ positive, 3★ neutral, 1–2★ negative), not Groq text analysis

---

### Screen 9: PM Buddy — `/pm-buddy`

- Chat layout: message thread + input bar
- System positions PM Buddy as a product-strategy copilot for repetitive listening and discovery friction
- Answers cite dataset stats, segment hints, and verbatim quotes from the evidence context
- Empty state when `GROQ_API_KEY` is not configured (503 from backend)
- Sidebar link between Home and Trends

---

### Screen 10: Run History — `/runs`

- Material-style **data table**: date, status pill, reviews analyzed, tokens used, duration
- Row expand → mini timeline of that run’s steps
- Failed rows: expandable error snippet
- **Compare runs** checkbox mode → side-by-side diff view
- Link each row → view insights from that run

---

### Screen 11: Synthesize Flow (modals / overlays)

**State 1 — Confirm dialog**

- Title: “Synthesize new insights?”
- Body: Collects last **7 days** of public feedback, re-runs cleaning and analysis. Takes ~2–3 minutes.
- Buttons: Cancel · **Start synthesis**

**State 2 — Already running**

- Dialog: “Synthesis in progress” — disable second run
- Show link to run status

**State 3 — In progress (banner + card)**

- Sticky top banner: linear progress + steps `Collecting → Cleaning → Synthesizing`
- Home header Synthesize button shows ring progress while running

**State 4 — Success snackbar**

- “Insights updated” + timestamp + “View results” action

**State 5 — Failed**

- Soft error card: “Synthesis incomplete” + retry button + error snippet

---

### Screen 11: Quote Expanded Modal

- Full-screen or large centered modal, backdrop blur
- Large quote text
- Source badge, rating stars, posted date
- **Previous / Next** navigation within filtered set
- Close button + swipe down on mobile

---

### Screen 12: Empty & Loading States

Design all of these (with shimmer skeletons, not spinners alone):

- **No data yet** — before first synthesis run
- **Question with zero mentions** — “Not enough data for this question”
- **Low confidence** — amber badge when source sample is thin (e.g. Reddit n=4)
- **Loading skeleton** — home bento grid, theme bars, quote cards
- **Partial run** — 6/7 questions complete, executive summary missing

---

## Component library to spec

1. **App shell** — collapsible left nav or top nav: Overview, Q1–Q6, Trends, Runs
2. **Metric tile** — animated count-up number + label
3. **Bento card** — varied sizes, hover lift
4. **Theme rank row** — bar + sentence + count + selected state
5. **Detail panel** — cross-fade content region
6. **Quote card** — carousel item + expanded modal variant
7. **Source chip** — filter toggle with icon per source
8. **Rating chip** — “1–3★ only” filter
9. **Stat chip** — compact pill (`4,805 mentions`)
10. **Status badge** — Success / Partial / Failed / Running
11. **Synthesis CTA** — button → progress ring morph
12. **Progress stepper** — Collect → Clean → Synthesize
13. **Interactive bar chart** — hover, click-to-filter
14. **Donut chart** — source mix
15. **Data table** — run history with expandable rows
16. **Snackbar / toast** — synthesis complete
17. **Export menu** — Copy narrative, Copy themes, Download summary
18. **Low confidence badge** — amber warning
19. **Footer audit strip** — `Run ID: f4a29a37` · `Model: llama-3.3-70b-versatile`

---

## Data model — use realistic placeholder content

### Executive summary

```json
{
  "summary_text": "Users generally find discovery workable, but recommendation quality, ad frequency on the free tier, and playback control gaps drive the loudest complaints. Premium value and shuffle limitations split the audience sharply.",
  "top_pain_points": [
    "Poor recommendation quality and repetitive suggestions",
    "Intrusive ads on the free tier",
    "Limited playback control (skip, shuffle, repeat)"
  ],
  "top_opportunities": [
    "Improve Discover Weekly visibility and personalization",
    "Clarify Premium value vs free limitations",
    "Fix shuffle and repeat behaviour on large playlists"
  ]
}
```

### Per-question theme (5 per question)

```json
{
  "theme": "Users receive suggestions for genres or songs they clearly do not like, indicating a lack of understanding of their music preferences.",
  "mention_count": 337,
  "summary": "Many users say playlists play random songs they did not add.",
  "example_quote": "I don't have Spotify premium but come on, a playlist is for a specific group of songs and now it plays random songs I don't like."
}
```

### Stats block (per question)

```json
{
  "total_mentions": 4805,
  "avg_rating": 2.53,
  "low_rating_count": 3200,
  "by_source": {
    "google_play": 4200,
    "app_store": 312,
    "reddit": 180,
    "community_forum": 64,
    "social_media": 49
  },
  "rating_distribution": {
    "1": 1200, "2": 900, "3": 1100, "4": 800, "5": 805
  }
}
```

### Quote object

```json
{
  "text": "Shuffle is rubbish, make a playlist with 47 hours of songs and every time you play you hear the same songs.",
  "source": "google_play",
  "rating": 2,
  "posted_at": "2026-05-12"
}
```

---

## Sample content — Q2 (use on question detail mock)

**Stats:** 4,805 mentions · 2.53★ avg · 3,200 low ratings

**Narrative excerpt:**  
*“Recommendation frustrations are widespread across Google Play reviews. Users most often blame the algorithm for repetitive or irrelevant suggestions. A smaller group praises curated mixes like Discover Weekly when they work well.”*

**Top 5 themes (real data):**

1. **751** — Users experience poor quality recommendations that do not meet their expectations.
2. **664** — The algorithm is blamed for suggesting music that feels wrong, repetitive, or out of touch with the user's taste.
3. **337** — Users receive suggestions for genres or songs they clearly do not like, indicating a lack of understanding of their music preferences.
4. **100** — Listeners complain that recommendations and mixes keep serving the same songs instead of surfacing fresh music.
5. **78** — Users refer to curated playlists like Discover Weekly when talking about recommendations.

**Sample quotes:**

- *“stop using algorithms! I am a premium user with over 2,000 songs on my playlist and I hear the same 100 to 200 songs every single day.”* — Google Play, 2★
- *“Every single update this app is getting worse. Discover weekly was always on the front page. Where is it now?”* — Google Play, 3★

---

## UX rules (non-negotiable)

1. **No chart without a “so what”** — one plain-English line under every chart
2. **Every theme shows mention count** — frequency drives prioritization
3. **Quotes are first-class UI** — carousel, modal, filterable — not footnotes
4. **Everything clickable filters something** — theme → quotes; source → charts + quotes; rating bar → angry quotes
5. **Low-confidence data** gets amber badge (thin segment, e.g. n<20)
6. **PII masked** in quotes (`[EMAIL]`) — UI must not break on placeholders
7. **Synthesize button** on home header only — disabled while run in progress; tooltip explains why
8. **Export Report** on home header — multi-page PDF of home, questions, and trends
9. **Export everywhere** narratives and themes are shown (copy buttons on cards)
10. **Avoid wiki layouts** — no 800px single column of uninterrupted text

---

## Responsive breakpoints

| Breakpoint | Behavior |
|---|---|
| Desktop 1280px+ | Bento grid, master-detail split, sidebar nav |
| Tablet 768–1279px | Single column, charts stack, quote carousel remains horizontal |
| Mobile <768px | Hamburger nav, stacked themes + detail, bottom sheet for filters |

---

## Accessibility

- WCAG AA contrast on dark backgrounds
- Charts use pattern + color (not color alone)
- Keyboard-focusable: theme rows, chips, Synthesize, quote modal
- Screen reader labels: “Theme 1 of 5, 751 mentions, recommendation quality”
- Reduced motion variant: disable count-up and bar animations, keep cross-fades minimal

---

## Deliverables requested from Stitch

1. **Design system page** — colors, type scale, spacing, radius, elevation, motion tokens
2. **Component sheet** — all 19 components with states (default, hover, selected, disabled, loading)
3. **Desktop mockups** — all screens listed above
4. **Mobile mockups** — Home + Question Detail + Quote Modal
5. **Interaction flow diagram** — Synthesize now (idle → confirm → progress → success/fail)
6. **Prototype notes** — which elements click/filter/navigate where
7. **Do not design** login/auth screens (SSO later)

---

## Style references (mood board)

Combine the best of:

- **Linear** — interaction density, dark polish, fast feel
- **Vercel Analytics** — clean charts, dark surfaces
- **Stripe Dashboard** — confident metrics, great tables
- **Apple Health** — ring progress, card hierarchy (for synthesis status)
- **Material 3 expressive** — chips, dialogs, motion specs

**Not:** consumer Spotify app, wiki/docs page, static PDF report, generic admin Bootstrap panel.

---

## One-line creative north star

> *“A premium, interactive command center for understanding what users are saying about music discovery — where every number opens a story, every theme is a button, and every quote is one click away.”*

---

## Usage note

If Stitch has a character limit, start with **Screen 1 (Home)**, **Screen 2 (Question Detail template)**, and the **Design system** section — those three carry the most visual weight.
