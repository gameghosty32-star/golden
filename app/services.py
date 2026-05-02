from flask import url_for
from sqlalchemy import or_
from .models import Provincia, Municipio, Bairro, Rua


def build_search_pattern(query):
    return f'%{query}%'


def query_feed():
    return {
        'provincias': Provincia.query.order_by(Provincia.created_at.desc()).limit(4).all(),
        'municipios': Municipio.query.order_by(Municipio.created_at.desc()).limit(4).all(),
        'bairros': Bairro.query.order_by(Bairro.created_at.desc()).limit(4).all(),
        'ruas': Rua.query.order_by(Rua.created_at.desc()).limit(4).all(),
    }


def get_counts():
    return {
        'provincias': Provincia.query.count(),
        'municipios': Municipio.query.count(),
        'bairros': Bairro.query.count(),
        'ruas': Rua.query.count(),
    }


def search_localidades(query):
    pattern = build_search_pattern(query)

    provincias = Provincia.query.filter(
        or_(
            Provincia.name.ilike(pattern),
            Provincia.description.ilike(pattern)
        )
    ).limit(8).all()

    municipios = Municipio.query.join(Provincia).filter(
        or_(
            Municipio.name.ilike(pattern),
            Municipio.description.ilike(pattern),
            Provincia.name.ilike(pattern)
        )
    ).limit(8).all()

    bairros = Bairro.query.join(Municipio).join(Provincia).filter(
        or_(
            Bairro.name.ilike(pattern),
            Bairro.description.ilike(pattern),
            Municipio.name.ilike(pattern),
            Provincia.name.ilike(pattern)
        )
    ).limit(8).all()

    ruas = Rua.query.join(Bairro).join(Municipio).join(Provincia).filter(
        or_(
            Rua.name.ilike(pattern),
            Rua.description.ilike(pattern),
            Bairro.name.ilike(pattern),
            Municipio.name.ilike(pattern),
            Provincia.name.ilike(pattern)
        )
    ).limit(8).all()

    results = []
    for provincia in provincias:
        results.append({
            'id': provincia.id,
            'type': 'provincia',
            'title': provincia.name,
            'subtitle': provincia.description or 'Sem descrição.',
            'path': provincia.name,
            'population': provincia.effective_population,
            'url': url_for('edit_provincia', provincia_id=provincia.id)
        })

    for municipio in municipios:
        results.append({
            'id': municipio.id,
            'type': 'municipio',
            'title': municipio.name,
            'subtitle': municipio.description or 'Sem descrição.',
            'path': municipio.full_path,
            'population': municipio.effective_population,
            'url': url_for('edit_municipio', municipio_id=municipio.id)
        })

    for bairro in bairros:
        results.append({
            'id': bairro.id,
            'type': 'bairro',
            'title': bairro.name,
            'subtitle': bairro.description or 'Sem descrição.',
            'path': bairro.full_path,
            'population': bairro.effective_population,
            'url': url_for('edit_bairro', bairro_id=bairro.id)
        })

    for rua in ruas:
        results.append({
            'id': rua.id,
            'type': 'rua',
            'title': rua.name,
            'subtitle': rua.description or 'Sem descrição.',
            'path': rua.full_path,
            'population': rua.effective_population,
            'url': url_for('edit_rua', rua_id=rua.id)
        })

    return results
