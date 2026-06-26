# Contexto 

Estou desenvolvendo uma aplicação simples em Streamlit.

## Caminhhos dos Arquivos

`data/faturas/*.csv`
`data/fichas/*.csv`
`data/identificadores/*.csv`

Em geral:
- Duas concessionárias: Sabesp e EDP

## Faturas

### EDP (`data/faturas/faturas_edp.csv`)

```csv
field_name,regex_pattern
num_fatura,\d{27}(\d{8})
uc,"(\d[\d.]{5,}-\d{2})"
medidor,MEDIDOR:\s*0*(\d+)
valor,"(?:(?:\d{2}/\d{2}/\d{4})\s+|TOTAL\s+)([\d.\s]+,\s*\d{2})"
consumo,"Consumo kWh\s*(\d+[\s\d]*),\d+,"
vencimento,(?:MEDIDOR:|CEP:)\s*.*?\s*(\d{2}/\d{2}/\d{4})
debito,Débito automático
retencao,"Retenção Imposto de Renda\s+(?:\d+,\d{4}\s+)?(\d+[\s\d]*,[\s\d]+)"
```

### Sabesp (`data/faturas/faturas_sabesp.csv`)

```csv
field_name,regex_pattern
num_fatura,(SOR\d+)
rgi,Pde/Rgi:\s*(\d+)
hidrometro,Hidrômetro:\s*([A-Z0-9]+)
valor,"TOTAL\s*:?\s*R\$\s*[\s\*]*([\d,.]+)"
consumo,Água:\s*\d{2}/\d{2}/\d{2}\s*\d+(?:\s*\d{2}/\d{2}/\d{2}\s*\d+)?\s*(\d+)
vencimento,VENCIMENTO:\s*(\d{2}/\d{2}/\d{4})
debito,DÉBITO AUTOMÁTICO
retencao,"Retenção:.*?%\s+(\d+,\d{2})"
```

### Fichas

> Obs: para preservar dados sensíveis, não irei colocá-los, mas irei informar os arquivos CSVs existentes e suas colunas.

### Arquivos

- `data/fichas/fichas_edp_centros.csv`:
    - **Colunas:** ficha,acao,secretaria,empenho,af
- `data/fichas/fichas_edp_sedis.csv`:
    - **Colunas:** ficha,acao,secretaria,empenho,af
- `data/fichas/fichas_sabesap_centros.csv`:
    - **Colunas:** ficha,acao,secretaria,empenho,af
- `data/fichas/fichas_sabesap_sedis.csv`:
    - **Colunas:** ficha,acao,secretaria,empenho,af

## Identificadores

> Obs: para preservar dados sensíveis, não irei colocá-los, mas irei informar os arquivos CSVs existentes e suas colunas.

### Arquivos

- `data/identificadores/identificadores_edp_centros`: UCs de Centros Comunitários
    - **Colunas:** ficha,acao,uc
- `data/identificadores/identificadores_sabesp_centros`: RGIs de Centros Comunitários
    - **Colunas:** ficha,acao,rgi
- `data/identificadores/identificadores_edp_sedis`: UCs da SEDIS
    - **Colunas:** ficha,acao,uc
- `data/identificadores/identificadores_sabesp_sedis`: RGIs da SEDIS
    - **Colunas:** ficha,acao,rgi

## Definições

- RGI = Identificador Sabesp
- UC = Identificador EDP
- Locais = SEDIS e Centros Comunitários

# Aplicação

## Estrutura do Projeto

```raw
core/

data/
    faturas/*.csv
    fichas/*.csv
    identificadores/*.csv

pages/
    home.py

app.py
README.md
requirements.txt
```

## Estrutura funcional

### 1. Geração de Planilha (`core/csv_processor.py`)

- Extração dos dados de faturas PDF das concessionárias EDP e Sabesp, utilizando os RegEx de cada uma (`data/faturas/*.csv`)
- Agrupamento de todas as faturas lançadas numa planilha CSV
- Obs: a planilha deve filtrar o local (Centro Comunitário ou SEDIS), com base na ficha vinculada ao identificador da fatura
- Ex: suponha que eu tenha lançado 41 faturas de uma vez, 20 são dos centros comunitários e 21 são da SEDIS e eu tenha selecionado o local como SEDIS. O sistema deve verificar o identificador presente no documento da fatura (RGI para Sabesp ou UC para EDP) através dos códigos RegEX, verificar se esse identificador existe na base de dados de identificadores do local selecionado e retornar na planilha somente os dados das faturas (campos dos RegEx viram colunas) que seus identificadores dão match com a base de dados de identificadores do local selecionado.

### 2. Geração de Relatório (`core/report_processor.py`)

- Agrupamento dos dados extraídos das faturas com base nas fichas orçamentárias.
- Somatório de faturas, com base no vínculo de seu identificador com a sua ficha
    Ex: supondo que há 5 RGIs (Sabesp) que está vinculada à ficha 133. O relatório deve retornar o somatório das 5 faturas.
- Relatório em formato `.xlsx`

#### Layout do relatório

- Colunas A-H
- Fonte padrão: Arial
- Imagens (Linha 1): Imagem 1 em A-B, Imagem 2 de C-F
- Título (Linha 2): Negrito, Merge A-H, Centralizado, 20pt, Fonte #ffffff, Fundo #2f5597
    - Conteúdo: `f'Relatório das faturas {concessionaria} referentes a {mes_competencia}'`
- Subtítulo (Linha 3): Negrito, Merge A-H, Centralizado, 20pt, Fonte #ffffff, Fundo #2f5597
    - Conteúdo `f'Débito {tipo_debito} - {conta} - Vencimento {vencimento} - {local}'`
- Colunas (Linha 4): Negrito, Centralizado, 11pt, Fonte #000000, Fundo #dae3f3
    - A4: 'DOTAÇÃO'
    - B4: 'AÇÃO'
    - C4: 'SECRETARIA RESPONSAVEL'
    - D4: 'EMPENHO'
    - E4: 'AF'
    - F4: 'VALOR LIQUIDO'
    - G4: 'IR'
    - H4: 'VALOR BRUTO'
        - OBS: F4 + G4

- Última linha:
    - Negrito, 11pt, Fonte #000000, Fundo #dae3f3
    - Colunas A-E: Merge, Centralizado
        - Conteúdo: 'Total Geral'
    - Coluna F: Somatório de 'VALOR LÍQUIDO'
    - Coluna G: Somatório de 'IR'
    - Coluna H: F+GS

#### Funcionalidade extra: ZIP

- Cópia das faturas PDFs em um arquivo ZIP
- Verificação dos identificadores das faturas PDF
- Agrupamento das faturas por ficha
- Criação de pastas dentro do ZIP, recebendo o nome da ficha + ação, no formato `ficha (ação)`
- **Ex:** Há 5 faturas que pertencem à ficha 133, vão para a pasta `133 (2122)` (supondo que a ação dela seja 2122)
- Essa funcionalidade deve estar totalmente alinhada à geração de relatório, seguindo os filtros de tipo de débito, local e concessionária

# Código `pages/home.py`

```py
import streamlit as st

if 'valid_upload' not in st.session_state:
    st.session_state.valid_upload = False

if 'valid_option' not in st.session_state:
    st.session_state.valid_option = False

def home():
    st.title('Sistema de Extração de Faturas')

    st.subheader('1. Upload de Faturas')
    
    left_column, right_column = st.columns(2)

    with left_column:
        concessionaria = st.selectbox(label='Selecione uma concessionária', options=['EDP', 'Sabesp'])
    with right_column:
        mes_competencia = st.text_input(label='Digite o mês de competência (ex. Jan/2026):')

    faturas = st.file_uploader('Faça o upload de suas faturas aqui:', type=['pdf'], accept_multiple_files=True)

    upload_button = st.button(label='Processar', width='stretch', type='primary', key='upload_button') 

    if upload_button:
        if not(mes_competencia and faturas):
            st.warning('Preencha todos os campos')
        else:
            st.session_state.valid_upload = True

    if st.session_state.get('valid_upload', False):
        st.subheader('2. Opções de Processamento')
        
        option = st.selectbox(label='Selecione uma opção de processamento:', options=['Planilha', 'Relatório'])
        
        if option == 'Planilha':
            local = st.selectbox(label='Selecione o local:', options=['SEDIS', 'Centros Comunitários'])
        if option == 'Relatório':
            local = st.selectbox(label='Selecione o local:', options=['SEDIS', 'Centros Comunitários'])
            
            left_column, right_column = st.columns(2)

            with left_column:
                tipo_debito = st.selectbox(label='Selecione o tipo de débito:', options=['Manual', 'Automático'])
            with right_column:
                conta = st.text_input(label='Digite a conta bancária:')
                
            gerar_zip = st.selectbox(label='Gerar arquivo ZIP?', options=['Sim', 'Não'])

        process_button = st.button(label='Processar', width='stretch', type='primary', key='process_button')

        if process_button:
            st.text(f'A opção "{option}" foi selecionada')
```

# Considerações finais

Você deve garantir que a geração de planilha siga estritamente a ordem dos identificadores em `data/identificadores/*.csv`

**Exemplo:**
- Suponha que em `identificadores_sabesp_centro.csv` a ordem de rgis seja: 1, 6, 7, 9
- Na planilha agrupada das faturas, deve aparecer as faturas na ordem dos identificadores.

Além disso:
- Adote strings com aspas simples
- Zero comentários nos códigos
- Adote boas práticas de programação
- Adote tratamentos de erro
- O código deve ser em inglês (EXCETO OS NOMES REFERENTES AOS DADOS DA UI E DOS CAMPOS DAS PLANILHAS)
- Você deve agir como um desenvolvedor sênior