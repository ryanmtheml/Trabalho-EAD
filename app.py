import json
import os
import time
from flask import Flask, render_template, request, session, redirect, url_for
from pathlib import Path #blioteca para manipular caminhos de ficheiros
from werkzeug.utils import secure_filename
from modules import upload as uploadlb
from flask_bcrypt import Bcrypt
from PIL import Image, ImageFilter, ImageEnhance


app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "secret"

UPLOAD_FOLDER = os.path.join('static', 'all_images') # criando caminho onde defino pasta para guardar as imagens (uso a os library)
os.makedirs(UPLOAD_FOLDER, exist_ok=True) #verificação da pasta (se não existir, é criada uma)



ficheiro_utilizadores = Path(app.root_path) / 'utilizadores.json'
ficheiro_photos = Path(app.root_path) / 'photos.json'
# Carregar lista de utilizadores
def carregar_utilizadores():
    try:
        with open(ficheiro_utilizadores, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def guardar_utilizadores(dados):
    with open(ficheiro_utilizadores, 'w', encoding='utf-8') as userFile:
        json.dump(dados, userFile, indent=4, ensure_ascii=False)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/feed')
def feed():
    with open(ficheiro_utilizadores, 'r', encoding='utf-8') as f:
        utilizadores = json.load(f)
        
        
    with open(ficheiro_photos, 'r', encoding='utf-8') as f:
        fotos = json.load(f)
    
    categoria = request.args.get('categoria')
    
    for user in utilizadores:
        if user['user_id'] == session.get('user_id'):
            categorias_escolhidas = user['categorias']
            break
    
    fotos_filtradas = []
    if categoria is None:
        for foto in fotos:
            for cat in foto['categoria']:
                if cat in categorias_escolhidas:
                    fotos_filtradas.append(foto)
                    break
    else:
        for foto in fotos:
            for cat in foto['categoria']:
                if cat == categoria and int(foto['autor_id']) != session.get('user_id'):
                    fotos_filtradas.append(foto)
    return render_template('feed.html', profile_pic=session.get('profile_pic'), fotos=fotos_filtradas[::-1])

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
            user_encontrado = True
            break
        if user['username'] == username and bcrypt.check_password_hash(user['password'], pw) == False:
            return "<h1>Erro: Palavra-passe incorreta!</h1>"
        

    if user_encontrado:
        
        return redirect('/feed')
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
    session['profile_pic'] = ''
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
    
    
    
    # 5. Redirecionar para a rota /feed
    return redirect('/feed')




@app.route('/uploadimg', methods = ['POST'] )
def uploadImagem():
    autor_id = session['user_id']
    imagem = request.files['imagem']
    
    if imagem.filename == '':
        return "Nenhum ficheiro selecionado!"
    
    # Garantir nome seguro
    nome_ficheiro = secure_filename(imagem.filename)
    id = int(time.time() * 1000) # time stamp, definindo assim nome unico para o id
    session['image_id'] = id
    extensao = nome_ficheiro.split('.')[-1]
    nome_final = f"{id}.{extensao}" 
    caminho = os.path.join(UPLOAD_FOLDER, nome_final) # pega a pasta e o arquivo, adicionando o caminho do arquivo na pasta
    imgprivacidade = True  # Por padrão será pública
    # Guardar imagem
    imagem.save(caminho) #salvo a imagem no caminho
    session['current_upload'] = caminho  # Store the file path
    uploadlb.criarImagem(autor_id,caminho,id, imgprivacidade)
    return render_template('edicaoFotos.html', imageURL='/static/all_images/' + nome_final, imageId = id, cropped=False)


@app.route('/crop', methods=['POST'])
def crop_image():
    imagem = session.get('current_upload')
    if not imagem:
        return "Nenhum ficheiro selecionado!"
    
    # Normalize the path to handle mixed separators
    imagem = os.path.normpath(imagem)
    img = Image.open(imagem)
    
    # Get crop parameters from form
    left = int(float(request.form.get('crop_x', 0)))
    top = int(float(request.form.get('crop_y', 0)))
    width = int(float(request.form.get('crop_width', img.width)))
    height = int(float(request.form.get('crop_height', img.height)))
    
    # Calculate right and bottom coordinates
    right = left + width
    bottom = top + height
    
    # Validate crop box
    if right <= left or bottom <= top:
        return "Coordenadas de crop inválidas!"
    
    # Crop the image
    img_cropped = img.crop((left, top, right, bottom))
    
    # Close original image to release file handle
    img.close()
    
    # Save cropped image, overwriting the original
    img_cropped.save(imagem)
    
    return render_template('edicaoFotos.html', imageURL='/static/all_images/' + os.path.basename(imagem), imageId = request.form.get('imageId'), cropped=False, filtered=False, contrasted=False)
    
    
    
@app.route('/showCroppedInput')
def showCroppedInput():
    imagem = session.get('current_upload')
    return render_template('edicaoFotos.html', imageURL='/static/all_images/' + os.path.basename(imagem), imageId = request.args.get('imageId'), cropped=True, filtered=False, contrasted=False)
    
    
@app.route('/showFilterInput')
def showFilterInput():
    imagem = session.get('current_upload')
    return render_template('edicaoFotos.html', imageURL='/static/all_images/' + os.path.basename(imagem), imageId = request.args.get('imageId'), cropped=False, filtered=True, contrasted=False)

@app.route('/showContrastInput')
def showContrastInput():
    imagem = session.get('current_upload')
    return render_template('edicaoFotos.html', imageURL='/static/all_images/' + os.path.basename(imagem), imageId = request.args.get('imageId'), cropped=False, filtered=False, contrasted=True)
    
    

@app.route('/applyFilter', methods=['POST'])
def applyFilter():
    current_path = session.get('current_upload')
    
    # Create backup on first filter application
    backup_path = current_path.replace('.', '_backup.')
    print(backup_path)
    if not os.path.exists(backup_path):
        img_original = Image.open(current_path)
        img_original.save(backup_path)
        img_original.close()
    
    # Always load from backup
    filtro = request.form.get('filter_type')
    img = Image.open(backup_path)
    
    if filtro=='blur':
        img_filtered = img.filter(ImageFilter.BLUR)
    elif filtro=='contour':
        img_filtered = img.filter(ImageFilter.CONTOUR)
    elif filtro=='detail':
        img_filtered = img.filter(ImageFilter.DETAIL)
    elif filtro=='edge_enhance':
        img_filtered = img.filter(ImageFilter.EDGE_ENHANCE)
    elif filtro=='edge_enhance_more':
        img_filtered = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    elif filtro=='emboss':
        img_filtered = img.filter(ImageFilter.EMBOSS)
    elif filtro=='find_edges':
        img_filtered = img.filter(ImageFilter.FIND_EDGES)
    elif filtro=='sharpen':
        img_filtered = img.filter(ImageFilter.SHARPEN)
    elif filtro=='smooth':
        img_filtered = img.filter(ImageFilter.SMOOTH)
    else:
        img_filtered = img
        
    img.close()
    img_filtered.save(current_path)
    
    return render_template('edicaoFotos.html', imageURL='/static/all_images/' + os.path.basename(current_path), imageId = request.args.get('imageId'), filtered=True)

@app.route('/applyContrast', methods=['POST'])
def applyContrast():
    current_path = session.get('current_upload')
    
    # Create backup on first application
    backup_path = current_path.replace('.', '_backup.')
    if not os.path.exists(backup_path):
        img_original = Image.open(current_path)
        img_original.save(backup_path)
        img_original.close()
    
    # Always load from backup
    contrast_value = float(request.form.get('contrast_value', 1.0))
    img = Image.open(backup_path)
    img_contrasted = ImageEnhance.Contrast(img)
    img_contrasted = img_contrasted.enhance(contrast_value)
    img.close()
    img_contrasted.save(current_path)
    
    return render_template('edicaoFotos.html', imageURL='/static/all_images/' + os.path.basename(current_path), imageId = request.args.get('imageId'), contrasted=True)

@app.route('/applyFlip')
def applyFlip():
    current_path = session.get('current_upload')
    
    # Create backup on first application
    backup_path = current_path.replace('.', '_backup.')
    if not os.path.exists(backup_path):
        img_original = Image.open(current_path)
        img_original.save(backup_path)
        img_original.close()
    
    # Always load from backup
    img = Image.open(backup_path)
    img_flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
    img.close()
    img_flipped.save(current_path)
    
    return render_template('edicaoFotos.html', imageURL='/static/all_images/' + os.path.basename(current_path), imageId = request.args.get('imageId'))


def getImageById(image_id):
    try:
        # Abrir o ficheiro JSON
        with open('photos.json', 'r', encoding='utf-8') as f:
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



def getAllImages():
    try:
        with open('photos.json', 'r', encoding='utf-8') as photos:
            allImages = json.load(photos)
            print(allImages)
            return allImages[::-1]

    except (FileNotFoundError, json.JSONDecodeError):
        return []



def getMyImages(private=False):
    try:
        with open('photos.json', 'r', encoding='utf-8') as photos:
            allImages = json.load(photos)
            user_id = session.get('user_id')
            
            print(f"DEBUG - user_id do session: {user_id} (tipo: {type(user_id)})")
            print(f"DEBUG - Total de imagens: {len(allImages)}")

            # Filtrar imagens do utilizador (converter ambos para string para comparar)
            minhas_imagens = [img for img in allImages if str(img.get('autor_id')) == str(user_id)]
            
            print(f"DEBUG - Imagens do utilizador (antes filtro público/privado): {len(minhas_imagens)}")

            if private:
                # Mostrar apenas privadas
                minhas_imagens = [img for img in minhas_imagens if img.get('isPublic') == False]
            else:
                # Mostrar apenas públicas
                minhas_imagens = [img for img in minhas_imagens if img.get('isPublic') == True]
            
            print(f"DEBUG - Imagens após filtro (private={private}): {len(minhas_imagens)}")
            for img in minhas_imagens:
                print(f"  - ID: {img.get('id')}, isPublic: {img.get('isPublic')}, URL: {img.get('url')}")

            return minhas_imagens[::-1]

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"DEBUG - Erro ao ler photos.json: {e}")
        return []



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

@app.route('/notificacoes')
def notificacoes():
    return render_template("notificacoes.html")

@app.route('/edicaoFotos')
def edicaoFotos():
    return render_template("edicaoFotos.html")

@app.route('/compartilhar')
def compartilhar():
    img = session.get('current_upload')
    return render_template('compartilhar.html', imageURL=img)

@app.route('/compartilhar', methods=['POST'])
def compartilhar_post():
    # Obter dados do formulário
    descricao = request.form.get('descricaoFoto')
    categorias = request.form.getlist('categorias')  # Lista de categorias selecionadas
    privacidade = request.form.get('privacidade')
    nova_categoria = request.form.get('nomeCategoria', '').strip()
    
    # Se criou uma nova categoria, adicionar à lista
    if nova_categoria:
        categorias.append(nova_categoria)
    
    # Validar que pelo menos uma categoria foi fornecida
    if not categorias:
        return "<h1>Erro: Deve selecionar pelo menos uma categoria ou criar uma nova!</h1>"
    
    # create object image with new data on the JSON photos.json
    imagem = session.get('current_upload')
    imageId = session.get('image_id')
    print(imageId)
    try:
        with open('photos.json', 'r', encoding='utf-8') as f:
            imagens = json.load(f)

        for img in imagens:
            if img['id'] == int(imageId):
                img['descricao'] = descricao
                img['categoria'] = categorias
                if privacidade == 'publico':
                    img['isPublic'] = True
                else:
                    img['isPublic'] = False
                break

        with open('photos.json', 'w', encoding='utf-8') as f:
            json.dump(imagens, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print("Erro ao atualizar imagem:", e)

    
    return redirect('/perfil')


@app.route('/descricaoFotos')
def descricaoFotos():
    imageId = request.args.get('imageId')
    imagem = getImageById(imageId)
    folders = []
    with open(ficheiro_photos, 'r', encoding='utf-8') as f:
        fotos = json.load(f)
        for foto in fotos:
            if foto['id'] == int(imageId):
                descricao=foto['descricao']
                likes=foto['likes']
                comments=foto['comments']
                commentsText=foto.get('commentsText', [])
                break
            
    try:
        with open('folders.json', 'r', encoding='utf-8') as f:
            all_folders = json.load(f)
            for folder in all_folders:
                if int(folder['autor_id']) == session.get('user_id'):
                    folders.append(folder)
    except (FileNotFoundError, json.JSONDecodeError):
        folders = []
    if imagem:
        return render_template('descricaoFoto.html', imagem=imagem, profile_pic=session.get('profile_pic'), username=session.get('username'), descricao=descricao, nmrLikes=likes, nmrComentarios=comments, comentarios=commentsText, folders=folders)
    else:
        return "<h1>Erro: Imagem não encontrada!</h1>"
    
@app.route('/addComment', methods=['POST'])
def addComment():
    imageId = request.form.get('imageId')
    comentario = request.form.get('comentario')
    
    try:
        with open('photos.json', 'r', encoding='utf-8') as f:
            fotos = json.load(f)

        for foto in fotos:
            if foto['id'] == int(imageId):
                foto['comments'] += 1  # Incrementar o número de comentários
                foto['commentsText'].append(comentario)
                break

        with open('photos.json', 'w', encoding='utf-8') as f:
            json.dump(fotos, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print("Erro ao adicionar comentário:", e)
    
    return redirect(f'/descricaoFotos?imageId={imageId}')

@app.route('/addLike', methods=['POST'])
def addLike():
    imageId = request.form.get('imageId')
    
    try:
        with open('photos.json', 'r', encoding='utf-8') as f:
            fotos = json.load(f)

        for foto in fotos:
            if foto['id'] == int(imageId):
                if session['user_id'] in foto['userLikesId']:
                    # Usuário já curtiu a foto, então não faz nada ou pode implementar "descurtir"
                    foto['likes'] -= 1
                    foto['userLikesId'].remove(session['user_id'])  
                    break
                foto['likes'] += 1  # Incrementar o número de likes
                foto['userLikesId'].append(session['user_id'])  # Adicionar o ID do usuário à lista de likes
                break

        with open('photos.json', 'w', encoding='utf-8') as f:
            json.dump(fotos, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print("Erro ao adicionar like:", e)
    
    return redirect(f'/descricaoFotos?imageId={imageId}')

@app.route('/pesquisa', methods=['POST'])
def pesquisa():
    query = request.form.get('query', '').lower()
    
    with open(ficheiro_photos, 'r', encoding='utf-8') as f:
        fotos = json.load(f)
    
    fotos_encontradas = []
    for foto in fotos:
        # Verificar se a query está em alguma categoria (convertendo para minúsculas)
        categoria_match = any(query in cat.lower() for cat in foto['categoria'])
        # Verificar se a query está na descrição
        descricao_match = query in foto['descricao'].lower()
        
        if categoria_match or descricao_match:
            fotos_encontradas.append(foto)
    
    return render_template('feed.html', profile_pic=session.get('profile_pic'), fotos=fotos_encontradas[::-1])


@app.route('/folders')
def folders():
    user_id = session.get('user_id')
    try:
        with open('folders.json', 'r', encoding='utf-8') as f:
            folders = json.load(f)
            user_folders = []
            for folder in folders :
                print(folder['autor_id'], user_id)
                if int(folder['autor_id']) == user_id:
                    user_folders.append(folder)
            return render_template('folders.html', profile_pic=session.get('profile_pic'), folders=user_folders,  nome=session.get('nome'), username=session.get('username'), email=session.get('email'), categorias=session.get('categorias'))
    except (FileNotFoundError, json.JSONDecodeError):
        return render_template('folders.html', profile_pic=session.get('profile_pic'), folders=[])

@app.route('/folder')
def folder():
    folder_id = request.args.get('folderId')
    try:
        with open('folders.json', 'r', encoding='utf-8') as f:
            folders = json.load(f)
            for folder in folders:
                print(folder['id'], folder_id)
                if str(folder['id']) == str(folder_id):
                    fotos_id = folder['fotos_id']
                    fotos = []
                    with open('photos.json', 'r', encoding='utf-8') as pf:
                        all_photos = json.load(pf)
                        for foto in all_photos:
                            if foto['id'] in fotos_id:
                                fotos.append(foto)
                    return render_template('folder.html', profile_pic=session.get('profile_pic'), folder_name=folder['nome'], fotos=fotos, nome=session.get('nome'), username=session.get('username'), email=session.get('email'), categorias=session.get('categorias'))
            return "<h1>Erro: Pasta não encontrada!</h1>"
    except (FileNotFoundError, json.JSONDecodeError):
        return "<h1>Erro: Pasta não encontrada!</h1>"

@app.route('/createFolder', methods=['POST'])
def createFolder():
    folder_name = request.form.get('folder_name')
    user_id = session.get('user_id')
    image_id = request.form.get('imageId')
    try:
        with open('folders.json', 'r', encoding='utf-8') as f:
            folders = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        folders = []
    capaFolder = ''
    try:
        with open('photos.json', 'r', encoding='utf-8') as pf:
            all_photos = json.load(pf)
            for foto in all_photos:
                if foto['id'] == int(image_id):
                    capaFolder = foto['url']
                    break
    except (FileNotFoundError, json.JSONDecodeError):
        capaFolder = ''
    folderId = folders[-1]['id'] + 1 if folders else 1
    new_folder = {
        'id': folderId,
        'autor_id': user_id,
        'nome': folder_name,
        'fotos_id': [int(image_id)],
        'capa': capaFolder
    }
    folders.append(new_folder)
    
    with open('folders.json', 'w', encoding='utf-8') as f:
        json.dump(folders, f, indent=4, ensure_ascii=False)
    
    return redirect('/folders')

@app.route('/saveToFolder', methods=['POST'])
def saveToFolder():
    folder_id = request.form.get('folder_id')
    image_id = request.form.get('imageId')
    try:
        with open('folders.json', 'r', encoding='utf-8') as f:
            folders = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        folders = []
    print(folder_id, image_id)
    for folder in folders:
        if str(folder['id']) == str(folder_id):
            if int(image_id) not in folder['fotos_id']:
                folder['fotos_id'].append(int(image_id))
            break

    with open('folders.json', 'w', encoding='utf-8') as f:
        json.dump(folders, f, indent=4, ensure_ascii=False)

    return redirect(f'/folder?folderId={folder_id}')

if __name__ == '__main__':
    app.run(debug=True)

