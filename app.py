import json
import os
import time
from flask import Flask, render_template, request, session, redirect, url_for
from pathlib import Path
from werkzeug.utils import secure_filename
from modules import upload as uploadlb

app = Flask(__name__)
app.secret_key = "secret"


UPLOAD_FOLDER = os.path.join(app.root_path, 'static/all_images') # criando caminho onde defino pasta para guardar as imagens (uso a os library)
os.makedirs(UPLOAD_FOLDER, exist_ok=True) #verificação da pasta (se não existir, é criada uma)

ficheiro_utilizadores = Path(app.root_path) / 'utilizadores.json'
# Carregar lista de utilizadores
def carregar_utilizadores():
    try:
        with open(ficheiro_utilizadores, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def guardar_utilizadores(dados):
    with open(ficheiro_utilizadores, 'w') as userFile:
        json.dump(dados, userFile, indent=4)

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
            session['username'] = user['username']
            session['nome'] = user['nome']
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
        
        
    if error:
        # mostrar ao utilizador o erro
        return render_template('home.html', error=error)
    utilizadores.append(novo_user)
    guardar_utilizadores(utilizadores)
    print(utilizadores)
    return render_template('home.html', registo_sucesso=True)
    
    

@app.route('/categorias', methods=['POST'])
def categorias():
    # 1. Recuperar as categorias selecionadas (vem como uma lista)
    categorias_escolhidas = request.form.getlist('categorias')
    
    # 2. Carregar os utilizadores atuais
    utilizadores = carregar_utilizadores()
    
    # 3. Identificar qual utilizador atualizar
    # Se acabaste de registar, ele é o último da lista:
    if utilizadores:
        utilizadores[-1]['categorias'] = categorias_escolhidas
        
        # 4. Guardar a lista atualizada de volta no JSON
        guardar_utilizadores(utilizadores)
    
    # 5. Redirecionar para o feed
    return redirect(url_for('feed'))



@app.route('/upload', methods = ['POST'] )
def uploadImagem():
    autor_id = session['user_id']

    imagem = request.files['imagem']
    
    if imagem.filename == '':
        return "Nenhum ficheiro selecionado!"
    
    # Garantir nome seguro
    nome_ficheiro = secure_filename(imagem.filename)
    
    extensao = nome_ficheiro.split('.')[-1]
    nome_final = f"{int(time.time() * 1000)}.{extensao}" # time stamp, definindo assim nome unico para a imagem
    caminho = os.path.join(UPLOAD_FOLDER, nome_final) # pega a pasta e o arquivo, adicionando o caminho do arquivo na pasta

    
    # Guardar imagem
    imagem.save(caminho) #salvo a imagem no caminho

    uploadlb.criarImagem(autor_id,caminho)
    return render_template('perfil.html')
    

@app.route('/perfil')
def perfil():
    return render_template("perfil.html")

@app.route('/upload')
def upload():
    # Verificar se o utilizador tem sessão ativa
    if 'user_id' not in session:
        return redirect(url_for('home'))
    return render_template("upload.html")

@app.route('/notificacoes')
def notificacoes():
    return render_template("notificacoes.html")

@app.route('/posts')
def posts():
    return render_template("posts.html")

if __name__ == '__main__':
    app.run(debug=True)
    
    