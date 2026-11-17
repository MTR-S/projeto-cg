# Trabalho de Computação Gráfica – Pipeline Gráfico 3D (2ª Etapa)

**Instituto Federal de Educação, Ciência e Tecnologia do Ceará (IFCE) – Campus Fortaleza**  
**Departamento de Telemática | Engenharia da Computação**  
**Disciplina:** Computação Gráfica (2026.2)  
**Professor:** Prof. Dr. Ajalmar Rocha Neto  
**Equipe:** Matheus, Miller e Vinicius  

---

## 📌 Sumário
1. [Sobre o Projeto](#-sobre-o-projeto)
2. [Divisão de Tarefas da Equipe](#-divisão-de-tarefas-da-equipe)
3. [Estrutura do Repositório](#-estrutura-do-repositório)
4. [Contrato de Dados e Assinaturas](#-contrato-de-dados-e-assinaturas)
5. [Instalação e Ambiente](#-instalação-e-ambiente)
6. [Instruções de Execução](#-instruções-de-execução)
7. [Fluxo de Trabalho Git](#-fluxo-de-trabalho-git)
8. [Checklist dos Requisitos](#-checklist-dos-requisitos)

---

## 📖 Sobre o Projeto

Este projeto consiste na implementação completa de um **pipeline gráfico 3D em software ("na mão")**, desde a modelagem matemática de sólidos até a rasterização por scanline e interpolação baricêntrica de cores, sem o uso de aceleradores gráficos como OpenGL ou motores de rasterização prontos.

### Objetos Escolhidos:
1. **Esponja de lavar louça** (Paralelepípedo subdividido) – *Matheus*
2. **Fatia de queijo** (Prisma triangular / cunha) – *Matheus*
3. **Prato** (Sólido de revolução em torno de Y) – *Miller*
4. **Rolo de massa** (Cilindro com hastes) – *Miller*
5. **Boia de piscina** (Toro paramétrico) – *Vinicius*

---

## 👥 Divisão de Tarefas da Equipe

A divisão foi planejada para equilibrar volume de código, complexidade conceitual e autonomia de testes:

| Integrante | Modelagem 3D | Pipeline Gráfico | Relatório & Integração | Pontos |
|---|---|---|---|:---:|
| **Matheus** | Esponja (1) + Queijo (1) | Cena no Mundo (2) + Câmera (2) + Projeção & Culling (3) | `main.py`, README, requirements (1) | **10** |
| **Miller** | Prato (2) + Rolo (2) | Iluminação Phong (3) + Baricêntricas & Viewport (3) | Seções de iluminação e resoluções | **10** |
| **Vinicius** | Boia (3) | Bresenham (2) + Par-Ímpar com Scanline (3) | Consolidação, introdução, capa e conclusão (2) | **10** |

---

## 📂 Estrutura do Repositório

```
trabalho_final/
├── docs/
│   ├── plano_de_acao_trabalho_CG.md   # Planejamento estratégico e arquitetural
│   └── Trabalho CG 2026_2.docx-2.pdf  # Especificação original do professor
├── solidos/
│   ├── __init__.py                    # Exporta geradores dos 5 sólidos
│   ├── esponja.py                     # [Matheus] Sólido: Esponja
│   ├── queijo.py                      # [Matheus] Sólido: Fatia de queijo
│   ├── prato.py                       # [Miller]  Sólido: Prato de revolução
│   ├── boia.py                        # [Vinicius] Sólido: Boia de piscina (toro)
│   └── rolo.py                        # [Miller]  Sólido: Rolo de massa
├── transformacoes.py                  # [Matheus] Matrizes 4x4 (Escala, Rotação, Translação)
├── camera.py                          # [Matheus] Base (u, v, w) e matriz de visão
├── projecao.py                        # [Matheus] Perspectiva, backface culling e janela 2D
├── iluminacao.py                      # [Miller]  Modelo de iluminação de Phong (Amb+Dif+Esp)
├── rasterizacao.py                    # [Vinicius & Miller] Bresenham, Par-Ímpar e Baricêntricas
├── cena.py                            # [Matheus] Montagem do mundo (|coord| <= 10 e AABB check)
├── main.py                            # Pipeline completo e gerador das figuras do relatório
├── requirements.txt                   # Dependências mínimas
└── README.md                          # Este documento
```

---

## 📐 Contrato de Dados e Assinaturas

Todos os módulos operam sob o seguinte dicionário padronizado:

```python
solido = {
    "vertices": np.ndarray,      # (N, 3) float64
    "faces": np.ndarray,         # (M, 3) int32, triângulos com orientação anti-horária (CCW)
    "arestas": np.ndarray,       # (K, 2) int32
    "normais_faces": np.ndarray, # (M, 3) float64, unitárias apontando para fora
    "cor": (r, g, b),            # tupla float no intervalo [0.0, 1.0]
    "nome": "identificador"      # str
}
```

### Assinaturas Principais
- `criar_<solido>(...) -> dict`
- `escala(sx, sy, sz) -> np.ndarray (4,4)`
- `rotacao_x/y/z(theta) -> np.ndarray (4,4)`
- `translacao(tx, ty, tz) -> np.ndarray (4,4)`
- `camera(eye, at, up) -> (u, v, w, matriz_visao)`
- `projetar(solido_cam, d, near, far) -> (pontos_2d, faces_visiveis)`
- `phong(solido, luz_pos, eye_pos, ...) -> cores_vertices (N,3)`
- `bresenham(x0, y0, x1, y1) -> lista de pixels (x, y)`
- `preencher_par_impar(triangulo_2d, cores_vertices, ...) -> None`
- `baricentricas(p, a, b, c) -> (lambda0, lambda1, lambda2)`

---

## ⚙️ Instalação e Ambiente

Requer **Python 3.10+**.

```bash
# Criar e ativar ambiente virtual (recomendado)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\Activate.ps1 # Windows PowerShell

# Instalar dependências
python -m pip install -r requirements.txt
```

---

## 🚀 Instruções de Execução

### Testes Isolados (Unitários)
Cada arquivo possui um bloco `if __name__ == "__main__":` autônomo:

```bash
# Testar sólidos
python solidos/esponja.py
python solidos/queijo.py
python solidos/prato.py
python solidos/boia.py
python solidos/rolo.py

# Testar módulos de pipeline
python transformacoes.py
python camera.py
python projecao.py
python iluminacao.py
python rasterizacao.py
python cena.py
```

### Execução Completa
Para rodar a demonstração e o pipeline integrado:

```bash
python main.py
```

---

## 🌿 Fluxo de Trabalho Git

1. **Branch `main` protegida:** Apenas código revisado e funcionando é mesclado nela.
2. **Branches por funcionalidade e integrante:**
   - `matheus/camera`
   - `miller/phong`
   - `vinicius/par-impar`
3. **Commits semânticos:**
   - `feat: adiciona calculo de normais dos vertices em iluminacao.py`
   - `fix: corrige orientacao de faces no solido do prato`
   - `docs: atualiza secao de camera no relatorio`

---

## ✅ Checklist dos Requisitos da Disciplina

- [x] 5 sólidos únicos e modelados em malha de triângulos
- [x] Normais unitárias das faces apontando para fora do objeto
- [x] Plot e exibição no sistema do objeto (Item 1e)
- [x] Cena no mundo com $|x|, |y|, |z| \le 10$ e sem interseção (Item 2)
- [x] Base da câmera ortonormal $(u, v, w)$ e marcação da origem do mundo (Item 3)
- [x] Suporte a diferentes posições de câmera (`eye`) (Item 3e)
- [x] Projeção em perspectiva com descarte de polígonos não visíveis (Item 4)
- [x] Cores distintas por sólido (arestas e faces correspondentes)
- [x] Modelo de Iluminação Phong (Ambiente, Difusa e Especular) nos vértices (Item 5)
- [x] Culling por normal antes da rasterização (Item 6)
- [x] Algoritmo de Bresenham (livro-texto 5.2.1) implementado manualmente
- [x] Algoritmo Par-Ímpar com Scanline implementado manualmente
- [x] Interpolação baricêntrica de cores no preenchimento
- [x] Geração e comparação em 3 resoluções diferentes (ex.: 200x200, 400x400, 800x800)
- [ ] Relatório final em PDF com Capa, Introdução, Objetivo, Desenvolvimento, Simulações, Conclusão e Referências
- [ ] Empacotamento em `.zip` com código-fonte para entrega oficial
