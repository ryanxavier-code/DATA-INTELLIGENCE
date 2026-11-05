# Escopo do conector inicial

## Objetivo

Começar a integração do Data Intelligence Engine com uma única fonte de relatórios de farmácia. A primeira entrega deve ler relatórios de estoque e vendas dessa fonte e preparar os dados para os modelos canônicos definidos pelo projeto.

O nome da organização e detalhes que possam identificá-la ficam fora desta documentação para que o repositório possa ser preparado para um portfólio público. A identificação da pasta local deve ficar apenas no ambiente privado do usuário.

## Referência de processo

O conector pretende atender a um fluxo genérico de relatórios de estoque e vendas de farmácia. Particularidades de uma automação privada devem ser traduzidas em regras documentadas e casos sintéticos antes de entrar no repositório; nomes de arquivos, caminhos, planilhas e identificadores privados não pertencem à documentação pública.

O projeto ainda não comprova equivalência com uma automação de trabalho. Antes de considerar qualquer substituição, será necessário validar cada regra com resultados esperados usando somente dados sintéticos e obter a aprovação necessária para o ambiente onde a ferramenta vier a ser usada.

## Comportamentos planejados para o conector

O conector genérico poderá precisar de etapas como:

1. ler arquivos Excel de entrada, possivelmente em formatos antigos;
2. reconhecer cabeçalhos por aliases e similaridade de texto;
3. associar registros a uma unidade por campos do arquivo ou por um cadastro de lojas;
4. normalizar EAN e outros identificadores;
5. descartar linhas vazias, totalizadores e linhas sem identificador, conforme regras específicas;
6. preencher planilhas-modelo de estoque e vendas, preservando parte da estrutura e formatação;
7. calcular indicadores monetários somente após confirmar a fórmula e a regra de negócio.

Essa lista é um escopo candidato, não uma declaração de capacidade implementada nem de regra de negócio aprovada. Cada etapa deverá ser validada com exemplos sintéticos e com a pessoa responsável pelo processo. Cálculos, filtros de linhas e critérios de associação de unidade exigem confirmação explícita antes de serem implementados.

## Arquitetura incremental desejada

```text
Relatório da fonte inicial
        │
        ▼
Adaptador específico da fonte
  leitura + identificação de cabeçalhos/unidade
        │
        ▼
Dataset comum do Data Intelligence Engine
        │
        ├── perfil e validações explicáveis
        ├── transformações de negócio aprovadas
        └── mapeamento revisado para o esquema canônico
                    │
                    ▼
          Modelo canônico de estoque ou vendas
```

O adaptador deve conter particularidades do formato da fonte. O núcleo comum deve receber dados tabulares e fornecer perfilamento, validações e mapeamentos revisáveis. Assim, os detalhes da origem não se espalham pelo motor central.

## Fórmulas de procura e relatórios agregados

Algumas planilhas de trabalho podem usar PROCV/PROCX (VLOOKUP/XLOOKUP) para buscar atributos em outra aba ou cadastro, e alguns relatórios podem ser preparados por tabela dinâmica. O pacote já tem funções genéricas de lookup exato e agregação em `transforms/`, mas ainda não orquestra automaticamente esses casos no conector ou na CLI.

O tratamento deve distinguir duas operações:

- **Procura por chave:** combinar uma tabela de origem com uma tabela de referência usando uma chave aprovada, como EAN ou código interno. O fluxo precisa conferir chaves duplicadas, registros sem correspondência e preservação de identificadores. A regra de junção deve ser determinística; ML pode sugerir quais colunas parecem ser a chave, mas não deve escolher ou aplicar a junção silenciosamente.
- **Agregação/tabela dinâmica:** entender quais campos identificam as linhas, qual métrica é agregada e qual operação foi aplicada (por exemplo, soma ou contagem). Uma saída já agregada não deve ser agregada novamente sem intenção explícita. Subtotais e totais gerais precisam ser identificados para não duplicar valores.

O protótipo usa dados e arquivos inteiramente sintéticos. Ele representa uma tabela dinâmica como uma tabela agregada exportada. Atualizar ou manipular o objeto nativo de tabela dinâmica do Excel é uma capacidade separada e fica fora do escopo inicial. A demonstração de lookup inclui uma chave de referência sem correspondência; ainda faltam cenários adicionais de chaves ausentes e duplicadas.

## Planilhas sem cabeçalho

Uma planilha sem nomes de colunas ainda pode ter colunas e células organizadas. Para esse caso, o perfilador precisa examinar valores por coluna: tipos, proporção de vazios, padrões de identificadores, comprimentos, cardinalidade e relações com outras colunas. Os exemplos rotulados atuais só ensinam classificação por cabeçalho e não cobrem essa situação. Antes de treinar o modelo, será necessário criar exemplos sintéticos sem cabeçalho e um gabarito separado com o significado correto de cada coluna.

## Integração de unidade e CNPJ já disponível

O motor pode receber o nome da unidade e consultar, somente para leitura, um cadastro Excel local com as colunas `Nome Fantasia` e `CNPJ`. A correspondência é exata após normalização de acentos, espaços, pontuação e caixa; deve haver exatamente um resultado e um CNPJ com 14 dígitos. O nome e o CNPJ encontrados são acrescentados ao conjunto canônico antes da exportação.

No momento, o nome da unidade é informado explicitamente para cada execução por `--store-name`; o caminho do cadastro é passado por `--store-lookup`. A relação entre o número contido no nome do arquivo e o nome da unidade ainda precisa ser movida para uma configuração local, sem valores reais no repositório.

## Componentes candidatos a extração

Ao migrar, extrair e documentar separadamente, conforme forem necessários:

- normalização de nomes de cabeçalho e aliases;
- leitura de Excel e seleção de aba;
- normalização de EAN preservando zeros à esquerda;
- conversão segura de números e valores monetários;
- resolução de unidade usando identificadores configuráveis;
- identificação de linhas vazias e totalizadores;
- escrita nos modelos de saída sem alterar os arquivos originais.

Não é necessário criar todos esses módulos agora. A sequência deve acompanhar um fluxo pequeno de ponta a ponta, começando por um relatório sintético e sem depender de arquivos empresariais.

## Privacidade e portfólio

- Não copiar scripts originais, planilhas de trabalho, cadastros de loja, CNPJ, nomes de clientes, caminhos locais ou credenciais para o repositório.
- Não incluir esses materiais no ZIP de compartilhamento.
- Usar dados sintéticos para desenvolvimento e demonstrações.
- Guardar configurações privadas localmente e fora do Git.
- Em documentação pública, descrever a origem como “fonte inicial” ou “sistema de origem”, sem identificar a empresa.

## Próximos passos

1. Criar dados e cadastro sintéticos para verificar filtros, unidade, CNPJ e escrita no modelo sem dados de trabalho.
2. Tornar configurável a relação entre identificador de filial no nome do arquivo e nome da unidade.
3. Consolidar o fluxo de estoque, incluindo o conjunto de arquivos de estoque, quando os exemplos sintéticos estiverem corretos.
4. Migrar o fluxo de vendas e suas regras de valor bruto depois de validar seus casos separadamente.
5. Só considerar uma segunda fonte depois que estoque e vendas dessa primeira fonte funcionarem de forma explicável e reproduzível.
