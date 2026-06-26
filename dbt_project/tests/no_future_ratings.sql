-- Test singulier : aucune note ne doit avoir une date dans le futur
select *
from {{ ref('fact_ratings') }}
where rated_at > current_timestamp
