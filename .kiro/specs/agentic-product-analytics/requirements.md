# Requirements Document: Agentic Product Analytics

## Introduction

This document specifies requirements for implementing agentic product analytics and monitoring capabilities in churnOS. Agentic products face unique monetization and retention challenges that differ fundamentally from traditional SaaS: unpredictable multi-step costs, opaque activation patterns, low switching costs, catastrophic reliability failures, and non-deterministic success metrics. 

This feature integrates agentic-specific analytics into the existing churnOS Streamlit application, providing dashboard signals, metric calculations, feature flag experimentation infrastructure, and alerting capabilities specifically designed for agentic/LLM products. The implementation extends the existing START → DECIDE → LEARN navigation structure and maintains the terminal-style Bloomberg aesthetic.

## Glossary

- **Agentic_Health_Dashboard**: A composite view combining cost-per-outcome, activation funnel, integration depth, catastrophic events, and predicted churn risk
- **Cost_Per_Successful_Outcome**: Total token/tool/infrastructure cost attributed to a workflow divided by the number of runs that reach a verified successful end state
- **Power_User_Margin_Leakage**: Gross margin contribution of the top X% of users ranked by token volume, revealing margin destruction under flat pricing
- **Time_To_First_Value**: Median hours/days from first successful payment to the first verified successful agent outcome for an account
- **Paying_But_Dormant_Rate**: Percentage of currently paying accounts that have generated zero verified successful outcomes in the trailing 14 days
- **Integration_Depth_Score**: Composite score per account based on number of active integrations, data sync volume, agent memory persistence, and custom workflow count
- **Catastrophic_Event_Rate**: Number of agent actions that produce irreversible negative side-effects per 1,000 agent runs
- **Human_Intervention_Rate**: Percentage of agent runs that require human takeover or significant correction before completion
- **Verified_Outcome_Success_Rate**: Percentage of multi-step agent runs that reach a verified successful end state (not merely "completed without crash")
- **Context_Window_Utilization**: Average percentage of the model's maximum context window consumed at the end of each agent run
- **Retry_Amplification_Factor**: Average number of model/tool invocations per logical user intent, quantifying hidden multi-step cost explosion
- **Unattributed_Spend_Percentage**: Share of total token/API/infrastructure spend that cannot be mapped to a specific agent run, user, or workflow
- **Static_Decision_Age**: Days since a model-routing, temperature, or tool-selection rule was last evaluated or updated
- **Agent_Coordination_Overhead**: Percentage of total tokens in a multi-agent session spent on inter-agent communication rather than goal progress
- **Feature_Flag_System**: Infrastructure enabling controlled rollout of experiments with automatic instrumentation of cost, activation, reliability, and retention metrics
- **Alert_Threshold_Engine**: Component that evaluates metric thresholds and triggers warnings based on account value or historical baselines
- **Cost_Attribution_Heatmap**: Visual breakdown of daily/weekly spend by agent type, workflow step, model, and customer cohort
- **Activation_Funnel**: Sign-up → first paid invoice → first successful agent outcome progression with revenue overlay
- **User**: A person using the churnOS platform to monitor and optimize agentic product performance
- **Workspace**: The existing churnOS data container holding agentic tables (seats, runs, capabilities, outcomes, etc.)
- **Product_Profile**: The agentic product configuration defining ontology, billing model, and operational thresholds

## Requirements

### Requirement 1: Cost-Per-Successful-Outcome Metric Calculation

**User Story:** As a product manager for an agentic product, I want to track cost per successful outcome, so that I can detect retry loops, context bloat, and inefficient model routing before they destroy margins.

#### Acceptance Criteria

1. WHEN a User views the Agentic_Health_Dashboard, THE Agentic_Health_Dashboard SHALL display Cost_Per_Successful_Outcome calculated as total run cost divided by verified successful outcomes
2. THE Cost_Per_Successful_Outcome calculation SHALL include input tokens, output tokens, tool costs, and infrastructure overhead where available
3. WHEN the Workspace lacks verified outcomes, THE Agentic_Health_Dashboard SHALL display Cost_Per_Successful_Outcome as the cost per successful run as a fallback
4. THE Agentic_Health_Dashboard SHALL display Cost_Per_Successful_Outcome trend over trailing 7, 14, and 30 days
5. WHEN Cost_Per_Successful_Outcome exceeds 1.5 times the trailing 30-day median for a workflow, THE Alert_Threshold_Engine SHALL trigger a warning
6. THE Agentic_Health_Dashboard SHALL segment Cost_Per_Successful_Outcome by capability, agent type, and customer cohort
7. FOR ALL valid Workspace instances, calculating Cost_Per_Successful_Outcome twice with identical data SHALL produce identical results (idempotence property)

### Requirement 2: Power-User Margin Leakage Detection

**User Story:** As a product manager, I want to identify margin-negative power users, so that I can detect the classic pattern where high-volume users under flat pricing destroy contribution margins.

#### Acceptance Criteria

1. WHEN a User views the Agentic_Health_Dashboard, THE Agentic_Health_Dashboard SHALL display Power_User_Margin_Leakage for the top 5% of users by token volume
2. THE Power_User_Margin_Leakage calculation SHALL compute revenue minus fully-loaded token/tool/infrastructure cost for the cohort
3. THE Agentic_Health_Dashboard SHALL display Power_User_Margin_Leakage as both absolute dollar value and percentage of cohort revenue
4. WHEN Power_User_Margin_Leakage is negative, THE Alert_Threshold_Engine SHALL flag the condition as margin destruction risk
5. THE Agentic_Health_Dashboard SHALL allow configurable cohort percentage (default 5%, adjustable to 1%, 5%, 10%)
6. THE Agentic_Health_Dashboard SHALL display a panel showing the top 5 margin-negative seats with their cost and revenue details
7. WHEN the billing model is usage_based, THE Power_User_Margin_Leakage panel SHALL display a note that margin risk is reduced under usage pricing

### Requirement 3: Context Window Utilization Monitoring

**User Story:** As a product manager, I want to monitor context window utilization, so that I can correlate high context usage with rising costs and failure rates.

#### Acceptance Criteria

1. WHEN a User views the Run Economics page, THE Run Economics page SHALL display Context_Window_Utilization as average percentage of maximum context consumed
2. THE Context_Window_Utilization calculation SHALL use final prompt tokens divided by model max context from the Product_Profile
3. THE Run Economics page SHALL display a histogram distribution of Context_Window_Utilization across all runs
4. WHEN Context_Window_Utilization exceeds 70% for more than 20% of runs, THE Alert_Threshold_Engine SHALL display a warning about rising input costs and retry correlation
5. THE Run Economics page SHALL segment Context_Window_Utilization by capability and model type
6. WHEN the model max context is not specified in Product_Profile, THE Context_Window_Utilization calculation SHALL use a default of 128,000 tokens

### Requirement 4: Retry Amplification Factor Tracking

**User Story:** As a product manager, I want to track the retry amplification factor, so that I can quantify hidden multi-step cost explosion from retry loops.

#### Acceptance Criteria

1. WHEN a User views the Run Economics page, THE Run Economics page SHALL display Retry_Amplification_Factor as total model and tool calls divided by distinct user-initiated goals
2. THE Retry_Amplification_Factor SHALL be calculated per workflow type and displayed as a multiplier (e.g., 4.2×)
3. WHEN Retry_Amplification_Factor exceeds 5×, THE Alert_Threshold_Engine SHALL flag excessive retry behavior
4. THE Run Economics page SHALL display Retry_Amplification_Factor trend over trailing 7, 14, and 30 days
5. THE Run Economics page SHALL allow drill-down to view the distribution of retry counts per run
6. THE Retry_Amplification_Factor calculation SHALL handle cases where user goal attribution is unavailable by using run count as denominator

### Requirement 5: Time-To-First-Value Measurement

**User Story:** As a product manager, I want to measure time to first value, so that I can detect when the product forces excessive behavior change or lacks a clear win definition.

#### Acceptance Criteria

1. WHEN a User views the Activation & Habit page, THE Activation & Habit page SHALL display Time_To_First_Value as median hours/days from first payment to first verified successful outcome
2. THE Activation & Habit page SHALL display the Time_To_First_Value distribution as a histogram with p50, p75, and p90 percentiles
3. WHEN Time_To_First_Value median exceeds 7 days, THE Alert_Threshold_Engine SHALL flag potential activation barrier
4. THE Activation & Habit page SHALL segment Time_To_First_Value by customer cohort (signup week)
5. THE Time_To_First_Value calculation SHALL handle accounts without verified outcomes by excluding them from the median calculation
6. THE Activation & Habit page SHALL display the percentage of accounts that never achieve first value as a separate metric

### Requirement 6: Paying-But-Dormant Detection

**User Story:** As a product manager, I want to identify paying-but-dormant accounts, so that I can detect leading indicators of imminent churn that revenue metrics alone would miss.

#### Acceptance Criteria

1. WHEN a User views the Activation & Habit page, THE Activation & Habit page SHALL display Paying_But_Dormant_Rate as percentage of paying accounts with zero verified outcomes in trailing 14 days
2. THE Activation & Habit page SHALL list the top 10 paying-but-dormant accounts with their revenue and days since last outcome
3. WHEN Paying_But_Dormant_Rate exceeds 15%, THE Alert_Threshold_Engine SHALL flag elevated churn risk
4. THE Paying_But_Dormant_Rate calculation SHALL use verified outcomes, not just completed runs, as the success criterion
5. THE Activation & Habit page SHALL allow configurable trailing window (default 14 days, adjustable to 7, 14, 30 days)
6. THE Activation & Habit page SHALL display trend of Paying_But_Dormant_Rate over trailing 4 weeks

### Requirement 7: Activation Funnel With Revenue Overlay

**User Story:** As a product manager, I want to see the activation funnel with revenue overlay, so that I can quantify the gap between payment and first success (the activation-as-churn problem).

#### Acceptance Criteria

1. WHEN a User views the Activation & Habit page, THE Activation & Habit page SHALL display an Activation_Funnel showing sign-up → first paid invoice → first verified successful outcome
2. THE Activation_Funnel SHALL display revenue overlay showing total revenue at each stage
3. THE Activation_Funnel SHALL calculate and display the conversion rate between each stage
4. THE Activation_Funnel SHALL highlight the gap between paid accounts and first-success accounts as "activation gap"
5. WHEN the activation gap exceeds 20%, THE Alert_Threshold_Engine SHALL flag activation failure disguised as churn
6. THE Activation_Funnel SHALL be filterable by customer cohort and time period
7. THE Activation_Funnel SHALL display absolute counts and percentages at each stage

### Requirement 8: Integration Depth Score

**User Story:** As a product manager, I want to calculate an integration depth score per account, so that I can predict churn propensity based on lock-in strength.

#### Acceptance Criteria

1. WHEN a User views the Connectors page, THE Connectors page SHALL display Integration_Depth_Score for each account
2. THE Integration_Depth_Score calculation SHALL use weighted formula: 0.3 × integrations count + 0.3 × normalized data volume + 0.2 × memory days + 0.2 × custom workflows
3. THE Integration_Depth_Score SHALL be normalized to a 0-100 scale
4. THE Connectors page SHALL display Integration_Depth_Score distribution across all accounts
5. WHEN Integration_Depth_Score is below 20 for an account, THE Alert_Threshold_Engine SHALL flag high churn propensity
6. THE Connectors page SHALL display the correlation between Integration_Depth_Score and retention/churn rates
7. THE Integration_Depth_Score SHALL be recalculated when connector events or workflows change

### Requirement 9: Catastrophic Event Rate Monitoring

**User Story:** As a product manager, I want to track catastrophic event rate, so that I can monitor agent actions that cause irreversible harm and drive permanent churn.

#### Acceptance Criteria

1. WHEN a User views the Trust & Approval page, THE Trust & Approval page SHALL display Catastrophic_Event_Rate as events per 1,000 agent runs
2. THE Catastrophic_Event_Rate calculation SHALL count agent actions flagged as producing irreversible negative side-effects
3. THE Trust & Approval page SHALL display a Catastrophic_Event_Log with timestamp, event type, account impact, and churn outcome
4. WHEN Catastrophic_Event_Rate exceeds 0.1 events per 1,000 runs, THE Alert_Threshold_Engine SHALL trigger a critical warning
5. THE Trust & Approval page SHALL display the correlation between catastrophic events and subsequent churn
6. THE Catastrophic_Event_Log SHALL be filterable by event type, severity, and time period
7. THE Trust & Approval page SHALL display trend of Catastrophic_Event_Rate over trailing 30 days

### Requirement 10: Human Intervention Rate Tracking

**User Story:** As a product manager, I want to track human intervention rate, so that I can detect declining reliability or increasing task complexity beyond agent capability.

#### Acceptance Criteria

1. WHEN a User views the Trust & Approval page, THE Trust & Approval page SHALL display Human_Intervention_Rate as percentage of runs requiring human takeover
2. THE Human_Intervention_Rate calculation SHALL count runs with significant human correction before completion
3. THE Trust & Approval page SHALL display Human_Intervention_Rate trend over trailing 7, 14, and 30 days
4. WHEN Human_Intervention_Rate increases by more than 20% week-over-week, THE Alert_Threshold_Engine SHALL flag reliability erosion
5. THE Trust & Approval page SHALL segment Human_Intervention_Rate by capability and workflow type
6. THE Trust & Approval page SHALL display the relationship between Human_Intervention_Rate and task complexity metrics
7. THE Human_Intervention_Rate calculation SHALL distinguish between approval-based interventions and error-based interventions

### Requirement 11: Verified Outcome Success Rate

**User Story:** As a product manager, I want to track verified outcome success rate, so that I can measure the gap between "completed without crash" and true value delivery.

#### Acceptance Criteria

1. WHEN a User views the Run Economics page, THE Run Economics page SHALL display Verified_Outcome_Success_Rate as percentage of runs reaching verified successful end state
2. THE Verified_Outcome_Success_Rate calculation SHALL use verification flags from outcomes data, not just run completion status
3. THE Run Economics page SHALL display the gap between run completion rate and Verified_Outcome_Success_Rate
4. WHEN Verified_Outcome_Success_Rate is below 70%, THE Alert_Threshold_Engine SHALL flag potential value delivery problem
5. THE Run Economics page SHALL segment Verified_Outcome_Success_Rate by workflow complexity (number of steps, tool calls)
6. THE Verified_Outcome_Success_Rate calculation SHALL support multiple verification methods (automated checkers, human review, downstream system confirmation)
7. THE Run Economics page SHALL display trend of Verified_Outcome_Success_Rate over trailing 30 days

### Requirement 12: Cost Attribution Heatmap Visualization

**User Story:** As a product manager, I want to see a cost attribution heatmap, so that I can identify which agent types, workflow steps, and models drive cost spikes.

#### Acceptance Criteria

1. WHEN a User views the Agentic_Health_Dashboard, THE Agentic_Health_Dashboard SHALL display a Cost_Attribution_Heatmap showing spend by agent type, workflow step, model, and cohort
2. THE Cost_Attribution_Heatmap SHALL highlight cells where cost exceeds expected threshold by more than 5×
3. THE Cost_Attribution_Heatmap SHALL support drill-down from any cell to view individual runs
4. THE Cost_Attribution_Heatmap SHALL be filterable by time period (daily, weekly, monthly)
5. THE Cost_Attribution_Heatmap SHALL use color intensity to indicate relative cost magnitude
6. THE Cost_Attribution_Heatmap SHALL display both absolute cost and percentage of total spend for each cell
7. WHEN a cell represents retry or verification steps, THE Cost_Attribution_Heatmap SHALL visually distinguish waste from productive work

### Requirement 13: Unattributed Spend Monitoring

**User Story:** As a product manager, I want to track unattributed spend percentage, so that I can detect missing instrumentation and infrastructure blind spots.

#### Acceptance Criteria

1. WHEN a User views the Agentic_Health_Dashboard, THE Agentic_Health_Dashboard SHALL display Unattributed_Spend_Percentage as share of total spend without complete attribution
2. THE Unattributed_Spend_Percentage calculation SHALL identify spend lacking agent run, user, workflow, or customer attribution
3. WHEN Unattributed_Spend_Percentage exceeds 10%, THE Alert_Threshold_Engine SHALL flag instrumentation gap
4. THE Agentic_Health_Dashboard SHALL display trend of Unattributed_Spend_Percentage over trailing 30 days
5. THE Agentic_Health_Dashboard SHALL provide recommendations for reducing Unattributed_Spend_Percentage
6. THE Unattributed_Spend_Percentage target SHALL be configurable (default <10%, target <5%)
7. THE Agentic_Health_Dashboard SHALL display the breakdown of missing attribution types (missing run, missing user, missing workflow)

### Requirement 14: Static Decision Age Monitoring

**User Story:** As a product manager, I want to track static decision age, so that I can identify frozen routing/model choices that no longer reflect current pricing and capabilities.

#### Acceptance Criteria

1. WHEN a User views the Run Economics page, THE Run Economics page SHALL display Static_Decision_Age as days since last routing/model rule update
2. THE Static_Decision_Age calculation SHALL track model-routing, temperature, and tool-selection rule ages
3. WHEN Static_Decision_Age exceeds 90 days, THE Alert_Threshold_Engine SHALL flag decision staleness
4. THE Run Economics page SHALL display current vs. original cost/performance for aged decisions
5. THE Run Economics page SHALL provide recommendations for revisiting static decisions based on model price changes
6. THE Static_Decision_Age SHALL be tracked per decision type and displayed as a summary metric
7. THE Run Economics page SHALL display the number of static decisions exceeding the staleness threshold

### Requirement 15: Agent Coordination Overhead Measurement

**User Story:** As a product manager, I want to measure agent coordination overhead, so that I can detect context pollution and inefficient multi-agent designs.

#### Acceptance Criteria

1. WHEN a User views the Agentic_Health_Dashboard, THE Agentic_Health_Dashboard SHALL display Agent_Coordination_Overhead as percentage of tokens spent on inter-agent communication
2. THE Agent_Coordination_Overhead calculation SHALL distinguish coordination messages from goal-progress messages
3. WHEN Agent_Coordination_Overhead exceeds 30%, THE Alert_Threshold_Engine SHALL flag inefficient multi-agent design
4. THE Agentic_Health_Dashboard SHALL segment Agent_Coordination_Overhead by multi-agent workflow type
5. THE Agentic_Health_Dashboard SHALL display trend of Agent_Coordination_Overhead over trailing 30 days
6. THE Agent_Coordination_Overhead calculation SHALL handle single-agent workflows by displaying zero overhead
7. THE Agentic_Health_Dashboard SHALL provide drill-down to view coordination overhead per multi-agent session

### Requirement 16: Feature Flag Experimentation Infrastructure

**User Story:** As a product manager, I want to run feature flag experiments with automatic instrumentation, so that I can measure cost, activation, reliability, and retention effects for every rollout.

#### Acceptance Criteria

1. WHEN a User creates a feature flag experiment, THE Feature_Flag_System SHALL automatically instrument Cost_Per_Successful_Outcome for treatment and control groups
2. THE Feature_Flag_System SHALL automatically instrument activation metrics (Time_To_First_Value, Paying_But_Dormant_Rate) for treatment and control groups
3. THE Feature_Flag_System SHALL automatically instrument reliability metrics (Human_Intervention_Rate, Catastrophic_Event_Rate) for treatment and control groups
4. THE Feature_Flag_System SHALL display experiment results with statistical significance indicators
5. WHEN an experiment shows negative impact on any instrumented metric, THE Feature_Flag_System SHALL highlight the tradeoff
6. THE Feature_Flag_System SHALL support gradual rollout with automatic metric comparison at each step
7. THE Feature_Flag_System SHALL store experiment configurations and results for retrospective analysis
8. THE Feature_Flag_System SHALL integrate with existing experiment_assignments, experiment_exposures, and experiment_outcomes tables in the Workspace

### Requirement 17: Alert Threshold Configuration

**User Story:** As a product manager, I want to configure alert thresholds based on account value or historical baselines, so that I can receive meaningful alerts rather than noise.

#### Acceptance Criteria

1. WHEN a User configures an alert threshold, THE Alert_Threshold_Engine SHALL allow thresholds based on absolute values, percentage change, or standard deviation from baseline
2. THE Alert_Threshold_Engine SHALL support thresholds relative to trailing 7, 14, or 30-day historical baselines
3. THE Alert_Threshold_Engine SHALL allow thresholds scaled by account value (e.g., higher sensitivity for high-value accounts)
4. WHEN an alert threshold is triggered, THE Alert_Threshold_Engine SHALL display the triggering metric, threshold, and current value
5. THE Alert_Threshold_Engine SHALL support both warning and critical severity levels
6. THE Alert_Threshold_Engine SHALL allow suppression rules for known acceptable deviations
7. THE Alert_Threshold_Engine SHALL store alert history for trend analysis

### Requirement 18: Agentic Health Composite Dashboard

**User Story:** As a product manager, I want a single agentic health dashboard combining all key metrics, so that I can quickly assess overall product health without navigating multiple pages.

#### Acceptance Criteria

1. WHEN a User navigates to the Agentic_Health_Dashboard, THE Agentic_Health_Dashboard SHALL display a composite health score combining cost, activation, reliability, and retention signals
2. THE Agentic_Health_Dashboard SHALL color-code accounts as red/yellow/green based on composite score
3. THE Agentic_Health_Dashboard SHALL display key metrics summary: Cost_Per_Successful_Outcome, Time_To_First_Value, Integration_Depth_Score, Catastrophic_Event_Rate
4. THE Agentic_Health_Dashboard SHALL display alerts requiring immediate attention at the top
5. THE Agentic_Health_Dashboard SHALL provide navigation to detailed views for each metric category
6. THE Agentic_Health_Dashboard SHALL display predictive churn risk scores for accounts with declining health
7. THE Agentic_Health_Dashboard SHALL maintain the existing terminal-style Bloomberg aesthetic of churnOS

### Requirement 19: Predictive Retention Feature Importance

**User Story:** As a product manager, I want to understand which early behavioral signals predict retention, so that I can focus on metrics that matter rather than traditional SaaS proxies.

#### Acceptance Criteria

1. WHEN a User views the Agentic_Health_Dashboard, THE Agentic_Health_Dashboard SHALL display Predictive_Retention_Feature_Importance showing relative importance of behavioral signals
2. THE Predictive_Retention_Feature_Importance SHALL include features: successful first outcome within 7 days, integration depth score, low retry rate, human-review acceptance rate
3. THE Agentic_Health_Dashboard SHALL compare Predictive_Retention_Feature_Importance against traditional SaaS metrics (logins, feature clicks) to show which have lost predictive power
4. THE Predictive_Retention_Feature_Importance calculation SHALL use SHAP values or equivalent interpretability method
5. THE Agentic_Health_Dashboard SHALL display changes in feature importance over time as the product evolves
6. THE Predictive_Retention_Feature_Importance SHALL be recalculated when new retention outcome data is available
7. THE Agentic_Health_Dashboard SHALL provide recommendations for focusing on high-importance features

### Requirement 20: High-LTV Activation Path Analysis

**User Story:** As a product manager, I want to identify activation paths that produce high-LTV cohorts, so that I can guide new users toward sequences that lead to retention.

#### Acceptance Criteria

1. WHEN a User views the Activation & Habit page, THE Activation & Habit page SHALL display High_LTV_Activation_Path_Share as percentage of new accounts following successful early sequences
2. THE Activation & Habit page SHALL identify and display the top 3 activation paths correlated with high lifetime value
3. THE Activation & Habit page SHALL compare High_LTV_Activation_Path_Share to overall activation rate to show the gap
4. WHEN High_LTV_Activation_Path_Share is below 30%, THE Alert_Threshold_Engine SHALL flag that most users are on low-value paths
5. THE Activation & Habit page SHALL display the characteristics that define high-LTV activation paths
6. THE Activation & Habit page SHALL provide recommendations for nudging users toward high-LTV paths
7. THE High_LTV_Activation_Path_Share calculation SHALL be updated as new cohort data becomes available

### Requirement 21: Post-Failure Trust Drop Measurement

**User Story:** As a product manager, I want to measure trust score drops after agent failures, so that I can quantify the retention impact of reliability shocks.

#### Acceptance Criteria

1. WHEN a User views the Trust & Approval page, THE Trust & Approval page SHALL display Post_Failure_Trust_Drop as change in satisfaction metrics 7-14 days after a visible failure
2. THE Post_Failure_Trust_Drop calculation SHALL use available satisfaction metrics (NPS, CSAT, expansion intent) from the Product_Profile
3. THE Trust & Approval page SHALL segment Post_Failure_Trust_Drop by failure type and severity
4. WHEN Post_Failure_Trust_Drop exceeds 10 points, THE Alert_Threshold_Engine SHALL flag significant trust erosion
5. THE Trust & Approval page SHALL display the correlation between Post_Failure_Trust_Drop and subsequent churn
6. THE Post_Failure_Trust_Drop calculation SHALL handle accounts without satisfaction data by displaying a data gap indicator
7. THE Trust & Approval page SHALL display trend of Post_Failure_Trust_Drop over trailing 90 days

### Requirement 22: Integration With Existing Decision Records

**User Story:** As a product manager, I want agentic analytics to integrate with existing decision records, so that I can take action on detected issues through the existing decision workflow.

#### Acceptance Criteria

1. WHEN a metric crosses a critical threshold, THE Alert_Threshold_Engine SHALL create a decision record in the existing decision card format
2. THE decision records for agentic metrics SHALL include the same fields as existing records: record_id, category, exception, economics, verdict, action
3. THE decision records SHALL appear in the existing Radar page alongside other capability and account decisions
4. THE decision records SHALL support the existing override workflow for manual intervention
5. THE decision records SHALL use existing ontology semantics for category classification
6. THE decision records SHALL integrate with existing decision card rendering in the UI
7. THE Alert_Threshold_Engine SHALL create decision records only for metrics exceeding critical thresholds, not warnings

### Requirement 23: Product Profile Extension For Agentic Thresholds

**User Story:** As a product manager, I want to configure agentic-specific thresholds in the product profile, so that alerts and recommendations reflect my product's specific characteristics.

#### Acceptance Criteria

1. WHEN a User views the Product Profile page, THE Product Profile page SHALL display agentic-specific configuration options
2. THE Product Profile page SHALL allow configuration of context window size (default 128,000 tokens)
3. THE Product Profile page SHALL allow configuration of max loops threshold (default 8)
4. THE Product Profile page SHALL allow configuration of retry amplification threshold (default 5×)
5. THE Product Profile page SHALL allow configuration of Time_To_First_Value threshold (default 7 days)
6. THE Product Profile page SHALL allow configuration of Integration_Depth_Score thresholds for churn prediction
7. THE Product Profile page SHALL persist agentic thresholds to the existing profile dictionary in session state
8. THE Product Profile page SHALL apply agentic thresholds to all metric calculations and alert conditions

### Requirement 24: Backward Compatibility With Existing Pages

**User Story:** As a product manager, I want existing pages to continue working, so that I don't lose access to current functionality when agentic analytics are added.

#### Acceptance Criteria

1. WHEN agentic analytics are deployed, THE existing Activation & Habit page SHALL continue to display its current metrics
2. WHEN agentic analytics are deployed, THE existing Run Economics page SHALL continue to display its current metrics
3. WHEN agentic analytics are deployed, THE existing Trust & Approval page SHALL continue to display its current metrics
4. WHEN agentic analytics are deployed, THE existing Connectors page SHALL continue to display its current metrics
5. THE agentic analytics additions SHALL be additive (new sections) rather than replacement of existing content
6. THE existing navigation structure (START → DECIDE → LEARN) SHALL be preserved
7. THE existing terminal-style Bloomberg aesthetic SHALL be maintained across all new components
8. WHEN the Workspace lacks agentic-specific data, THE pages SHALL gracefully degrade to existing functionality

### Requirement 25: Cost Waterfall Visualization Enhancement

**User Story:** As a product manager, I want an enhanced cost waterfall visualization, so that I can understand the breakdown of costs from input tokens to final outcome.

#### Acceptance Criteria

1. WHEN a User views the Run Economics page, THE Run Economics page SHALL display an enhanced cost waterfall showing input tokens, output tokens, tool costs, retry overhead, and verification costs
2. THE cost waterfall SHALL distinguish productive costs from waste costs using color coding
3. THE cost waterfall SHALL allow drill-down from any segment to view individual runs
4. THE cost waterfall SHALL be filterable by capability, time period, and success status
5. THE cost waterfall SHALL display both absolute cost and percentage of total
6. THE cost waterfall SHALL integrate with existing cost_waterfall_sample visualization where available
7. WHEN the enhanced waterfall is not available, THE Run Economics page SHALL display the existing waterfall as fallback
