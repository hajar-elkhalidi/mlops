-- staging users — nettoyage des métadonnées démographiques (ml-100k : u.user)
with source as (
    select * from {{ source('raw', 'users') }}
),

cleaned as (
    select
        cast(user_id as integer) as user_id,
        cast(age as integer)     as age,
        upper(trim(sex))         as sex,
        lower(trim(occupation))  as occupation,
        zip_code
    from source
    where user_id is not null
)

select * from cleaned
