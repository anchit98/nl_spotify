# Weekly insights review — template

Use this agenda for the Phase 5 feedback loop meeting ([architecture.md](../../docs/architecture.md) Phase 5). Duration: **30–45 minutes**.

**Attendees:** Product lead, user researcher, data engineer (optional: PM Buddy facilitator)

**Before the meeting**

- [ ] Latest `phase5-operations/reports/latest_health_report.md` (or GitHub Actions artifact)
- [ ] Dashboard home + Trends pages (live Vercel URL)
- [ ] PDF export from **Export Report** (optional handout)
- [ ] Open items from `ops.review_actions` where `status` is `open` or `in_progress`

---

## 1. Pipeline health (5 min)

- Any **critical** alerts since last review? (`ops.alerts` or webhook history)
- Collection volume per source — anything dried up?
- Latest synthesis: success? executive summary present? model version matches pin?

## 2. What changed in user feedback (10 min)

- Trends chart: sentiment or rating shifts since last month
- **Rising themes** from health report (sustained spikes, not one-off blips)
- Top pain points / opportunities from executive summary

## 3. Research questions — deltas (10 min)

Walk the six questions; note only **what changed** vs last review:

| Question | Top theme delta | Decision needed? |
|----------|-----------------|------------------|
| Q1 Repetitive listening | | |
| Q2 Recommendation frustrations | | |
| Q3 Listening goals | | |
| Q4 Discovery barriers | | |
| Q5 Feature gaps | | |
| Q6 Unmet needs | | |

## 4. Actions (10 min)

For each insight that needs product response, record in `ops.review_actions`:

| Insight | Owner | Due | Status |
|---------|-------|-----|--------|
| | | | open |

Example SQL (Supabase SQL editor):

```sql
INSERT INTO ops.review_actions (insight_summary, action_owner, action_due, synthesis_run_id)
VALUES (
  'Users report playlist repetition after Discover Weekly refresh',
  'PM Discovery',
  CURRENT_DATE + 14,
  'YOUR_LATEST_RUN_UUID'
);
```

## 5. Close (5 min)

- Confirm next review date (recommend: weekly, same day as pipeline cron)
- Note whether prompt/model refresh is due (`ops.model_registry` vs current pin)

---

## After the meeting

- Update `review_actions.status` when work ships
- In the **next** review, check whether feedback volume or themes shifted after the fix (closes the loop)
