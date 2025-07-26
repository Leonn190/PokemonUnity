from PIL import Image
import os

def fatiar_spritesheet(caminho_imagem, largura_frame, altura_frame, pasta_saida):
    os.makedirs(pasta_saida, exist_ok=True)
    
    imagem = Image.open(caminho_imagem)
    img_largura, img_altura = imagem.size

    contador = 0
    for y in range(0, img_altura, altura_frame):
        for x in range(0, img_largura, largura_frame):
            box = (x, y, x + largura_frame, y + altura_frame)
            frame = imagem.crop(box)
            caminho_frame = os.path.join(pasta_saida, f"frame_{contador}.png")
            frame.save(caminho_frame)
            contador += 1

    print(f"✅ {contador} frames extraídos para: {pasta_saida}")


fatiar_spritesheet("164996.png", 70, 70, "FramesExtraddidos")