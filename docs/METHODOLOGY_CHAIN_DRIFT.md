# APIx Aggregation Methodology & the Chain-Drift Problem

**Status**: normative. `apix/index/aggregate.py` implements this document.
**Audience**: MoSPI / NSO reviewers, SIH evaluators, and anyone extending the index.

---

## 1. Summary

APIx aggregates elementary indices with a **fixed-base Laspeyres**, not a
daily-chained one. This is a deliberate methodological choice, and it is the
single most consequential decision in the index.

A daily-chained index of noisy prices manufactures inflation that is not there.
Before this was corrected, the published 45-day APIx series read **+29.27%**
over a window in which the underlying fare level had moved **+0.94%**. Roughly
28 percentage points of the headline number were an artefact of the aggregation
formula.

---

## 2. The two formulations

Let $I_{i,t}$ be the elementary (Jevons) index for stratum $i$ on day $t$, and
$w_i$ the DGCA passenger-traffic weight of that stratum.

**Fixed base** — every day compared to the base period:

$$I_t = 100 \times \sum_i w_i \cdot \frac{I_{i,t}}{I_{i,0}}$$

**Daily chain** — every day compared to the day before, then multiplied up:

$$I_t = I_{t-1} \times \sum_i w_i \cdot \frac{I_{i,t}}{I_{i,t-1}}$$

These are algebraically different, and the difference is not small.

---

## 3. Why the daily chain drifts

The chain link is a weighted **arithmetic** mean of price relatives. For
relatives that are noisy but trendless, Jensen's inequality gives

$$\mathbb{E}\left[\sum_i w_i r_{i,t}\right] > \exp\left(\mathbb{E}[\ln r]\right) = 1$$

For log-normally distributed relatives with dispersion $\sigma$, the expected
link value is $\exp(\sigma^2)$. Over $n$ links the bias compounds:

$$\text{bias} = \exp(n \sigma^2)$$

Airfare daily dispersion is around $\sigma \approx 0.08$. That is
$\exp(0.08^2) \approx 1.0064$ per link — **about +0.64% per day of purely
spurious inflation**, roughly +26% per year on prices that never moved.

The mechanism is not exotic. A price that goes up 10% and back down to exactly
where it started produces relatives of $1.10$ and $0.909$. Their product is
$1.000$ (correct), but the index does not multiply them together in isolation —
it averages each *across strata* arithmetically first, and the arithmetic mean
of an up-move and its exact reversal exceeds 1. Repeat daily and the error
accumulates without bound.

### Verified empirically

`tests/test_index.py` constructs a panel whose true price level is flat by
construction (every observation is a base price times i.i.d. lognormal noise)
and asserts:

| Method | Index after 45 days | Correct answer |
|---|---:|---:|
| `fixed_base` (headline) | ~100.0 | 100.0 |
| `geometric` (sensitivity) | ~100.0 | 100.0 |
| `chained` (diagnostic only) | ~105 and rising | 100.0 |

`test_index_returns_to_base_when_prices_return_to_base` pins the property that
matters to a reviewer: if prices rise and come back to exactly their starting
level, the index returns to exactly 100. The daily chain does not.

---

## 4. This is the standard position, not a local invention

High-frequency chain drift is a known and documented problem in exactly the
setting APIx operates in — high-frequency scraped price data.

- Ivancic, Diewert & Fox (2011), *Scanner data, time aggregation and the
  construction of price indexes* — the canonical statement of the problem.
- Eurostat (2022), *Guide on Multilateral Methods in the Harmonised Index of
  Consumer Prices* — recommends multilateral methods precisely to avoid drift.
- ONS (2023), alternative data sources methodology — same conclusion for
  scraped and scanner data.

**CPI itself is not daily-chained.** It is a fixed-base Laspeyres within a
weight-reference period, re-linked at long intervals. APIx follows that
practice, which is also what makes it a coherent input to CPI rather than a
differently-constructed number sitting beside it.

---

## 5. What APIx implements

`build_aggregate_index(..., method=...)` offers three modes:

| Mode | Use | Drift |
|---|---|---|
| `fixed_base` (**default**) | The published headline series | None |
| `geometric` | Sensitivity analysis — chained, but a weighted *geometric* mean of relatives, which is unbiased for lognormal noise | None |
| `chained` | **Diagnostic only.** Retained so the drift can be quantified side by side. Do not publish. | Yes, by design |

`rebase_period_days` re-links the fixed-base computation at a chosen interval
(e.g. 30 days), so route weights can be refreshed as traffic shifts without
inheriting daily chaining. `None` means a single fixed base.

`apix/backfill_demo.py` prints both the headline and the chained figure on every
run, so the gap stays visible rather than becoming folklore.

---

## 6. Elementary level

The elementary level is a **chained matched-sample Jevons** index — a geometric
mean of price relatives across carriers priced on both the current and the
reference day. Jevons is unbiased in logs, so chaining is safe here; the drift
problem is specific to arithmetic aggregation across strata.

Three properties matter:

1. **Matched sample.** Only carriers present on both days enter the ratio. A
   carrier entering or leaving the schedule does not move the index.
2. **Sold out is missing, not zero.** An unavailable flight has
   `total_fare_inr = None` and drops out of that day's comparison. It is never
   recorded as a price of 0.
3. **Gaps are bridged, not broken.** The reference for a comparison is the most
   recent day that actually had prices, not blindly $t-1$. Without this, one
   missing collection day permanently erases two days of genuine price movement
   from the chain.

---

## 7. Stated assumptions

These are assumptions, not estimates. They are listed so a reviewer can
challenge them directly rather than discover them.

### 7.1 Advance-window weighting

Each route's DGCA traffic weight is divided **evenly across the five advance
horizons** (T+1, T+7, T+15, T+30, T+45) — 20% each.

The defensible version weights each horizon by the share of bookings actually
made at that lead time. That requires a booking-lead-time distribution, which
DGCA does not publish. Until one is available, the even split is a stated
simplification. It is a real limitation: if most consumers book at T+30, the
index currently over-weights last-minute fares relative to consumer experience.

### 7.2 Tariff sheets in the matched sample

DGCA Rule 135(2) tariff sheets are **declared fare bands** — a regulatory floor
and ceiling per inventory bucket, republished monthly. Two consequences:

- **They do not move day to day.** Within a month, a tariff-sourced carrier
  contributes a price relative of exactly 1.0 every day. It occupies a slot in
  the matched sample while carrying no price signal, damping the index toward
  zero movement.
- **They are not transacted prices.** Band midpoints sit well above what a
  consumer pays.

`ADVANCE_WINDOW_TO_BUCKET` in `apix/collector/adapters/tariff_sheet.py` maps
each advance window to a fare bucket, which at least recovers the
advance-purchase structure the sheet does encode. But the tier remains a **level
reference and coverage backstop, not a daily price signal**. The index should
not be run on tariff sheets alone; they exist to cover carriers that no live
source reaches.

### 7.3 Basket coverage

The 12-route basket covers roughly 31% of all-India domestic passenger traffic
(`total_basket_pax` and `basket_share_of_domestic_pct` in
`apix/data/route_weights.json`). Movements on unlisted routes are assumed to be
represented by the basket.

---

## 8. Outlier screening

Outliers are screened on each carrier's **own period-to-period price
relatives**, not on the daily cross-section of competing carriers.

Cross-sectional screening flags a carrier for being priced differently from its
rivals — which is a genuine market feature, not a data error. Air India costing
more than IndiGo is a real price; excluding it biases the index toward the
cheapest carrier. Eurostat and ONS guidance for scraped data screens relatives,
not cross-vendor level differences.

The concrete failure this replaced: once regulatory tariff-band fares
(~₹14,000) sat in the same daily group as market fares (~₹5,000), the
cross-sectional fence was fitting a bimodal sample and flagging near-randomly.

Outliers are **tagged, never deleted** (`quality_flag="outlier"`), and excluded
from price relatives downstream. The cross-sectional methods remain available as
`method="tukey"` / `method="mad"` for diagnostics.

---

## 9. Known limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Advance-window weights are an even split | Over/under-weights horizons relative to real booking behaviour | Replace with a booking-lead-time distribution when one is obtainable |
| Tariff sheets are constant within a month | Damps daily movement for 6E / AI / QP | Treat as level reference; prioritise live Tier 1/3 sources |
| No Tier 1 commercial API access | 40% of the current basket resolves to simulated fallback | Outreach tracked in `docs/data-sources/COMMERCIAL_API_OUTREACH.md`; the fallback is labelled `collection_method="simulated"` in every row |
| Basket covers ~31% of domestic traffic | Unlisted routes assumed represented | Expand basket as DGCA weights allow |
| Fixed base does not satisfy time reversal in general | A theoretical property, not a practical defect at this horizon | Documented; `geometric` mode available for sensitivity |

**A note on the time reversal test.** An earlier version of the back-test report
asserted that the index "satisfies the Time Reversal Test". That claim was
false for the daily-chained Laspeyres then in use — failing time reversal is
precisely what chain drift *is*. The claim has been removed. What APIx now
guarantees, and tests, is the narrower and true property in §3: prices returning
to their base level return the index to exactly 100.
