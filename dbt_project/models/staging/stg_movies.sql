-- staging movies — extraction de l'année, split des genres (ml-100k : u.item)
with source as (
    select * from {{ source('raw', 'movies') }}
),

cleaned as (
    select
        cast(movie_id as integer) as movie_id,
        trim(regexp_replace(title, '\(\d{4}\)', '')) as title,
        -- NULLIF gère les titres sans année entre parenthèses (ex: "Unknown"),
        -- où regexp_extract renvoie '' (chaîne vide) plutôt que NULL dans DuckDB ;
        -- caster '' directement en INTEGER lève une erreur de conversion.
        cast(nullif(regexp_extract(title, '\((\d{4})\)', 1), '') as integer) as release_year,
        genres
    from source
    where movie_id is not null
)

select * from cleaned
