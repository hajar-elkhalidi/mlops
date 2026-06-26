-- Mart analytique (Data Analysts) : popularité et note moyenne par genre
with dim_movies as (
    select * from {{ ref('dim_movies') }}
),

fact_ratings as (
    select * from {{ ref('fact_ratings') }}
),

exploded as (
    select
        f.movie_id,
        f.rating,
        unnest(m.genres_list) as genre
    from fact_ratings f
    inner join dim_movies m on f.movie_id = m.movie_id
),

final as (
    select
        genre,
        count(*)               as nb_ratings,
        round(avg(rating), 2)  as avg_rating,
        count(distinct movie_id) as nb_movies
    from exploded
    where genre is not null and genre != '(no genres listed)'
    group by genre
    order by nb_ratings desc
)

select * from final
