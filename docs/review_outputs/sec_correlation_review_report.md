## A. Resumo das principais alteracoes

- Reescrita completa da subsecao para remover extrapolacoes causais e adotar linguagem proporcional a magnitudes de correlacao.
- Padronizacao da forma de apresentacao para pares principais como `(r = ..., rho = ...)` com arredondamento de duas casas.
- Correcao numerica de afirmacao no painel `KE_adv_250`: no texto original, `C_A` foi citado como `r = +0.43`; no CSV, o valor para `|KE_adv_250|` (domain abs mean) e `r = +0.34` (`rho = +0.40`).
- Inclusao explicita de um caso fraco relevante: `Ge x PV_200 border_west` com `(r = -0.05, rho = -0.01)`, interpretado como associacao nao robusta.
- Inclusao de cautelas metodologicas sobre dependencia entre testes, significancia de campo e diferenca entre associacao estatistica e mecanismo fisico.
- Mantida a estrutura interpretativa fisica principal (AdvT-APE, AFC-reservatorios, dipolo PV200 E-W), mas com qualificacoes tecnicas.

## B. Verificacao dos valores de correlacao

Fonte auditada: `results/exploratory/figure9_signed_r_table.csv`

| Quantidade/campo discutido | Valor citado no texto original | Valor encontrado no CSV | Valor usado na versao revisada | Status |
|---|---|---|---|---|
| Pares com `|r| >= 0.20` | `126` | `126` | `126` | correto |
| Concordancia de sinal `r` vs `rho` | `100%` | `100%` | `100%` | correto |
| Pares com `||r|-|rho|| > 0.10` | `2` | `2` | `2` | correto |
| `PV_850`: pares acima do limiar | `7/91 (7.7%)` | `7/91 (7.7%)` | `7/91 (7.7%)` | correto |
| `Ca x AdvT_850 sector_west` | `r=-0.46, rho=-0.55` | `r=-0.458, rho=-0.553` | `r=-0.46, rho=-0.55` | correto |
| `Ca x AdvT_850 sector_north` | `r=-0.44, rho=-0.55` | `r=-0.445, rho=-0.556` | `r=-0.45, rho=-0.56` | corrigido |
| `Ca x AdvT_850 domain_mean` | `r=-0.44` | `r=-0.437, rho=-0.499` | `r=-0.44, rho=-0.50` | adicionado |
| `BAe x AdvT_850 border_east` | `r=+0.28` | `r=+0.280, rho=+0.290` | `r=+0.28, rho=+0.29` | adicionado |
| `BAe x AdvT_850 sector_east` | `r=+0.28` | `r=+0.279, rho=+0.299` | `r=+0.28, rho=+0.30` | adicionado |
| `BAe x AdvT_850 contrast_ew` | `r=+0.33` | `r=+0.330, rho=+0.307` | `r=+0.33, rho=+0.31` | adicionado |
| `BAe x AdvT_850 border_west` | `r=-0.24` | `r=-0.243, rho=-0.204` | `r=-0.24, rho=-0.20` | adicionado |
| `BAe x AdvT_850 sector_west` | `r=-0.37` | `r=-0.367, rho=-0.277` | `r=-0.37, rho=-0.28` | adicionado |
| `Ck x AdvT_850 domain_mean` | `r=+0.20` | `r=+0.203, rho=+0.204` | `r=+0.20, rho=+0.20` | adicionado |
| `|AFC| x Ke` (domain abs mean) | `r=+0.53` | `r=+0.531, rho=+0.570` | `r=+0.53, rho=+0.57` | adicionado |
| `|AFC| x Ae` (domain abs mean) | `r=+0.51` | `r=+0.514, rho=+0.560` | `r=+0.51, rho=+0.56` | adicionado |
| `Ca x AFC domain_mean` | `r=+0.43` | `r=+0.426, rho=+0.376` | `r=+0.43, rho=+0.38` | adicionado |
| `Ck x AFC domain_mean` | `r=-0.22` | `r=-0.216, rho=-0.234` | `r=-0.22, rho=-0.23` | adicionado |
| `KE_adv`: `Ae` associado a `|KE_adv|` | `r=+0.43` | `r=+0.432, rho=+0.480` | `r=+0.43, rho=+0.48` | adicionado |
| `KE_adv`: `Ke` associado a `|KE_adv|` | `r=+0.32` | `r=+0.327, rho=+0.396` | `r=+0.33, rho=+0.40` | corrigido |
| `KE_adv`: `Ca` associado a `|KE_adv|` | `r=+0.43` | `r=+0.336, rho=+0.404` | `r=+0.34, rho=+0.40` | corrigido |
| `Ae x KE_adv_250 sector_west` | `r=-0.45, rho=-0.45` | `r=-0.444, rho=-0.445` | `r=-0.44, rho=-0.45` | correto |
| `BKe x KE_adv_250 border_west` | `r=+0.37` | `r=+0.371, rho=+0.331` | `r=+0.37, rho=+0.33` | adicionado |
| `PV_200 contrast_ew x Ge` | `r=+0.59, rho=+0.57` | `r=+0.587, rho=+0.574` | `r=+0.59, rho=+0.57` | correto |
| `PV_200 contrast_ew x Ae` | `r=+0.57, rho=+0.59` | `r=+0.573, rho=+0.589` | `r=+0.57, rho=+0.59` | correto |
| `PV_200 contrast_ew x Ca` | `r=+0.45, rho=+0.47` | `r=+0.447, rho=+0.467` | `r=+0.45, rho=+0.47` | correto |
| `PV_200 border_west x Ca` | `r=-0.30` | `r=-0.296, rho=-0.310` | `r=-0.30, rho=-0.31` | adicionado |
| `PV_200 border_west x Ae` | `r=-0.44` | `r=-0.443, rho=-0.470` | `r=-0.44, rho=-0.47` | adicionado |
| `PV_200 sector_west x Ca` | `r=-0.24` | `r=-0.240, rho=-0.251` | `r=-0.24, rho=-0.25` | adicionado |
| `PV_200 sector_west x Ae` | `r=-0.37` | `r=-0.366, rho=-0.386` | `r=-0.37, rho=-0.39` | adicionado |
| `PV_200 border_west x Ge` | nao citado numericamente | `r=-0.053, rho=-0.010` | `r=-0.05, rho=-0.01` | adicionado |

Observacao: alguns trechos originais eram qualitativos (`Ke` com `|r|=0.22-0.35`; sinais opostos AFC vs KE_adv) sem mapeamento unico por feature. Esses casos foram mantidos com linguagem mais cautelosa e, quando util, complementados com pares explicitos.

## C. Avaliacao da interpretacao cientifica

- Bem sustentado:
  - Relacao entre adveccao termica de baixos niveis e termos de APE (`Ca`, `Ae`) no painel `AdvT_850`.
  - Importancia de metricas de amplitude (`|AFC|`, `|KE_adv|`) para `Ae/Ke`.
  - Papel do contraste E-W de `PV_200` como principal indicador estatistico no conjunto.

- Suavizado/corrigido:
  - Trechos que aproximavam associacao de mecanismo causal foram reformulados para "covariabilidade" e "consistencia fisica".
  - Correlacoes fracas ou marginais (ex.: `r` em torno de 0.20) passaram a ser tratadas explicitamente como efeito modesto.
  - O caso `Ge x PV_200 border_west` foi explicitamente classificado como associacao fraca/nao robusta.

- Pontos que ainda exigem cautela no artigo:
  - Dependencia entre preditores espaciais (borda, setor e contrastes nao sao ortogonais).
  - Ausencia de analise de defasagem temporal (lead-lag) entre campos dinamicos e termos energeticos.
  - Potencial inflacao de significancia por autocorrelacao espacial/temporal e testes multiplos.

## D. Pontas soltas e sugestoes de melhoria

- Incluir no suplemento uma tabela completa de pares acima do limiar com `(r, rho, p, n)` e convencao de sinal.
- Adicionar uma checagem de robustez por bootstrap por ciclone ou por estacao para verificar estabilidade dos sinais.
- Considerar teste com correlacoes parciais (controlando intensidade do sistema) para separar forcantes compartilhadas.
- Incluir uma analise lead-lag simples (por exemplo, janelas de 6-24 h) para avaliar coerencia temporal de mecanismos.
- Avaliar significancia de campo (nao apenas teste univariado por celula), dado o grande numero de comparacoes.

## E. Referencias sugeridas

Status de bibliografia no workspace:
- O manuscrito chama `\bibliography{sn-bibliography}`, mas nenhum arquivo `.bib` correspondente foi encontrado no workspace atual.
- Por isso, foi criado um arquivo BibTeX auxiliar em `review_outputs/sec_correlation_suggested_references.bib`.

Referencias (peer-reviewed) consultadas/sugeridas:
- Hoskins, McIntyre and Robertson (1985), QJRMS, DOI: `10.1002/qj.49711147002`.
  - Relevancia: interpretacao dinamica de PV e estrutura de cavado/crista.
- Davis and Emanuel (1991), MWR, DOI: `10.1175/1520-0493(1991)119<1929:PVDOC>2.0.CO;2`.
  - Relevancia: diagnosticos de ciclogenese por PV e acoplamento em diferentes niveis.
- Davies (2015), MWR, DOI: `10.1175/MWR-D-14-00098.1`.
  - Relevancia: base formal para interpretacao QG (forcantes verticais e desenvolvimento ciclonico).
- Orlanski and Sheldon (1993), JAS, DOI: `10.1175/1520-0469(1993)050<0212:AGFIDA>2.0.CO;2`.
  - Relevancia: fluxos ageostroficos e downstream/upstream development.
- Orlanski and Katzfey (1991), JAS, DOI: `10.1175/1520-0469(1991)048<1972:TLCOAC>2.0.CO;2`.
  - Relevancia: ciclo de vida e orcamento energetico de onda ciclonica no HS.
- Livezey and Chen (1983), MWR, DOI: `10.1175/1520-0493(1983)111<0046:SFSAID>2.0.CO;2`.
  - Relevancia: significancia de campo e controle de inferencias em multiplos testes espaciais.
- Bretherton et al. (1999), J. Climate, DOI: `10.1175/1520-0442(1999)012<1990:TENOSD>2.0.CO;2`.
  - Relevancia: graus de liberdade efetivos em campos espaciais/temporais.
- Wilks (2016), BAMS, DOI: `10.1175/BAMS-D-15-00267.1`.
  - Relevancia: cautela na apresentacao de significancia estatistica em geociencias.

Limitacao operacional:
- A revisao bibliografica foi feita com consulta online de metadados via Crossref (DOI/titulo/periodico/ano).