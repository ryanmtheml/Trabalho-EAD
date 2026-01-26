import json
import os
import time
from flask import Flask, render_template, request, session, redirect, url_for
from pathlib import Path #blioteca para manipular caminhos de ficheiros
from werkzeug.utils import secure_filename
from modules import upload as uploadlb
from flask_bcrypt import Bcrypt
from datetime import datetime 
import matplotlib
matplotlib.use('Agg')  # backend sem interface gráfica
import matplotlib.pyplot as grafico

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "secret"

UPLOAD_FOLDER = os.path.join( 'static/all_images') # criando caminho onde defino pasta para guardar as imagens (uso a os library)
os.makedirs(UPLOAD_FOLDER, exist_ok=True) #verificação da pasta (se não existir, é criada uma)

# UTILIZADORES FUNCTION

ficheiro_utilizadores = Path(app.root_path) / 'utilizadores.json'
ficheiro_photos = Path(app.root_path) / 'photos.json'
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

@app.route('/removerUser/<user_id>')
def remover_utilizador(user_id):
    utilizadores = carregar_utilizadores()


    if not user_id:
        return redirect("/admin")

    try:
        user_id = int(user_id)
    except:
        return redirect("/admin")

    utilizadores = carregar_utilizadores()

    # 🔥 Remover o utilizador da lista
    novos_utilizadores = [u for u in utilizadores if u["user_id"] != user_id]

    # Guardar o ficheiro atualizado
    guardar_utilizadores(novos_utilizadores)

    return redirect("/admin")


@app.route('/feed')
def feed():
    with open(ficheiro_photos, 'r') as f:
        fotos = json.load(f)
    
    categoria = request.args.get('categoria')
    fotos_filtradas = fotos 

    if categoria:
        fotos_filtradas = []
        for foto in fotos:
            if foto['categoria'] == categoria:
                fotos_filtradas.append(foto)

    return render_template('feed.html', profile_pic=session.get('profile_pic'), fotos=fotos_filtradas[::-1], isAdmin = session.get("isAdmin"))

@app.route('/validation', methods=['POST'])
def validation():
    utilizadores = carregar_utilizadores()
    pw = request.form.get('password')
    username = request.form.get('username') 
    
    user_encontrado = False

    for user in utilizadores:

        if user['username'] == username and bcrypt.check_password_hash(user['password'], pw):

            session['profile_picture'] = user['profile_picture']
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['nome'] = user['nome']
            session['email'] = user['email']
            session['isAdmin']= user['isAdmin']
            
            user_encontrado= True
            break

            

        if user['username'] == username and bcrypt.check_password_hash(user['password'], pw):
            return "<h1>Erro: Palavra-passe incorreta!</h1>"
    
    if user_encontrado:
        if user['isAdmin']:
            return redirect('/admin') 
        else:
            return redirect ('/feed')
    else:
        return "<h1>Erro: Utilizador não encontrado!</h1>"

    


@app.route('/register', methods=['POST'])
def criar_conta():
    error = None
    utilizadores = carregar_utilizadores()
    nome= request.form.get('nome')
    email = request.form.get('email')
    password = request.form.get('password')
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    username = request.form.get('username')
    novo_user = {
        'user_id': utilizadores[-1]['user_id'] + 1 if utilizadores else 1,
        'profile_picture': '',
        'nome': nome,
        'username': username,
        'email': email,
        'password': hashed_password,
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
        return f"<h1>{error}</h1>"
    utilizadores.append(novo_user)
    guardar_utilizadores(utilizadores)
    session['user_id'] = novo_user['user_id']
    session['username'] = novo_user['username']
    session['nome'] = novo_user['nome']
    session['email'] = novo_user['email']
    return render_template('categ.html')
    
    

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
        session['categorias'] = categorias_escolhidas
    
        
    
    # 5. Redirecionar para o feed
    return redirect ('/feed')


# END OF UTILIZADORES FUNCTION

# UPLOAD FUNCTION

@app.route('/uploadimg', methods = ['POST'] )
def uploadImagem():
    autor_id = session['user_id']

    imagem = request.files['imagem']
    
    if imagem.filename == '':
        return "Nenhum ficheiro selecionado!"
    
    # Garantir nome seguro
    nome_ficheiro = secure_filename(imagem.filename)
    id = int(time.time() * 1000) # time stamp, definindo assim nome unico para o id
    extensao = nome_ficheiro.split('.')[-1]
    nome_final = f"{id}.{extensao}" 
    caminho = os.path.join(UPLOAD_FOLDER, nome_final) # pega a pasta e o arquivo, adicionando o caminho do arquivo na pasta
    imgprivacidade = True
    # Guardar imagem
    imagem.save(caminho) #salvo a imagem no caminho
    uploadlb.criarImagem(autor_id,caminho,id, imgprivacidade)

    try:
        with open('notificacoes.json', 'r') as f:
            lista = json.load(f)
    except:
        lista = []

    novaNotificacao = {
        "nome": session.get('nome'),
        "mensagem": "nova imagem adicionada",
        "hora": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "autor_id": autor_id
        
    }

    lista.append(novaNotificacao)

    with open('notificacoes.json', 'w') as f:
        json.dump(lista, f, indent=4)

    gerar_grafico_imagens()


    return render_template('edicaoFotos.html', imageURL='/static/all_images/' + nome_final, imageId = id)
    

def gerar_grafico_imagens():
    with open('photos.json', 'r') as f:
            imagens = json.load(f)

    categorias_oficiais = [
        "comida", "paisagens", "moda", "arte", "animais", "arquitetura",
        "viagens", "tecnologia", "desporto", "música", "cinema"
    ]

    contagem = {cat: 0 for cat in categorias_oficiais}
    contagem["outros"] = 0

    for img in imagens:
        cat = img["categoria"].strip().lower()
        if cat in contagem:
            contagem[cat] += 1
        else:
            contagem["outros"] += 1

    labels = list(contagem.keys())
    valores = list(contagem.values())

    grafico.figure(figsize=(9, 4))
    grafico.bar(labels, valores)
    grafico.xticks(rotation=45, ha="right")
    grafico.ylabel("Nº de imagens")
    grafico.title("Imagens por Categoria")
    grafico.tight_layout()

    
    grafico.savefig("static/grafico_categorias.png")
    grafico.close()



@app.route('/privar', methods = ['POST'])
def atualizarPrivacidade():
    imageId = request.form.get('imageId')
    print(imageId)
    try:
        with open('photos.json', 'r') as f:
            imagens = json.load(f)

        for img in imagens:
            print(img['id'])
            if img['id'] == int(imageId):
                img['isPublic'] = False
                print('alterado para false ')
                break
        print(imagens)
        with open('photos.json', 'w') as f:
            json.dump(imagens, f, indent=4)
    except Exception as e:
        print("Erro ao atualizar privacidade:", e)
    return redirect('/privadas')

def getImageById(image_id):
    try:
        # Abrir o ficheiro JSON
        with open('photos.json', 'r') as f:
            imagens = json.load(f)

        # Procurar a imagem pelo ID
        for img in imagens:
            if img['id'] == int(image_id):  # Garantir que compara como inteiro
                return img  # Retorna o objeto encontrado

        # Se não encontrar
        return None
    except Exception as e:
        print("Erro ao ler o ficheiro:", e)
        return None

@app.route('/privadas')
def renderizarprivadas():
    myImages = getMyImages(True)
    return render_template("privadas.html", nome=session.get('nome'), username=session.get('username'), email=session.get('email'), categorias=session.get('categorias'), profile_pic=session.get('profile_pic'), myImages = myImages)


def getMyImages(private=False):
    try:
        with open('photos.json', 'r') as photos:
            allImages = json.load(photos)
            user_id = session.get('user_id')

            # Filtrar imagens do utilizador
            minhas_imagens = [img for img in allImages if img.get('autor_id') == user_id]

            if private:
                # Mostrar apenas privadas
                minhas_imagens = [img for img in minhas_imagens if img.get('isPublic') == False]
            else:
                # Mostrar apenas públicas
                minhas_imagens = [img for img in minhas_imagens if img.get('isPublic') == True]

            return minhas_imagens[::-1]

    except (FileNotFoundError, json.JSONDecodeError):
        return []

# END OF UPLOAD FUNCTION

@app.route('/perfil')
def perfil():
    myImages = getMyImages()
    return render_template("perfil.html", nome=session.get('nome'), username=session.get('username'), email=session.get('email'), categorias=session.get('categorias'), profile_pic=session.get('profile_pic'), myImages = myImages)

@app.route('/uploadProfilePic', methods=['POST'])
def upload_profile_pic():
    
    profile_picture = request.files.get('profile_picture')
    
    # Garantir nome seguro
    nome_ficheiro = secure_filename(profile_picture.filename)
    extensao = nome_ficheiro.split('.')[-1]
    nome_final = f"profile_{session['user_id']}_{int(time.time() * 1000)}.{extensao}"
    caminho = os.path.join(UPLOAD_FOLDER, nome_final)
    
    # Guardar imagem
    profile_picture.save(caminho)
    
    # Atualizar utilizador no JSON
    utilizadores = carregar_utilizadores()
    for user in utilizadores:
        if user['user_id'] == session['user_id']:
            user['profile_pic'] = f'/static/all_images/{nome_final}'
            session['profile_pic'] = user['profile_pic']
            break
    
    guardar_utilizadores(utilizadores)
    
    return redirect(url_for('perfil'))

@app.route('/upload')
def upload():
    # Verificar se o utilizador tem sessão ativa
    if 'user_id' not in session:
        return redirect(url_for('home'))
    return render_template("upload.html")

# NOTIFICATIONS FUNCTION

@app.route('/notificacoes')
def notificacoes():
    
    try:
        with open('notificacoes.json', 'r') as f:
            todas = json.load(f)

            user_id = session.get('user_id')

            minhas_notificacoes = [notificacoes for notificacoes in todas if notificacoes.get('autor_id') == user_id or notificacoes.get('fromAdmin')][::-1]
    except:
        minhas_notificacoes = []

    return render_template("notificacoes.html", notificacoes=minhas_notificacoes)

@app.route('/posts')
def posts():
    return render_template("posts.html")

@app.route('/edicaoFotos')
def edicaoFotos():
    return render_template("edicaoFotos.html")

@app.route('/compartilhar/<imageId>')
def compartilhar(imageId):
    img = getImageById(imageId)
    return render_template('compartilhar.html', imageId= imageId, imageURL= img['url'])

@app.route('/admin')
def paginaAdmin():

    utilizadores = carregar_utilizadores()

    
    total_admin = sum(1 for admin in utilizadores if admin["isAdmin"])
    total_normal = sum(1 for admin in utilizadores if not admin["isAdmin"])

    #CÓDIGO PARA GERAR OS GRÁFICOS:

    #gráfico para utilizadores e admins
    legendas = ['Admins', 'Users']
    valores= [total_admin, total_normal]

    
    grafico.figure(figsize=(4,4))
    grafico.pie(valores, labels=legendas, autopct='%1.1f%%')
    grafico.title("Distribuição de Utilizadores")

    
    grafico.savefig("static/grafico_admins.png")
    grafico.close()

    return render_template('admin.html', utilizadores = utilizadores)

@app.route ("/admin/enviar-notificacao", methods=['POST'])
def enviar_notificacao():
    mensagem = request.form.get('mensagem') 

    try:
        with open('notificacoes.json', 'r') as f:
            lista = json.load(f)
    except:
        lista = []

    novaNotificacao = {
        "nome": session.get('nome'),
        "mensagem": mensagem,
        "hora": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "fromAdmin": True
        
    }

    lista.append(novaNotificacao)

    with open('notificacoes.json', 'w') as f:
        json.dump(lista, f, indent=4)

    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True)
    
    