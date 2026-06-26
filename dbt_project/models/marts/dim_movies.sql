-- dimension films — enrichie avec genres en tableau (ml-100k : pas d'IDs IMDb/TMDb)
with movies as (
    select * from {{ ref('stg_movies') }}
),

final as (
    select
        movie_id,
        title,
        release_year,
        genres,
        string_split(genres, '|') as genres_list
    from movies
)

select * from final
