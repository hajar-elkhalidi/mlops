{#
    Surcharge du comportement par défaut de dbt qui préfixe les schémas custom
    par le schéma du target (ex: dev_marts). On veut des schémas stables
    (staging, marts) quel que soit le target (dev, ci), car le code Python
    en aval (ml/src, dagster checks, scripts) référence ces schémas par leur
    nom exact.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
