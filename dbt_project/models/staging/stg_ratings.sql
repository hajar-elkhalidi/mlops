-- staging ratings — nettoyage, typage, renommage (ml-100k : notes entières 1-5)
with source as (
    select * from {{ source('raw', 'ratings') }}
),

cleaned as (
    select
        cast(user_id as integer)     as user_id,
        cast(movie_id as integer)    as movie_id,
        cast(rating as integer)      as rating,
        cast(timestamp as timestamp) as rated_at
    from source
    where rating is not null
)

select * from cleaned
