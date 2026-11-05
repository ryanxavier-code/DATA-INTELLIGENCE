# Demonstração sintética de estoque e vendas

> Todos os nomes, códigos, produtos, valores, períodos, unidades e CNPJs deste diretório foram criados para demonstração e são fictícios. Os exemplos não contêm linhas, identificadores ou valores operacionais reais.

## Arquivos

- `TESTEML_ESTOQUE.xlsx`: relatório de estoque sintético para demonstrar leitura e padronização.
- `TESTEML_VENDAS.xlsx`: relatório de vendas sintético para demonstrar leitura e padronização.
- `cadastro_unidades_demo.xlsx`: cadastro fictício usado para demonstrar a busca de unidade/CNPJ.
- `modelo_estoque_demo.xlsx`: cabeçalhos canônicos de saída para a demonstração de estoque.
- `modelo_vendas_demo.xlsx`: cabeçalhos canônicos de saída para a demonstração de vendas.
- `DATASET_FORMATOS_FICTICIOS.xlsx`: exemplos de relatórios com e sem cabeçalhos, uma tabela de referência, lookup com PROCV e um resumo agregado estático semelhante a uma tabela dinâmica. A aba `Gabarito_Colunas` guarda os rótulos esperados para as colunas de entrada.
- `column_value_features_demo.csv` e `column_value_labels_demo.csv`: características e rótulos separados das 24 colunas do workbook pequeno.
- `column_value_training_X_demo.csv` e `column_value_training_y_demo.csv`: 280 exemplos de características e rótulos separados, gerados a partir de 20 sistemas inteiramente fictícios.
- `column_value_manifest_demo.csv`: origem fictícia, tipo de relatório, posição e indicação de cabeçalho para esses exemplos.
- `column_mappings_header_ml_demo.csv`: 318 nomes fictícios de colunas, 18 classes e 17 sistemas com seus rótulos canônicos, para avaliar a heurística e o classificador de cabeçalhos.
- `source_profile_folds_demo.csv`: cinco grupos para futura avaliação, sem separar exemplos do mesmo sistema entre grupos.
- `header_ml_oof_predictions_demo.csv`: previsões de avaliação fora do treino do primeiro classificador sintético; não é um modelo treinado.

As entradas incluem deliberadamente um registro sem EAN e uma linha de total. Isso permite observar a regra de remoção de linhas sem EAN quando uma coluna de origem é mapeada para o campo canônico `ean`. A saída deve ser gravada fora desta pasta, em `data/processed/`.

O conjunto novo demonstra padrões diferentes, mas não significa que o motor já os processe automaticamente. A aba `Vendas_Resumo` é uma tabela exportada com agregações calculadas no script de criação, não um objeto nativo de tabela dinâmica do Excel. O exemplo de lookup tem uma chave fictícia ausente do cadastro para demonstrar o tratamento de não correspondência.

Para reproduzir o perfil das colunas do arquivo novo:

```powershell
python examples/profile_synthetic_columns.py
```

O script usa o gabarito somente como rótulo esperado; os rótulos não são usados para calcular as características das colunas.

Para demonstrar o lookup exato e a agregação com as funções Python reutilizáveis:

```powershell
python examples/process_synthetic_lookup_and_aggregation.py
```

Esse exemplo preserva a linha cujo EAN não existe no cadastro e informa a não correspondência. A agregação usa apenas as linhas detalhadas recebidas e as dimensões definidas no script; a função não tenta identificar ou remover totalizadores automaticamente.

## Preparação e primeiro experimento de ML

Regere e valide o corpus com:

```powershell
python examples/generate_synthetic_ml_dataset.py
python examples/validate_pre_ml_dataset.py
python examples/evaluate_value_majority_baseline.py
python examples/evaluate_header_ml_model.py
```

O último comando testa TF-IDF de caracteres com regressão logística e grava previsões de validação em `header_ml_oof_predictions_demo.csv`. As métricas altas descrevem somente este corpus artificial; revise as previsões e não use o resultado para automatizar relatórios reais.

Os dados usados para criar as características são montados em memória pelo gerador; nenhum arquivo empresarial é lido. `X` contém estatísticas derivadas dos valores, sem nomes de colunas, IDs de sistema, amostras textuais ou rótulos. `y` contém somente o campo canônico esperado. O manifesto mantém as informações de rastreio fora dos preditores. O classificador avalia cabeçalhos sintéticos; ainda não interpreta valores sem cabeçalho nem habilita tratamento automático de planilhas.

## Rodar o estoque no PowerShell

Execute na raiz do repositório, com o ambiente virtual ativo:

```powershell
data-intelligence `
  ".\data\synthetic\farmacia_demo\TESTEML_ESTOQUE.xlsx" `
  --text-column EAN `
  --report-type estoque `
  --map-column EAN=ean `
  --map-column Produto=descricao_produto `
  --map-column Categoria=grupo `
  --map-column Departamento=subgrupo `
  --map-column Laboratório=laboratorio `
  --map-column Estoque=quantidade `
  --map-column "Giro Mensal=giro_mensal" `
  --map-column Custo=valor_total_custo `
  --map-column "Custo Médio=custo_medio" `
  --map-column Venda=valor_total_liquido `
  --store-name "FARMÁCIA MODELO - UNIDADE 27" `
  --store-lookup ".\data\synthetic\farmacia_demo\cadastro_unidades_demo.xlsx" `
  --template ".\data\synthetic\farmacia_demo\modelo_estoque_demo.xlsx" `
  --output ".\data\processed\ESTOQUE_PADRONIZADO_DEMO.xlsx"
```

## Rodar as vendas no PowerShell

```powershell
data-intelligence `
  ".\data\synthetic\farmacia_demo\TESTEML_VENDAS.xlsx" `
  --text-column EAN `
  --report-type vendas `
  --map-column Período=mes `
  --map-column filial=filial `
  --map-column EAN=ean `
  --map-column Produto=descricao_produto `
  --map-column Categoria=grupo `
  --map-column Departamento=subgrupo `
  --map-column Laboratório=laboratorio `
  --map-column "Quantidade Vendida=quantidade" `
  --map-column "Valor Vendido=valor_total_liquido" `
  --map-column Custo=valor_total_custo `
  --map-column "Lucro Bruto=lucro_bruto" `
  --map-column "Desconto Máximo=desconto_maximo" `
  --map-column "Desconto Padrão=desconto_padrao" `
  --map-column "Desconto Preferencial=desconto_preferencial" `
  --store-name "FARMÁCIA MODELO - UNIDADE 27" `
  --store-lookup ".\data\synthetic\farmacia_demo\cadastro_unidades_demo.xlsx" `
  --template ".\data\synthetic\farmacia_demo\modelo_vendas_demo.xlsx" `
  --output ".\data\processed\VENDAS_PADRONIZADAS_DEMO.xlsx"
```

Os mapeamentos acima são exemplos de estudo para os dados fictícios. Antes de aplicar regras de negócio a uma nova fonte, confira o significado de cada campo e valide o resultado esperado.

## Conferir as planilhas de saída

Depois de executar os dois comandos da CLI, compare os arquivos gravados com os valores esperados:

```powershell
python examples/verify_synthetic_template_outputs.py
```

No teste atual, cada entrada tinha 10 linhas; as duas linhas sem EAN foram retiradas pelas regras padrão ao mapear a coluna para `ean`. As saídas tiveram 8 linhas, 12 colunas de estoque e 16 de vendas, sem células vazias, preservando EAN e CNPJ como texto. A conferência encontrou os 224 valores esperados em ambas as saídas (100%). Isso mede o preenchimento com mapeamentos explícitos e revisados, não a capacidade do ML de mapear os campos.

Para medir separadamente o que o classificador sugere nos cabeçalhos dos mesmos workbooks:

```powershell
python examples/evaluate_synthetic_template_mapping.py
```

No teste atual, ele acertou 20/24 campos em Top-1 e 23/24 em Top-3; oito cabeçalhos exatos também aparecem no corpus de treino. Errou `Categoria`/`Departamento` em alguns casos, `Venda` no estoque e `Valor Vendido` em vendas. Unidade e CNPJ continuam vindo da consulta ao cadastro. Esses resultados são um exercício com nomes artificiais e não autorizam o uso automático.
