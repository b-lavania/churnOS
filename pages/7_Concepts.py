"""
Page 7: Concepts & Playbook
==============================
An encyclopedic glossary of every business concept, metric, and framework used
across churnOS — written so a marketplace operator or B2C product person can
actually *use* it, not just nod along.
"""

import streamlit as st
from pathlib import Path

# ── Load CSS ──
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ── Header ──
st.markdown('<div class="terminal-header">SYSTEM DOCS // CONCEPTS & PLAYBOOK v2.0</div>', unsafe_allow_html=True)
st.markdown('<h1 class="gradient-text" style="font-size:3rem; margin-bottom:0.5rem;">Concepts & Playbook</h1>', unsafe_allow_html=True)
st.markdown(
    '<p style="max-width: 800px; margin-bottom: 2rem; line-height:1.6;">'
    'Every metric, formula, and framework used in churnOS — explained in plain language '
    'with worked examples and industry benchmarks. If a concept feels like it would '
    '"fly over the head of an MBA," this is the page that grounds it.'
    '</p>',
    unsafe_allow_html=True,
)

# ── Helper function for concept cards ──
def concept_section(title, tagline, color="#00f2ff"):
    """Render a styled section header for a concept group."""
    st.markdown(
        f'<div class="terminal-header" style="margin-top: 2.5rem; border-color: {color}; color: {color};">'
        f'{title}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="font-size: 0.88rem; color: #94a3b8; margin-bottom: 1rem;">{tagline}</p>',
        unsafe_allow_html=True,
    )


def concept_card(name, one_liner, formula, example, benchmark, why_it_matters, common_mistakes=None, color="#00f2ff"):
    """Render a single concept card inside an expander."""
    with st.expander(f"📐  {name} — {one_liner}"):
        cols = st.columns([3, 2])
        with cols[0]:
            st.markdown(f"**What it is:** {one_liner}")
            if formula:
                st.markdown("**Formula:**")
                st.code(formula, language="text")
            if example:
                st.markdown(f"**Worked Example:**\n\n{example}")
            if common_mistakes:
                st.markdown(f"**⚠️ Common Mistakes:**\n\n{common_mistakes}")
        with cols[1]:
            st.markdown(
                f"""
                <div class="techno-card" style="border-top: 2px solid {color}; padding: 1rem;">
                    <div style="font-family: 'JetBrains Mono'; font-size: 0.65rem; color: {color}; 
                                text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 0.5rem;">
                        INDUSTRY BENCHMARK
                    </div>
                    <div style="font-size: 0.85rem; margin-bottom: 1rem;">{benchmark}</div>
                    <div style="font-family: 'JetBrains Mono'; font-size: 0.65rem; color: #ff9d00;
                                text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 0.5rem;">
                        WHY IT MATTERS
                    </div>
                    <div style="font-size: 0.85rem;">{why_it_matters}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════
#  SECTION 1: CUSTOMER LIFECYCLE & RETENTION
# ══════════════════════════════════════════════════════════════

concept_section(
    "SECTION 01 // CUSTOMER LIFECYCLE & RETENTION",
    "How customers arrive, stay, and eventually leave — and why the shape of that curve determines everything.",
    "#00f2ff",
)

concept_card(
    "Churn Rate",
    "The percentage of customers who stop buying / unsubscribe in a period",
    "Monthly Churn Rate = (Customers lost this month) / (Customers at start of month) × 100",
    "You start January with 10,000 active buyers. By Jan 31, 800 haven't placed an order in 30+ days. "
    "Your monthly churn is **800 / 10,000 = 8.0%**.\n\n"
    "Annualized: 1 − (1 − 0.08)¹² ≈ **63%** — meaning almost two-thirds of your base churns within a year at that rate.",
    "**SaaS:** < 5% monthly (great < 2%)\n\n**E-commerce / DTC:** 15–30% monthly is common\n\n"
    "**Marketplace (buyer-side):** 20–40% monthly",
    "Churn is the *leak in the bucket*. No amount of marketing spend fixes a product that can't retain. "
    "A 1pp reduction in monthly churn from 8% → 7% can increase CLV by ~15%.",
    "• Confusing **logo churn** (count of customers) with **revenue churn** (dollar-weighted). "
    "If your cheapest segment churns fastest, revenue churn will be lower than logo churn — that's OK.\n\n"
    "• Not defining a consistent \"churn rule.\" Is it 30 days no order? 60 days? Cancelled subscription? "
    "Pick one and stick with it.",
    "#00f2ff",
)

concept_card(
    "Logo Churn vs. Revenue Churn",
    "Two different ways to count churn — by headcount or by dollars",
    "Logo Churn  = # customers lost / # total customers\n"
    "Revenue Churn = $ MRR lost (net of expansion) / $ total MRR",
    "Imagine 100 customers paying $10/mo, and 20 customers paying $100/mo.\n\n"
    "• 10 of the $10 customers churn, and 1 of the $100 customers churn.\n"
    "• Logo churn = 11 / 120 = **9.2%**\n"
    "• Revenue churn = ($100 + $100) / ($1000 + $2000) = $200 / $3000 = **6.7%**\n\n"
    "Revenue churn is lower because your high-value segment is stickier. That's a *great* sign.",
    "When revenue churn is **much lower** than logo churn, you're retaining your whales. "
    "When they diverge the *other* way — your best customers are leaving — it's a five-alarm fire.",
    "Tells you whether you're losing heads or wallets. Both matter, but they imply very different actions. "
    "High logo churn + low revenue churn → your entry tier is leaky (maybe fine). "
    "Low logo churn + high revenue churn → your top customers are downgrading or leaving (not fine).",
    color="#00f2ff",
)

concept_card(
    "Cohort Retention / Survival Curves",
    "Tracking what percentage of a signup group is still active N months later",
    "M(n) Retention % = (Customers from cohort still active in month n) / (Cohort size at M0) × 100",
    "A January cohort of 1,000 customers:\n"
    "• M0: 1,000 (100%)\n"
    "• M1: 720 (72%) — big initial drop, normal\n"
    "• M3: 480 (48%)\n"
    "• M6: 310 (31%)\n"
    "• M12: 190 (19%)\n"
    "• M24: 120 (12%)\n\n"
    "The curve flattens over time because survivors are increasingly loyal. "
    "This flattening is *critical* — it means your long-run retention is better than early numbers suggest.",
    "**DTC / Ecom:**\n"
    "• M1: 30–50% (first repeat purchase)\n"
    "• M12: 10–25%\n\n"
    "**Subscription / SaaS:**\n"
    "• M1: 85–95%\n"
    "• M12: 55–80%",
    "The shape of this curve is the single most important input to CLV. "
    "A convex (flattening) curve means you have a core of loyal users. "
    "A concave (steepening) curve means even your \"retained\" users are leaving — you have a product problem.",
    "• Reading M1 retention in isolation. Early drops are normal — what matters is where the curve *flattens*.\n\n"
    "• Comparing non-subscription ecom retention to SaaS retention. Completely different benchmarks.",
    color="#8a2be2",
)

concept_card(
    "Subscribe & Save / Subscription Programs",
    "Offering automatic repeat orders at a discount to reduce churn",
    "Effective Churn = Base Churn × (1 - Sub% × Churn Reduction)\n\n"
    "Example: 8% base churn, 30% of customers subscribe, subscribers churn 80% less\n"
    "Effective Churn = 8% × (1 - 0.30 × 0.80) = 8% × 0.76 = 6.08%",
    "Amazon's \"Subscribe & Save\" turns a one-time $15 dog food purchase into an auto-recurring $13.50 order. "
    "Even though the margin per order drops ~10%, the retention improvement means CLV increases 40–60% "
    "because the customer stays 2.5× longer.",
    "**Penetration:** Top DTC brands achieve 20–40% subscribe rates\n\n"
    "**Churn reduction:** Subscribers typically churn 50–80% less than non-subscribers",
    "The most reliable lever to flatten your retention curve. Even a modest 15% subscribe rate "
    "with 60% churn reduction meaningfully improves CLV. It's the closest thing to a \"cheat code\" in ecommerce.",
    color="#14b8a6",
)

concept_card(
    "Reactivation Rate",
    "The percentage of churned customers who come back and order again",
    "Reactivation % = (Previously churned customers who ordered this month) / (Total churned customers)",
    "You have 5,000 churned customers. You run a winback email campaign and 100 place a new order. "
    "Reactivation rate = 100 / 5,000 = **2.0%/month**.\n\n"
    "Sounds tiny, but over 12 months that compounds: ~1,200 reactivated customers from that pool alone.",
    "**Good:** 1–3% per month\n\n**Great:** 3–5% per month\n\n**Exceptional:** 5%+ (usually with strong winback programs)",
    "Reactivation is *cheap* customer acquisition — these people already know your brand. "
    "In the causal model, even a small reactivation rate meaningfully slows the decline of your active base "
    "and provides compounding returns over a 24-month horizon.",
    color="#ff9d00",
)


# ══════════════════════════════════════════════════════════════
#  SECTION 2: UNIT ECONOMICS & PROFITABILITY
# ══════════════════════════════════════════════════════════════

concept_section(
    "SECTION 02 // UNIT ECONOMICS & PROFITABILITY",
    "Is each customer profitable — and when? The building blocks of whether your business actually works.",
    "#14b8a6",
)

concept_card(
    "Customer Lifetime Value (CLV / LTV)",
    "Total profit a customer generates over their entire relationship with you",
    "Simple CLV = AOV × Purchase Frequency × Avg Customer Lifespan × Gross Margin %\n\n"
    "Cohort CLV = Σ(monthly margin per active user × retention % at month n)  for n = 0..N",
    "**Simple method:**\n"
    "AOV = $65, Frequency = 1.8/mo, Lifespan = 12 months, Margin = 42%\n"
    "CLV = $65 × 1.8 × 12 × 0.42 = **$589.68**\n\n"
    "**Cohort method (more accurate):**\n"
    "Month 0: 100% active × $49.14 margin = $49.14\n"
    "Month 1: 72% active × $49.14 = $35.38\n"
    "Month 2: 62% active × $49.14 = $30.47\n"
    "... sum to Month 24 = **$412.50** (lower because it accounts for the actual retention curve)\n\n"
    "The cohort method is what churnOS uses — it's more honest.",
    "**DTC / Ecom:** $100–$500 (24 months)\n\n**SaaS:** $500–$5,000+\n\n**Marketplace buyer:** $80–$300",
    "CLV is the *ceiling* on what you can spend to get a customer. It determines your CAC budget, "
    "your marketing strategy, and ultimately whether the business model works. "
    "The #1 metric for long-term viability.",
    "• Using the \"simple\" formula (AOV × Freq × Lifespan) without adjusting for the actual retention curve. "
    "This always *overstates* CLV.\n\n"
    "• Not backing out costs. CLV should be profit-based, not revenue-based. "
    "Revenue CLV gives you a dangerously inflated view.\n\n"
    "• Measuring at too short a horizon. Some businesses take 12+ months to be profitable per customer.",
    color="#14b8a6",
)

concept_card(
    "Customer Acquisition Cost (CAC)",
    "The all-in cost to acquire one new customer",
    "Blended CAC = (Paid CAC × Paid Mix %) + (Organic CAC × Organic Mix %)\n\n"
    "CAC = Total Marketing Spend / New Customers Acquired",
    "You spend $35,000 on Facebook ads and get 1,000 new customers → Paid CAC = **$35.00**\n"
    "Your SEO / organic content brings in another 1,200 customers at ~$8 each → Organic CAC = **$8.00**\n"
    "Paid Mix = 1,000 / 2,200 = 45%\n\n"
    "Blended CAC = ($35 × 0.45) + ($8 × 0.55) = $15.75 + $4.40 = **$20.15**",
    "**DTC / Ecom:** $15–$80 blended\n\n**SaaS:** $100–$500\n\n"
    "**Marketplace:** $5–$30 (buyer side), $50–$200 (seller side)",
    "CAC is the *price tag on growth*. If CLV is the ceiling, CAC is what you're actually paying. "
    "The relationship between them (LTV:CAC) determines whether growth creates or destroys value.",
    "• Not including all costs. CAC should include headcount, tooling, content, agency fees — not just ad spend.\n\n"
    "• Not separating paid vs. organic. Blending them without understanding the mix hides whether "
    "paid channels are actually working.\n\n"
    "• Ignoring rising CAC. As you scale, paid CAC almost always increases because you exhaust the cheapest audiences first.",
    color="#f43f5e",
)

concept_card(
    "LTV:CAC Ratio",
    "The efficiency of customer acquisition — for every $1 spent, how much lifetime value do you get back?",
    "LTV:CAC = Customer Lifetime Value / Customer Acquisition Cost",
    "CLV = $412, Blended CAC = $20.15\n"
    "LTV:CAC = $412 / $20.15 = **20.4×**\n\n"
    "That's exceptional. Most businesses target 3× as a minimum.\n\n"
    "If your CLV is $120 and your CAC is $45: LTV:CAC = 2.7× — you're below the healthy threshold "
    "and need to either improve retention (raise CLV) or reduce acquisition cost.",
    "**Minimum viable:** 3.0× (you break even accounting for OpEx)\n\n"
    "**Good:** 3–5×\n\n**Great:** 5–8×\n\n**Very high (>10×):** You might be *under-spending* on growth",
    "This is the *single number* that tells investors and operators whether the growth engine is healthy. "
    "Below 3× you're losing money with every customer. Above 5× you might be leaving growth on the table.",
    "• Using LTV:CAC > 3× as a hard rule without context. A fast-payback 2.5× can be fine; a slow-payback 4× can be dangerous.\n\n"
    "• Not pairing it with payback period. LTV:CAC tells you *if* you'll profit; payback tells you *when*.",
    color="#8a2be2",
)

concept_card(
    "Payback Period",
    "How many months until a customer's cumulative profit covers their acquisition cost",
    "Payback Month = smallest n where Cumulative CLV(n) ≥ CAC",
    "CAC = $20.15\n"
    "Month 0: CLV = $49.14 → already exceeds CAC!\n\n"
    "But for a harder case:\n"
    "CAC = $120, Monthly margin per active user = $18\n"
    "Month 1: $18 × 0.72 = $12.96 → cumulative $12.96\n"
    "Month 2: $18 × 0.62 = $11.16 → cumulative $24.12\n"
    "...\n"
    "Month 9: cumulative = $121.50 → **Payback at Month 9**",
    "**SaaS:** 12–18 months (acceptable)\n\n**DTC / Ecom:** 1–6 months (fast recovery is critical)\n\n"
    "**Marketplace:** 6–12 months",
    "Payback is about *cash flow*. Even with a great LTV:CAC ratio, if payback takes 18 months, "
    "you need 18 months of working capital for every cohort. Fast payback = you can reinvest sooner = faster compounding growth.",
    color="#ff9d00",
)

concept_card(
    "Average Order Value (AOV)",
    "The average revenue generated per transaction",
    "AOV = Total Revenue / Total Orders",
    "Last month: $325,000 revenue across 5,000 orders\n"
    "AOV = $325,000 / 5,000 = **$65.00**\n\n"
    "When modeling: AOV × Purchase Frequency = Monthly Revenue per Active Customer.",
    "Highly category-dependent:\n"
    "• **Grocery / CPG:** $30–$60\n• **Fashion:** $60–$120\n"
    "• **Electronics:** $150–$400\n• **B2B / Enterprise:** $500+",
    "AOV is a direct lever on CLV. Increasing AOV by 15% (through bundling, upsells, or premium options) "
    "has the same CLV impact as improving retention by a similar percentage — but it's often easier to execute.",
    color="#14b8a6",
)

concept_card(
    "Purchase Frequency",
    "How often a customer orders per period (usually per month)",
    "Purchase Frequency = Total Orders / Total Active Customers / # Months",
    "5,000 orders from 2,800 active customers in one month\n"
    "Frequency = 5,000 / 2,800 = **1.8 orders/month**",
    "• **Grocery / Consumables:** 2–4×/mo\n• **Fashion / DTC:** 0.3–1.5×/mo\n"
    "• **SaaS:** N/A (monthly subscription)\n• **Marketplace:** 1–3×/mo",
    "Frequency is the *hidden multiplier* in CLV. Most operators obsess over AOV, "
    "but frequency improvements compound more aggressively because they also signal deeper engagement.",
    color="#14b8a6",
)

concept_card(
    "Gross Margin / Net Revenue per Order",
    "What's actually left after you pay for the thing you sold and ship it",
    "Net Revenue per Order = AOV\n"
    "  − COGS (cost of goods)\n"
    "  − Shipping\n"
    "  − Refund losses (AOV × refund rate)\n"
    "  − Discount losses (AOV × discount frequency × discount depth)\n\n"
    "Gross Margin % = Net Revenue per Order / AOV × 100",
    "AOV = $65.00\n"
    "COGS (40%) = −$26.00\n"
    "Shipping = −$5.00\n"
    "Refunds (5% of AOV) = −$3.25\n"
    "Discounts (25% of orders at 15% off) = −$2.44\n\n"
    "Net Revenue = $65 − $26 − $5 − $3.25 − $2.44 = **$28.31**\n"
    "Gross Margin = $28.31 / $65.00 = **43.6%**",
    "**DTC / Ecom:** 40–65%\n\n**Grocery:** 20–35%\n\n**Software:** 70–90%\n\n**Marketplace platform:** 60–85%",
    "This is your *true* per-order profit. Many operators look at revenue-based CLV and wonder "
    "why they're not profitable — it's because they forgot about all the line items between revenue and margin.\n\n"
    "churnOS uses margin-based CLV, which is why your numbers may look lower (but more honest) than other calculators.",
    "• Forgetting shipping costs. Free shipping isn't \"free\" — it eats margin.\n\n"
    "• Treating discounts as marketing spend instead of a revenue reduction. "
    "If 25% of orders have a 15% discount, that's a permanent 3.75% drag on your margin.",
    color="#f43f5e",
)

concept_card(
    "COGS (Cost of Goods Sold)",
    "The direct cost of the products you sell — materials, manufacturing, purchasing from suppliers",
    "COGS % = Cost to Produce or Purchase / Selling Price × 100",
    "You sell a candle for $35. The wax, wick, jar, and label cost $12. "
    "COGS = $12 / $35 = **34.3%**.\n\n"
    "For a marketplace: COGS is typically the seller's cost, not the platform's. "
    "The platform's \"COGS\" is closer to payment processing + infrastructure.",
    "• **DTC (manufactured):** 25–45%\n• **Reseller / Wholesale:** 50–70%\n"
    "• **SaaS / Digital:** 5–15%\n• **Marketplace platform:** 10–25% (just processing + infra)",
    "COGS determines your margin ceiling. A 60% COGS product can never have more than 40% gross margin, "
    "no matter how well you optimize everything else. If COGS is too high, you need premium positioning.",
    color="#14b8a6",
)

concept_card(
    "CAC Ceiling",
    "The maximum you can afford to spend on acquisition while maintaining a target LTV:CAC ratio",
    "CAC Ceiling = CLV(horizon) / Target LTV:CAC Ratio\n\n"
    "Example: CLV(24mo) = $412, Target = 3×\n"
    "CAC Ceiling = $412 / 3 = $137.33",
    "This tells you that at current retention and margin, you can spend up to **$137** to acquire a customer "
    "and still hit a 3× return. If your current blended CAC is $20, you have **$117 of headroom** "
    "— meaning you could *significantly* increase ad spend before becoming unprofitable.\n\n"
    "Conversely, if your ceiling is $30 and your CAC is $40, you're destroying value with every customer you acquire.",
    "The headroom between your CAC and your ceiling tells you how aggressively you can scale.\n\n"
    "**Lots of headroom (>50%):** Step on the gas\n\n**Tight (<20%):** Tread carefully, optimize before scaling",
    "A powerful strategic lens for growth planning. "
    "Instead of asking \"how much should we spend on marketing?\" — ask \"what's the most we *can* spend and still make money?\"",
    color="#8a2be2",
)


# ══════════════════════════════════════════════════════════════
#  SECTION 3: THE CAUSAL MODEL / WATERFALL
# ══════════════════════════════════════════════════════════════

concept_section(
    "SECTION 03 // THE CAUSAL MODEL & SENSITIVITY",
    "How everything connects — change one input, and watch it ripple through the entire business.",
    "#8a2be2",
)

concept_card(
    "Revenue Waterfall",
    "A step-by-step bridge from gross revenue to net profit per order",
    "AOV (start)\n"
    "  ↓ minus COGS\n"
    "  ↓ minus Shipping\n"
    "  ↓ minus Refund Losses\n"
    "  ↓ minus Discount Losses\n"
    "  = Net Margin per Order",
    "Think of it like a waterfall: money flows in at the top ($65 AOV), "
    "and each cost category carves out a piece as it falls.\n\n"
    "What lands at the bottom is what you actually keep. If the waterfall \"goes negative\" — "
    "you're paying customers to buy from you.",
    "Healthy businesses have < 60% of AOV consumed by costs.\n\n"
    "If your net margin is < 15% of AOV, you're in a razor-thin business and churn improvement is critical.",
    "Waterfalls make invisible margin erosion *visible*. "
    "Most operators can't tell you off the top of their head how much they lose to refunds + discounts combined. "
    "The waterfall forces that answer.",
    color="#8a2be2",
)

concept_card(
    "Sensitivity / Tornado Analysis",
    "Which input variables have the most leverage over your bottom-line metrics?",
    "For each input, perturb it ±10% from its current value.\n"
    "Measure the resulting change in the output metric (e.g., CLV).\n"
    "Rank by absolute swing (high swing = high leverage).\n\n"
    "Elasticity = (% change in CLV) / (% change in input)",
    "You perturb Monthly Churn from 8% → 7.2% (−10%) and CLV goes from $412 → $478 (+16%).\n"
    "You perturb AOV from $65 → $71.50 (+10%) and CLV goes from $412 → $445 (+8%).\n\n"
    "Churn has an elasticity of −1.6 (a 10% churn reduction = 16% CLV gain).\n"
    "AOV has an elasticity of +0.8 (a 10% AOV increase = 8% CLV gain).\n\n"
    "→ **Churn is 2× more impactful than AOV.** Focus there first.",
    "Sensitivity analysis tells you where to focus.\n\n"
    "Longer bars in the tornado chart = more leverage. "
    "Optimizing a low-sensitivity variable is wasted effort.",
    "This is the most *strategically actionable* output in churnOS. "
    "Instead of guessing what to work on, you can quantify: \"a 10% improvement in X is worth 3× more than a 10% improvement in Y.\"",
    "• Only looking at upside. If a variable is highly sensitive, it means it can also go wrong in a big way.\n\n"
    "• Optimizing everything at once. Realistic teams can move 1–2 levers at a time. "
    "Pick the biggest one.",
    color="#ff9d00",
)

concept_card(
    "Health Score",
    "A composite 0–100 index of overall business health based on key metric thresholds",
    "Health Score = weighted average of sub-scores:\n"
    "  • LTV:CAC ratio score (is it > 3×?)\n"
    "  • Payback speed (< 6 months?)\n"
    "  • Gross margin (> 40%?)\n"
    "  • Retention curve shape (flattening?)\n"
    "  • CLV trajectory (growing over time?)",
    "A score of 72/100 means your business is in good shape but has room for improvement. "
    "Below 40 indicates structural issues. Above 80 means your unit economics are strong.\n\n"
    "Think of it like a credit score for your business model.",
    "**< 40:** Structural issues — fix retention or margin before scaling\n\n"
    "**40–70:** Viable but needs optimization\n\n"
    "**> 70:** Strong fundamentals — scale with confidence",
    "A single number to gut-check your business. "
    "Useful for tracking progress over time and communicating with stakeholders "
    "who don't want to look at 15 different metrics.",
    color="#14b8a6",
)

concept_card(
    "Segment Churn Multipliers",
    "Different customer segments churn at different rates — model that explicitly",
    "Segment Churn = Base Churn Rate × Segment Multiplier\n\n"
    "Example: Base = 8%\n"
    "  Budget (1.6×)     → 12.8%\n"
    "  Mid-Range (1.0×)  → 8.0%\n"
    "  Premium (0.6×)    → 4.8%\n"
    "  Enterprise (0.3×) → 2.4%",
    "Not all customers are created equal. A Budget customer spending $20/order who churns at 13% "
    "is *very* different from a Premium customer spending $150/order who churns at 5%.\n\n"
    "Aggregate churn masks these differences. Segment multipliers make them explicit.",
    "Typical multiplier ranges:\n"
    "• **Low-spend / discount-seekers:** 1.3–2.0×\n"
    "• **Core / average:** 0.8–1.2×\n"
    "• **High-spend / loyal:** 0.3–0.7×",
    "Without segmented churn, you'll over-invest in retaining low-value customers and under-invest in "
    "protecting the high-value ones. Segment modeling reveals where retention spend has the highest ROI.",
    color="#f43f5e",
)


# ══════════════════════════════════════════════════════════════
#  SECTION 4: CONVERSION & FUNNEL
# ══════════════════════════════════════════════════════════════

concept_section(
    "SECTION 04 // CONVERSION & FUNNEL OPTIMIZATION",
    "The path from casual visitor to paying customer — and where they fall off.",
    "#ff9d00",
)

concept_card(
    "Conversion Rate (CVR)",
    "The percentage of visitors who complete a purchase",
    "CVR = Purchases / Total Visits × 100",
    "30,000 sessions, 900 purchases\n"
    "CVR = 900 / 30,000 = **3.0%**\n\n"
    "A 1pp improvement (3% → 4%) means 300 more customers "
    "from the *same traffic*. At a $412 CLV, that's $123,600 in additional lifetime value.",
    "**Overall ecommerce:** 2.0–4.0%\n\n**Desktop:** 3–5%\n**Mobile:** 1.5–3%\n\n"
    "**Category leaders:** 5–8%",
    "CVR is the *multiplier* on your traffic investment. Doubling CVR is equivalent to doubling your traffic — "
    "but it costs nothing in incremental ad spend.",
    "• Optimizing CVR without controlling for traffic quality. If you shift ad spend to cheaper, lower-intent sources, "
    "CVR will drop even if your site is fine.\n\n"
    "• Not segmenting by device. Mobile CVR is typically 40–60% of desktop CVR. Treat them separately.",
    color="#ff9d00",
)

concept_card(
    "The Ecommerce Funnel",
    "The standard stages a user goes through: Visit → View → Cart → Checkout → Purchase",
    "Each step has a pass-through rate:\n"
    "  Visit → Product View:  ~60-80%\n"
    "  Product View → Cart:   ~10-20%\n"
    "  Cart → Checkout:       ~30-50%\n"
    "  Checkout → Purchase:   ~50-70%",
    "30,000 visits:\n"
    "• 21,000 view a product (70%)\n"
    "• 4,200 add to cart (20% of viewers)\n"
    "• 1,680 start checkout (40% of carts)\n"
    "• 900 purchase (54% of checkouts)\n\n"
    '**Drop-off analysis** identifies the biggest leaks. If Cart → Checkout drops 60%, '
    'that\'s 2,520 abandoned carts — a massive opportunity for cart recovery emails.',
    "**Cart abandonment rate:** 65–80% industry average\n\n"
    "**Checkout completion:** 40–60%\n\n"
    "The biggest drop is almost always Cart → Checkout (surprise costs, shipping, trust).",
    "Understanding *where* users drop off tells you *what* to fix. "
    "No point optimizing product pages if the real issue is at checkout.",
    color="#ff9d00",
)

concept_card(
    "A/B Test Statistical Significance",
    "Determining whether a test result is real or just random noise",
    "z = (p_variant - p_control) / √(p_pooled × (1 - p_pooled) × (1/n_control + 1/n_variant))\n\n"
    "p-value < 0.05 → Statistically significant at 95% confidence",
    "Control: 10,000 visitors, 350 conversions (3.50%)\n"
    "Variant: 10,000 visitors, 420 conversions (4.20%)\n"
    "Lift: +20%\n\n"
    "If p-value = 0.003 → **Significant!** The improvement is real, not noise.\n"
    "If p-value = 0.12 → **Not significant.** You don't have enough data to be sure. Run longer.",
    "**Minimum sample:** 1,000+ per variant for most ecom tests\n\n"
    "**Runtime:** At least 1 full business cycle (7–14 days minimum)\n\n"
    "**Don't peek:** Checking halfway inflates your false positive rate",
    "Without significance testing, you're making product decisions based on coin flips. "
    "A 20% lift that isn't significant is just noise — shipping it will waste engineering time and may even hurt.",
    color="#ff9d00",
)

concept_card(
    "CVR → CLV Impact",
    "Connecting funnel improvements to lifetime revenue using the causal model",
    "Additional Customers = Sessions × (New CVR - Old CVR)\n"
    "Monthly Margin Gain = Additional Customers × Margin per Active User\n"
    "24-Month Value = Additional Customers × CLV(24)",
    "Current CVR: 3.0%, Sessions: 30,000, CLV: $412\n"
    "Improve checkout step by 10% → New CVR: 3.3%\n"
    "Additional customers = 30,000 × 0.003 = **90 more customers/month**\n"
    "24-month value = 90 × $412 = **$37,080/month** in incremental lifetime value",
    "This bridges the gap between \"funnel metrics\" (which CRO teams look at) "
    "and \"business metrics\" (which leadership looks at). It makes every test result into a dollar figure.",
    "Most funnel optimization stops at \"we improved CVR by X%.\" "
    "The causal connection to CLV translates that into actual business impact, "
    "making it much easier to justify CRO investment.",
    color="#ff9d00",
)


# ══════════════════════════════════════════════════════════════
#  SECTION 5: MARKETPLACE ECONOMICS
# ══════════════════════════════════════════════════════════════

concept_section(
    "SECTION 05 // MARKETPLACE ECONOMICS",
    "The unique levers of two-sided marketplaces — take rates, liquidity, and the platform vs. seller tension.",
    "#f43f5e",
)

concept_card(
    "Gross Merchandise Volume (GMV)",
    "The total dollar value of goods sold through your marketplace, before any fees",
    "GMV = Σ (Transaction Value) for all transactions",
    "If 500 sellers collectively sell $2.5M worth of goods in a month, your GMV = **$2.5M**.\n\n"
    "⚠️ GMV is *not* your revenue. Your revenue is what you take as a commission. "
    "A $2.5M GMV marketplace with a 15% take rate earns $375K in revenue.",
    "**Etsy:** ~$13B annual GMV\n**Uber Eats:** ~$60B\n**Amazon 3P:** ~$400B+\n\n"
    "GMV growth without margin can be vanity. Profitable GMV is what matters.",
    "GMV tells you the size of the economic activity flowing through your platform. "
    "It's the \"total pie\" — your take rate determines what slice you keep. "
    "Investors care about GMV growth as a signal of product-market fit, but revenue is what pays bills.",
    color="#f43f5e",
)

concept_card(
    "Take Rate / Commission Rate",
    "The percentage of each transaction that the marketplace keeps as revenue",
    "Take Rate = Platform Revenue / GMV × 100\n\n"
    "Effective Take Rate may differ from nominal if you have:\n"
    "  • Tiered commissions (high-volume sellers get lower rates)\n"
    "  • Fixed per-transaction fees\n"
    "  • Different buyer vs seller fee splits",
    "Nominal rate: 15% commission on all sales\n"
    "But you also charge a $0.30 fixed fee per transaction.\n"
    "On a $20 item: $3.00 commission + $0.30 fee = $3.30, effective take = **16.5%**\n"
    "On a $200 item: $30.00 commission + $0.30 fee = $30.30, effective take = **15.15%**\n\n"
    "The fixed fee makes your effective take rate *regressive* — higher on small tickets.",
    "**Travel / Booking:** 12–18%\n**Ecom marketplace:** 10–25%\n"
    "**Food delivery:** 25–35%\n**Services / gig:** 15–30%",
    "Take rate is the central tension of marketplace economics. "
    "Too low → you can't cover costs. Too high → sellers leave for a competitor. "
    "The optimal take rate maximizes *your revenue* without killing *seller economics*.",
    "• Setting a single flat rate. Sophisticated marketplaces use tiered rates — "
    "give volume sellers a break to grow the pie.\n\n"
    "• Ignoring the buyer-side fee opportunity. Many marketplaces extract value from both sides. "
    "Splitting fees 60/40 seller/buyer can increase total take without alienating sellers.",
    color="#f43f5e",
)

concept_card(
    "Price Elasticity of Demand",
    "How much does demand change when you change the price?",
    "Elasticity (ε) = (% Change in Quantity Demanded) / (% Change in Price)\n\n"
    "ε < −1: Elastic (demand drops faster than price rises)\n"
    "ε = −1: Unit elastic (revenue stays constant)\n"
    "ε > −1: Inelastic (demand barely changes with price)",
    "You raise prices 10% and demand drops 15%.\n"
    "ε = −15% / +10% = **−1.5** (elastic)\n\n"
    "Revenue impact: was $50 × 1000 = $50K, now $55 × 850 = $46.75K → **you lost revenue** by raising prices.\n\n"
    "If demand only dropped 5%: ε = −0.5 (inelastic)\n"
    "Revenue: $55 × 950 = $52.25K → **you gained revenue**.\n\n"
    "Optimal revenue is at |ε| = 1. churnOS finds that point.",
    "• **Commodities:** |ε| > 2 (very elastic — any price increase destroys demand)\n"
    "• **Branded / luxury:** |ε| = 0.3–0.8 (inelastic)\n"
    "• **Most ecom:** |ε| = 1.0–2.0",
    "Knowing your elasticity prevents expensive pricing mistakes. "
    "If you're elastic, raising prices kills revenue. If you're inelastic, you're leaving money on the table by not raising them.",
    color="#8a2be2",
)

concept_card(
    "Buyer-to-Seller Ratio (Liquidity)",
    "The balance between demand and supply on a marketplace platform",
    "B:S Ratio = Active Buyers / Active Sellers",
    "10,000 active buyers, 500 active sellers → B:S = **20:1**\n\n"
    "Higher ratio = sellers make more sales (good for retention) but buyers have less choice.\n"
    "Lower ratio = buyers have great selection but sellers starve (churn risk).\n\n"
    "The sweet spot depends on your category — 8:1 for niche, 20–40:1 for broad markets.",
    "**Services marketplaces:** 3–8:1\n**Ecom marketplaces:** 15–30:1\n"
    "**Uber-style:** 2–5:1 (supply-constrained)",
    "Liquidity is the *health metric of a two-sided marketplace*. "
    "If the ratio is too low, sellers leave → less selection → buyers leave → death spiral. "
    "If it's too high, buyer experience degrades and you need more supply.",
    color="#f43f5e",
)

concept_card(
    "Seller Concentration / Pareto Analysis",
    "How dependent is your GMV on a small number of top sellers?",
    "Plot cumulative % of GMV against seller rank percentile.\n"
    "The 80/20 rule: do 20% of sellers generate 80% of GMV?",
    "You rank 500 sellers by GMV.\n"
    "Top 100 (20%) generate $1.8M of your $2.5M GMV = **72%**.\n\n"
    "A Pareto curve that bows sharply (top 10% = 60%+) means you have \"whale\" dependency. "
    "If even one or two top sellers leave, your GMV takes a serious hit.",
    "**Healthy:** Top 20% = 50–65% of GMV (some concentration, but diversified)\n\n"
    "**Risky:** Top 20% > 80% of GMV (whale dependency)\n\n"
    "**Super concentrated:** Top 5% > 50% of GMV (one bad day away from crisis)",
    "Concentration risk is an existential marketplace threat. "
    "If your top 10 sellers represent 40% of GMV, you're effectively running a B2B business with 10 clients, "
    "not a marketplace with 500 sellers.",
    color="#f43f5e",
)

concept_card(
    "Commission Tiers",
    "Charging different commission rates based on seller volume to incentivize growth",
    "Example tier structure:\n"
    "  Standard:   < $10K/mo GMV  → 18% commission\n"
    "  Silver:   $10K–$50K/mo     → 15% commission\n"
    "  Gold:     $50K–$200K/mo    → 12% commission\n"
    "  Platinum: > $200K/mo       → 10% commission",
    "A seller doing $80K/mo at the Gold tier pays 12% = $9,600/mo.\n"
    "Same seller at the Standard tier would pay 18% = $14,400/mo.\n\n"
    "You give up $4,800/mo in commission, but the lower rate keeps the seller locked in "
    "and growing. Meanwhile, attracting large sellers improves selection for buyers.",
    "Tiered structures are used by Etsy, Amazon, eBay, and most sophisticated marketplaces.\n\n"
    "The key is that total revenue often *increases* because volume gains outpace rate reductions.",
    "Tiers align seller incentives with platform growth. "
    "Without them, top sellers eventually build their own DTC channel to avoid your commission.",
    color="#f43f5e",
)

concept_card(
    "Buyer vs. Seller Fee Split",
    "How marketplace fees are divided between the buyer and seller sides of the transaction",
    "Total Fee = Take Rate × Order Value\n"
    "Seller Pays = Total Fee × (1 - Buyer Fee Split %)\n"
    "Buyer Pays = Total Fee × Buyer Fee Split %",
    "Take rate = 15%, Order = $100, Buyer Fee Split = 40%\n"
    "Total fee = $15\n"
    "Seller pays = $15 × 60% = **$9.00** (embedded in their listing pricing)\n"
    "Buyer pays = $15 × 40% = **$6.00** (shown as service/delivery fee)\n\n"
    "Shifting more to the buyer side makes seller economics more attractive (easier to recruit sellers). "
    "But too much buyer-side fee = sticker shock at checkout = abandoned carts.",
    "**Uber:** ~75% buyer-side (service fees + surge)\n"
    "**Etsy:** ~85% seller-side\n"
    "**DoorDash:** ~60% buyer-side",
    "The split is a strategic lever. Early-stage marketplaces that need supply (sellers) "
    "should lean buyer-heavy. Mature marketplaces with strong buyer demand can lean seller-heavy.",
    color="#f43f5e",
)


# ══════════════════════════════════════════════════════════════
#  SECTION 6: PUTTING IT ALL TOGETHER
# ══════════════════════════════════════════════════════════════

concept_section(
    "SECTION 06 // THE CAUSAL CHAIN — HOW EVERYTHING CONNECTS",
    "churnOS isn't a collection of dashboards — it's a single causal model where every input propagates to every output.",
    "#14b8a6",
)

st.markdown(
    """
    <div class="techno-card" style="border-top: 2px solid #14b8a6; padding: 2rem;">
        <h3 style="color: #14b8a6; margin-top: 0;">The Causal Chain</h3>
        <p style="font-size: 0.92rem; line-height: 1.8; margin-bottom: 1.5rem;">
            Every metric in churnOS is connected. Here's the flow:
        </p>
        <div style="font-family: 'JetBrains Mono'; font-size: 0.8rem; line-height: 2.2; color: #f8fafc;">
            <span style="color: #ff9d00;">ACQUISITION</span>
            &nbsp;&nbsp;→ CAC (Paid + Organic mix)
            <br>
            <span style="color: #ff9d00;">MONETIZATION</span>
            &nbsp;&nbsp;→ AOV × Frequency → Gross Rev → minus COGS, Shipping, Refunds, Discounts → 
            <span style="color: #14b8a6;">Net Margin/Order</span>
            <br>
            <span style="color: #ff9d00;">RETENTION</span>
            &nbsp;&nbsp;→ Base Churn × Segment Multipliers × Subscribe&Save → 
            <span style="color: #14b8a6;">Effective Churn</span>
            &nbsp;→ Survival Curve
            <br>
            <span style="color: #ff9d00;">LIFETIME VALUE</span>
            &nbsp;&nbsp;→ Integrate Margin × Survival Curve over 24 months → 
            <span style="color: #14b8a6;">CLV</span>
            <br>
            <span style="color: #ff9d00;">EFFICIENCY</span>
            &nbsp;&nbsp;→ CLV / CAC = 
            <span style="color: #14b8a6;">LTV:CAC Ratio</span>
            &nbsp;&nbsp;|&nbsp;&nbsp; When CLV &gt; CAC → 
            <span style="color: #14b8a6;">Payback Month</span>
            <br>
            <span style="color: #ff9d00;">SENSITIVITY</span>
            &nbsp;&nbsp;→ Perturb each input ±10% → Rank by impact → 
            <span style="color: #14b8a6;">Focus Areas</span>
        </div>
        <p style="font-size: 0.85rem; margin-top: 1.5rem; color: #94a3b8;">
            <strong>The power of the causal model:</strong> When you change churn rate on the Business Model page, 
            it automatically recalculates the survival curve, which recalculates CLV, which changes LTV:CAC, 
            which changes the payback month, which changes the health score — everywhere, on every page.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="techno-card" style="border-top: 2px solid #8a2be2; padding: 2rem; margin-top: 1rem;">
        <h3 style="color: #8a2be2; margin-top: 0;">Where to Start</h3>
        <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                <td style="padding: 12px 8px; color: #ff9d00; font-family: 'JetBrains Mono'; width: 30%;">
                    I'm a NEW OPERATOR
                </td>
                <td style="padding: 12px 8px;">
                    Go to <strong>Business Model</strong> → pick your archetype → hit Run → 
                    check <strong>Executive Summary</strong> for your health score. 
                    If it's below 40, focus on retention first.
                </td>
            </tr>
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                <td style="padding: 12px 8px; color: #00f2ff; font-family: 'JetBrains Mono';">
                    I WANT TO GROW FASTER
                </td>
                <td style="padding: 12px 8px;">
                    Check the <strong>Sensitivity Analysis</strong> on the Executive Summary — 
                    it tells you exactly which lever gives you the most CLV bang per buck. 
                    Then check your <strong>CAC Ceiling</strong> in Unit Economics to see how much headroom you have to scale.
                </td>
            </tr>
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                <td style="padding: 12px 8px; color: #14b8a6; font-family: 'JetBrains Mono';">
                    RETENTION IS MY PROBLEM
                </td>
                <td style="padding: 12px 8px;">
                    Go to <strong>Retention & Churn</strong> → use the What-If sliders to model Subscribe & Save 
                    and reactivation improvements. Look at the <strong>Segment Comparison</strong> tab — 
                    your worst-performing segment is where to focus.
                </td>
            </tr>
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                <td style="padding: 12px 8px; color: #f43f5e; font-family: 'JetBrains Mono';">
                    I RUN A MARKETPLACE
                </td>
                <td style="padding: 12px 8px;">
                    Set your business type to <strong>Marketplace</strong> in the Business Model, then explore the 
                    <strong>Marketplace</strong> page for take rate, elasticity, and concentration risk. 
                    Watch your <strong>Buyer:Seller ratio</strong> — it's your liquidity pulse.
                </td>
            </tr>
            <tr>
                <td style="padding: 12px 8px; color: #8a2be2; font-family: 'JetBrains Mono';">
                    MY FUNNEL LEAKS
                </td>
                <td style="padding: 12px 8px;">
                    <strong>Conversion & Funnel</strong> → identify the biggest drop-off step → 
                    use the CVR → CLV Impact calculator to put a dollar value on fixing it. 
                    Run A/B tests and use the significance calculator before shipping.
                </td>
            </tr>
        </table>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Footer ──
st.markdown("---")
st.markdown(
    """
    <div style="text-align:center; padding: 1rem; font-family: 'JetBrains Mono'; font-size: 0.7rem; color: #475569;">
        // CONCEPTS v2.0 // LAST UPDATED: APRIL 2026 // churnOS KNOWLEDGE ENGINE
    </div>
    """,
    unsafe_allow_html=True,
)
