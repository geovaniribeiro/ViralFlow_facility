# Manual ViralFlow GUI

> Interface gráfica para facilitar a execução do **ViralFlow** e a geração de relatórios de resultados.

## Sumário
- [Requisitos e Pré‑instalação](#requisitos-e-pré-instalação)
- [Instalação do ViralFlow](#instalação-do-viralflow)
- [Instalação da Interface Gráfica](#instalação-da-interface-gráfica)
- [Iniciando a Interface](#iniciando-a-interface)
- [Menu Inicial](#menu-inicial)
- [Utilitários](#utilitários)
- [Metadados e Avisos](#metadados-e-avisos)
  - [Ajuste do `config.yaml`](#ajuste-do-configyaml)
  - [Metadados do GAL](#metadados-do-gal)
- [Análise de SARS‑CoV‑2](#análise-de-sars-cov-2)
  - [Entradas Obrigatórias e Opcionais](#entradas-obrigatórias-e-opcionais)
  - [Selecionando Pastas/Arquivos](#selecionando-pastasarquivos)
  - [Parâmetros](#parâmetros)
  - [Execução](#execução)
  - [Saída e Estrutura de Resultados](#saída-e-estrutura-de-resultados)
  - [Conteúdo da pasta `RNSG_REPORT`](#conteúdo-da-pasta-rnsg_report)
- [Análise de DENV / CHIKV](#análise-de-denv--chikv)

---

## Requisitos e Pré‑instalação

> [!IMPORTANT]
> Para executar os instaladores `.AppImage` em sistemas baseados em Debian/Ubuntu, instale a biblioteca **libfuse2**.

```bash
sudo apt update
sudo apt install -y libfuse2
```

---

## Instalação do ViralFlow

1. (Opcional, se já instalado) Acesse a pasta `ViralFlow_facility/setup` e execute:
   - **Linux (GUI/duplo clique):** `ViralFlow_installer.AppImage`
2. Um terminal será aberto. Pressione **Enter** para iniciar a instalação.
3. Sua senha de usuário poderá ser solicitada.
4. Ao final, uma mensagem de sucesso será exibida no terminal.

---

## Instalação da Interface Gráfica

1. Na pasta `ViralFlow_facility/setup`, execute:
   - **Linux (GUI/duplo clique):** `ViralFlowGUI_installer.AppImage`
2. O terminal abrirá automaticamente. Pressione **Enter** para iniciar.
3. A senha do usuário poderá ser solicitada.
4. Ao término, uma mensagem de sucesso será exibida.

---

## Iniciando a Interface

1. Pressione a tecla **Iniciar** (Super/Windows).  
2. Pesquise por **“ViralFlow GUI”**.  
3. Clique no ícone para abrir.

> [!NOTE]
> Um terminal é aberto junto com a interface para acompanhar o progresso das análises. **Não feche o terminal** enquanto houver processamento.

---

## Menu Inicial

1. **Atualizar ViralFlow** — baixa a versão mais recente do repositório dos desenvolvedores.  
2. **Atualizar bancos** — atualiza *pangolin* e *nextclade*.  
3. **Selecionar vírus** — define o organismo alvo da análise.  
4. **Ir para Análise** — abre a tela de análise conforme o vírus selecionado.  
5. **Sair** — fecha a interface.

---

## Utilitários

### Atualização do ViralFlow
Atualiza o ViralFlow para a versão estável mais recente (https://viralflow.github.io/).

### Atualização de Banco de Dados
Atualiza as classificações do *pangolin* (SARS‑CoV‑2) e o *nextclade* quando aplicável.

---

## Metadados e Avisos

A interface executa o **ViralFlow** (montagem, variantes e classificação) e **gera arquivos complementares**: relatório de qualidade, planilhas de resultados e arquivos para submissão no **GISAID** (detalhes abaixo).

São usados **dois arquivos** para integrar montagem + dados epidemiológicos/usuário:

- `config.yaml`
- CSV de metadados exportado do **GAL**

### Ajuste do `config.yaml`

Edite o arquivo `ViralFlow_facility/config.yaml` e ajuste as chaves:

- `submitter`: usuário responsável pela submissão ao GISAID  
- `subm_lab`: nome do laboratório que submete  
- `subm_lab_addr`: endereço do laboratório  
- `authors`: lista de autores (responsáveis e chefias)

> [!WARNING]
> **Não remova as aspas** onde houver (linhas `subm_lab`, `subm_lab_addr` e `authors`). Salve o arquivo após as alterações.

### Metadados do GAL

1. Baixe o CSV em **Biologia Médica/Sequenciamento** (ou **Vírus / Sequenciamento**).  
2. **Não edite** o CSV para evitar problemas de codificação.  
3. **Correspondência de nomes**: o nome da amostra no sequenciador deve bater com o **código da amostra** ou **número de requisição** do GAL.  
4. Use a aba **Relatório Epidemiológico por Exame** → **Selecionar Campos: Marcar Todos** → defina o intervalo de datas → **Gerar**.  
5. Faça o download do `.zip` e **extraia** para obter o CSV a ser usado na análise.

---

## Análise de SARS‑CoV‑2

### Entradas Obrigatórias e Opcionais

- **Obrigatórios**
  - **Arquivo BED**
  - **Pasta de Entrada** (FASTQs)
  - **Pasta de Saída** (resultados)

- **Opcionais**
  - **Metadados (CSV)** do GAL
  - **Arquivo de Configuração (`config.yaml`)**

> Se os opcionais não forem fornecidos, a interface fará **apenas a montagem** (sem gerar arquivos de submissão ao GISAID e sem planilha de resultados).

### Selecionando Pastas/Arquivos

- Use o botão **Browse** para navegar e **Open/Choose** para selecionar.  
- Para voltar um nível, use **Diretório Parental**.  
- Na **Pasta de Saída**, crie uma nova pasta (ex.: `run_YYYYMMDD`) e selecione **Choose**.

### Parâmetros

- Clique em **Configurar Parâmetros** para ajustar as flags do ViralFlow.  
- A descrição completa dos parâmetros está na documentação oficial.

### Execução

- Com as entradas definidas, clique em **Executar ViralFlow**.  
- Acompanhe o progresso no terminal aberto junto à GUI.  
- Ao final, o terminal exibirá mensagem de conclusão, indicando sucesso ou erro.

### Saída e Estrutura de Resultados

Na **Pasta de Saída**, o ViralFlow cria:

1. **Diretórios por amostra**: `prefixo_results` (um por amostra).  
   - `prefixo` é derivado do nome do arquivo FASTQ.  
2. **`COMPILED_OUTPUT/`**: resultados compilados de toda a corrida.  
3. **`RNSG_REPORT/`**: artefatos processados para validação e submissões.

> A lista detalhada de arquivos do `COMPILED_OUTPUT` está na documentação do projeto viralflow (https://viralflow.github.io/).

### Conteúdo da pasta `RNSG_REPORT`

- `EpiCov.csv` — CSV pronto para submissão ao **GISAID EpiCoV**.  
- `LACEN_seq.fasta` — FASTA formatado para submissão (apenas genomas com **> 90% de cobertura**).  
- `Planilha_de_Resultado.xlsx` — planilha de resultados.  
- `Quality_check.png` — gráficos para inspeção da qualidade (profundidade, % de cobertura e leituras por amostra).

---

## Análise de DENV / CHIKV

- Processo idêntico ao de SARS‑CoV‑2, **com um campo adicional**: **RefSeq**.  
- Selecione genoma de referência (DENV1/2/3/4 ou CHIKV).

Além dos itens padrão, é gerado o arquivo **`EpiArbo.csv`** para submissão na plataforma **GISAID EpiArbo**.

---

