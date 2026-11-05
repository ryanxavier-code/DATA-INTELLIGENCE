# Fluxo desejado do produto

## Objetivo para a pessoa usuária

A pessoa seleciona ou arrasta os arquivos extraídos para a interface. Os nomes dos arquivos ou uma pasta de envio identificam a unidade. A ferramenta reconhece se cada arquivo contém estoque ou vendas, escolhe o processo configurado para aquela unidade e executa o tratamento. A pessoa acompanha o resultado em uma segunda aba da interface, confere a prévia e baixa os dados finais para carregá-los manualmente no serviço de banco de dados.

A etapa de envio ao banco permanece manual. O produto prepara e valida os dados; não faz o carregamento no banco.

## Fluxo da interface

### Protótipo local atual

O MVP local está em `app/streamlit_app.py` e segue um fluxo guiado de quatro passos: envio, identificação e revisão, prévia e download do modelo preenchido. Aliases exatos preenchem os campos conhecidos; um classificador scikit-learn treinado com cabeçalhos sintéticos sugere campos para nomes menos familiares. As sugestões continuam revisáveis. O classificador considera apenas o tipo do relatório e o nome do cabeçalho: não interpreta valores de colunas sem cabeçalho nem escolhe regras de transformação. Os modelos finais podem ser lidos de uma pasta local configurável e não são armazenados no repositório; entradas sintéticas ficam em `data/synthetic/farmacia_demo/`. O app exige EAN e descrição em cada linha exportada e deixa sem valor os campos sem mapeamento. Ainda não identifica automaticamente uma unidade real nem descobre regras de automações locais. Os arquivos enviados são processados em diretório temporário, que é removido ao final do processamento.

Este protótipo serve para validar a experiência da interface enquanto construímos o catálogo de perfis e as validações de compatibilidade descritas abaixo.

1. **Entrada:** receber um ou mais arquivos CSV/Excel e capturar o nome da unidade pelo nome do arquivo ou da pasta. A interface mostra os arquivos identificados.
2. **Identificação:** determinar unidade, tipo de relatório (estoque/vendas), abas e estrutura. Cabeçalhos ajudam quando existem; conteúdo e contexto ajudam quando faltam.
3. **Seleção do processo:** resolver a unidade para um perfil de tratamento local e selecionar a receita de estoque ou vendas correspondente.
4. **Tratamento:** executar as regras aprovadas para aquela unidade, incluindo limpeza, mapeamentos, consultas por chave, cálculos e agregações aplicáveis.
5. **Validação:** conferir campos, formatos, contagens de linhas, EANs, valores, correspondências e totais esperados. Registrar quais regras foram executadas e o que foi removido ou sinalizado.
6. **Resultado:** abrir uma segunda aba chamada, por exemplo, “Dados tratados”, com resumo, avisos e prévia tabular. Disponibilizar arquivo de saída alinhado ao modelo de destino, pronto para a carga manual.

Se nome de unidade, tipo de relatório, campo ou regra não puder ser determinado com segurança, a ferramenta deve mostrar a ambiguidade antes de marcar o resultado como pronto. Aprovações podem atualizar o perfil local de tratamento.

## Compatibilidade exata com cada automação

Cada unidade pode ter regras e modelos diferentes. O perfil de tratamento precisa registrar, por relatório:

- como reconhecer a unidade e as variantes dos arquivos;
- quais abas e cabeçalhos ler, e como identificar colunas sem cabeçalho;
- os nomes canônicos e a correspondência de cada coluna de origem;
- filtros de linhas vazias, EAN ausente e totalizadores;
- tabelas de referência e chaves de lookup, incluindo o tratamento de não correspondências;
- dimensões, métricas e operações de agregação;
- fórmulas comerciais confirmadas;
- ordem, nomes e tipos das colunas do modelo final;
- verificações e totais que comprovam que a saída reproduz o processo esperado.

Essa receita é executada por funções compartilhadas do motor e regras específicas da unidade. O ML recomenda mapeamentos ou reconhece estruturas; regras de negócio aprovadas determinam as transformações. O resultado só deve ser considerado compatível após comparar os dados sintéticos de entrada com um gabarito sintético de saída.

## Catálogo local das automações existentes

Para evitar que a pessoa tenha de abrir e explicar manualmente cada script, uma etapa de descoberta local deve inventariar os códigos existentes e extrair candidatos a:

- arquivos/abas de entrada e arquivos/modelos de saída;
- nomes de campos e mapeamentos;
- filtros, conversões, joins/PROCV e operações de agrupamento;
- unidade e tipo de relatório associados;
- dependências e parâmetros necessários para execução.

O inventário serve para montar e manter os perfis locais. Scripts arbitrários não serão tratados como regras confirmadas apenas por terem sido encontrados: a equivalência é demonstrada com casos sintéticos e as verificações de saída. Quando um padrão não puder ser interpretado, a ferramenta mantém esse passo identificado para revisão sem impedir a catalogação dos demais.

O inventário, scripts privados, caminhos, cadastros e regras identificáveis ficam no computador do usuário e fora do GitHub. O repositório público contém somente o mecanismo genérico, perfis fictícios e testes com dados sintéticos.

## Critérios para considerar uma unidade pronta

- O arquivo é encaminhado à unidade e ao tipo de relatório corretos a partir dos nomes recebidos ou dos dados.
- A saída segue exatamente a ordem e os campos do modelo definido para o processo.
- O resultado reproduz filtros, lookup, cálculos e agregações aprovados.
- As verificações explicam linhas removidas, valores inválidos, chaves ausentes e diferenças nos totais.
- Os arquivos de origem permanecem intactos; a prévia e o arquivo final são cópias de saída.
- A saída é revisável na interface e está pronta para carregamento manual no banco de dados.
- A unidade só é marcada como concluída quando as comparações com o gabarito sintético passam.

## Implementação incremental

Ernesto continua sendo o primeiro piloto definido no escopo atual. A arquitetura começa com perfis por unidade e por tipo de relatório, para que outras unidades possam ser adicionadas ao catálogo sem duplicar o motor. A interface vem depois que o fluxo de identificação, tratamento, validação e exportação puder ser executado como um serviço Python reutilizável.
