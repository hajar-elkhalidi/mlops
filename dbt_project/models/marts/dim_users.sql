-- dimension utilisateurs — métadonnées démographiques (ml-100k) + agrégats comportementaux
with users as (
    select * from {{ ref('stg_users') }}
),

ratings as (
    select * from {{ ref('stg_ratings') }}
),

ratings_agg as (
    select
        user_id,
        count(*)              as nb_ratings,
        round(avg(rating), 2)  as avg_rating,
        min(rated_at)          as first_rating_at,
        max(rated_at)          as last_rating_at
    from ratings
    group by user_id
),

final as (
    select
        u.user_id,
        u.age,
        u.sex,
        u.occupation,
        u.zip_code,
        coalesce(r.nb_ratings, 0)  as nb_ratings,
        r.avg_rating,
        r.first_rating_at,
        r.last_rating_at
    from users u
    left join ratings_agg r on u.user_id = r.user_id
)

select * from final
