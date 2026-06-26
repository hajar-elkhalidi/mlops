-- Test singulier : aucun utilisateur ne doit avoir noté le même film deux fois
-- au même timestamp (détection de doublons résiduels après merge dlt)
select
    user_id,
    movie_id,
    rated_at,
    count(*) as nb_duplicates
from {{ ref('fact_ratings') }}
group by user_id, movie_id, rated_at
having count(*) > 1
