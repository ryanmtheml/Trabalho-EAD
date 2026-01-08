import json
from flask import Flask, render_template, request, session, redirect, url_for
from pathlib import Path

app = Flask(__name__)
app.secret_key = "secret"
ficheiro_utilizadores = Path(app.root_path) / 'utilizadores.json'
# Carregar lista de utilizadores
def carregar_utilizadores():
    try:
        with open(ficheiro_utilizadores, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def guardar_utilizadores(coco):
    with open('utilizadores.json', 'w') as userFile:
        json.dump(coco, userFile, indent=4)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/feed')
def feed():
    return render_template('feed.html')

@app.route('/validation', methods=['POST'])
def validation():
    utilizadores = carregar_utilizadores()
    pw = request.form.get('password')
    nome = request.form.get('username') 
    print(utilizadores)
    user_encontrado = False 
    for user in utilizadores:
        print(user['nome'])
        print(nome)
        print(user['password'])
        print(pw)
        if user['nome'] == nome and user['password'] == pw:
            userData=user['nome']
            session['user_id'] = user['id']
            user_encontrado = True
            break
        if user['nome'] == nome and user['password'] != pw:
            return "<h1>Erro: Palavra-passe incorreta!</h1>"
        

    if user_encontrado:
        
        return render_template('feed.html')
    else:
        return "<h1>Erro: Utilizador não encontrado!</h1>"

    


@app.route('/register', methods=['POST'])
def criar_conta():
    error = None
    utilizadores = carregar_utilizadores()
    nome= request.form.get('nome')
    email = request.form.get('email')
    password = request.form.get('password')
    username = request.form.get('username')
    novo_user = {
        'id': len(utilizadores) + 1,
        'nome': nome,
        'username': username,
        'email': email,
        'password': password,
        'isAdmin': False,
        'isBlocked': False
    }

    for user in utilizadores:
        if user['username'] == username:
            error = "Erro: Nome de utilizador já registado!"
        if user['email'] == email:
            error = "Erro: Email já registado!"
        
        
    if error != '':
        # mostrar ao utilizador o erro
        return render_template('home.html', error=error)
    utilizadores.append(novo_user)
    guardar_utilizadores(utilizadores)
    
    images = [
    {
        "id": i,
        "user_id": 100 + i,
        "url": f"https://unsplash.com/pt-br/fotografias/picos-irregulares-das-montanhas-banhados-pela-luz-dourada-da-hora-D1D-qXFh5g0",
        "name": f"Image {i}",
        "category": "Nature",
        "likes": i * 7,
        "description": f"Beautiful Unsplash image number {i}"
    }
    for i in range(1, 21)
    ]
    return render_template("feed.html", username=username, images=images)

@app.route('/categorias')
def categorias():
    return render_template("feed.html")

@app.route('/perfil')
def perfil():
    return render_template("perfil.html")

@app.route('/upload')
def upload():
    return render_template("upload.html")

@app.route('/notificacoes')
def notificacoes():
    return render_template("notificacoes.html")

@app.route('/posts')
def posts():
    return render_template("posts.html")

if __name__ == '__main__':
    app.run(debug=True)
    
    