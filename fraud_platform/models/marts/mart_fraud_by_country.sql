-- Mart: fraud summary per country, ready for dashboards.
select
    country,
    count(*)                                as total_transactions,
    sum(is_fraud)                           as fraud_transactions,
    round(sum(is_fraud) / count(*) * 100, 2) as fraud_rate_pct
from {{ ref('stg_transactions') }}
group by country
order by fraud_rate_pct desc