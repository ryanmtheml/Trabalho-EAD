from datetime import datetime
import json

def carregarImagens(): #carregando as características das imagens da página photos.json
    try:
        with open('photos.json', 'r', encoding='utf-8') as photos:
            return json.load(photos)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def escreverImagens(dados):
    with open('photos.json', 'w', encoding='utf-8') as photos:
        json.dump(dados, photos, indent=4, ensure_ascii=False)

def criarImagem(autor_id,caminho, id, imgprivacidade):
    fotos = carregarImagens()

    novafoto = {    
        # "id": int(datetime.now().timestamp()), #criando id unico 
        "id": id,
        "autor_id": autor_id,
        "url": caminho,
        "isPublic": imgprivacidade,
        "categoria": [],
        "descricao": "",
        "likes": 0,
        "comments": 0,
        "folders": []
    }

    fotos.append(novafoto)

    escreverImagens(fotos)

    print(fotos)

