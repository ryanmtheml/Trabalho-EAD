import json
from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "secret"

# Carregar lista de utilizadores [cite: 139]
def carregar_utilizadores():
    try:
        with open('utilizadores.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def guardar_utilizadores(coco):
    with open('utilizadores.json', 'w') as userFile:
        json.dump(coco, userFile, indent=4)

@app.route('/')
def index():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    
    images = [
    {
        "id": i,
        "user_id": 100 + i,
        "url": f"static/photo.jpg",
        "name": f"Image {i}",
        "category": "Nature",
        "likes": i * 7,
        "description": f"Beautiful Unsplash image number {i}"
    }
    for i in range(1, 21)
    ]
    return render_template("feed.html",images=images)

@app.route('/login')
def login():
    return render_template('login.html')



@app.route('/validation', methods=['POST'])
def validation():
    utilizadores = carregar_utilizadores()
    pw = request.form.get('password')
    nome = request.form.get('username') 
    
    user_encontrado = False 
    for user in utilizadores:
        if user['nome'] == nome and user['password'] == pw:
            userData=user['nome']
            session['user_id'] = user['id']
            user_encontrado = True
            break
        if user['nome'] == nome and user['password'] != pw:
            return "<h1>Erro: Palavra-passe incorreta!</h1>"
        

    if user_encontrado:
        
        return redirect(url_for("index"))
    else:
        return "<h1>Erro: Utilizador não encontrado!</h1>"

    


@app.route('/register', methods=['POST'])
def criar_conta():
    error = None
    utilizadores = carregar_utilizadores()
    email = request.form.get('email')
    password = request.form.get('password')
    username = request.form.get('username')
    novo_user = {
        'id': len(utilizadores) + 1,
        'nome': username,
        'email': email,
        'password': password,
        'isAdmin': False,
        'isBlocked': False
    }

    for user in utilizadores:
        if user['nome'] == username:
            error = "Erro: Nome de utilizador já registado!"
        if user['email'] == email:
            error = "Erro: Email já registado!"
        
        
    if error != '':
        return render_template("feed.html", error=error, username=username)
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

if __name__ == '__main__':
    app.run(debug=True)