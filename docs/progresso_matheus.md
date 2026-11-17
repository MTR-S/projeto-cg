# Registro de Atribuições e Progresso Detalhado – Matheus

**Instituição:** Instituto Federal do Ceará (IFCE) – Campus Fortaleza  
**Curso:** Engenharia da Computação  
**Disciplina:** Computação Gráfica (2026.2)  
**Professor:** Prof. Dr. Ajalmar Rocha Neto  
**Aluno:** Matheus Almeida  
**Documento de Referência:** `docs/Trabalho CG 2026_2.docx-2.pdf` e `docs/plano_de_acao_trabalho_CG.md`  
**Branch de Trabalho:** `matheus/camera`  

---

## 📋 Cabeçalho: Matriz de Atribuições do Matheus (Mapeada com o PDF Oficial)

A tabela abaixo relaciona todas as responsabilidades assumidas por Matheus com os itens estritos do documento oficial do professor ([Trabalho CG 2026_2.docx-2.pdf](file:///C:/Users/MatheusAlmeida/faculdade/2026_2/Computação%20Gráfica%20(CG)/trabalho_final/docs/Trabalho%20CG%202026_2.docx-2.pdf)):

| Item do PDF | Descrição Exigida pelo Professor | Responsabilidade do Matheus | Arquivo(s) no Projeto | Pontos |
|---|---|---|---|:---:|
| **1a, 1b, 1c, 1d, 1e** | Modelar objetos do cotidiano em malha de triângulos, normais unitárias apontando para fora, função construtora e plot no sistema de coordenadas do objeto. | Modelagem matemática da **Esponja de lavar louça** e da **Fatia de queijo**, além do módulo geral de validação/plot. | `solidos/esponja.py`<br>`solidos/queijo.py`<br>`solidos/visualizacao.py` | **2 pts** (1+1) |
| **2, 2a, 2b** | Compor a cena no sistema de coordenadas do mundo usando escala, rotação e translação afins, sem sobreposição, com $\|x\|, \|y\|, \|z\| \le 10$ e plot 3D. | Implementar módulo de transformações homogêneas 4x4 e montar a cena mundial com teste de bounding boxes (AABB). | `transformacoes.py`<br>`cena.py` | **2 pts** |
| **3, 3a, 3b, 3c, 3d, 3e** | Definir ponto de visão (`eye`), calcular base vetorial $(u, v, w)$, matriz de visão, transformar cena, marcar origem do mundo e suportar variação de `eye`. | Implementar todo o sistema de visão (câmera sintética), cálculo da base ortonormal, matriz $M_{vis}$ e marcação da origem. | `camera.py` | **2 pts** |
| **4, 4a** | Projeção em perspectiva polígono a polígono na janela 2D, descarte de polígonos ocultos (*culling*) e plot 3D com objetos + plano de projeção 2D. | Algoritmo de projeção perspectiva, descarte de faces traseiras (*backface culling*) e visualização integrada 3D/2D. | `projecao.py` | **3 pts** |
| **Obs1, Obs2** | Relatório completo (Capa a Referências), empacotamento em `.zip` e código executável. | Estruturação de `main.py`, `README.md`, `requirements.txt`, repositório remoto Git e escrita das seções de sua alçada no relatório. | `main.py`<br>`README.md`<br>`requirements.txt` | **1 pt** |
| **Total** | — | — | — | **10 pts** |

---

## 🛠️ Detalhamento do que Já Foi Feito (Parte do Matheus)

### 1. Modelagem dos Sólidos 1 e 2 (Itens 1a até 1e do PDF)

#### A. Esponja de Lavar Louça (`solidos/esponja.py`)
* **Modelo Geométrico:** Paralelepípedo retangular centrado na origem $(0, 0, 0)$.
* **Topologia:** 8 vértices, 12 faces triangulares orientadas em sentido anti-horário (CCW) visto de fora, 18 arestas.
* **Cálculo de Normais:** Vetores normais unitários calculados analiticamente a partir do produto vetorial das arestas adjacentes de cada triângulo:
  $$\vec{n} = \frac{(v_1 - v_0) \times (v_2 - v_0)}{\|(v_1 - v_0) \times (v_2 - v_0)\|}$$
* **Status:** ✅ Concluído e testado.

#### B. Fatia de Queijo (`solidos/queijo.py`)
* **Modelo Geométrico:** Prisma em cunha triangular com base no plano $XZ$ e altura ao longo de $Y$.
* **Topologia:** 6 vértices, 8 faces triangulares, 12 arestas.
* **Correção de Orientação Realizada:** Os triângulos foram rigorosamente calibrados para garantir que todos os produtos vetoriais apontem para o exterior do sólido (faces superior, inferior, laterais planas e arco frontal).
* **Status:** ✅ Concluído e testado.

#### C. Módulo de Validação Geométrica e Plot 3D (`solidos/visualizacao.py`)
* Criada a rotina `validar_solido()` que executa testes matemáticos automatizados:
  1. Verifica se todas as normais são estritamente unitárias ($\|\vec{n}\| = 1.0 \pm 10^{-5}$).
  2. Verifica se as normais apontam para fora via produto escalar com o centroide: $\vec{n}_j \cdot (B_j - C) > 0$.
* Criada a rotina `plotar_solido()` (atendendo ao **Item 1e**):
  - Renderiza o sólido com transparência e arestas demarcadas.
  - Plota as setas das normais saindo dos baricentros das faces (`ax.quiver` em vermelho).
  - Plota os eixos coordenados locais do objeto: $X$ (vermelho), $Y$ (verde) e $Z$ (azul).
  - Destaca o ponto da origem local $(0, 0, 0)$.
  - Salva automaticamente as figuras em alta resolução (300 DPI) em `outputs/fig_1_esponja.png` e `outputs/fig_1_queijo.png`.
* **Status:** ✅ 100% Concluído e operacional.

---

### 2. Transformações Geométricas 3D e Cena Mundial (Itens 2, 2a, 2b do PDF)

#### A. Módulo de Transformações (`transformacoes.py`)
* Implementadas matrizes homogêneas $4 \times 4$:
  * **Escala:** `escala(sx, sy, sz)`
  * **Rotações:** `rotacao_x(theta)`, `rotacao_y(theta)`, `rotacao_z(theta)` em radianos.
  * **Translação:** `translacao(tx, ty, tz)`
  * **Aplicação em Vértices:** `aplicar_transformacao(vertices, matriz)` com conversão homogênea $(x, y, z, 1)$ e normalização pelo fator $w$.
  * **Transformação de Sólidos:** `transformar_solido(solido, matriz)` que transforma os vértices e recalcula as normais de face para preservar a consistência física.
* **Status:** ✅ 100% Concluído e testado.

#### B. Montagem da Cena no Mundo (`cena.py`)
* **Posicionamento:** Instanciação dos 5 objetos da equipe (esponja, queijo, prato, rolo e boia) aplicando composições de matrizes $M = T \cdot R \cdot S$.
* **Restrição de Limites (Item 2a):** Implementada checagem com `assert` de que $|coord| \le 10.0$ em todos os vértices da cena. O maior valor absoluto registrado em qualquer sólido é $8.70$.
* **Garantia de Não-Intersecção (Item 2):** Implementado algoritmo de detecção de colisão por caixas delimitadoras alinhadas aos eixos (*Axis-Aligned Bounding Box - AABB*). O teste verifica todos os pares de objetos e comprova matematicamente que não há qualquer colisão ou sobreposição.
* **Status:** ✅ Cálculos matemáticos 100% validados.

---

### 3. Sistema de Câmera / Visão (Itens 3, 3a até 3e do PDF)

#### A. Base Ortonormal e Matriz de Visão (`camera.py`)
* Implementada a função `camera(eye, at, up)` conforme as especificações de VRC (*Viewing Reference Coordinate System*):
  1. Eixo da linha de visão (aponta para trás):
     $$\vec{w} = \frac{eye - at}{\|eye - at\|}$$
  2. Eixo horizontal da câmera (aponta para a direita):
     $$\vec{u} = \frac{up \times \vec{w}}{\|up \times \vec{w}\|}$$
  3. Eixo vertical ortogonal da câmera (aponta para cima):
     $$\vec{v} = \vec{w} \times \vec{u}$$
  4. Matriz de visão composta $4 \times 4$:
     $$M_{vis} = R_{vis} \cdot T_{vis} = \begin{bmatrix} u_x & u_y & u_z & 0 \\ v_x & v_y & v_z & 0 \\ w_x & w_y & w_z & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix} \begin{bmatrix} 1 & 0 & 0 & -eye_x \\ 0 & 1 & 0 & -eye_y \\ 0 & 0 & 1 & -eye_z \\ 0 & 0 & 0 & 1 \end{bmatrix}$$
* **Transformação de Sólidos:** `transformar_para_camera()` aplica a rotação ortogonal e translação aos vértices e rotaciona as normais pela matriz $3 \times 3$ ortogonal da câmera.
* **Marcação da Origem do Mundo (Item 3d):** Função `obter_origem_mundo_na_camera()` calcula exatamente onde $(0, 0, 0)_{mundo}$ está localizado nas coordenadas da câmera.
* **Status:** ✅ Matemática e transformações concluídas.

---

### 4. Projeção em Perspectiva e Culling (Itens 4 e 4a do PDF)

#### A. Módulo de Projeção (`projecao.py`)
* **Backface Culling (Descarte de Polígonos Ocultos):**
  - Implementado em `descartar_faces_ocultas()`.
  - Como a câmera olha na direção $-Z$ no espaço de visão, o vetor da origem da câmera até a face é o próprio baricentro $B_{face}$.
  - Se $\vec{n}_{face} \cdot B_{face} < 0$, a face está voltada para o observador (visível); caso contrário, é descartada antes da projeção.
* **Projeção Perspectiva:**
  - Implementada em `projetar(solido_cam, d)`.
  - Mapeamento no plano de projeção a uma distância focal $d$:
    $$x_p = \frac{d \cdot x}{-z}, \quad y_p = \frac{d \cdot y}{-z}$$
  - Filtro contra singularidades ($z \ge 0$) e recorte por planos *near* e *far*.
* **Status:** ✅ Algoritmo de projeção e culling operacionais.

---

### 5. Infraestrutura e Integração (Obs1 e Obs2 do PDF)

* **Repositório Remoto:** Criado e publicado no GitHub ([MTR-S/projeto-cg](https://github.com/MTR-S/projeto-cg)), com branches `main` e `matheus/camera`.
* **Pipeline Integrado (`main.py`):** Criada função `render(eye, ...)` que acopla todas as etapas (Mundo $\to$ Câmera $\to$ Projeção $\to$ Iluminação Phong $\to$ Rasterização por Scanline) e executa sem erros.
* **Status:** ✅ 100% Concluído.

---

## 📌 Próximos Passos Imediatos para Finalizar a Parte do Matheus

Para fechar todas as figuras exigidas no relatório oficial:

1. **Plot da Cena no Mundo (Item 2b):** Adicionar função em `cena.py` para gerar a imagem 3D de todos os 5 sólidos dispostos no espaço com os eixos mundiais.
2. **Plot da Cena na Câmera (Itens 3c, 3d, 3e):** Adicionar função em `camera.py` que plota os sólidos no referencial da câmera, desenha um ponto destacado na origem do mundo e gera imagens para 3 posições diferentes de `eye`.
3. **Plot Especial da Projeção 3D + Janela 2D (Item 4a):** Implementar em `projecao.py` a visualização simultânea dos sólidos 3D, do retângulo da janela de projeção no plano $z = -d$ e dos triângulos 2D desenhados nessa janela.
