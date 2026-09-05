-- Staging: clean, well-typed transactions, one row per raw record.
select
    transaction_id,
    user_id,
    cast(amount as float64)              as amount,
    currency,
    cast(timestamp as timestamp)         as transaction_ts,
    country,
    ip_address,
    device_id,
    merchant,
    merchant_category,
    payment_method,
    cast(is_fraud as int64)              as is_fraud,
    cast(_ingested_at as timestamp)      as ingested_at
from {{ source('fraud', 'raw_transactions') }}