# Manual de Instalação e Uso - ViralFlow GUI

## Instalação

### Passo 1: Acessar o Diretório de Instalação
1. Navegue até o local onde a pasta `ViralFlow_Facility` foi salva.
2. Entre na pasta `Installer`.
3. Pressione `Ctrl + Shift` e clique com o botão direito do mouse.
4. Selecione a opção `Abrir Terminal`.

### Passo 2: Executar o Script de Instalação
No terminal, digite o comando correspondente e pressione `Enter`:

- Para instalação completa (**ViralFlow + Interface Gráfica**):
  ```sh
  ./viralflow_full.sh
  ```
- Para instalar apenas a **interface gráfica** (caso o ViralFlow já esteja instalado):
  ```sh
  ./viralflow_GUI_setup.sh
  ```

### Passo 3: Concluir a Instalação
- Insira a senha de `sudo` (a mesma senha do usuário) e pressione `Enter`.
- Ao final da instalação, uma mensagem de conclusão será exibida.

## Abrindo a Interface Gráfica
1. Pressione o botão `Iniciar` no teclado.
2. No campo de busca, digite `ViralFlow GUI`.
3. Clique no ícone correspondente para abrir a interface gráfica.

Uma interface semelhante à mostrada abaixo será aberta, juntamente com um terminal.

## ⚠️ Avisos Importantes
O uso desta ferramenta requer o pareamento de informações entre arquivos **FASTQ** e dados obtidos do **GAL**. Para evitar erros:

- **Baixe** o arquivo em formato **CSV** do GAL (*módulo Sequenciamento e/ou "Vírus, Biologia Médica/Sequenciamento"*).
- **Não edite** o arquivo CSV para evitar problemas de formatação e codificação.
- O **nome das amostras cadastradas no sequenciador** deve corresponder aos códigos das amostras oriundas do GAL (*coluna `Código de Amostra`*).

## 🚀 Principais Funcionalidades
1. **📥 Baixar Atualizações** diretamente do repositório do ViralFlow.
2. **🔄 Atualizar Bancos de Dados** do Pangolin e Nextclade.
3. **🦠 Selecionar o Vírus** de interesse para análise.
4. **🔬 Ir para Tela de Montagem** para iniciar a análise.
5. **❌ Finalizar a Interface Gráfica** ao concluir o uso.

## 📌 Atualização de Bancos de Dados
Para manter a análise precisa, utilize a opção de atualização dos bancos de dados do **Pangolin** e **Nextclade** sempre que possível.

## 🧬 Montagem do Sars-CoV-2
A ferramenta permite a **montagem e análise de genomas do Sars-CoV-2** de maneira eficiente e integrada.

---
Este manual fornece as informações necessárias para a **instalação e uso** da interface gráfica do ViralFlow. Para mais detalhes técnicos e suporte, consulte a documentação oficial do projeto.
