# Plano de Ação – Trabalho de Computação Gráfica (2ª etapa)

**Instituição:** Instituto Federal do Ceará – Campus Fortaleza
**Curso:** Engenharia da Computação
**Disciplina:** Computação Gráfica
**Professor:** Ajalmar Rocha Neto, Dr.
**Equipe:** Matheus, Miller e Vinicius
**Objetos escolhidos:** esponja de lavar louça, fatia de queijo, prato, boia de piscina e rolo de massa

---

## Sumário

1. Decisões iniciais
2. Divisão de tarefas (equilibrada)
3. Por que essa divisão funciona
4. Como operar com essa divisão
5. Modelagem dos objetos (item 1)
6. Cena no mundo (item 2)
7. Câmera (item 3)
8. Projeção em perspectiva (item 4)
9. Iluminação (item 5)
10. Rasterização (item 6)
11. Relatório (Obs1)
12. Entrega e apresentação
13. Cronograma sugerido
14. Checklist final

---

## 1. Decisões iniciais (fazer logo, em grupo)

### Linguagem e bibliotecas

Sugestão: **Python** com **NumPy**, **Matplotlib** (visualização 3D e 2D) e, opcionalmente, **Pillow** para salvar as imagens rasterizadas. O professor pede rasterização "na mão" (Bresenham e par-ímpar com scanline), então não usar OpenGL nem funções de desenho prontas nessa etapa. O Matplotlib serve apenas para exibir resultados.

### Estrutura do repositório

Usar Git (o enunciado proíbe link de Drive na entrega).

```
projeto_cg/
  solidos/
    esponja.py
    queijo.py
    prato.py
    boia.py
    rolo.py
  transformacoes.py   # escala, rotação, translação (matrizes 4x4)
  camera.py           # base vetorial, matriz de visão
  projecao.py         # perspectiva, culling, janela 2D
  iluminacao.py       # ambiente + difusa + especular
  rasterizacao.py     # Bresenham, par-ímpar, baricêntricas
  cena.py             # compõe a cena
  main.py             # gera todas as figuras do relatório
  README.md
  requirements.txt
```

### Formato padrão do sólido

Combinar isso antes de qualquer código evita retrabalho:

```python
{
  "vertices": np.array (N,3),
  "faces": np.array (M,3),           # índices, triângulos
  "arestas": np.array (K,2),
  "normais_faces": np.array (M,3),   # unitárias, apontando para fora
  "cor": (r,g,b),
  "nome": "prato"
}
```

Todos os sólidos devem seguir **a mesma orientação dos triângulos (anti-horária vista de fora)**. Assim, a normal vem de `cross(v1-v0, v2-v0)` e já aponta para fora.

### Assinaturas das funções (contrato entre os integrantes)

```python
# solidos/*.py
def criar_prato(...) -> dict
# transformacoes.py
def escala(sx, sy, sz) -> (4,4)
def rotacao_x/y/z(theta) -> (4,4)
def translacao(tx, ty, tz) -> (4,4)
# camera.py
def camera(eye, at, up) -> (u, v, w, matriz_visao)
# projecao.py
def projetar(solido_camera, d, fov, near, far) -> pontos_2d, faces_visiveis
# iluminacao.py
def phong(solido, normais_vertices, luz, eye, material) -> cores_vertices (N,3)
# rasterizacao.py
def bresenham(x0, y0, x1, y1) -> lista de pixels
def preencher_par_impar(triangulo_2d, ...) -> lista de pixels
def baricentricas(p, a, b, c) -> (l0, l1, l2)
def rasterizar(cena_2d, cores, resolucao) -> imagem (H,W,3)
```

Se alguém precisar mudar uma assinatura, avisa os outros dois **antes**.

---

## 2. Divisão de tarefas (equilibrada)

### Estimativa de dificuldade (1 a 5)

Considerando complexidade matemática, risco de bugs e volume de trabalho:

| Tarefa | Pontos |
|---|---|
| Esponja (caixa) | 1 |
| Fatia de queijo (prisma) | 1 |
| Prato (sólido de revolução) | 2 |
| Rolo de massa (cilindros) | 2 |
| Boia (toro, fechamento nas duas direções) | 3 |
| Cena (transformações, bounding boxes) | 2 |
| Câmera (base, matriz de visão) | 2 |
| Projeção + culling + figura 4a | 3 |
| Iluminação Phong | 3 |
| Bresenham | 2 |
| Par-ímpar com scanline | 3 |
| Baricêntricas + viewport + 3 resoluções | 3 |
| Relatório (integração, formatação, README) | 3 |

**Total: 30 pontos, ou 10 por pessoa.**


### Divisão final

| Pessoa | Tarefas | Pontos |
|---|---|---|
| **Matheus** | Esponja (1) + Queijo (1) + Cena (2) + Câmera (2) + Projeção/culling (3) + `main.py`, README e `requirements.txt` (1) | **10** |
| **Miller** | Prato (2) + Rolo (2) + Iluminação Phong (3) + Baricêntricas, viewport e 3 resoluções (3) | **10** |
| **Vinicius** | Boia (3) + Bresenham (2) + Par-ímpar com scanline (3) + montagem e formatação do relatório (2) | **10** |

---

## 3. Por que essa divisão funciona

- **Coerência técnica.** Matheus fica com o fluxo geométrico (mundo → câmera → projeção), que é uma cadeia natural: a saída de uma etapa é a entrada da outra. Miller fica com tudo que lida com cor (Phong e interpolação baricêntrica, que usa as cores dos vértices). Vinicius fica com os algoritmos de desenho 2D (retas e preenchimento de polígonos).
- **Paralelismo.** Vinicius desenvolve Bresenham e par-ímpar com pontos 2D de teste, sem esperar a câmera. Miller testa Phong e baricêntricas com um triângulo qualquer. Ninguém fica bloqueado esperando o outro.
- **Um "item difícil" para cada um:** projeção/culling (Matheus), Phong com interpolação (Miller) e toro com par-ímpar (Vinicius).
- **Carga distribuída ao longo do tempo.** Cada pessoa tem trabalho na fase de modelagem, na fase de pipeline e na fase de relatório, em vez de concentrar tudo no final.
- **Relatório sem gargalo.** Cada um escreve as seções das suas próprias partes; Vinicius apenas consolida e padroniza.

> Os pontos são uma estimativa. Se alguém tiver mais afinidade com uma parte, troquem tarefas de **peso equivalente** para manter o equilíbrio.

---

## 4. Como operar com essa divisão

### 4.1 Fluxo de trabalho no Git

- Branch `main` protegida: só recebe código que roda.
- Uma branch por pessoa e por tarefa (`matheus/camera`, `miller/phong`, `vinicius/par-impar`).
- Commits pequenos e frequentes; 
- Cada módulo deve ter um bloco `if __name__ == "__main__":` com um teste isolado, para rodar sem depender dos demais.

### 4.2 Ordem das dependências

1. **Dia 1, em grupo:** fechar o formato do dicionário do sólido e as assinaturas das funções (seção 1).
2. **Parte 1:** os cinco sólidos (cada um o seu) e a infraestrutura de Matheus (transformações e câmera), porque o resto depende dela.
3. **Parte 2 e 3:** projeção, Phong, Bresenham e par-ímpar, em paralelo.
4. **Parte 3 ou 4:** integração (baricêntricas sobre as saídas de Phong e projeção) e as 3 resoluções.

### 4.3 Como cada um testa sem depender dos outros

| Pessoa | Entrada falsa para testar sozinho |
|---|---|
| Matheus | Um cubo simples como sólido de teste, para validar câmera e projeção |
| Miller | Um triângulo com normais e cores de vértices definidos à mão, para validar Phong e baricêntricas |
| Vinicius | Pontos 2D e polígonos desenhados à mão (incluindo casos com vértice exatamente na scanline), para validar Bresenham e par-ímpar |

### 4.4 Rotina de acompanhamento

- **Reunião de integração** ao final das partes 2 e 3: juntar os módulos na `main` e rodar `render(eye)` de ponta a ponta.
- Se uma tarefa atrasar, avisar logo e redistribuir; não esperar chegar no final.

### 4.5 Relatório distribuído

| Pessoa | Escreve no relatório |
|---|---|
| Matheus | Modelagem da esponja e do queijo, cena, câmera, projeção/culling |
| Miller | Modelagem do prato e do rolo, Phong, baricêntricas e resoluções |
| Vinicius | Modelagem da boia, Bresenham, par-ímpar; **capa, introdução, objetivo, conclusão e referências**; consolidação e formatação final |

Cada um entrega suas seções com **fórmulas, trechos curtos de código, figuras e comentários**. Vinicius uniformiza estilo, numeração de figuras e referências.

### 4.6 Conhecimento cruzado (a nota vem da apresentação)

A nota é dada na apresentação, e todos podem ser questionados sobre qualquer parte. Por isso:

- Ao fim de cada fase, cada pessoa faz uma **explicação de 10 minutos** da sua parte para os outros dois.
- Antes de apresentar, cada um **lê e executa o código dos outros**.
- Ensaiem a apresentação completa pelo menos uma vez, trocando quem apresenta cada etapa.

---

## 5. Modelagem dos objetos (item 1)

Cada função retorna o dicionário do sólido, independente de qualquer plot.

| Objeto | Responsável | Ideia de malha |
|---|---|---|
| Esponja | Matheus | Paralelepípedo com subdivisão da malha. Se quiserem camada verde e amarela, tratem como um sólido só (regra de cor única por sólido) |
| Fatia de queijo | Matheus | Prisma triangular (cunha) ou fatia retangular fina; buracos são extra opcional |
| Prato | Miller | Sólido de revolução: perfil 2D (fundo, borda e aba) girado em torno do eixo Y em N fatias, ligando anéis de vértices com triângulos. Garantir fundo fechado ou perfil com espessura |
| Rolo de massa | Miller | Cilindro (corpo) mais duas hastes finas nas pontas, ou um único perfil de revolução. Tampas com triângulos em leque |
| Boia de piscina | Vinicius | Toro: `((R + r cos v) cos u, r sin v, (R + r cos v) sin u)`, triangulando a grade (cuidado com o fechamento nas duas direções) |

**Verificações obrigatórias por sólido:**

1. Normais apontando para fora (teste: produto escalar entre a normal e o vetor do centroide até o centro da face positivo, para sólidos convexos ou aproximadamente convexos; no toro, comparar com o centro do anel).
2. Plot 3D no sistema do objeto, com eixos x, y, z desenhados e, se possível, setas das normais (`quiver`) em algumas faces.
3. Função de construção independente de qualquer plot.

---

## 6. Cena no mundo (item 2) — Matheus

- Matrizes 4x4 de escala `S`, rotação `R` (Rx, Ry, Rz) e translação `T`; aplicar `M = T·R·S` em cada sólido.
- Restrição: **|x|, |y|, |z| ≤ 10** em todos os vértices. Escolher escalas para que cada objeto caiba em uma "célula" separada (cinco posições em fila ou semicírculo, com folga).
- Verificar a não interseção com caixas delimitadoras (bounding boxes) usando `assert`. É um bom argumento na apresentação.
- Mostrar a cena em 3D com os eixos do mundo.

**Atenção às normais:** com escala não uniforme, as normais devem ser transformadas pela inversa transposta da parte 3x3 da matriz. Mais simples: recalcular as normais das faces após transformar os vértices.

---

## 7. Câmera (item 3) — Matheus

Dados `eye`, `at` (ponto para onde olha) e `up`:

```
w = (eye - at) / |eye - at|      # eixo z da câmera (aponta para trás)
u = (up × w) / |up × w|          # eixo x
v = w × u                        # eixo y
```

Matriz de visão: rotação com u, v, w nas linhas, multiplicada pela translação por `-eye`.

**Entregáveis:**

- Imprimir e mostrar no relatório a base (u, v, w).
- Plotar os sólidos no sistema da câmera, com **um ponto marcando a origem do mundo** (transformada para a câmera).
- Gerar imagens para **pelo menos 2 ou 3 valores de eye diferentes** (item 3e). Criar a função `render(eye)` que roda o pipeline completo, o que facilita a demonstração ao vivo.

---

## 8. Projeção em perspectiva (item 4) — Matheus

- Definir o plano de projeção a uma distância `d` da câmera e o volume de visão (FOV, near, far).
- Projeção: `x' = d·x/(-z)`, `y' = d·y/(-z)` (ajustar o sinal conforme a convenção de `w`).
- **Descartar polígonos não visíveis:** triângulos de costas e triângulos fora do volume de visão (atrás da câmera ou além do far). Evitar `z` próximo de zero.
- Mostrar no mesmo gráfico 3D: os objetos, o plano de projeção e as projeções 2D (item 4a). Depois, uma figura só 2D da janela de projeção.
- Cores: cada sólido uma cor distinta, arestas e faces com a mesma cor.

---

## 9. Iluminação (item 5) — Miller

Modelo de Phong aplicado **nos vértices** dos triângulos visíveis:

```
I = Ka·Ia + Kd·Il·max(0, N·L) + Ks·Il·max(0, R·V)^n
```

- Definir posição e cor da luz e `Ka`, `Kd`, `Ks`, `n` por objeto (prato e boia com brilho especular maior; esponja e queijo mais difusos).
- Para vértices compartilhados, usar a normal do vértice (média das normais das faces adjacentes) para resultado suave. A alternativa mais simples (normal da face) deixa as cores facetadas.
- Calcular L, V e R no mesmo espaço (câmera ou mundo), de forma consistente.
- No relatório, mostrar separadamente as componentes ambiente, difusa e especular e a soma.

---

## 10. Rasterização (item 6)

Responsáveis: **Vinicius** (Bresenham e par-ímpar) e **Miller** (baricêntricas, viewport e resoluções).

Ordem recomendada:

1. **Culling por normal:** descartar o triângulo se `N · (direção do olho até o centro da face) ≥ 0` (ou, no sistema da câmera, pela componente z da normal). Deve ser feito *antes* de rasterizar, como o enunciado pede.
2. **Bresenham** (livro-texto 5.2.1) para as arestas. Testar todos os octantes, incluindo verticais e inclinação negativa. *(Vinicius)*
3. **Par-ímpar com scanline** para preenchimento: para cada linha y, achar as interseções com as arestas, ordenar e preencher entre pares. Cuidado com vértices exatamente na scanline (regra: `ymin` incluso, `ymax` excluso). *(Vinicius)*
4. **Coordenadas baricêntricas** para interpolar o RGB dentro de cada triângulo a partir das cores dos três vértices. *(Miller)*
5. **Viewport e 3 resoluções** (por exemplo 200×200, 400×400 e 800×800): mostrar as três imagens lado a lado e comentar qualidade e tempo. *(Miller)*

**Limitação a citar no relatório:** o enunciado não pede z-buffer e só remove faces de costas pela normal. Com objetos separados e sem sobreposição na tela isso funciona; se dois objetos se sobrepuserem na projeção, haverá artefatos. Escolher `eye` que evite isso, ou implementar o algoritmo do pintor (ordenação por profundidade) como extra opcional.

---

## 11. Relatório (Obs1)

Estrutura exigida: capa, introdução, objetivo, desenvolvimento, simulações computacionais, conclusão e referências.

- **Capa:** instituição, curso, disciplina, professor, título, integrantes, data.
- **Introdução e objetivo:** pipeline gráfico e o que será feito.
- **Desenvolvimento:** uma subseção por etapa (modelagem de cada objeto com as fórmulas, transformações, câmera, projeção, Phong, Bresenham, par-ímpar, baricêntricas), com equações e trechos curtos de código.
- **Simulações computacionais:** figuras de cada item, na ordem do enunciado (1e, 2b, 3c, 3e, 4a, 5, 6 com 3 resoluções).
- **Conclusão:** dificuldades, limitações e aprendizados.
- **Referências:** livro-texto da disciplina, notas de aula e documentação das bibliotecas.

**Dica:** salvar as figuras já no `main.py`, com nomes padronizados (`fig_2b_cena_mundo.png`, `fig_6_res_400.png` etc.). Assim o relatório é só montar.

---

## 12. Entrega e apresentação

- **Entrega:** apenas 2 arquivos: um `.zip` com o código (sem link de Drive) e um `.pdf` com o relatório. Incluir no zip um `README` com instruções de execução e o `requirements.txt`.
- **Apresentação (é a nota):** roteiro de demonstração: rodar `main.py`, mostrar cada etapa, mudar o `eye` ao vivo e mostrar a nova imagem.
- **Perguntas para treinar:**
  - Por que a normal sai do produto vetorial?
  - Como vocês garantiram que ela aponta para fora?
  - Como o par-ímpar trata vértices na scanline?
  - Por que a matriz de visão usa a base (u, v, w) nas linhas?
  - Qual a diferença entre normal de face e normal de vértice na iluminação?

---

## 13. Cronograma sugerido

A data de entrega não foi informada; ajustem as semanas ao prazo real.

| Fase | Conteúdo | Meta | Quem |
|---|---|---|---|
| **1** | Formato do sólido, repositório, assinaturas das funções | Dia 1–2 | Todos |
| **2** | Modelar os 5 sólidos + plots no sistema do objeto; transformações e câmera | Semana 1 | Cada um o seu; Matheus: transformações e câmera |
| **3** | Cena no mundo + `render(eye)` | Semana 2 | Matheus |
| **4** | Projeção + culling; Phong; Bresenham e par-ímpar (em paralelo) | Semanas 2–3 | Matheus / Miller / Vinicius |
| **5** | Integração: baricêntricas + 3 resoluções | Semana 3–4 | Miller (com apoio de todos) |
| **6** | Relatório, revisão de código cruzada, ensaio da apresentação | Última semana | Todos; Vinicius consolida |

---

## 14. Checklist final

- [ ] 5 sólidos únicos, cada um com função que retorna vértices, arestas, faces, normais e cor
- [ ] Normais das faces apontando para fora (verificado)
- [ ] Cada sólido plotado no seu sistema de coordenadas
- [ ] Cena com |coordenadas| ≤ 10, sem interseção, usando escala, rotação e translação
- [ ] Base da câmera calculada e impressa; origem do mundo marcada
- [ ] Imagens para mais de um valor de `eye`
- [ ] Projeção em perspectiva polígono a polígono, com descarte de não visíveis
- [ ] Cores distintas por sólido (aresta e face iguais)
- [ ] Phong (ambiente + difusa + especular) nos vértices
- [ ] Culling por normal antes da rasterização
- [ ] Bresenham, par-ímpar com scanline e interpolação baricêntrica implementados por vocês
- [ ] 3 resoluções diferentes
- [ ] Relatório completo em PDF (capa, introdução, objetivo, desenvolvimento, simulações, conclusão, referências)
- [ ] Zip com código, README e requirements.txt
- [ ] Os três integrantes dominam o código inteiro
