from datetime import datetime
import json

def carregarImagens(): #carregando as características das imagens da página photos.json
    try:
        with open('photos.json', 'r') as photos:
            return json.load(photos)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def escreverImagens(dados):
    with open('photos.json', 'w+') as photos:
     jsonDados = json.dumps(dados)
     photos.write(jsonDados)

def criarImagem(autor_id,caminho):
    fotos = carregarImagens()

    novafoto = {    
        "id": int(datetime.now().timestamp()), #criando id unico 
        "autor_id": autor_id,
        "url": caminho
    }

    fotos.append(novafoto)

    escreverImagens(fotos)

    print(fotos)
