# Primeiro problema de machine learning

## Primeiro subproblema: cabeçalhos presentes

Sistemas diferentes podem usar nomes diferentes para o mesmo dado. O objetivo inicial do ML é sugerir qual campo canônico corresponde a cada coluna de uma planilha de origem.

Exemplos fictícios:

| Nome da coluna de origem | Campo canônico esperado |
| --- | --- |
| `EAN`, `GTIN`, `Código de barras` | `ean` |
| `Estoque`, `Saldo atual`, `Quantidade disponível` | `quantidade` |
| `Valor vendido`, `Venda líquida` | `valor_total_liquido` |

O modelo responde uma pergunta limitada: **“que campo esta coluna provavelmente representa?”** Ele não decide por conta própria que linhas apagar, como calcular valores ou como preencher dados ausentes.

Este foi o primeiro subproblema. O conjunto rotulado de cabeçalhos ensina a associar nomes de origem ao campo esperado. Em separado, outro corpus contém características sintéticas dos valores para o futuro experimento com colunas sem cabeçalho.

## Entradas e saída do modelo

Cada exemplo rotulado descreve uma coluna, não uma linha de produto. Os atributos candidatos são:

- nome do cabeçalho, normalizado e como texto;
- tipo aparente do campo, como texto, número ou data;
- percentual de valores ausentes;
- proporção de valores únicos e comprimento típico;
- tipo de relatório informado, como estoque ou vendas.

A saída é um campo canônico candidato, uma pontuação de confiança e evidências compreensíveis. Os primeiros exemplos devem ser sintéticos. Mapeamentos corrigidos e aprovados podem depois acrescentar rótulos sem armazenar registros empresariais.

O conjunto inicial está em `data/synthetic/column_mappings_demo.csv`. Ele tem 120 exemplos de cabeçalhos, 10 perfis de sistemas inventados, dois tipos de relatório e 8 campos-alvo. Cada linha representa um cabeçalho rotulado, não um produto ou uma venda. `examples/validate_mapping_dataset.py` confere colunas, rótulos permitidos, campos vazios e exemplos duplicados.

## Conjunto sintético ampliado

O gerador `examples/generate_synthetic_ml_dataset.py` cria entradas totalmente fictícias para dois experimentos separados:

- `column_mappings_header_ml_demo.csv`: cabeçalhos rotulados para os campos presentes nos dois modelos sintéticos de saída; a linha de base atual pode ser reproduzida com o mesmo avaliador;
- `column_value_training_X_demo.csv` e `column_value_training_y_demo.csv`: características estatísticas das colunas e rótulos canônicos em arquivos distintos;
- `column_value_manifest_demo.csv`: IDs, sistema fictício, relatório, posição e presença de cabeçalho, para rastreio e análise;
- `source_profile_folds_demo.csv`: divisão em cinco grupos, mantendo cada sistema inteiro na mesma dobra.

O gerador cria 20 sistemas inventados, 280 colunas de valores sem cabeçalho e 318 exemplos de cabeçalho distribuídos por 17 sistemas. A tarefa por valores ainda cobre nove classes; o conjunto de cabeçalhos agora cobre 18 campos usados nos modelos de saída. Os dados das tabelas são gerados em memória e não vêm de arquivos empresariais. Cada linha de `X` contém estatísticas de conteúdo; nomes de sistema, IDs, cabeçalhos, exemplos textuais e rótulos ficam fora das características preditoras. `report_type` é metadado disponível para organizar uma avaliação futura, e sua inclusão como preditor deve ser uma decisão explícita.

Prepare e valide os dados e compare a linha de base:

```powershell
python examples/generate_synthetic_ml_dataset.py
python examples/validate_pre_ml_dataset.py
python examples/evaluate_mapping_baseline.py --dataset data/synthetic/farmacia_demo/column_mappings_header_ml_demo.csv
```

A validação confere alinhamento de `X`/`y`, rótulos autorizados pelos esquemas, presença de exemplos com e sem cabeçalho e separação de sistemas entre grupos. Ela não treina nem avalia um modelo.

Na versão atual da heurística, o conjunto de cabeçalhos ampliado resulta em Top-1 de 45,9% (146/318), Top-3 de 55,0% (175/318) e macro-F1 de 0,541. Esses números são uma linha de base sintética, não diretamente comparável aos 120 exemplos iniciais: a quantidade, cobertura de campos e composição mudaram.

O primeiro classificador supervisionado está em `examples/evaluate_header_ml_model.py`. Ele junta o tipo do relatório e o nome do cabeçalho como texto, transforma sequências de dois a cinco caracteres em pesos TF-IDF e usa regressão logística para prever o campo canônico. Uma `Pipeline` mantém vetorização e classificador no mesmo fluxo, ajustando ambos somente nos exemplos de treino de cada dobra. A validação `GroupKFold` mantém os sistemas inteiros separados. O script também verifica que a mesma combinação de relatório/cabeçalho não aparece nos dois lados de uma dobra.

Com as 18 classes que correspondem aos campos dos modelos sintéticos, o resultado atual é Top-1 **76,4%**, Top-3 **95,3%** e macro-F1 **0,770**, contra 45,9%, 55,0% e 0,541 da heurística no mesmo conjunto. A Top-1 caiu comparada ao experimento inicial de nove classes; agora o problema cobre mais campos e inclui distinções difíceis como grupo/subgrupo e bruto/líquido. O resultado ainda descreve somente exemplos fabricados. Não demonstra desempenho em farmácias reais nem justifica aplicar sugestões sem revisão. O script salva previsões fora do treino em `header_ml_oof_predictions_demo.csv`, não um modelo final.

Também há uma comparação didática contra os cabeçalhos dos arquivos sintéticos `TESTEML_ESTOQUE.xlsx` e `TESTEML_VENDAS.xlsx`, no script `examples/evaluate_synthetic_template_mapping.py`. Top-1 foi **20/24 (83,3%)** e Top-3 **23/24 (95,8%)**; oito cabeçalhos exatos também aparecem no corpus de treino. Os erros Top-1 atuais são `Categoria` previsto como `subgrupo`, `Departamento` previsto como `grupo`, `Venda` previsto como `unidade` e `Valor Vendido` previsto como `valor_total_bruto`. Esses dados continuam sintéticos, e o pequeno conjunto não representa uma avaliação independente de sistemas reais. O mapeamento usado para preencher os modelos foi revisado e explícito; a exportação acertou os 224 valores esperados, mas esse resultado não deve ser atribuído ao ML.

Para a tarefa separada de interpretar os valores, `examples/evaluate_value_majority_baseline.py` mede uma referência ingênua com previsão fora do grupo de treino. Ela usa o tipo de relatório e sempre escolhe o campo mais frequente naquele relatório, sem ler as características de `X`. No corpus equilibrado atual, obteve Top-1 de 14,3% e macro-F1 de 0,036. O valor baixo é esperado e funciona como piso; não é uma solução utilizável. Reproduza com `python examples/evaluate_value_majority_baseline.py`.

## Próximo subproblema: interpretar valores quando falta cabeçalho

Para uma planilha sem cabeçalho, a amostra rotulada descreve a coluna por meio dos valores: tipo inferido, taxa de ausentes, fração numérica, comprimentos, proporção de valores únicos, padrões de data/moeda/EAN e estatísticas resumidas. O corpus atual já inclui esses exemplos sintéticos. O perfil e o tipo de relatório ajudam a agrupar e analisar resultados; o sistema de origem fica reservado para separar a avaliação.

O escopo de origem também inclui arquivos onde fórmulas PROCV/PROCX buscam dados em tabelas de referência e relatórios exportados já agregados como tabela dinâmica. Resolver junções por chave e reconhecer/produzir agregações são tarefas de transformação separadas do classificador de cabeçalhos. Elas permanecem determinísticas, auditáveis e aprovadas explicitamente. ML poderá recomendar campos-chave, dimensões ou métricas; não deve inventar a chave, a agregação ou a fórmula comercial.

O material sintético atual cobre tabelas de estoque e vendas, nomes de cabeçalhos variados, colunas sem cabeçalho, ordens diferentes, lookup por chave e agregação com exemplos esperados. Continua sendo uma amostra didática pequena, gerada artificialmente; aumentar a variedade e confirmar os resultados esperados de cada transformação seguem como trabalho posterior. Fórmulas são representadas por regras de transformação, e atualizar objetos nativos de tabela dinâmica do Excel continua fora do escopo atual.

## Linha de base e primeiro modelo

Antes do ML, a heurística já existente de aliases e similaridade textual foi medida como linha de base. O primeiro classificador supervisionado combina TF-IDF de caracteres com regressão logística. Essa técnica é um experimento didático, não uma escolha definitiva; resultados posteriores e erros revisados determinarão se vale mantê-la.

O conjunto de validação separa sistemas inteiros com `GroupKFold`. Separar aleatoriamente variações do mesmo sistema poderia inflar as métricas e dar uma falsa impressão de que o modelo entende um sistema novo.

`examples/evaluate_mapping_baseline.py` mede a heurística no conjunto sintético e detalha resultados e erros por perfil. Como ela não é treinada, essa medição não é uma validação cruzada. O primeiro classificador é avaliado separando sistemas inteiros em cada rodada. Os dados continuam pequenos e artificiais, insuficientes para afirmar que o mecanismo funcionará em sistemas reais.

## Como avaliar

- **Top-1:** o primeiro campo sugerido está correto?
- **Top-3:** o campo correto aparece entre até três sugestões?
- **Macro-F1:** o desempenho é razoável também para campos menos frequentes?
- **Precisão em alta confiança:** entre as sugestões que poderiam ser aplicadas automaticamente, quantas estão corretas?

A pontuação de similaridade da heurística não é uma probabilidade. Portanto, não se deve chamar uma sugestão de “alta confiança” nem automatizar sua aplicação usando essa pontuação sem calibração e avaliação próprias.

O erro mais importante é associar silenciosamente uma coluna ao campo errado. No início, o modelo apenas recomenda. Uma sugestão de baixa confiança ou com conflito precisa de revisão; a automação só pode aumentar depois de validação por campo, fonte e regra.

## O que continua determinístico

Transformações conhecidas devem permanecer em regras explícitas e reproduzíveis, por exemplo:

- combinar cadastros por uma chave exata e relatar chaves sem correspondência;
- agrupar linhas e calcular métricas somente com dimensões e operações configuradas;
- preservar EAN como texto e zeros à esquerda;
- remover linhas sem EAN quando essa regra estiver aprovada para o fluxo;
- tratar linhas de total conforme o formato de origem;
- converter datas, quantidades e valores monetários com regras verificáveis;
- calcular bruto, líquido ou lucro somente quando a fórmula de negócio estiver confirmada.

ML não deve substituir regras determinísticas só para tornar o projeto mais “inteligente”. Um modelo pode sugerir o significado de uma coluna; o código de transformação aplica a regra validada e registra o resultado.

## Critério para avançar

A primeira experiência de ML está concluída: há um classificador de cabeçalhos avaliado em dados sintéticos, uma função reutilizável para características por valor e os exemplos de lookup e agregação. O classificador não está integrado à ferramenta e não há um modelo final salvo. O próximo subproblema é treinar e avaliar um classificador separado para colunas sem cabeçalho. O corpus continua pequeno e artificial; a validação estrutural e as métricas atuais não demonstram generalização para sistemas reais.

O protótipo de ML estará pronto para integração quando superar a linha de base em fontes sintéticas não vistas, produzir confiança utilizável, expor ambiguidades e não aplicar mapeamentos incertos silenciosamente. Antes de substituir uma automação existente, o fluxo completo também precisa gerar os resultados esperados nos exemplos de estoque e vendas.
