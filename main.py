from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///db.db"

@app.route('/')
def home():
    nome_usuario='Délcio'#Depois automatizar

    return render_template('index.html', nome=nome_usuario)

if __name__ == '__main__':
    app.run(debug=True)