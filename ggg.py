from PIL import Image
import os

def remover_borda_1px(pasta_entrada, pasta_saida):
    os.makedirs(pasta_saida, exist_ok=True)

    for nome_arquivo in os.listdir(pasta_entrada):
        if nome_arquivo.endswith(".png"):
            caminho_entrada = os.path.join(pasta_entrada, nome_arquivo)
            imagem = Image.open(caminho_entrada)
            largura, altura = imagem.size

            # Define nova caixa sem a borda de 1px
            box = (1, 1, largura - 1, altura - 1)
            imagem_cortada = imagem.crop(box)

            caminho_saida = os.path.join(pasta_saida, nome_arquivo)
            imagem_cortada.save(caminho_saida)

    print(f"✅ Bordas removidas e salvas em: {pasta_saida}")


# Exemplo de uso
remover_borda_1px("FramesSemBorda", "FFF")