from datetime import datetime
from .database import db


class User(db.Model):
    """Usuário autenticado do sistema."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Provincia(db.Model):
    """Entidade de província com municípios relacionados."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    population = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    municipios = db.relationship(
        'Municipio', backref='provincia', cascade='all, delete-orphan', passive_deletes=True
    )

    @property
    def computed_population(self):
        return sum(municipio.effective_population for municipio in self.municipios)

    @property
    def effective_population(self):
        return self.computed_population if self.computed_population else (self.population if self.population is not None else 0)

    def __repr__(self):
        return f'<Provincia {self.name}>'


class Municipio(db.Model):
    """Entidade de município com relação para província e bairros."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    population = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    provincia_id = db.Column(db.Integer, db.ForeignKey('provincia.id', ondelete='CASCADE'), nullable=False)
    bairros = db.relationship('Bairro', backref='municipio', cascade='all, delete-orphan', passive_deletes=True)

    @property
    def full_path(self):
        return f'{self.provincia.name} / {self.name}'

    @property
    def computed_population(self):
        return sum(bairro.effective_population for bairro in self.bairros)

    @property
    def effective_population(self):
        return self.computed_population if self.computed_population else (self.population if self.population is not None else 0)

    def __repr__(self):
        return f'<Municipio {self.name}>'


class Bairro(db.Model):
    """Entidade de bairro com relação para município e ruas."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    population = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    municipio_id = db.Column(db.Integer, db.ForeignKey('municipio.id', ondelete='CASCADE'), nullable=False)
    ruas = db.relationship('Rua', backref='bairro', cascade='all, delete-orphan', passive_deletes=True)

    @property
    def full_path(self):
        return f'{self.municipio.provincia.name} / {self.municipio.name} / {self.name}'

    @property
    def computed_population(self):
        return sum(rua.effective_population for rua in self.ruas)

    @property
    def effective_population(self):
        return self.computed_population if self.computed_population else (self.population if self.population is not None else 0)

    def __repr__(self):
        return f'<Bairro {self.name}>'


class Rua(db.Model):
    """Entidade de rua com relação para bairro."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    population = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    bairro_id = db.Column(db.Integer, db.ForeignKey('bairro.id', ondelete='CASCADE'), nullable=False)

    @property
    def full_path(self):
        return f'{self.bairro.municipio.provincia.name} / {self.bairro.municipio.name} / {self.bairro.name} / {self.name}'

    @property
    def effective_population(self):
        return self.population if self.population is not None else 0

    def __repr__(self):
        return f'<Rua {self.name}>'
