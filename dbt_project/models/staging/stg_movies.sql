-- US-04 : staging movies — extraction de l'année, split des genres
with source as (
    select * from {{ source('raw', 'movies') }}
),

cleaned as (
    select
        cast(movie_id as integer)                                   as movie_id,
        trim(regexp_replace(title, '\(\d{4}\)', ''))                as title,
        cast(regexp_extract(title, '\((\d{4})\)', 1) as integer)    as release_year,
        genres
    from source
    where movie_id is not null
)

select * from cleaned
