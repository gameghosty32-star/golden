from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'batata'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Provincia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    municipios = db.relationship('Municipio', backref='provincia', cascade='all, delete-orphan', passive_deletes=True)


class Municipio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    provincia_id = db.Column(db.Integer, db.ForeignKey('provincia.id', ondelete='CASCADE'), nullable=False)
    bairros = db.relationship('Bairro', backref='municipio', cascade='all, delete-orphan', passive_deletes=True)


class Bairro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    municipio_id = db.Column(db.Integer, db.ForeignKey('municipio.id', ondelete='CASCADE'), nullable=False)
    ruas = db.relationship('Rua', backref='bairro', cascade='all, delete-orphan', passive_deletes=True)


class Rua(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    bairro_id = db.Column(db.Integer, db.ForeignKey('bairro.id', ondelete='CASCADE'), nullable=False)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            flash('Faça login para continuar.', 'warning')
            return redirect(url_for('login'))
        return view(*args, **kwargs)

    return wrapped_view


def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())


@app.route('/')
def home():
    if get_current_user():
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not email or not password:
            flash('Preencha todos os campos.', 'danger')
            return render_template('signup.html', name=name, email=email)

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Este e-mail já está cadastrado.', 'danger')
            return render_template('signup.html', name=name, email=email)

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        flash('Cadastro realizado com sucesso.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
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
    session.pop('user_id', None)
    flash('Logout efetuado com sucesso.', 'success')
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/provincias')
@login_required
def provincias():
    provincias = Provincia.query.order_by(Provincia.name).all()
    return render_template('provincias.html', provincias=provincias)


@app.route('/provincias/add', methods=['GET', 'POST'])
@login_required
def add_provincia():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Nome da província obrigatório.', 'danger')
        elif Provincia.query.filter_by(name=name).first():
            flash('Essa província já existe.', 'danger')
        else:
            db.session.add(Provincia(name=name))
            db.session.commit()
            flash('Província criada com sucesso.', 'success')
            return redirect(url_for('provincias'))

    return render_template('form_provincia.html', action='Adicionar', provincia=None)


@app.route('/provincias/<int:provincia_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_provincia(provincia_id):
    provincia = Provincia.query.get_or_404(provincia_id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Nome da província obrigatório.', 'danger')
        elif Provincia.query.filter(Provincia.name == name, Provincia.id != provincia.id).first():
            flash('Outra província já usa esse nome.', 'danger')
        else:
            provincia.name = name
            db.session.commit()
            flash('Província atualizada com sucesso.', 'success')
            return redirect(url_for('provincias'))

    return render_template('form_provincia.html', action='Editar', provincia=provincia)


@app.route('/provincias/<int:provincia_id>/delete', methods=['POST'])
@login_required
def delete_provincia(provincia_id):
    provincia = Provincia.query.get_or_404(provincia_id)
    db.session.delete(provincia)
    db.session.commit()
    flash('Província removida.', 'success')
    return redirect(url_for('provincias'))


@app.route('/municipios')
@login_required
def municipios():
    municipios = Municipio.query.order_by(Municipio.name).all()
    return render_template('municipios.html', municipios=municipios)


@app.route('/municipios/add', methods=['GET', 'POST'])
@login_required
def add_municipio():
    provincias = Provincia.query.order_by(Provincia.name).all()
    if not provincias:
        flash('Cadastre uma província antes de adicionar um município.', 'warning')
        return redirect(url_for('provincias'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        provincia_id = request.form.get('provincia_id')
        if not name or not provincia_id:
            flash('Nome e província são obrigatórios.', 'danger')
        else:
            provincia = Provincia.query.get(int(provincia_id))
            if not provincia:
                flash('Província inválida.', 'danger')
            else:
                db.session.add(Municipio(name=name, provincia=provincia))
                db.session.commit()
                flash('Município criado com sucesso.', 'success')
                return redirect(url_for('municipios'))

    return render_template('form_municipio.html', action='Adicionar', municipio=None, provincias=provincias)


@app.route('/municipios/<int:municipio_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_municipio(municipio_id):
    municipio = Municipio.query.get_or_404(municipio_id)
    provincias = Provincia.query.order_by(Provincia.name).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        provincia_id = request.form.get('provincia_id')
        if not name or not provincia_id:
            flash('Nome e província são obrigatórios.', 'danger')
        else:
            provincia = Provincia.query.get(int(provincia_id))
            if not provincia:
                flash('Província inválida.', 'danger')
            else:
                municipio.name = name
                municipio.provincia = provincia
                db.session.commit()
                flash('Município atualizado com sucesso.', 'success')
                return redirect(url_for('municipios'))

    return render_template('form_municipio.html', action='Editar', municipio=municipio, provincias=provincias)


@app.route('/municipios/<int:municipio_id>/delete', methods=['POST'])
@login_required
def delete_municipio(municipio_id):
    municipio = Municipio.query.get_or_404(municipio_id)
    db.session.delete(municipio)
    db.session.commit()
    flash('Município removido.', 'success')
    return redirect(url_for('municipios'))


@app.route('/bairros')
@login_required
def bairros():
    bairros = Bairro.query.order_by(Bairro.name).all()
    return render_template('bairros.html', bairros=bairros)


@app.route('/bairros/add', methods=['GET', 'POST'])
@login_required
def add_bairro():
    municipios = Municipio.query.order_by(Municipio.name).all()
    if not municipios:
        flash('Cadastre um município antes de adicionar um bairro.', 'warning')
        return redirect(url_for('municipios'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        municipio_id = request.form.get('municipio_id')
        if not name or not municipio_id:
            flash('Nome e município são obrigatórios.', 'danger')
        else:
            municipio = Municipio.query.get(int(municipio_id))
            if not municipio:
                flash('Município inválido.', 'danger')
            else:
                db.session.add(Bairro(name=name, municipio=municipio))
                db.session.commit()
                flash('Bairro criado com sucesso.', 'success')
                return redirect(url_for('bairros'))

    return render_template('form_bairro.html', action='Adicionar', bairro=None, municipios=municipios)


@app.route('/bairros/<int:bairro_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_bairro(bairro_id):
    bairro = Bairro.query.get_or_404(bairro_id)
    municipios = Municipio.query.order_by(Municipio.name).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        municipio_id = request.form.get('municipio_id')
        if not name or not municipio_id:
            flash('Nome e município são obrigatórios.', 'danger')
        else:
            municipio = Municipio.query.get(int(municipio_id))
            if not municipio:
                flash('Município inválido.', 'danger')
            else:
                bairro.name = name
                bairro.municipio = municipio
                db.session.commit()
                flash('Bairro atualizado com sucesso.', 'success')
                return redirect(url_for('bairros'))

    return render_template('form_bairro.html', action='Editar', bairro=bairro, municipios=municipios)


@app.route('/bairros/<int:bairro_id>/delete', methods=['POST'])
@login_required
def delete_bairro(bairro_id):
    bairro = Bairro.query.get_or_404(bairro_id)
    db.session.delete(bairro)
    db.session.commit()
    flash('Bairro removido.', 'success')
    return redirect(url_for('bairros'))


@app.route('/ruas')
@login_required
def ruas():
    ruas = Rua.query.order_by(Rua.name).all()
    return render_template('ruas.html', ruas=ruas)


@app.route('/ruas/add', methods=['GET', 'POST'])
@login_required
def add_rua():
    bairros = Bairro.query.order_by(Bairro.name).all()
    if not bairros:
        flash('Cadastre um bairro antes de adicionar uma rua.', 'warning')
        return redirect(url_for('bairros'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        bairro_id = request.form.get('bairro_id')
        if not name or not bairro_id:
            flash('Nome e bairro são obrigatórios.', 'danger')
        else:
            bairro = Bairro.query.get(int(bairro_id))
            if not bairro:
                flash('Bairro inválido.', 'danger')
            else:
                db.session.add(Rua(name=name, bairro=bairro))
                db.session.commit()
                flash('Rua criada com sucesso.', 'success')
                return redirect(url_for('ruas'))

    return render_template('form_rua.html', action='Adicionar', rua=None, bairros=bairros)


@app.route('/ruas/<int:rua_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_rua(rua_id):
    rua = Rua.query.get_or_404(rua_id)
    bairros = Bairro.query.order_by(Bairro.name).all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        bairro_id = request.form.get('bairro_id')
        if not name or not bairro_id:
            flash('Nome e bairro são obrigatórios.', 'danger')
        else:
            bairro = Bairro.query.get(int(bairro_id))
            if not bairro:
                flash('Bairro inválido.', 'danger')
            else:
                rua.name = name
                rua.bairro = bairro
                db.session.commit()
                flash('Rua atualizada com sucesso.', 'success')
                return redirect(url_for('ruas'))

    return render_template('form_rua.html', action='Editar', rua=rua, bairros=bairros)


@app.route('/ruas/<int:rua_id>/delete', methods=['POST'])
@login_required
def delete_rua(rua_id):
    rua = Rua.query.get_or_404(rua_id)
    db.session.delete(rua)
    db.session.commit()
    flash('Rua removida.', 'success')
    return redirect(url_for('ruas'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
