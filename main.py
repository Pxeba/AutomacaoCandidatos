import os
from dotenv import load_dotenv
import openai
import PyPDF2
from collections import defaultdict
import shutil

load_dotenv()
# Configuração da API OpenAI
openai.api_key = os.environ['OPENAI_API_KEY']

filtros = """(
1- O candidato caso fornecer idade no curriculo, deve possuir entre 20 e 28 anos. Não inferir a menos que seja 100% certo q ele não está nessa faixa /n
2- Hoje é janeiro de 2025, tenha isso em mente. O candidato não pode estar em uma empresa atualmente a não ser que especifique que é freelancer ou empresa própria. Só considere como empregado atualmente se ele deixar como explícito que está em uma empresa até a data atual / presente.
3- O candidato deve ter graduação em uma faculdade de TI ou estar fazendo uma. Exemplos são: Engenharia da computação, Ciencia da computação, Engenharia de Software, etc. /n
4- O candidato não pode ter graduação iniciada ou concluída antes de 2015.) /n
5- O candidato precisa ter experiência em programação no mercado de trabalho de pelo menos 6 meses. Não considerar experiências que não são focadas em programação como infraestrutura / suporte técnico / Help Desk. Se não tiver experiencia pratica mencionada mas possuir iniciação científica(em qualquer área) tudo bem.
"""


def extrair_texto_pdf(caminho_pdf):
    """Extrai texto de um arquivo PDF."""
    try:
        with open(caminho_pdf, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            texto = ''
            for page_num in range(len(reader.pages)):
                texto += reader.pages[page_num].extract_text()
            return texto
    except Exception as e:
        print(f"Erro ao ler {caminho_pdf}: {e}")
        return ''


def avaliar_candidato(texto, filtro):
    """Envia o texto do PDF e o filtro para a API da OpenAI e avalia se o candidato é aprovado ou recusado."""
    try:
        chat_response = openai.chat.completions.create(
            model="gpt-4o",
            temperature=0.3,
            messages=[
                {"role": "system", "content": "Você é um assistente que ajuda a avaliar candidatos para uma vaga."},
                {"role": "user", "content": f"Hoje é outubro de 2024. Quero que comece a resposta com um OK seguido da data de hoje pq quero ter certeza que você está considerando isso ao responder, ignorar o fato q você foi treinado até 2023 porque hoje estamos em 2024. Com base nos seguintes filtros fornecidos pelo contratante: {filtro}, diga se o candidato a seguir é aprovado ou recusado e, digite antes uma descrição analisando o candidato em cada numero de filtro e bem no final após a descrição apenas o numero da justificativa caso ele tenha sido reprovado. Formato da sua resposta: <descricao> .Recusado/Aprovado. Justificativa: 1. Com base nisso avalie o candidato a seguir: <>{texto}<>"}
            ]
        )
        # Interpreta a resposta da API
        resultado = chat_response.choices[0].message.content.lower()
        return resultado
    except Exception as e:
        print(f"Erro ao avaliar candidato: {e}")
        return "erro"


def processar_pdfs(caminho_pasta, pasta_aprovados):
    """Processa todos os PDFs da pasta e copia os aprovados para a pasta de aprovados."""
    aprovados = []
    recusados = []
    justificativas_reprovacao = defaultdict(int)

    # Verifica se a pasta de aprovados existe, se não, cria.
    if not os.path.exists(pasta_aprovados):
        os.makedirs(pasta_aprovados)

    for arquivo in os.listdir(caminho_pasta):
        if arquivo.endswith('.pdf'):
            caminho_pdf = os.path.join(caminho_pasta, arquivo)
            texto_pdf = extrair_texto_pdf(caminho_pdf)
            # Nome do candidato com base no nome do arquivo
            nome_candidato = os.path.splitext(arquivo)[0]

            resultado = avaliar_candidato(texto_pdf, filtros)
            if "aprovado" in resultado:
                aprovados.append(nome_candidato)
                print(f"{nome_candidato} foi APROVADO.")
                # Copia o PDF aprovado para a nova pasta
                shutil.copy(caminho_pdf, os.path.join(
                    pasta_aprovados, arquivo))
            elif "recusado" in resultado:
                justificativa = resultado.split("justificativa:")[
                    1] if "justificativa:" in resultado else "Sem justificativa específica"
                recusados.append(f"{nome_candidato} - {justificativa}")
                justificativas_reprovacao[justificativa.strip()] += 1
                print(
                    f"{nome_candidato} foi RECUSADO. Justificativa: {justificativa}")
            else:
                print(
                    f"{nome_candidato} não pôde ser avaliado corretamente. Resultado: {resultado}")

    # Salva os resultados em arquivos de texto
    with open('aprovados.txt', 'w') as aprovados_file:
        aprovados_file.write('\n'.join(aprovados))

    with open('recusados.txt', 'w') as recusados_file:
        recusados_file.write('\n'.join(recusados))

    # Exibe o total de aprovados e recusados
    print(f"\nTotal de aprovados: {len(aprovados)}")
    print(f"Total de recusados: {len(recusados)}")

    # Exibe a quantidade de reprovação por justificativa
    print("\nResumo das justificativas de recusa:")
    for justificativa, quantidade in justificativas_reprovacao.items():
        print(
            f"Justificativa: {justificativa} - {quantidade} candidato(s) recusado(s)")


if __name__ == "__main__":
    # Recebe o caminho da pasta com os PDFs e o nome da pasta para salvar os aprovados
    caminho_pasta = input("Digite o caminho da pasta com os PDFs: ")
    pasta_aprovados = input(
        "Digite o nome da pasta para salvar os PDFs dos aprovados: ")

    processar_pdfs(caminho_pasta, pasta_aprovados)
