# Linha de base do mapeamento

## Escopo

Esta medição registra o comportamento da heurística atual de aliases e similaridade textual sobre `data/synthetic/column_mappings_demo.csv`. O arquivo contém apenas cabeçalhos artificiais: 120 exemplos, dez perfis de sistemas inventados e doze pares de relatório/campo-alvo.

## Como reproduzir

Na raiz do projeto, com o ambiente virtual ativado:

```powershell
python examples/validate_mapping_dataset.py
python examples/evaluate_mapping_baseline.py
```

O primeiro comando valida as colunas do CSV, valores vazios, rótulos permitidos, duplicidades, cobertura dos campos-alvo e quantidade de perfis. O segundo mede Top-1, Top-3 e macro-F1 no conjunto e separadamente por perfil, além de listar os erros Top-1.

## Resultado inicial

| Medida | Resultado |
| --- | ---: |
| Exemplos avaliados | 120 |
| Top-1 | 43,3% (52/120) |
| Top-3 | 52,5% (63/120) |
| Macro-F1 | 0,531 |
| Sem acerto Top-1 | 68/120 |

O resultado varia por sistema fictício. No conjunto inicial, Top-1 varia de 8,3% a 66,7%. Isso mostra que o vocabulário atual é insuficiente para muitos dos cabeçalhos inventados. Essa medição serve como referência do protótipo; não representa desempenho em dados reais.

## Limites da medição

- Os perfis e cabeçalhos são sintéticos, pequenos e escritos para exercitar diferenças de vocabulário.
- A heurística não é treinada; o relatório por perfil mostra variação entre fontes, mas não é uma validação cruzada de modelo.
- A pontuação de similaridade não é probabilidade. Não medimos nem autorizamos aplicação automática por confiança.
- O conjunto cobre somente oito campos canônicos iniciais. Campos adicionais exigem novos exemplos e validação das regras de negócio.
- A linha de base não foi ajustada para maximizar essas métricas. Isso evita confundir a inclusão dos próprios exemplos como aliases com generalização para um sistema novo.

## Critérios antes de integração ou substituição

O primeiro classificador já foi comparado com a heurística usando sistemas inteiros fora do treino. Mesmo que supere a heurística nestes exemplos, isso não basta para integrar recomendações à CLI nem para substituir uma automação: será necessária mais variedade sintética, revisão dos erros e avaliação separada das regras e resultados em entradas exclusivamente sintéticas.

## Linha de base ampliada para os exemplos sintéticos de cabeçalho

O gerador `examples/generate_synthetic_ml_dataset.py` também produz um conjunto ampliado com 318 cabeçalhos e 18 classes em 17 sistemas fictícios. Os sistemas sem cabeçalho não aparecem neste experimento de nomes, mas aparecem no manifesto de características de valores. A heurística atual alcança Top-1 **45,9% (146/318)**, Top-3 **55,0% (175/318)** e macro-F1 **0,541**. Reproduza com:

```powershell
python examples/evaluate_mapping_baseline.py --dataset data/synthetic/farmacia_demo/column_mappings_header_ml_demo.csv
```

Esta medição tem 18 campos canônicos e uma composição diferente da linha de base inicial; não é uma comparação direta com os 120 exemplos. Sistemas fictícios inteiros são mantidos fora do treino por dobra, sem misturar exemplos do mesmo sistema entre treino e validação.

O classificador de cabeçalhos atingiu Top-1 **76,4%**, Top-3 **95,3%** e macro-F1 **0,770** na mesma base ampliada. A queda em relação ao primeiro experimento de nove classes é esperada porque agora também precisa distinguir campos semelhantes dos modelos, como `grupo`/`subgrupo` e valor bruto/líquido. A avaliação dos cabeçalhos do workbook `TESTEML` foi 20/24 em Top-1 e 23/24 em Top-3. Esses números são sintéticos e não comprovam desempenho fora do material gerado.
