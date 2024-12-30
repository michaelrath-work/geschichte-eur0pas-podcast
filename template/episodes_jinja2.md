<a href="https://geschichteeuropas.podigee.io/">
<img src="https://main.podigee-cdn.net/uploads/u10696/804bb26c-c59e-496d-b961-c2531f60dd76.jpg" alt="https://main.podigee-cdn.net/uploads/u10696/804bb26c-c59e-496d-b961-c2531f60dd76.jpg" width="200">
</a>

[![Geschichte Eur0pas Podcast](https://img.shields.io/static/v1?label=Tobias%20Jakobi&message=geschichteeuropas.podigee.io&color=orange&logo=podcast%20index)](https://geschichteeuropas.podigee.io/

<a id="top"></a>

# Geschichte Eur0pas

<a id="categories"></a>

## Categories

| id  | curated name | #episodes | organic name(s) |
|-----|:-------------|----------:|-----------------|
{% for category in categories -%}
| {{ category.marker }} | [{{category.marker}}: {{category.curated_name}}](#{{category.html_anchor_name()}}) | {{ category.episodes|length }} | {{ '<br>'.join(category.organic_names) }} |
{% endfor %}


## Episodes per category

{% for category in categories %}

<a id="{{ category.html_anchor_name() }}"></a>
### {{ category.marker}}: {{ category.curated_name }}
[top](#top)

[![{{category.marker}}](https://img.shields.io/static/v1?label=Tobias%20Jakobi&message={{category.curated_name.replace(' ', '%20')}}&color=orange&logo=podcast%20index)](rss/{{category.marker.lower()}}.xml)

{% if category.organic_names|length >= 1 %}
Organic category names
{% for n in category.organic_names|sort() -%}
- {{ n }}
{% endfor %}
{% endif %}

{% if category.episodes|length > 0 %}
|title |episode | duration | publication | keywords | linked episodes |
|:-----|-------:|---------:|------------:|:-------- |:----------------|
{% for e in category.episodes -%}
| {{ e.html_link() }} | {{ "%00d"|format(e.number) }} | {{ e.duration_str }} | {{ e.publication_str }} | {{ ', '.join(e.keywords) }} | {{ e.linked_episodes_html() }} |
{% endfor %}
{% endif %}

{% endfor %}