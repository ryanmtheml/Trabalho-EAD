import json
from flask import Flask, render_template, request

app = Flask(__name__)

# Carregar lista de utilizadores [cite: 139]
def carregar_utilizadores():
    try:
        with open('utilizadores.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def guardar_utilizadores(utilizadores):
    with open('utilizadores.json', 'w') as userFile:
        json.dump(utilizadores, userFile, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    utilizadores = carregar_utilizadores()
    pw = request.form.get('password')
    nome = request.form.get('username') 
    
    user_encontrado = False 
    for user in utilizadores:
        if user['nome'] == nome and user['password'] == pw:
            user_encontrado = True
            userData = user
            break
        if user['nome'] == nome and user['password'] != pw:
            return "<h1>Erro: Palavra-passe incorreta!</h1>"
        

    if user_encontrado:
        return f"<h1>Bem-vindo, {userData['nome']}!</h1>"
    else:
        return "<h1>Erro: Utilizador não encontrado!</h1>"

    


@app.route('/register', methods=['POST'])
def criar_conta():
    utilizadores = carregar_utilizadores()
    email = request.form.get('email')
    password = request.form.get('password')
    username = request.form.get('username')
    novo_user = {
        'nome': username,
        'email': email,
        'password': password,
        'isAdmin': False,
        'isBlocked': False
    }

    for user in utilizadores:
        if user['nome'] == username:
            return "<h1>Erro: Nome de utilizador já registado!</h1>"
        if user['email'] == email:
            return "<h1>Erro: Email já registado!</h1>"
        
        
    
    utilizadores.append(novo_user)
    guardar_utilizadores(utilizadores)
    return f"<h1>Conta criada para {email}!</h1>"

if __name__ == '__main__':
    app.run(debug=True)