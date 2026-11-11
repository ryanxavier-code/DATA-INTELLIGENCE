# Data Intelligence Engine

![Capa do Data Intelligence Engine: tratamento revisável de estoque e vendas](assets/data-intelligence-cover.svg)

> Ferramenta em Python para inspecionar arquivos tabulares, entender sua qualidade e preparar uma representação consistente dos dados.

> **Status:** MVP aplicado, em piloto local. A ferramenta já é usada no trabalho para preparar relatórios tabulares, com revisão dos mapeamentos e exportação para modelos Excel. O repositório público contém apenas exemplos sintéticos; arquivos, cadastros e dados empresariais ficam fora dele. O classificador experimental agora participa do app como recomendador revisável de cabeçalhos; ele não escolhe regras comerciais nem trata fontes de forma autônoma.

## Índice

- [Visão geral](#visão-geral)
- [Tecnologias e ferramentas](#tecnologias-e-ferramentas)
- [Competências técnicas evidenciadas](#competências-técnicas-evidenciadas)
- [Objetivos de aprendizado](#objetivos-de-aprendizado)
- [O que a versão atual faz](#o-que-a-versão-atual-faz)
- [O que ainda não faz](#o-que-ainda-não-faz)
- [Machine learning neste projeto](#machine-learning-neste-projeto)
- [Como a execução funciona](#como-a-execução-funciona)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Requisitos e instalação](#requisitos-e-instalação)
- [Executar a ferramenta](#executar-a-ferramenta)
- [Abrir o aplicativo local](#abrir-o-aplicativo-local)
- [Entender o relatório](#entender-o-relatório)
- [Configurar regras de qualidade](#configurar-regras-de-qualidade)
- [Usar como biblioteca Python](#usar-como-biblioteca-python)
- [Conceitos e decisões técnicas](#conceitos-e-decisões-técnicas)
- [Dados de demonstração](#dados-de-demonstração)
- [Fluxo desejado da interface](#fluxo-desejado-da-interface)
- [Testes](#testes)
- [Limitações conhecidas](#limitações-conhecidas)
- [Próximos passos](#próximos-passos)
- [Licença](#licença)

## Visão geral

O **Data Intelligence Engine** é um projeto aplicado de engenharia de dados, desenvolvido também como trilha de aprendizado em engenharia de machine learning. Seu propósito é receber tabelas, encontrar problemas e preparar dados de maneira rastreável. O fluxo atual já apoia uma atividade real de trabalho; o objetivo de longo prazo é ampliar sua capacidade para reconhecer formatos e automatizar tratamentos com segurança.

Esta versão contém uma biblioteca Python reutilizável, uma interface de linha de comando (CLI) e um aplicativo local em Streamlit. A CLI faz uma análise descritiva mais ampla; o app guia o envio, o mapeamento revisável e a exportação de uma planilha. Os exemplos e conjuntos usados no experimento de ML são sintéticos.

### O que você consegue fazer nesta versão

- Abrir arquivos CSV e Excel e inspecionar o conteúdo tabular.
- Ver quantidade de linhas e colunas, tipos aparentes, valores vazios, valores distintos, frequências e duplicidades.
- Configurar verificações de qualidade, como campos obrigatórios e valores únicos.
- Receber sugestões de equivalência entre cabeçalhos conhecidos e campos canônicos.
- No app, enviar relatórios de estoque/vendas, confirmar o tipo, revisar sugestões de mapeamento, conferir uma prévia e baixar uma cópia de um modelo Excel.
- Usar funções reutilizáveis para limpeza explícita, busca por chave (lookup) e agregação tabular em exemplos.

O app combina correspondências exatas de aliases com sugestões do classificador para cabeçalhos menos familiares e exibe os campos para revisão. O ML considera o tipo do relatório e o texto do cabeçalho; não examina valores das células. Quando não existe cabeçalho ou quando a regra depende de lógica comercial, a ferramenta ainda não consegue decidir sozinha. EAN e descrição precisam estar preenchidos para que uma linha seja exportada; campos sem mapeamento ficam vazios.

### Tecnologias e ferramentas

| Tecnologia/ferramenta | Onde é usada | Papel no projeto |
| --- | --- | --- |
| Python | Todo o projeto | Linguagem que conecta a interface, a CLI, o processamento de tabelas e os exemplos. |
| pandas | Ingestão, perfilamento, transformações e exportação | Lê e manipula os dados tabulares usando `DataFrame`. |
| openpyxl | Arquivos `.xlsx` e modelos Excel | Lê e grava planilhas, preservando a estrutura e estilos básicos do modelo de saída. |
| xlrd | Arquivos antigos `.xls` | Permite a leitura do formato legado do Excel. |
| Streamlit | `app/streamlit_app.py` | Cria o app local no navegador, sem exigir um front-end separado em JavaScript. |
| scikit-learn | `src/data_intelligence/ml/` e app | Treina e executa o classificador experimental que recomenda campos para cabeçalhos; não aplica regras de negócio. |
| pytest | `tests/` | Executa os testes automatizados do projeto; é dependência opcional de desenvolvimento. |
| VS Code | Desenvolvimento | Editor usado para ler e alterar os arquivos do projeto. |
| PowerShell | Exemplos de comandos no Windows | Terminal para instalar dependências, executar a CLI e iniciar o app. |
| Git | Controle de versão local | Registra mudanças em commits e ajuda a acompanhar a evolução do código. |
| GitHub | Repositório remoto | Hospeda o código e a documentação do portfólio. Não executa o processamento local das planilhas. |
| `abrir_data_intelligence.bat` | Raiz do projeto | Atalho para iniciar o app no Windows; usa o Python do `.venv` quando ele existe. |

As bibliotecas e suas dependências opcionais estão declaradas em [`pyproject.toml`](pyproject.toml). A opção `excel` adiciona suporte a Excel; `app` instala Streamlit e scikit-learn para disponibilizar as sugestões ML na interface; `ml` instala scikit-learn para os experimentos; `dev` instala pytest.

## Competências técnicas evidenciadas

Este projeto demonstra prática na construção de uma ferramenta de dados em Python. A tabela associa as competências a implementações que podem ser conferidas diretamente no repositório:

| Competência | O que foi implementado | Evidência no repositório |
| --- | --- | --- |
| Python e organização de software | Pacote dividido por responsabilidades, funções reutilizáveis, validações de entrada e tratamento de erros. | [`src/data_intelligence/`](src/data_intelligence/) e [`pyproject.toml`](pyproject.toml) |
| Engenharia de dados | Ingestão de CSV/Excel, limpeza explícita, padronização de esquemas, lookup por chave, agregação e exportação para modelos Excel. | [`ingestion/`](src/data_intelligence/ingestion/), [`transforms/`](src/data_intelligence/transforms/) e [`canonical/`](src/data_intelligence/canonical/) |
| Qualidade e perfilamento | Métricas de ausências, valores distintos e repetidos, tipos aparentes e verificações configuráveis. | [`profiling/`](src/data_intelligence/profiling/) e [`quality/`](src/data_intelligence/quality/) |
| Fundamentos de engenharia de ML | Preparação de exemplos sintéticos rotulados, comparação com uma linha de base e avaliação separando perfis de sistemas entre treino e validação. | [`examples/generate_synthetic_ml_dataset.py`](examples/generate_synthetic_ml_dataset.py), [`examples/evaluate_mapping_baseline.py`](examples/evaluate_mapping_baseline.py) e [`docs/mapping_baseline.md`](docs/mapping_baseline.md) |
| ML com scikit-learn | Pipeline de TF-IDF de caracteres e regressão logística para sugerir campos; avaliação Top-1, Top-3 e macro-F1 separada por sistemas sintéticos. | [`src/data_intelligence/ml/`](src/data_intelligence/ml/) e [`examples/evaluate_header_ml_model.py`](examples/evaluate_header_ml_model.py) |
| Interface de aplicação | Fluxo Streamlit para enviar arquivos, identificar relatório, revisar mapeamentos, visualizar prévia e baixar resultado. | [`app/streamlit_app.py`](app/streamlit_app.py) |
| Qualidade de software | Testes unitários para ingestão, perfilamento, esquema, motor e CLI, além de exemplos sintéticos com gabaritos verificáveis. | [`tests/unit/`](tests/unit/) e [`data/synthetic/`](data/synthetic/) |
| Documentação e versionamento | Guias de instalação e uso, documentação do problema de ML e arquitetura organizada em Git. | [`README.md`](README.md), [`docs/`](docs/) e histórico Git |

### Resumo profissional do projeto

> MVP aplicado em Python para análise e padronização de dados tabulares, usado como piloto local no tratamento de relatórios de trabalho. Combina biblioteca modular, CLI e interface Streamlit, com ingestão de CSV/Excel, perfilamento, verificações de qualidade, mapeamento revisável, transformações reutilizáveis e exportação para modelos Excel. Também inclui um experimento de classificação de cabeçalhos com scikit-learn avaliado somente em dados sintéticos.

**Como apresentar o nível:** não é apenas um exercício acadêmico: é um MVP aplicado que já apoia um fluxo real, ainda com revisão humana e regras conhecidas. O classificador ML está integrado como recomendador de cabeçalhos, mas sua avaliação é sintética e ele não escolhe as regras de tratamento. A generalização para sistemas reais e a automação autônoma continuam em desenvolvimento.

## Produto pretendido

O objetivo de longo prazo é receber arquivos de estoque e vendas identificados por unidade, reconhecer seus formatos, executar o tratamento correspondente àquela unidade e apresentar os dados finais numa segunda aba da interface. A saída deverá respeitar o modelo exato usado pelo fluxo aprovado e estar pronta para carga manual no banco de dados. A ferramenta mostrará o que identificou, quais regras executou e por que algum registro foi sinalizado ou removido.

O projeto deve automatizar sem adivinhar silenciosamente. Para formatos conhecidos e regras já validadas, a ferramenta poderá processar o arquivo e explicar o resultado. Quando encontrar um campo ambíguo, uma estrutura nova ou uma regra de negócio desconhecida, deverá pedir revisão antes de produzir uma saída definitiva. Correções aprovadas poderão melhorar os perfis de origem e, no futuro, as sugestões de ML.

O critério para substituir uma automação existente não é apenas gerar uma planilha: o novo fluxo precisa reproduzir as regras e resultados esperados, mostrar as verificações realizadas e facilitar a adaptação a outras fontes sem duplicar scripts inteiros.

A interface pretendida aceita arquivos nomeados por unidade. Um catálogo local de automações ajudará a descobrir entradas, saídas, campos, filtros, lookups e agregações dos scripts existentes e a associá-los aos perfis de unidade e relatório. A visão funcional e os critérios de compatibilidade estão em [`docs/target_product_workflow.md`](docs/target_product_workflow.md). A carga final no banco continua manual.

O primeiro problema de ML definido para estudo é **sugerir o campo canônico de uma coluna de origem**. O modelo deverá usar o nome da coluna e sinais estruturais, como tipo aparente e percentual de valores ausentes, para sugerir um campo como `ean`, `quantidade` ou `valor_total_liquido`. A sugestão precisa mostrar confiança e evidências; a aplicação de regras de negócio continua separada e explícita. O escopo inicial está detalhado em [`docs/ml_problem_definition.md`](docs/ml_problem_definition.md).

## Objetivos de aprendizado

Ao evoluir o projeto, serão praticados conceitos usados em sistemas de dados e ML:

- organização de código Python em pacotes e módulos;
- ambientes virtuais e gerenciamento de dependências;
- leitura de fontes tabulares com pandas;
- perfilamento e validação exploratória de dados;
- identificação de valores ausentes e registros repetidos;
- descoberta e padronização de esquemas;
- interfaces de linha de comando;
- testes automatizados;
- versionamento e documentação de software;
- classificação experimental de cabeçalhos com scikit-learn e dados sintéticos;
- etapas posteriores: integrar sugestões de ML ao app, validar tratamentos por fonte e ampliar as verificações de qualidade.

## O que a versão atual faz

### CLI e biblioteca Python

- Lê CSV e Excel e representa os dados como `Dataset`, uma estrutura do projeto que guarda a tabela e informações da origem.
- Calcula perfis descritivos, duplicidades e verificações de qualidade configuradas.
- Sugere mapeamentos por aliases e semelhança entre nomes de colunas.
- Aplica mapeamento somente quando ele é informado/aprovado explicitamente.
- Pode exportar dados mapeados para uma cópia de um modelo Excel.

### App local

- Identifica o tipo de relatório usando o nome do arquivo e sinais nos cabeçalhos, com confirmação da pessoa usuária.
- Pré-preenche sugestões por aliases exatos e pelo classificador ML; a tela identifica a origem da sugestão e permite revisar ou corrigir cada associação.
- Remove linhas sem EAN ou descrição, processa os campos mapeados e deixa os demais vazios.
- Mostra uma prévia e permite baixar uma cópia do modelo de estoque ou vendas.
- Lê apenas as colunas selecionadas para reduzir trabalho em arquivos maiores; não calcula o perfil estatístico completo da CLI.

O app e a CLI usam funções do pacote, mas têm fluxos distintos: a CLI chama o motor de análise completo; o app usa diretamente as funções de leitura, preparação, mapeamento e exportação necessárias à interface.

## O que ainda não faz

Esta versão não identifica unidades reais automaticamente nem lê um cadastro empresarial de lojas pelo app. Não descobre ou executa scripts de tratamento privados, não infere o significado de colunas sem cabeçalho e não aplica fórmulas comerciais por conta própria. As funções de lookup e agregação existem como componentes reutilizáveis e exemplos, mas ainda não estão conectadas ao fluxo da interface. O classificador sugere cabeçalhos conhecidos a partir do texto; não examina os valores das colunas, não aprende com as correções durante o uso e não escolhe transformações. Também não há integração com banco de dados ou nuvem, deduplicação aproximada nem atualização de objetos nativos de tabela dinâmica do Excel. A origem não é sobrescrita. Consulte [`docs/initial_connector_scope.md`](docs/initial_connector_scope.md) para o escopo planejado.

## Machine learning neste projeto

O ML já está conectado à etapa de identificação do app como recomendador revisável; as operações de tratamento continuam determinísticas e separadas:

1. **Problema:** sugerir o campo canônico de uma coluna, como `ean`, `quantidade` ou `valor_total_liquido`.
2. **Dados:** exemplos artificiais com nomes de cabeçalhos e rótulos conhecidos; nenhum relatório real da empresa é usado no conjunto versionado.
3. **Modelo experimental:** `TfidfVectorizer` transforma pedaços de caracteres dos cabeçalhos em números; `LogisticRegression` aprende a associar esses padrões aos campos rotulados.
4. **Avaliação:** validação separada por perfis/sistemas sintéticos, para testar se o classificador generaliza para perfis que não viu durante o treino.
5. **Limite atual:** o app treina o pipeline em memória com exemplos sintéticos e o mantém em cache durante a sessão; não salva um modelo de produção, não aprende com as correções de uso, não interpreta colunas sem cabeçalho e não escolhe transformações de negócio. O score não é uma probabilidade calibrada nem garantia de acerto.

Para executar o app com as sugestões de ML, instale `.[excel,app]`. Para reproduzir a avaliação, instale `.[excel,ml]` e siga os comandos da seção [Dados de demonstração](#dados-de-demonstração). Os resultados medidos são referências do conjunto sintético, não uma promessa de desempenho em arquivos reais.

## Como a execução funciona

```text
Comando no terminal
        │
        ▼
__main__.py ── inicia a CLI
        │
        ▼
cli.py ── interpreta arquivo e opções
        │
        ▼
engine.py / analyze_file ── coordena o fluxo
        ├── ingestion/csv.py ou ingestion/excel.py ── lê o arquivo
        ├── dataset.py ── mantém tabela e metadados
        ├── profiling/profiler.py ── calcula o perfil descritivo
        ├── profiling/column_features.py ── extrai características por coluna para estudo de mapeamento
        ├── engine.py ── seleciona linhas integralmente duplicadas
        ├── quality/checks.py ── executa regras configuradas
        ├── schema/column_mapping.py ── sugere equivalências
        └── canonical/mapping.py ── aplica mapeamento aprovado, se fornecido
        │
        ▼
AnalysisResult ── reúne resultados para a CLI ou outro consumidor
```

O comando **não executa os scripts de `examples/` em sequência**. A CLI chama o motor, e o motor chama funções reutilizáveis nos módulos. Os exemplos são demonstrações independentes dessas mesmas peças.

## Estrutura do repositório

```text
.
├── data/
│   └── synthetic/              # pequenos arquivos fictícios para demonstração
├── app/
│   └── streamlit_app.py         # protótipo da interface web local
├── examples/                   # exemplos de uso das funções do pacote
├── docs/                       # escopo e notas de arquitetura
│   └── initial_connector_scope.md # escopo do único conector inicial
├── src/
│   └── data_intelligence/      # código-fonte do pacote
│       ├── canonical/          # aplicação explícita de nomes canônicos
│       │   └── excel_export.py # grava dados canônicos em uma cópia de modelo Excel
│       ├── ingestion/          # leitura de CSV e Excel
│       ├── identity/           # resolução de unidade/CNPJ por cadastro local
│       ├── ml/                 # classificador experimental de cabeçalhos
│       ├── profiling/          # perfilamento descritivo e características por coluna
│       ├── quality/            # verificações explícitas de qualidade
│       ├── schema/             # sugestões de equivalência de colunas
│       │   └── templates.py    # vocabulários-alvo de estoque e vendas
│       ├── transforms/         # preparação, lookup e agregação determinísticos
│       │   ├── cleaning.py    # filtros de preparação escolhidos explicitamente
│       │   ├── lookup.py      # enriquecimento por chave, com relatório de não correspondências
│       │   └── aggregation.py # agrupamentos e métricas configurados explicitamente
│       ├── __main__.py         # execução com python -m
│       ├── cli.py              # interface de linha de comando
│       ├── dataset.py          # objeto que representa a tabela carregada
│       └── engine.py           # orquestração da análise
├── tests/
│   └── unit/                   # testes automatizados
├── .gitignore                  # arquivos locais/gerados ignorados pelo Git
├── pyproject.toml              # metadados, dependências e configuração do pacote
└── README.md                   # documentação e guia de uso
```

`data_intelligence_engine.egg-info/`, quando aparece após uma instalação editável, contém metadados gerados pelo empacotamento e não é código-fonte. A `.venv/` é o ambiente local do Python e também não deve ser enviada ao Git.

### Módulos principais

| Módulo | Responsabilidade |
| --- | --- |
| `__main__.py` | Permite iniciar o pacote com `python -m data_intelligence`. |
| `cli.py` | Lê argumentos do terminal, chama o motor e imprime o relatório. |
| `engine.py` | Coordena ingestão, perfilamento, duplicidades e esquema; devolve `AnalysisResult`. |
| `dataset.py` | Agrupa o `DataFrame`, caminho de origem e formato, expondo dimensões e colunas. |
| `ingestion/csv.py` | Lê CSV e transforma erros de leitura em `IngestionError`. |
| `ingestion/excel.py` | Lê uma planilha/aba de Excel e transforma erros em `IngestionError`. |
| `identity/store_lookup.py` | Busca unidade e CNPJ por nome exato normalizado em um cadastro Excel local. |
| `ml/header_classifier.py` | Treina o pipeline TF-IDF + regressão logística e retorna candidatos de campo para o app. |
| `profiling/profiler.py` | Calcula métricas descritivas por coluna e para o conjunto. |
| `profiling/column_features.py` | Calcula atributos numéricos de uma coluna e seu contexto tabular; não escolhe o rótulo canônico. |
| `quality/checks.py` | Verifica valores obrigatórios, unicidade configurada e linhas idênticas. |
| `transforms/cleaning.py` | Aplica remoção de linhas vazias, filtros de valores e limpeza de espaços, quando solicitados. |
| `transforms/lookup.py` | Enriquece uma cópia da tabela com correspondência exata muitos-para-um e informa chaves sem correspondência. |
| `transforms/aggregation.py` | Agrupa linhas e calcula soma, contagem, média, mínimo ou máximo conforme configuração explícita. |
| `schema/column_mapping.py` | Compara cabeçalhos com aliases e ordena sugestões explicáveis. |
| `schema/templates.py` | Define os campos canônicos e aliases dos modelos de estoque e vendas. |
| `canonical/mapping.py` | Cria um novo `Dataset` com renomeações aprovadas e valida colisões. |
| `canonical/excel_export.py` | Preenche um modelo Excel com colunas canônicas e grava em outro caminho. |

## Requisitos e instalação

### Requisitos

- Python 3.10 ou superior;
- `pip`;
- PowerShell no exemplo abaixo (em outros sistemas, adapte os comandos de ativação).

O pandas é uma dependência principal. A opção `excel` instala `openpyxl` para arquivos `.xlsx`/`.xlsm` e `xlrd` para leitura de arquivos `.xls`. A instalação `dev` inclui pytest para desenvolvimento.

### Windows / PowerShell

Abra o terminal na pasta que contém `pyproject.toml` e `README.md`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[excel,dev]"
```

Se o PowerShell bloquear a ativação do ambiente, é possível chamar diretamente o Python do ambiente, por exemplo `\.venv\Scripts\python.exe -m data_intelligence ...`. A política de execução do PowerShell depende da configuração local do Windows.

`-e` instala o pacote em modo editável: alterações em `src/` passam a ser usadas sem reinstalar o projeto. As opções entre colchetes instalam dependências extras: `excel` e `dev`.

Para seguir a aula de ML, instale a opção adicional:

```powershell
python -m pip install -e ".[excel,dev,ml]"
```

Para instalar também a interface web, inclua a opção `app`:

```powershell
python -m pip install -e ".[excel,app]"
```

Para instalar de uma vez Excel, app, ML e testes de desenvolvimento:

```powershell
python -m pip install -e ".[excel,app,ml,dev]"
```

## Abrir o aplicativo local

Com o ambiente virtual ativado e a opção `app` instalada, execute na raiz do projeto:

```powershell
streamlit run app/streamlit_app.py
```

O Streamlit abre a interface no navegador, servida localmente pelo seu computador. Para testar, use as entradas fictícias em `data/synthetic/farmacia_demo/`. O fluxo guiado apresenta quatro passos: envio, identificação e revisão de mapeamentos, prévia e download. O app usa `estoque.xlsx` e `vendas.xlsx` da pasta `Desktop/Banco de Dados/Modelos principais` quando os arquivos existem; também aceita outra pasta pela variável `DATA_INTELLIGENCE_TEMPLATE_DIR`. Os modelos empresariais ficam fora do repositório. Sem modelos exatos, a exportação é bloqueada. EAN e descrição são obrigatórios; campos sem origem ficam vazios. Para reduzir trabalho em arquivos grandes, a interface lê somente as colunas selecionadas. Na etapa de identificação, aliases exatos têm prioridade e o classificador ML treinado com exemplos sintéticos recomenda correspondências para cabeçalhos restantes. A pessoa usuária revisa essas sugestões; score de ML não é probabilidade calibrada. O app não interpreta valores de colunas sem cabeçalho nem executa o perfil estatístico completo da CLI. Veja [`docs/target_product_workflow.md`](docs/target_product_workflow.md).

## Executar a ferramenta

Os comandos seguintes devem ser executados na raiz do repositório, onde está `pyproject.toml`.

### Ver opções disponíveis

```powershell
python -m data_intelligence --help
```

Depois da instalação, também fica disponível o comando `data-intelligence`.

### Analisar os exemplos incluídos

Planilha fictícia, preservando EAN como texto:

```powershell
python -m data_intelligence data\synthetic\produtos_demo_ean.xlsx --text-column EAN
```

CSV de demonstração:

```powershell
python -m data_intelligence data\synthetic\produtos_demo.csv
```

Se o CSV usar ponto e vírgula como separador:

```powershell
python -m data_intelligence caminho\para\arquivo.csv --separator ";"
```

Escolher uma aba do Excel pelo nome ou índice (começando em zero):

```powershell
python -m data_intelligence dados.xlsx --sheet "Produtos"
python -m data_intelligence dados.xlsx --sheet 1
```

Forçar várias colunas a texto, por exemplo identificadores que podem conter zeros iniciais:

```powershell
python -m data_intelligence dados.xlsx --text-column EAN --text-column COD_INTERNO
```

### Aprovar e aplicar mapeamentos

O relatório pode sugerir, por exemplo, `DESCRICAO_PRODUTO → descricao_produto`. Para aplicar um mapeamento revisado, informe cada par como `ORIGEM=CANONICO`:

```powershell
python -m data_intelligence data\synthetic\produtos_demo_ean.xlsx `
  --text-column EAN `
  --map-column EAN=ean `
  --map-column DESCRICAO_PRODUTO=descricao_produto `
  --map-column GRUPO=grupo `
  --map-column PRECO=preco
```

O mapeamento é aplicado à representação em memória e aparece como prévia no terminal. Sem `--template` e `--output`, nenhum arquivo de saída é gravado. Com essas opções, a CLI preenche uma cópia do modelo indicado. A entrada e o modelo não são sobrescritos; uma saída existente no mesmo caminho será substituída. O projeto rejeita colunas de origem inexistentes, nomes canônicos vazios e colisões de nomes finais.

Exemplo de exportação explícita:

```powershell
python -m data_intelligence entrada.xlsx `
  --text-column EAN `
  --map-column EAN=ean `
  --map-column DESCRICAO=descricao_produto `
  --template modelo.xlsx `
  --output saida_padronizada.xlsx
```

### Argumentos da CLI

| Argumento | Obrigatório? | Descrição |
| --- | --- | --- |
| `arquivo` | Sim | Caminho de um arquivo CSV ou Excel suportado. |
| `--separator` | Não | Separador CSV; padrão `,`. Para CSV brasileiro comum, use `;`. |
| `--sheet` | Não | Índice começando em zero ou nome da aba Excel; padrão `0` (primeira aba). |
| `--text-column COLUNA` | Não | Força uma coluna a texto. Pode ser repetido. |
| `--map-column ORIGEM=CANONICO` | Não | Aplica um mapeamento revisado. Pode ser repetido. |
| `--required-column COLUNA` | Não | Exige que os valores da coluna estejam preenchidos. Pode ser repetido. |
| `--unique-column COLUNA` | Não | Exige que os valores não vazios da coluna sejam únicos. Pode ser repetido. |
| `--drop-empty-rows` | Não | Remove linhas em que todas as células estão vazias. |
| `--require-value-column COLUNA` | Não | Remove linhas sem valor na coluna indicada. Pode ser repetido. |
| `--exclude-value COLUNA=VALOR` | Não | Remove linhas em que a coluna corresponda ao texto indicado. Pode ser repetido. |
| `--strip-text` | Não | Remove espaços externos de valores textuais antes dos filtros. |
| `--report-type {estoque,vendas}` | Não | Compara cabeçalhos com o vocabulário do tipo de relatório selecionado. |
| `--template ARQUIVO.xlsx` | Não | Modelo `.xlsx` a preencher; exige mapeamento aprovado e `--output`. |
| `--output ARQUIVO.xlsx` | Não | Caminho da saída `.xlsx`; exige `--template` e `--map-column`. |
| `--store-name NOME` | Não | Unidade a localizar no cadastro para preencher unidade e CNPJ; exige `--store-lookup`. |
| `--store-lookup ARQUIVO.xlsx` | Não | Cadastro local com colunas `Nome Fantasia` e `CNPJ`; exige `--store-name`. |

### Modelos canônicos de estoque e vendas

O projeto possui dois vocabulários-alvo baseados nos cabeçalhos dos modelos de referência:

- **Estoque:** `cnpj`, `unidade`, `mes`, `ean`, `descricao_produto`, `grupo`, `subgrupo`, `laboratorio`, `quantidade`, `valor_total_custo`, `data_cadastro` e `data_ultima_venda`.
- **Vendas:** `cnpj`, `unidade`, `ean`, `codigo_reduzido`, `mes`, `descricao_produto`, `grupo`, `subgrupo`, `laboratorio`, `quantidade`, `valor_total_bruto`, `valor_total_liquido` e `valor_total_custo`.

Use `--report-type estoque` ou `--report-type vendas` para que as sugestões considerem o contexto correto. A ferramenta também lista campos do padrão que não receberam uma sugestão de cabeçalho. Isso é um aviso para revisar aliases e o arquivo, não prova que a informação esteja ausente: um sistema pode usar um nome que ainda não está no vocabulário. Por exemplo:

```powershell
python -m data_intelligence caminho\para\estoque_de_outro_sistema.xlsx --report-type estoque --text-column EAN
python -m data_intelligence caminho\para\vendas_de_outro_sistema.xlsx --report-type vendas --text-column EAN
```

Os nomes de destino são padronizados em `schema/templates.py`. A CLI usa aliases e similaridade textual; o app combina aliases exatos com um classificador de cabeçalhos baseado em scikit-learn. O classificador é treinado com exemplos sintéticos incluídos no projeto e não aprende sozinho com as correções feitas na interface. No futuro, mapeamentos aprovados poderão formar novos exemplos rotulados, guardando somente metadados de esquema e sem linhas de relatórios privados.

## Configurar regras de qualidade

Perfilamento descreve os dados; regras de qualidade comparam os dados com uma expectativa. A ferramenta não consegue saber sozinha se uma coluna deve ser obrigatória ou única. Por isso, essas expectativas são declaradas por você ao executar o comando.

Por exemplo, se cada registro precisar ter um EAN preenchido e o EAN não puder se repetir:

```powershell
python -m data_intelligence data\synthetic\produtos_demo_ean.xlsx `
  --text-column EAN `
  --required-column EAN `
  --unique-column EAN
```

As opções podem ser repetidas para várias colunas. Valores nulos e textos vazios ou com espaços são tratados como ausentes na regra de obrigatoriedade. Na regra de unicidade, valores ausentes são ignorados; cada valor repetido além da primeira ocorrência gera uma ocorrência de erro. Se uma coluna configurada não existir no arquivo, a ferramenta informa o problema em vez de ignorar a regra.

As regras configuráveis produzem `ERROR` quando um requisito declarado não é atendido. Linhas inteiras idênticas produzem `WARNING`, pois uma repetição pode ser legítima dependendo do negócio. As opções de preparação removem linhas quando solicitadas: por exemplo, `--drop-empty-rows`, `--require-value-column Produto` e `--exclude-value "Produto=Total"`. A CLI informa quantas linhas foram removidas.

Há uma regra padrão para a padronização: quando o mapeamento aprovado liga uma coluna de origem ao campo canônico `ean`, linhas sem EAN são removidas. Isso vale mesmo que a origem use outro cabeçalho, como `GTIN`. Essa regra mantém o conjunto de saída com um identificador de produto por linha; o arquivo de entrada continua intacto.

## Entender o relatório

### Resumo do conjunto

- **Linhas e colunas:** dimensões da tabela carregada.
- **Linhas completamente repetidas:** número de ocorrências repetidas além da primeira. Quando encontradas, a CLI exibe todas as linhas envolvidas nessas repetições.

### Métricas por coluna

- **tipo:** tipo aparente inferido pelo pandas, não necessariamente o significado de negócio;
- **nulos:** quantidade de valores ausentes;
- **percentual de nulos:** `nulos ÷ total de linhas × 100`;
- **únicos:** quantidade de valores distintos não nulos;
- **duplicidades:** ocorrências não nulas além de uma ocorrência por valor, calculadas como `não nulos − únicos`;
- **mais frequente:** valor não nulo que aparece mais vezes, quando há valores disponíveis.

O objeto de perfil também contém comprimento médio de valores convertidos em texto e os indícios `possible_identifier`, `possible_category`, `possible_numeric` e `possible_date`. A saída resumida atual da CLI não imprime todos esses campos.

### Duplicidade por coluna e duplicidade de linha

São conceitos diferentes. Uma coluna pode repetir um grupo ou categoria sem que as linhas completas sejam duplicadas. `duplicate_count` mede ocorrências repetidas de valores naquela coluna. `duplicate_row_count` considera uma linha repetida quando todos os seus valores são iguais aos de outra linha.

Nenhuma duplicidade é removida automaticamente. Uma repetição pode ser erro, mas também pode ser válida conforme a regra de negócio.

### Sugestões de esquema

As sugestões usam aliases e similaridade textual. A pontuação fica entre 0 e 1, mas **não é uma probabilidade de acerto**. A evidência e o método ficam disponíveis nos objetos de sugestão. Confira cada resultado antes de passar `--map-column`.

O vocabulário genérico em `schema/column_mapping.py` continua disponível quando nenhum tipo de relatório é informado. Os modelos específicos ficam em `schema/templates.py`. Código reduzido e EAN são campos separados; não se deve presumir que um código interno seja um código de barras.

## Usar como biblioteca Python

Além da CLI, o motor pode ser chamado por outro código Python:

```python
from data_intelligence import analyze_file

result = analyze_file(
    "data/synthetic/produtos_demo_ean.xlsx",
    text_columns=["EAN"],
)

print(result.profile.row_count)
print(result.profile.column_count)
print(result.profile.duplicate_row_count)

for column in result.profile.columns:
    print(column.name, column.null_count, column.unique_count)

for suggestion in result.schema_suggestions:
    print(suggestion.source_column, suggestion.candidates)
```

Para criar uma versão padronizada em memória, forneça um mapeamento aprovado:

```python
result = analyze_file(
    "produtos.xlsx",
    text_columns=["EAN"],
    approved_mapping={
        "EAN": "ean",
        "DESCRICAO_PRODUTO": "descricao_produto",
    },
)

if result.canonical_dataset is not None:
    print(result.canonical_dataset.column_names)
```

`AnalysisResult` contém `dataset` (entrada carregada), `profile` (métricas), `duplicate_rows` (linhas envolvidas em duplicidade integral), `quality_issues` (ocorrências das regras), `schema_suggestions` (sugestões) e `canonical_dataset` (novo conjunto renomeado ou `None`).

### Gravar o conjunto canônico em um modelo Excel

A exportação é uma etapa separada e explícita. Primeiro analise o arquivo e aplique um mapeamento revisado; depois passe o conjunto canônico para a função de exportação. O modelo precisa ter cabeçalhos que correspondam aos nomes das colunas canônicas, desconsiderando maiúsculas/minúsculas e espaços externos. Colunas do modelo que não tenham correspondência ficam vazias. A mesma operação também pode ser feita pela CLI com `--template` e `--output`.

```python
from data_intelligence import analyze_file
from data_intelligence.canonical import write_excel_template

result = analyze_file(
    "entrada.xlsx",
    text_columns=["EAN"],
    approved_mapping={
        "EAN": "ean",
        "DESCRICAO": "descricao_produto",
    },
)

if result.canonical_dataset is None:
    raise ValueError("Aplique e revise um mapeamento antes de exportar.")

write_excel_template(
    result.canonical_dataset,
    template_path="modelo.xlsx",
    output_path="saida_padronizada.xlsx",
)
```

`write_excel_template` mantém a linha de cabeçalho e os estilos da aba selecionada, substitui os valores das linhas de dados e grava em `output_path`. A correspondência de cabeçalhos ignora maiúsculas/minúsculas e espaços externos. Ela impede que a saída sobrescreva o modelo ou o arquivo de origem, mas uma saída existente com o mesmo caminho será substituída. A função não infere mapeamentos nem aplica regras específicas da fonte. A CLI só exporta quando recebe o modelo, a saída e pelo menos um mapeamento explicitamente informado.

### Preencher unidade e CNPJ por uma planilha de cadastro

Quando o arquivo de entrada não traz esses campos, a CLI pode consultar um cadastro Excel local. Informe o nome da unidade e o caminho do cadastro; o programa procura uma correspondência exata normalizada na coluna `Nome Fantasia`, lê o `CNPJ` correspondente e adiciona ambos ao conjunto canônico antes da exportação. A busca ignora diferenças de caixa, acentos, espaços e pontuação. Se não houver exatamente uma correspondência ou o CNPJ não tiver 14 dígitos, a execução para sem produzir a saída.

```powershell
python -m data_intelligence entrada.xlsx `
  --map-column EAN=ean `
  --store-name "Unidade Exemplo" `
  --store-lookup "cadastro_local.xlsx" `
  --template modelo.xlsx `
  --output saida.xlsx
```

O cadastro permanece no caminho local informado e não é copiado para o repositório. `--store-name` identifica a unidade para essa execução; a extração automática do número da filial pelo nome do arquivo e a tabela local filial→unidade ficam para uma etapa posterior.

As regras também podem ser chamadas diretamente pelo motor Python:

```python
result = analyze_file(
    "produtos.xlsx",
    text_columns=["EAN"],
    required_columns=["EAN", "DESCRICAO_PRODUTO"],
    unique_columns=["EAN"],
)

for issue in result.quality_issues:
    print(issue.severity, issue.rule_id, issue.column, issue.count, issue.message)
```

## Conceitos e decisões técnicas

### Ingestão não é limpeza

A ingestão lê a fonte e a representa em uma estrutura comum (`Dataset`). Nesta etapa, os leitores não corrigem valores nem sobrescrevem os arquivos. Erros de leitura são apresentados como `IngestionError` com contexto sobre a fonte.

### Preservação de identificadores

EAN, GTIN, CPF, códigos e outros identificadores geralmente devem ser tratados como texto, mesmo quando contêm apenas dígitos. Eles identificam algo; não são necessariamente quantidades para cálculo. Use `--text-column EAN` na CLI ou `dtype={"EAN": "string"}` nas funções de leitura.

### Heurísticas são indícios

O profiler usa regras simples, não entendimento semântico. Na implementação atual:

- uma coluna pode parecer identificadora quando o nome contém termos como `ID`, `COD`, `CNPJ`, `CPF`, `EAN` ou `SKU`; alternativamente, com pelo menos 10 valores não nulos, quando pelo menos 98% são únicos;
- uma coluna textual pode parecer categórica quando possui até 20 valores únicos e a razão de valores únicos para não nulos é de até 20%;
- uma coluna numérica é marcada pelo tipo reconhecido pelo pandas;
- uma coluna de texto pode parecer data se pelo menos 80% de uma amostra de até 1.000 valores for interpretável como data.

Essas regras podem gerar falsos positivos ou não reconhecer casos válidos. Por exemplo, datas numéricas ou formatos ambíguos dependem do padrão dos dados e da interpretação. Revise os dados antes de tomar decisões.

## Dados de demonstração

Os arquivos em `data/synthetic/` são artificiais, preparados para aprendizagem e execução local. Eles demonstram valores ausentes, repetições, identificadores como texto, formatos diferentes de estoque/vendas, cabeçalhos ausentes, lookups e agregações. Não use arquivos da empresa neste repositório.

O conjunto inicial [`column_mappings_demo.csv`](data/synthetic/column_mappings_demo.csv) contém 120 cabeçalhos fictícios de dez sistemas. O conjunto ampliado é gerado por `examples/generate_synthetic_ml_dataset.py`: tem 20 sistemas, 280 exemplos de características de colunas sem cabeçalho em `X`, rótulos em `y`, manifesto, cinco grupos de avaliação e 318 exemplos de cabeçalhos que cobrem 18 campos dos modelos. Confira a preparação e reproduza as medições:

```powershell
python examples/validate_mapping_dataset.py
python examples/evaluate_mapping_baseline.py
python examples/generate_synthetic_ml_dataset.py
python examples/validate_pre_ml_dataset.py
python examples/evaluate_mapping_baseline.py --dataset data/synthetic/farmacia_demo/column_mappings_header_ml_demo.csv
python examples/evaluate_value_majority_baseline.py
python examples/evaluate_header_ml_model.py
python examples/evaluate_selective_header_model.py
```

As medições informam Top-1, Top-3 e macro-F1, além dos erros por perfil. Os conjuntos e limitações estão descritos em [`docs/mapping_baseline.md`](docs/mapping_baseline.md) e [`docs/ml_problem_definition.md`](docs/ml_problem_definition.md). Os números são referências sintéticas, não desempenho esperado em sistemas reais. Nenhum desses arquivos representa registros reais de clientes, produtos ou da empresa. Não coloque dados empresariais privados ou credenciais no repositório público.

O arquivo [`DATASET_FORMATOS_FICTICIOS.xlsx`](data/synthetic/farmacia_demo/DATASET_FORMATOS_FICTICIOS.xlsx) contém exemplos artificiais com e sem cabeçalhos, lookup por PROCV, dados detalhados de vendas, resumo agregado e gabarito separado. Para gerar um perfil de características das colunas a partir desses exemplos:

```powershell
python examples/profile_synthetic_columns.py
```

O perfil gerado é material de estudo; ele não treina um modelo e não significa que o motor já reconheça automaticamente esses formatos.

O gerador ampliado prepara características estatísticas de colunas com os rótulos em arquivo separado. A coluna `source_profile` serve para separar sistemas inteiros nas avaliações; ela não entra como pista do modelo. No primeiro experimento, o tipo de relatório e o nome do cabeçalho entram juntos como texto, para que o contexto estoque/vendas possa ajudar a interpretação. Scikit-learn é uma dependência opcional, instalada pelo extra `ml`.

O primeiro classificador de cabeçalhos usa TF-IDF de pedaços de caracteres e regressão logística. No conjunto ampliado, acertou 76,4% Top-1 e 95,3% Top-3 com sistemas fictícios inteiros reservados por dobra. A heurística no mesmo conjunto acertou 45,9% e 55,0%. A tarefa cresceu de nove para 18 classes, então compare esses números somente nessa base. Para reproduzir o experimento:

```powershell
python examples/evaluate_header_ml_model.py
```

O script treina um classificador dentro de cada dobra de validação, mantendo sistemas inteiros fora do treino, e salva apenas as previsões de avaliação em `header_ml_oof_predictions_demo.csv`. Ele não grava um modelo reutilizável. A pontuação exibida pelo classificador não foi calibrada para decidir processamento automático.

No app, o pipeline é treinado em memória a partir do conjunto sintético e fica em cache durante a execução. Aliases conhecidos continuam sendo aplicados primeiro; o ML recomenda campos para os cabeçalhos restantes, sem preencher automaticamente os campos de unidade ou CNPJ. Em avaliação aninhada com abstenção, o modelo aceitou 82/318 sugestões: 78 estavam corretas (**95,1% de precisão seletiva**, com **25,8% de cobertura**). O corte é escolhido dentro do treino de cada dobra e avaliado em perfis inteiros reservados. Esse resultado mostra o custo da cautela: o modelo deixa a maioria dos cabeçalhos sem sugestão. Não é 100%, não foi medido em dados reais e não garante precisão semelhante fora do corpus sintético. Reproduza com `python examples/evaluate_selective_header_model.py`.

Para comparar o classificador com os cabeçalhos dos workbooks `TESTEML` e conferir as saídas já preenchidas pelos mapeamentos explícitos, consulte [a documentação da demonstração de farmácia](data/synthetic/farmacia_demo/README.md). O classificador acertou 20/24 cabeçalhos Top-1 e 23/24 Top-3; a exportação, usando mapeamentos revisados, foi conferida contra os 224 valores esperados. Esses 224/224 verificam somente a exportação com mapeamentos explícitos revisados; não medem a precisão do ML.

Para executar as funções genéricas de lookup e agregação sobre o workbook sintético:

```powershell
python examples/process_synthetic_lookup_and_aggregation.py
```

## Testes

Os testes unitários ficam em `tests/unit/`. Com o pacote e as dependências de desenvolvimento instalados, execute na raiz:

```powershell
python -m pytest
```

Também é possível executar a suíte com a biblioteca padrão do Python:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

## Limitações conhecidas

- A ferramenta trabalha com arquivos tabulares locais e ainda não conecta a bancos, APIs ou nuvem.
- A CLI imprime resultados no terminal; relatórios em PDF ou HTML ainda não estão implementados.
- A exportação para Excel exige mapeamentos explícitos e cabeçalhos correspondentes; ainda não há geração automática de modelos nem validação de regras específicas da fonte.
- A CLI usa aliases e similaridade textual; o app acrescenta ML para sugerir cabeçalhos. Nenhum dos fluxos aprende com aprovações nem entende completamente o contexto de negócio.
- A detecção de duplicidades exige igualdade da linha completa; ainda não há correspondência aproximada.
- As regras de qualidade cobrem apenas campos obrigatórios, unicidade explícita e linhas idênticas; ainda não existem limites numéricos, formatos ou regras configuráveis em arquivo.
- O classificador de cabeçalhos está integrado ao app como recomendador e foi avaliado com dados sintéticos. Ele não interpreta valores de colunas sem cabeçalho, não escolhe regras de negócio e não está pronto para operar autonomamente em sistemas reais.

## Próximos passos

O objetivo de longo prazo é uma plataforma que conecte fluxos de trabalho de dados de farmácias por uma interface comum. Para manter o início simples, a primeira integração será apenas uma fonte, descrita em `docs/initial_connector_scope.md`. O desenvolvimento seguirá etapas pequenas:

1. [concluído para cabeçalhos presentes] criar exemplos sintéticos rotulados e medir a heurística;
2. [protótipo criado] preparar planilhas sintéticas de estoque/vendas, incluindo cabeçalhos ausentes, ordem diferente de colunas, lookup por chave e relatório agregado com gabarito; ampliar os cenários antes de avaliar generalização;
3. [protótipo implementado] oferecer funções reutilizáveis para lookup exato e agregação; integrar essas regras num fluxo por fonte e ampliar a validação;
4. [experimento inicial concluído] treinar e avaliar classificador didático de cabeçalhos com scikit-learn;
5. comparar e aprimorar o classificador; depois, treinar um modelo separado para interpretar perfis de valores, mantendo sistemas inteiros fora do treino;
6. [protótipo integrado] usar ML como recomendador revisável no app; registrar aprovações e manter ambiguidades visíveis;
7. comparar resultados sintéticos do motor com resultados esperados antes de considerar substituir qualquer automação;
8. [protótipo criado] iniciar a interface web local com dados sintéticos; em seguida, conectar um catálogo de perfis de unidade e validar as receitas de tratamento;
9. só depois considerar automação autônoma de casos confiáveis, novas fontes, banco de dados e execução em ambiente empresarial aprovado.

## Licença

Nenhuma licença foi definida neste repositório ainda. Antes de publicar o projeto como reutilizável por outras pessoas, escolha uma licença e adicione o arquivo `LICENSE`.
