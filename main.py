from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, text
from werkzeug.security import generate_password_hash, check_password_hash

# --- Application configuration ------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'batata'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# --- Data models --------------------------------------------------------------
class User(db.Model):
    """Usuário autenticado do sistema."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def check_password(self, password):
        """Verifica se a senha informada corresponde ao hash armazenado."""
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


# --- Helper functions ---------------------------------------------------------
def login_required(view):
    """Decorator para rotas que precisam de usuário autenticado."""

    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            flash('Faça login para continuar.', 'warning')
            return redirect(url_for('login'))
        return view(*args, **kwargs)

    return wrapped_view


def get_current_user():
    """Retorna o usuário logado na sessão, ou None se não houver."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


@app.context_processor
def inject_user():
    """Injeta o usuário atual em todos os templates."""
    return dict(current_user=get_current_user())


def get_required_string(field_name):
    """Lê um campo de texto do form e retorna a string limpa."""
    return request.form.get(field_name, '').strip()


def get_optional_string(field_name):
    """Lê um campo de texto opcional de um form."""
    return request.form.get(field_name, '').strip() or None


def get_optional_int(field_name):
    """Lê um campo numérico opcional e converte para inteiro."""
    raw_value = request.form.get(field_name, '').strip()
    if raw_value == '':
        return None
    try:
        value = int(raw_value)
        return value if value >= 0 else None
    except ValueError:
        return None


def query_feed():
    """Consulta os itens que aparecerão no feed da página inicial."""
    return {
        'provincias': Provincia.query.order_by(Provincia.created_at.desc()).limit(4).all(),
        'municipios': Municipio.query.order_by(Municipio.created_at.desc()).limit(4).all(),
        'bairros': Bairro.query.order_by(Bairro.created_at.desc()).limit(4).all(),
        'ruas': Rua.query.order_by(Rua.created_at.desc()).limit(4).all(),
    }


def get_counts():
    """Retorna contadores rápidos de cada entidade."""
    return {
        'provincias': Provincia.query.count(),
        'municipios': Municipio.query.count(),
        'bairros': Bairro.query.count(),
        'ruas': Rua.query.count(),
    }


def build_search_pattern(query):
    """Gera o padrão usado nas consultas de busca."""
    return f'%{query}%'


def search_localidades(query):
    """Retorna resultados de busca global para localidades hierárquicas."""
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
            'population': provincia.population,
            'url': url_for('edit_provincia', provincia_id=provincia.id)
        })

    for municipio in municipios:
        results.append({
            'id': municipio.id,
            'type': 'municipio',
            'title': municipio.name,
            'subtitle': municipio.description or 'Sem descrição.',
            'path': municipio.full_path,
            'population': municipio.population,
            'url': url_for('edit_municipio', municipio_id=municipio.id)
        })

    for bairro in bairros:
        results.append({
            'id': bairro.id,
            'type': 'bairro',
            'title': bairro.name,
            'subtitle': bairro.description or 'Sem descrição.',
            'path': bairro.full_path,
            'population': bairro.population,
            'url': url_for('edit_bairro', bairro_id=bairro.id)
        })

    for rua in ruas:
        results.append({
            'id': rua.id,
            'type': 'rua',
            'title': rua.name,
            'subtitle': rua.description or 'Sem descrição.',
            'path': rua.full_path,
            'population': rua.population,
            'url': url_for('edit_rua', rua_id=rua.id)
        })

    return results


@app.route('/search')
def search():
    """Busca global de localidades em tempo real."""
    query = request.args.get('q', '').strip()
    if query == '':
        return jsonify(results=[])
    return jsonify(results=search_localidades(query))


# --- Public routes -----------------------------------------------------------
@app.route('/')
def home():
    """Página inicial com o feed de localidades."""
    feed = query_feed()
    counts = get_counts()
    return render_template('index.html', feed=feed, counts=counts)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Rota de cadastro de usuário."""
    if request.method == 'POST':
        name = get_required_string('name')
        email = get_required_string('email').lower()
        password = request.form.get('password', '')

        if not name or not email or not password:
            flash('Preencha todos os campos.', 'danger')
            return render_template('signup.html', name=name, email=email)

        if User.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado.', 'danger')
            return render_template('signup.html', name=name, email=email)

        user = User(name=name, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        flash('Cadastro realizado com sucesso.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Rota de login de usuário."""
    if request.method == 'POST':
        email = get_required_string('email').lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('E-mail ou senha incorretos.', 'danger')
            return render_template('login.html', email=email)

        session['user_id'] = user.id
        flash(f'Bem-vindo, {user.name}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Limpa a sessão do usuário e volta para a página inicial."""
    session.pop('user_id', None)
    flash('Logout efetuado com sucesso.', 'success')
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Área interna do usuário logado."""
    return render_template('dashboard.html')


# --- CRUD de províncias ------------------------------------------------------
@app.route('/provincias')
@login_required
def provincias():
    """Lista de províncias cadastradas."""
    provincias = Provincia.query.order_by(Provincia.name).all()
    return render_template('provincias.html', provincias=provincias)


@app.route('/provincias/add', methods=['GET', 'POST'])
@login_required
def add_provincia():
    """Formulário para criar uma nova província."""
    if request.method == 'POST':
        name = get_required_string('name')
        description = get_optional_string('description')
        raw_population = request.form.get('population', '').strip()
        population = get_optional_int('population')

        if not name:
            flash('Nome da província obrigatório.', 'danger')
        elif raw_population and population is None:
            flash('População deve ser um número inteiro não-negativo.', 'danger')
        elif Provincia.query.filter_by(name=name).first():
            flash('Essa província já existe.', 'danger')
        else:
            db.session.add(Provincia(name=name, description=description, population=population))
            db.session.commit()
            flash('Província criada com sucesso.', 'success')
            return redirect(url_for('provincias'))

    return render_template('form_provincia.html', action='Adicionar', provincia=None)


@app.route('/provincias/<int:provincia_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_provincia(provincia_id):
    """Formulário para editar uma província existente."""
    provincia = Provincia.query.get_or_404(provincia_id)
    if request.method == 'POST':
        provincia.name = get_required_string('name')
        provincia.description = get_optional_string('description')
        raw_population = request.form.get('population', '').strip()
        population = get_optional_int('population')

        if not provincia.name:
            flash('Nome da província obrigatório.', 'danger')
        elif raw_population and population is None:
            flash('População deve ser um número inteiro não-negativo.', 'danger')
        elif Provincia.query.filter(Provincia.name == provincia.name, Provincia.id != provincia.id).first():
            flash('Outra província já usa esse nome.', 'danger')
        else:
            provincia.population = population
            db.session.commit()
            flash('Província atualizada com sucesso.', 'success')
            return redirect(url_for('provincias'))

    return render_template('form_provincia.html', action='Editar', provincia=provincia)


@app.route('/provincias/<int:provincia_id>/delete', methods=['POST'])
@login_required
def delete_provincia(provincia_id):
    """Remove uma província e todos os municípios relacionados."""
    provincia = Provincia.query.get_or_404(provincia_id)
    db.session.delete(provincia)
    db.session.commit()
    flash('Província removida.', 'success')
    return redirect(url_for('provincias'))


# --- CRUD de municípios ------------------------------------------------------
@app.route('/municipios')
@login_required
def municipios():
    """Lista de municípios cadastrados."""
    municipios = Municipio.query.order_by(Municipio.name).all()
    return render_template('municipios.html', municipios=municipios)


@app.route('/municipios/add', methods=['GET', 'POST'])
@login_required
def add_municipio():
    """Formulário para criar um novo município."""
    provincias = Provincia.query.order_by(Provincia.name).all()
    if not provincias:
        flash('Cadastre uma província antes de adicionar um município.', 'warning')
        return redirect(url_for('provincias'))

    if request.method == 'POST':
        name = get_required_string('name')
        provincia_id = request.form.get('provincia_id')
        description = get_optional_string('description')
        raw_population = request.form.get('population', '').strip()
        population = get_optional_int('population')

        if not name or not provincia_id:
            flash('Nome e província são obrigatórios.', 'danger')
        elif raw_population and population is None:
            flash('População deve ser um número inteiro não-negativo.', 'danger')
        else:
            provincia = Provincia.query.get(int(provincia_id))
            if not provincia:
                flash('Província inválida.', 'danger')
            else:
                db.session.add(Municipio(name=name, description=description, population=population, provincia=provincia))
                db.session.commit()
                flash('Município criado com sucesso.', 'success')
                return redirect(url_for('municipios'))

    return render_template('form_municipio.html', action='Adicionar', municipio=None, provincias=provincias)


@app.route('/municipios/<int:municipio_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_municipio(municipio_id):
    """Formulário para editar um município existente."""
    municipio = Municipio.query.get_or_404(municipio_id)
    provincias = Provincia.query.order_by(Provincia.name).all()

    if request.method == 'POST':
        municipio.name = get_required_string('name')
        municipio.description = get_optional_string('description')
        raw_population = request.form.get('population', '').strip()
        population = get_optional_int('population')
        provincia_id = request.form.get('provincia_id')

        if not municipio.name or not provincia_id:
            flash('Nome e província são obrigatórios.', 'danger')
        elif raw_population and population is None:
            flash('População deve ser um número inteiro não-negativo.', 'danger')
        else:
            provincia = Provincia.query.get(int(provincia_id))
            if not provincia:
                flash('Província inválida.', 'danger')
            else:
                municipio.population = population
                municipio.provincia = provincia
                db.session.commit()
                flash('Município atualizado com sucesso.', 'success')
                return redirect(url_for('municipios'))

    return render_template('form_municipio.html', action='Editar', municipio=municipio, provincias=provincias)


@app.route('/municipios/<int:municipio_id>/delete', methods=['POST'])
@login_required
def delete_municipio(municipio_id):
    """Remove um município e todos os bairros relacionados."""
    municipio = Municipio.query.get_or_404(municipio_id)
    db.session.delete(municipio)
    db.session.commit()
    flash('Município removido.', 'success')
    return redirect(url_for('municipios'))


# --- CRUD de bairros ---------------------------------------------------------
@app.route('/bairros')
@login_required
def bairros():
    """Lista de bairros cadastrados."""
    bairros = Bairro.query.order_by(Bairro.name).all()
    return render_template('bairros.html', bairros=bairros)


@app.route('/bairros/add', methods=['GET', 'POST'])
@login_required
def add_bairro():
    """Formulário para criar um novo bairro."""
    municipios = Municipio.query.order_by(Municipio.name).all()
    if not municipios:
        flash('Cadastre um município antes de adicionar um bairro.', 'warning')
        return redirect(url_for('municipios'))

    if request.method == 'POST':
        name = get_required_string('name')
        municipio_id = request.form.get('municipio_id')
        description = get_optional_string('description')
        raw_population = request.form.get('population', '').strip()
        population = get_optional_int('population')

        if not name or not municipio_id:
            flash('Nome e município são obrigatórios.', 'danger')
        elif raw_population and population is None:
            flash('População deve ser um número inteiro não-negativo.', 'danger')
        else:
            municipio = Municipio.query.get(int(municipio_id))
            if not municipio:
                flash('Município inválido.', 'danger')
            else:
                db.session.add(Bairro(name=name, description=description, population=population, municipio=municipio))
                db.session.commit()
                flash('Bairro criado com sucesso.', 'success')
                return redirect(url_for('bairros'))

    return render_template('form_bairro.html', action='Adicionar', bairro=None, municipios=municipios)


@app.route('/bairros/<int:bairro_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_bairro(bairro_id):
    """Formulário para editar um bairro existente."""
    bairro = Bairro.query.get_or_404(bairro_id)
    municipios = Municipio.query.order_by(Municipio.name).all()

    if request.method == 'POST':
        bairro.name = get_required_string('name')
        bairro.description = get_optional_string('description')
        raw_population = request.form.get('population', '').strip()
        population = get_optional_int('population')
        municipio_id = request.form.get('municipio_id')

        if not bairro.name or not municipio_id:
            flash('Nome e município são obrigatórios.', 'danger')
        elif raw_population and population is None:
            flash('População deve ser um número inteiro não-negativo.', 'danger')
        else:
            municipio = Municipio.query.get(int(municipio_id))
            if not municipio:
                flash('Município inválido.', 'danger')
            else:
                bairro.population = population
                bairro.municipio = municipio
                db.session.commit()
                flash('Bairro atualizado com sucesso.', 'success')
                return redirect(url_for('bairros'))

    return render_template('form_bairro.html', action='Editar', bairro=bairro, municipios=municipios)


@app.route('/bairros/<int:bairro_id>/delete', methods=['POST'])
@login_required
def delete_bairro(bairro_id):
    """Remove um bairro e todas as ruas relacionadas."""
    bairro = Bairro.query.get_or_404(bairro_id)
    db.session.delete(bairro)
    db.session.commit()
    flash('Bairro removido.', 'success')
    return redirect(url_for('bairros'))


# --- CRUD de ruas -----------------------------------------------------------
@app.route('/ruas')
@login_required
def ruas():
    """Lista de ruas cadastradas."""
    ruas = Rua.query.order_by(Rua.name).all()
    return render_template('ruas.html', ruas=ruas)


@app.route('/ruas/add', methods=['GET', 'POST'])
@login_required
def add_rua():
    """Formulário para criar uma nova rua."""
    bairros = Bairro.query.order_by(Bairro.name).all()
    if not bairros:
        flash('Cadastre um bairro antes de adicionar uma rua.', 'warning')
        return redirect(url_for('bairros'))

    if request.method == 'POST':
        name = get_required_string('name')
        bairro_id = request.form.get('bairro_id')
        description = get_optional_string('description')
        raw_population = request.form.get('population', '').strip()
        population = get_optional_int('population')

        if not name or not bairro_id:
            flash('Nome e bairro são obrigatórios.', 'danger')
        elif raw_population and population is None:
            flash('População deve ser um número inteiro não-negativo.', 'danger')
        else:
            bairro = Bairro.query.get(int(bairro_id))
            if not bairro:
                flash('Bairro inválido.', 'danger')
            else:
                db.session.add(Rua(name=name, description=description, population=population, bairro=bairro))
                db.session.commit()
                flash('Rua criada com sucesso.', 'success')
                return redirect(url_for('ruas'))

    return render_template('form_rua.html', action='Adicionar', rua=None, bairros=bairros)


@app.route('/ruas/<int:rua_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_rua(rua_id):
    """Formulário para editar uma rua existente."""
    rua = Rua.query.get_or_404(rua_id)
    bairros = Bairro.query.order_by(Bairro.name).all()

    if request.method == 'POST':
        rua.name = get_required_string('name')
        rua.description = get_optional_string('description')
        raw_population = request.form.get('population', '').strip()
        population = get_optional_int('population')
        bairro_id = request.form.get('bairro_id')

        if not rua.name or not bairro_id:
            flash('Nome e bairro são obrigatórios.', 'danger')
        elif raw_population and population is None:
            flash('População deve ser um número inteiro não-negativo.', 'danger')
        else:
            bairro = Bairro.query.get(int(bairro_id))
            if not bairro:
                flash('Bairro inválido.', 'danger')
            else:
                rua.population = population
                rua.bairro = bairro
                db.session.commit()
                flash('Rua atualizada com sucesso.', 'success')
                return redirect(url_for('ruas'))

    return render_template('form_rua.html', action='Editar', rua=rua, bairros=bairros)


@app.route('/ruas/<int:rua_id>/delete', methods=['POST'])
@login_required
def delete_rua(rua_id):
    """Remove uma rua do banco de dados."""
    rua = Rua.query.get_or_404(rua_id)
    db.session.delete(rua)
    db.session.commit()
    flash('Rua removida.', 'success')
    return redirect(url_for('ruas'))


def ensure_database_schema():
    """Adiciona colunas faltantes no banco SQLite existente."""
    def ensure_column(table_name, column_name):
        existing_columns = [row[1] for row in db.session.execute(text(f"PRAGMA table_info({table_name})"))]
        if column_name not in existing_columns:
            db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} INTEGER"))
            db.session.commit()

    ensure_column('provincia', 'population')
    ensure_column('municipio', 'population')
    ensure_column('bairro', 'population')
    ensure_column('rua', 'population')


# --- Application entry point --------------------------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        ensure_database_schema()
    app.run(debug=True)
