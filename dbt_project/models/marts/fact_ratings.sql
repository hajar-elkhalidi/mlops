-- US-05 : table de faits — grain = 1 ligne par (user, movie, rating)
with ratings as (
    select * from {{ ref('stg_ratings') }}
),

movies as (
    select movie_id from {{ ref('dim_movies') }}
),

users as (
    select user_id from {{ ref('dim_users') }}
),

final as (
    select
        r.user_id,
        r.movie_id,
        r.rating,
        r.rated_at
    from ratings r
    inner join movies m on r.movie_id = m.movie_id
    inner join users u on r.user_id = u.user_id
)

select * from final
