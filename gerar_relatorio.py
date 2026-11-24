"""
Gerador do Relatório Técnico em PDF para o Trabalho de Computação Gráfica (IFCE 2026.2).

Coleta métricas e figuras reais do pipeline, monta HTML acadêmico autocontido
com imagens em Base64 e converte para PDF via navegador Chromium/Edge headless.
"""

from __future__ import annotations

import base64
import html
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import numpy as np

from camera import camera, obter_origem_mundo_na_camera, transformar_para_camera
from cena import montar_cena, obter_bounding_box
from projecao import descartar_faces_ocultas, projetar
from solidos import (
    criar_boia,
    criar_esponja,
    criar_prato,
    criar_queijo,
    criar_rolo,
)
from visualizacao_3d import gerar_figuras_3d
from visualizacao_pipeline import (
    plotar_iluminacao_phong,
    plotar_projecao_3d_2d,
    plotar_rasterizacao_eyes,
    plotar_rasterizacao_resolucoes,
)

EYES_PADRAO: tuple[tuple[float, float, float], ...] = (
    (12.0, 8.0, 14.0),
    (-12.0, 8.0, 14.0),
    (0.0, 14.0, 16.0),
)


def encontrar_navegador_headless() -> str:
    """
    Localiza um executável de navegador Chromium/Edge compatível com --headless
    e --print-to-pdf no sistema.
    """
    candidatos_which = ("msedge.exe", "msedge", "chrome.exe", "chrome", "google-chrome", "chromium")
    for nome in candidatos_which:
        encontrado = shutil.which(nome)
        if encontrado and os.path.isfile(encontrado):
            return encontrado

    caminhos_windows = (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    )
    for caminho in caminhos_windows:
        if os.path.isfile(caminho):
            return caminho

    raise FileNotFoundError(
        "Nenhum navegador headless (msedge.exe ou chrome.exe) foi encontrado no PATH "
        "nem nos diretórios padrão do Windows."
    )


def _limpar_vetor_lista(vetor: np.ndarray, casas: int = 4) -> list[float]:
    """Arredonda vetor NumPy evitando -0.0 e retorna lista de floats Python."""
    resultado: list[float] = []
    for val in vetor:
        f = round(float(val), casas)
        resultado.append(0.0 if abs(f) < 1e-9 else f)
    return resultado


def coletar_dados_estaticos_pipeline() -> dict:
    """
    Coleta métricas determinísticas do pipeline (sólidos, cena, câmeras,
    estatísticas de projeção/culling e parâmetros de iluminação).
    """
    solidos_padrao = [
        criar_esponja(),
        criar_queijo(),
        criar_prato(),
        criar_rolo(),
        criar_boia(),
    ]
    info_solidos = [
        {
            "nome": s["nome"],
            "vertices": int(len(s["vertices"])),
            "faces": int(len(s["faces"])),
            "arestas": int(len(s["arestas"])),
            "cor": tuple(round(float(c), 3) for c in s["cor"]),
        }
        for s in solidos_padrao
    ]

    cena_mundo = montar_cena()
    info_cena = []
    for s in cena_mundo:
        bmin, bmax = obter_bounding_box(s["vertices"])
        info_cena.append(
            {
                "nome": s["nome"],
                "vertices": int(len(s["vertices"])),
                "faces": int(len(s["faces"])),
                "arestas": int(len(s["arestas"])),
                "bbox_min": _limpar_vetor_lista(bmin, 3),
                "bbox_max": _limpar_vetor_lista(bmax, 3),
                "max_abs_coord": round(float(np.max(np.abs(s["vertices"]))), 3),
                "cor": tuple(round(float(c), 3) for c in s["cor"]),
            }
        )

    at = (0.0, 0.0, 0.0)
    up = (0.0, 1.0, 0.0)
    info_cameras = []
    for eye in EYES_PADRAO:
        u, v, w, m_vis = camera(eye=eye, at=at, up=up)
        origem_cam = obter_origem_mundo_na_camera(m_vis)
        info_cameras.append(
            {
                "eye": [float(c) for c in eye],
                "at": [float(c) for c in at],
                "up": [float(c) for c in up],
                "u": _limpar_vetor_lista(u, 4),
                "v": _limpar_vetor_lista(v, 4),
                "w": _limpar_vetor_lista(w, 4),
                "origem_mundo_cam": _limpar_vetor_lista(origem_cam, 3),
            }
        )

    eye_ref = EYES_PADRAO[0]
    d_proj = 1.8
    near = 0.5
    far = 100.0
    _, _, _, m_vis_ref = camera(eye=eye_ref, at=at, up=up)
    proj_por_solido = []
    for s_mundo in cena_mundo:
        s_cam = transformar_para_camera(s_mundo, m_vis_ref)
        idx_culling = descartar_faces_ocultas(s_cam)
        _, faces_vis = projetar(s_cam, d=d_proj, near=near, far=far)
        proj_por_solido.append(
            {
                "nome": s_mundo["nome"],
                "faces_totais": int(len(s_mundo["faces"])),
                "faces_apos_culling": int(len(idx_culling)),
                "faces_visiveis": int(len(faces_vis)),
            }
        )

    return {
        "solidos": info_solidos,
        "cena_mundo": info_cena,
        "cameras": info_cameras,
        "projecao": {
            "d_proj": d_proj,
            "near": near,
            "far": far,
            "eye": list(eye_ref),
            "por_solido": proj_por_solido,
        },
        "iluminacao": {
            "luz_pos": [0.0, 10.0, 5.0],
            "eye_pos": list(eye_ref),
            "ia": 0.2,
            "il": 0.8,
            "ka": 0.3,
            "kd": 0.7,
            "ks": 0.5,
            "n_especular": 16.0,
        },
    }


def coletar_metricas_pipeline(
    diretorio_figuras: str = "outputs",
) -> tuple[dict, dict[str, str]]:
    """
    Executa as visualizações do pipeline, coleta métricas reais dos sólidos,
    bounding boxes da cena, bases de câmera e tempos de rasterização nas três
    resoluções (200x200, 400x400, 800x800).
    """
    os.makedirs(diretorio_figuras, exist_ok=True)
    metricas = coletar_dados_estaticos_pipeline()

    caminhos_figuras = gerar_figuras_3d(diretorio_saida=diretorio_figuras)
    caminhos_figuras["fig_4a"] = plotar_projecao_3d_2d(diretorio_saida=diretorio_figuras)
    caminhos_figuras["fig_5"] = plotar_iluminacao_phong(diretorio_saida=diretorio_figuras)
    caminho_res, tempos_por_res = plotar_rasterizacao_resolucoes(
        resolucoes=((200, 200), (400, 400), (800, 800)),
        diretorio_saida=diretorio_figuras,
    )
    caminhos_figuras["fig_6_resolucoes"] = caminho_res
    caminhos_figuras["fig_6_eyes"] = plotar_rasterizacao_eyes(
        eyes=EYES_PADRAO,
        diretorio_saida=diretorio_figuras,
    )

    metricas["tempos_resolucoes"] = {
        k: round(float(v), 4) for k, v in tempos_por_res.items()
    }
    return metricas, caminhos_figuras


def _imagem_para_data_uri(caminho_png: str) -> str:
    """Lê um arquivo PNG e converte para Data URI Base64."""
    if not caminho_png or not os.path.isfile(caminho_png):
        raise FileNotFoundError(f"Figura obrigatória não encontrada: {caminho_png}")
    with open(caminho_png, "rb") as f:
        dados = f.read()
    if not dados:
        raise ValueError(f"Arquivo de figura vazio: {caminho_png}")
    b64 = base64.b64encode(dados).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _formatar_vetor(vec: list[float] | tuple[float, ...], casas: int = 3) -> str:
    """Formata um vetor numérico 3D como string legível sem -0.0."""
    partes = []
    for val in vec:
        num = 0.0 if abs(float(val)) < 1e-9 else float(val)
        partes.append(f"{num:.{casas}f}")
    return f"({', '.join(partes)})"


def _swatch_cor(cor: tuple[float, float, float]) -> str:
    """Retorna pequeno quadrado colorido em HTML representando a cor RGB [0, 1]."""
    r, g, b = (int(round(min(1.0, max(0.0, c)) * 255)) for c in cor)
    return (
        f'<span class="swatch" style="background-color: rgb({r}, {g}, {b});"></span>'
        f"({cor[0]:.2f}, {cor[1]:.2f}, {cor[2]:.2f})"
    )


def montar_html_relatorio(metricas: dict, caminhos_figuras: dict[str, str]) -> str:
    """
    Constrói o documento HTML5 completo e autocontido (com CSS A4 e figuras em
    Base64) contendo todas as seções acadêmicas exigidas pela Obs1.
    """
    chaves_obrigatorias = (
        "fig_1e",
        "fig_2b",
        "fig_3c",
        "fig_3e",
        "fig_4a",
        "fig_5",
        "fig_6_resolucoes",
        "fig_6_eyes",
    )
    imagens_b64 = {
        chave: _imagem_para_data_uri(caminhos_figuras.get(chave, ""))
        for chave in chaves_obrigatorias
    }

    solidos = metricas["solidos"]
    cena_mundo = metricas["cena_mundo"]
    cameras = metricas["cameras"]
    projecao = metricas["projecao"]
    iluminacao = metricas["iluminacao"]
    tempos_res = metricas["tempos_resolucoes"]

    # Linhas da tabela de sólidos (Seção 3.1)
    linhas_solidos = []
    descricoes_solidos = {
        "esponja": "Paralelepípedo fechado (<code>criar_esponja</code>)",
        "queijo": "Prisma triangular em cunha (<code>criar_queijo</code>)",
        "prato": "Sólido de revolução fechado com espessura (<code>criar_prato</code>)",
        "rolo": "Cilindro central + duas hastes e tampas em leque (<code>criar_rolo</code>)",
        "boia": "Toro paramétrico fechado em <i>u</i> e <i>v</i> (<code>criar_boia</code>)",
    }
    for s in solidos:
        nome = str(s["nome"])
        linhas_solidos.append(
            "<tr>"
            f"<td><strong>{html.escape(nome.capitalize())}</strong></td>"
            f"<td>{descricoes_solidos.get(nome, html.escape(nome))}</td>"
            f'<td class="num">{s["vertices"]}</td>'
            f'<td class="num">{s["faces"]}</td>'
            f'<td class="num">{s["arestas"]}</td>'
            f"<td>{_swatch_cor(s['cor'])}</td>"
            "</tr>"
        )
    tabela_solidos_html = "\n".join(linhas_solidos)

    # Linhas da tabela de bounding boxes na cena do mundo (Seção 4 - Fig. 2)
    linhas_bboxes = []
    for item in cena_mundo:
        linhas_bboxes.append(
            "<tr>"
            f"<td><strong>{html.escape(str(item['nome']).capitalize())}</strong></td>"
            f'<td class="mono">{_formatar_vetor(item["bbox_min"], 2)}</td>'
            f'<td class="mono">{_formatar_vetor(item["bbox_max"], 2)}</td>'
            f'<td class="num">{item["max_abs_coord"]:.2f}</td>'
            f'<td class="num">{item["faces"]}</td>'
            "</tr>"
        )
    tabela_bboxes_html = "\n".join(linhas_bboxes)

    # Linhas da tabela de bases da câmera (Seção 4 - Fig. 3 / 4)
    linhas_cameras = []
    for cam in cameras:
        linhas_cameras.append(
            "<tr>"
            f'<td class="mono">{_formatar_vetor(cam["eye"], 1)}</td>'
            f'<td class="mono">{_formatar_vetor(cam["u"], 3)}</td>'
            f'<td class="mono">{_formatar_vetor(cam["v"], 3)}</td>'
            f'<td class="mono">{_formatar_vetor(cam["w"], 3)}</td>'
            f'<td class="mono">{_formatar_vetor(cam["origem_mundo_cam"], 2)}</td>'
            "</tr>"
        )
    tabela_cameras_html = "\n".join(linhas_cameras)

    # Linhas da tabela de projeção e culling (Seção 4 - Fig. 5)
    linhas_projecao = []
    total_faces_cena = 0
    total_culling = 0
    total_visiveis = 0
    for p in projecao["por_solido"]:
        tot = int(p["faces_totais"])
        cul = int(p["faces_apos_culling"])
        vis = int(p["faces_visiveis"])
        total_faces_cena += tot
        total_culling += cul
        total_visiveis += vis
        perc = (100.0 * vis / tot) if tot > 0 else 0.0
        linhas_projecao.append(
            "<tr>"
            f"<td><strong>{html.escape(str(p['nome']).capitalize())}</strong></td>"
            f'<td class="num">{tot}</td>'
            f'<td class="num">{cul}</td>'
            f'<td class="num">{vis}</td>'
            f'<td class="num">{perc:.1f}%</td>'
            "</tr>"
        )
    perc_total = (100.0 * total_visiveis / total_faces_cena) if total_faces_cena > 0 else 0.0
    linhas_projecao.append(
        '<tr class="total-row">'
        "<td><strong>Total da Cena</strong></td>"
        f'<td class="num"><strong>{total_faces_cena}</strong></td>'
        f'<td class="num"><strong>{total_culling}</strong></td>'
        f'<td class="num"><strong>{total_visiveis}</strong></td>'
        f'<td class="num"><strong>{perc_total:.1f}%</strong></td>'
        "</tr>"
    )
    tabela_projecao_html = "\n".join(linhas_projecao)

    # Linhas da tabela de resoluções e tempos (Seção 4 - Fig. 7)
    linhas_tempos = []
    t_base = float(tempos_res.get("200x200", 0.0))
    for res_str in ("200x200", "400x400", "800x800"):
        larg_s, alt_s = res_str.split("x")
        pixels = int(larg_s) * int(alt_s)
        dt = float(tempos_res[res_str])
        fator = (dt / t_base) if t_base > 0 else 1.0
        linhas_tempos.append(
            "<tr>"
            f"<td><strong>{larg_s} &times; {alt_s}</strong></td>"
            f'<td class="num">{pixels:,}</td>'.replace(",", ".")
            + f'<td class="num">{dt:.3f} s</td>'
            f'<td class="num">{fator:.2f}&times;</td>'
            "</tr>"
        )
    tabela_tempos_html = "\n".join(linhas_tempos)

    # Trechos curtos reais do repositório
    code_normais = html.escape(
        "v0 = vertices[faces[:, 0]]\n"
        "v1 = vertices[faces[:, 1]]\n"
        "v2 = vertices[faces[:, 2]]\n"
        "normais = np.cross(v1 - v0, v2 - v0)\n"
        "normas = np.linalg.norm(normais, axis=1, keepdims=True)\n"
        "normais_unitarias = normais / np.where(normas == 0, 1.0, normas)"
    )
    code_cena = html.escape(
        "esponja = criar_esponja(largura=2.6, altura=1.0, profundidade=1.8, cor=(0.85, 0.85, 0.15))\n"
        "m_esponja = translacao(-6.0, 5.0, -2.0) @ rotacao_y(np.radians(20)) @ escala(1.15, 1.2, 1.1)\n"
        "esponja_mundo = transformar_solido(esponja, m_esponja)\n"
        "# Validação: |coord| <= 10.0 e verificar_intersecao_aabb(box_a, box_b) == False"
    )
    code_camera = html.escape(
        "w = (eye_arr - at_arr) / np.linalg.norm(eye_arr - at_arr)\n"
        "u = np.cross(up_arr, w) / np.linalg.norm(np.cross(up_arr, w))\n"
        "v = np.cross(w, u)\n"
        "matriz_visao = R @ T  # R possui u, v, w nas linhas; T translada por -eye"
    )
    code_projecao = html.escape(
        "baricentros = (vertices[faces[:, 0]] + vertices[faces[:, 1]] + vertices[faces[:, 2]]) / 3.0\n"
        "dots = np.sum(normais * baricentros, axis=1)\n"
        "faces_visiveis = faces[np.where(dots < 0.0)[0]]\n"
        "mascara_frustum = np.all((z[faces_visiveis] <= -near) & (z[faces_visiveis] >= -far), axis=1)\n"
        "xp = (d * vertices[:, 0]) / (-z); yp = (d * vertices[:, 1]) / (-z)"
    )
    code_phong = html.escape(
        "I_amb = ka * ia * cor_base\n"
        "n_dot_l = np.sum(N * L, axis=1, keepdims=True)\n"
        "I_dif = kd * il * np.maximum(0.0, n_dot_l) * cor_base\n"
        "R = 2.0 * n_dot_l * N - L\n"
        "R = R / np.where(np.linalg.norm(R, axis=1, keepdims=True) == 0, 1.0, np.linalg.norm(R, axis=1, keepdims=True))\n"
        "I_esp = ks * il * (np.maximum(0.0, np.sum(R * V, axis=1, keepdims=True)) ** n_especular) * cor_luz\n"
        "I_total = np.clip(I_amb + I_dif + I_esp, 0.0, 1.0)"
    )
    code_raster = html.escape(
        "if (y_a <= y < y_b) or (y_b <= y < y_a):\n"
        "    t = (y - y_a) / (y_b - y_a)\n"
        "    intersecoes_x.append(x_a + t * (x_b - x_a))\n"
        "# Entre pares (x_start, x_end): interpolação baricêntrica e teste de profundidade\n"
        "l0, l1, l2 = baricentricas((x, y), a, b, c)\n"
        "depth = float(l0 * z_vertices[0] + l1 * z_vertices[1] + l2 * z_vertices[2])\n"
        "if depth < z_buffer[y, x]:\n"
        "    z_buffer[y, x] = depth\n"
        "    buffer_cor[y, x] = np.clip(l0 * c_a + l1 * c_b + l2 * c_c, 0.0, 1.0)"
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>Relatório Técnico — Pipeline Gráfico 3D em Software (IFCE 2026.2)</title>
  <style>
    @page {{
      size: A4;
      margin: 20mm 18mm;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      font-family: "Segoe UI", "Liberation Sans", Arial, sans-serif;
      font-size: 10.5pt;
      line-height: 1.52;
      color: #1e293b;
      margin: 0;
      padding: 0;
    }}
    /* Capa */
    .capa {{
      min-height: 250mm;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      text-align: center;
      padding: 12mm 8mm;
      page-break-after: always;
      break-after: page;
    }}
    .capa-instituicao p {{
      margin: 3px 0;
      font-size: 11.5pt;
      font-weight: 600;
      letter-spacing: 0.3px;
      color: #0f172a;
    }}
    .capa-instituicao .sub {{
      font-weight: 400;
      font-size: 10.5pt;
      color: #334155;
    }}
    .capa-titulo {{
      margin: 28mm 0;
      padding: 12mm 8mm;
      border-top: 2px solid #0f172a;
      border-bottom: 2px solid #0f172a;
    }}
    .capa-titulo .etiqueta {{
      font-size: 10pt;
      text-transform: uppercase;
      letter-spacing: 1.4px;
      color: #475569;
      margin-bottom: 10px;
    }}
    .capa-titulo h1 {{
      font-size: 18pt;
      line-height: 1.3;
      margin: 0 0 10px 0;
      color: #0f172a;
    }}
    .capa-titulo .subtitulo {{
      font-size: 11.5pt;
      color: #334155;
      margin: 0;
    }}
    .capa-meta {{
      text-align: left;
      max-width: 135mm;
      margin: 0 auto 14mm auto;
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      padding: 12px 18px;
      font-size: 10.5pt;
    }}
    .capa-meta p {{
      margin: 5px 0;
    }}
    .capa-rodape {{
      font-size: 10.5pt;
      font-weight: 600;
      color: #334155;
    }}
    /* Conteúdo principal */
    h2 {{
      font-size: 14pt;
      color: #0f172a;
      border-bottom: 1.5px solid #334155;
      padding-bottom: 4px;
      margin-top: 22px;
      margin-bottom: 10px;
      page-break-after: avoid;
      break-after: avoid;
    }}
    h3 {{
      font-size: 11.5pt;
      color: #1e3a8a;
      margin-top: 16px;
      margin-bottom: 6px;
      page-break-after: avoid;
      break-after: avoid;
    }}
    p {{
      text-align: justify;
      margin: 0 0 9px 0;
    }}
    ul, ol {{
      margin: 6px 0 10px 0;
      padding-left: 20px;
    }}
    li {{
      margin-bottom: 4px;
      text-align: justify;
    }}
    code {{
      font-family: "Consolas", "Liberation Mono", "Courier New", monospace;
      font-size: 9.2pt;
      background: #f1f5f9;
      padding: 1px 4px;
      border-radius: 3px;
      color: #0f172a;
    }}
    pre {{
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-left: 3.5px solid #1e3a8a;
      border-radius: 4px;
      padding: 9px 12px;
      margin: 8px 0 12px 0;
      overflow-x: hidden;
      white-space: pre-wrap;
      word-break: break-word;
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    pre code {{
      background: transparent;
      padding: 0;
      font-size: 8.6pt;
      line-height: 1.42;
    }}
    .formula-box {{
      background: #f8fafc;
      border: 1px solid #dbeafe;
      border-radius: 4px;
      padding: 8px 14px;
      margin: 8px 0 10px 0;
      font-family: "Cambria Math", "Liberation Serif", Georgia, serif;
      font-size: 10.5pt;
      color: #0f172a;
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    .formula-box p {{
      margin: 3px 0;
      text-align: left;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 10px 0 14px 0;
      font-size: 9.2pt;
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    th, td {{
      border: 1px solid #cbd5e1;
      padding: 6px 8px;
      text-align: left;
      vertical-align: middle;
    }}
    th {{
      background-color: #e2e8f0;
      color: #0f172a;
      font-weight: 700;
    }}
    tr:nth-child(even) td {{
      background-color: #f8fafc;
    }}
    tr.total-row td {{
      background-color: #eef2ff;
    }}
    td.num, th.num {{
      text-align: right;
      font-variant-numeric: tabular-nums;
    }}
    td.mono {{
      font-family: "Consolas", "Courier New", monospace;
      font-size: 8.5pt;
    }}
    .swatch {{
      display: inline-block;
      width: 10px;
      height: 10px;
      border: 1px solid #475569;
      margin-right: 6px;
      vertical-align: middle;
      border-radius: 2px;
    }}
    figure {{
      margin: 12px 0 16px 0;
      padding: 8px;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      background: #ffffff;
      text-align: center;
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    figure img {{
      max-width: 100%;
      max-height: 118mm;
      height: auto;
      display: block;
      margin: 0 auto;
    }}
    figcaption {{
      margin-top: 7px;
      font-size: 9.2pt;
      color: #334155;
      text-align: center;
    }}
    .refs li {{
      margin-bottom: 6px;
      text-align: left;
    }}
  </style>
</head>
<body>

  <!-- CAPA -->
  <section class="capa">
    <div class="capa-instituicao">
      <p>INSTITUTO FEDERAL DE EDUCAÇÃO, CIÊNCIA E TECNOLOGIA DO CEARÁ (IFCE)</p>
      <p class="sub">Campus Fortaleza &mdash; Departamento de Telemática</p>
      <p class="sub">Curso de Engenharia da Computação</p>
    </div>

    <div class="capa-titulo">
      <div class="etiqueta">Trabalho &mdash; 2ª Etapa &mdash; Computação Gráfica (2026.2)</div>
      <h1>Implementação de Pipeline Gráfico 3D em Software: Modelagem, Transformações, Projeção, Iluminação de Phong e Rasterização</h1>
      <p class="subtitulo">Relatório Técnico e Evidências de Simulação Computacional</p>
    </div>

    <div class="capa-meta">
      <p><strong>Disciplina:</strong> Computação Gráfica (2026.2)</p>
      <p><strong>Professor:</strong> Prof. Dr. Ajalmar Rocha Neto</p>
      <p><strong>Equipe:</strong> Matheus, Miller e Vinicius</p>
      <p><strong>Repositório:</strong> <code>projeto-cg</code> (Python, NumPy, Matplotlib, Pillow)</p>
    </div>

    <div class="capa-rodape">
      Fortaleza &ndash; CE<br />
      2026
    </div>
  </section>

  <!-- 1. INTRODUÇÃO -->
  <h2>1. Introdução</h2>
  <p>
    O pipeline gráfico tridimensional descreve a sequência de transformações matemáticas e algorítmicas
    responsáveis por converter modelos geométricos definidos no espaço 3D em uma imagem bidimensional
    discreta exibida em tela. Em bibliotecas modernas como OpenGL ou Vulkan, grande parte dessas operações
    é abstraída pelo hardware gráfico. Contudo, a compreensão profunda de cada estágio requer implementar
    manualmente a cadeia completa em software.
  </p>
  <p>
    Este trabalho apresenta o desenvolvimento integral de um pipeline gráfico 3D em Python utilizando
    exclusivamente álgebra linear numérica via <strong>NumPy</strong>, sem emprego de aceleradores de
    renderização ou APIs gráficas 3D prontas para o traçado final. O projeto cobre desde a geração de cinco
    malhas triangulares fechadas com normais externas consistentes até a rasterização final em memória com
    traçado de arestas por Bresenham, preenchimento par-ímpar por <em>scanline</em>, interpolação baricêntrica
    de cores e resolução de oclusão por <em>Z-buffer</em>.
  </p>

  <!-- 2. OBJETIVO -->
  <h2>2. Objetivo</h2>
  <p>
    <strong>Objetivo Geral:</strong> Projetar, implementar, validar e documentar um pipeline gráfico 3D
    completo em software capaz de sintetizar uma cena tridimensional composta por cinco sólidos distintos
    em diferentes pontos de vista e resoluções espaciais.
  </p>
  <p><strong>Objetivos Específicos (correspondentes aos 6 itens da especificação):</strong></p>
  <ol>
    <li><strong>Modelagem Geométrica (Item 1):</strong> Modelar cinco sólidos únicos (<em>esponja</em>, <em>queijo</em>, <em>prato</em>, <em>rolo</em> e <em>boia</em>) em malhas de triângulos com orientação anti-horária (CCW) e normais unitárias externas, visualizados isoladamente no referencial do objeto.</li>
    <li><strong>Composição da Cena no Mundo (Item 2):</strong> Aplicar matrizes homogêneas 4&times;4 de escala, rotação e translação para posicionar os cinco objetos no domínio <code>|x|, |y|, |z| &le; 10</code> sem interseções físicas entre suas caixas delimitadoras (AABBs).</li>
    <li><strong>Sistema de Coordenadas da Câmera (Item 3):</strong> Construir a base ortonormal <code>(u, v, w)</code> e a matriz de visão <code>R &middot; T</code>, marcando a origem do mundo no espaço da câmera e variando o ponto de observação <code>eye</code>.</li>
    <li><strong>Projeção em Perspectiva e Culling (Item 4):</strong> Projetar os vértices no plano <code>z = &minus;d</code> com recorte de frustum (<code>near</code>/<code>far</code>) e descarte de faces voltadas para trás (<em>backface culling</em>).</li>
    <li><strong>Iluminação de Phong (Item 5):</strong> Calcular a reflexão de Phong (componentes ambiente, difusa e especular) nos vértices usando normais suavizadas para sombreamento Gouraud.</li>
    <li><strong>Rasterização Manual (Item 6):</strong> Implementar o algoritmo de Bresenham (seção 5.2.1 do livro-texto), o preenchimento par-ímpar com <em>scanline</em>, a interpolação baricêntrica de cores com <em>Z-buffer</em> e o mapeamento de <em>viewport</em> nas resoluções 200&times;200, 400&times;400 e 800&times;800.</li>
  </ol>

  <!-- 3. DESENVOLVIMENTO -->
  <h2>3. Desenvolvimento</h2>

  <h3>3.1 Modelagem dos 5 Sólidos e Garantia de Normais Externas CCW</h3>
  <p>
    Cada gerador em <code>solidos/</code> retorna um dicionário padronizado com chaves
    <code>vertices</code> (<code>N&times;3</code>, <code>float64</code>), <code>faces</code> (<code>M&times;3</code>,
    <code>int32</code>), <code>arestas</code> (<code>K&times;2</code>, <code>int32</code>),
    <code>normais_faces</code> (<code>M&times;3</code>, <code>float64</code>), <code>cor</code> e <code>nome</code>.
    Todas as faces triangulares seguem a convenção anti-horária (CCW) quando observadas pelo lado externo do sólido,
    de modo que o produto vetorial entre duas arestas incidentes produza sempre normais unitárias apontando para fora:
  </p>
  <div class="formula-box">
    <p><strong>Normal da face:</strong> &nbsp; <b>N</b> = (<b>v</b><sub>1</sub> &minus; <b>v</b><sub>0</sub>) &times; (<b>v</b><sub>2</sub> &minus; <b>v</b><sub>0</sub>), &nbsp;&nbsp; <b>n</b>&#770; = <b>N</b> / &Vert;<b>N</b>&Vert;</p>
    <p><strong>Fatia de queijo (<code>criar_queijo</code>):</strong> &nbsp; x<sub>2</sub> = r &middot; cos(&theta;), &nbsp; z<sub>2</sub> = r &middot; sin(&theta;), &nbsp; y &isin; {{&minus;h/2, +h/2}}</p>
    <p><strong>Boia toroidal (<code>criar_boia</code>):</strong> &nbsp; x(u, v) = (R + r &middot; cos v) &middot; cos u, &nbsp; y(u, v) = r &middot; sin v, &nbsp; z(u, v) = &minus;(R + r &middot; cos v) &middot; sin u</p>
  </div>
  <p>
    O <strong>prato</strong> (<code>criar_prato</code>) é modelado como sólido de revolução fechado em torno do eixo Y com
    espessura de parede explícita (<code>0 &lt; espessura &lt; altura</code>), conectando o fundo externo, parede externa,
    borda superior, parede interna e fundo interno em cinco seções contínuas de anéis. O <strong>rolo de massa</strong>
    (<code>criar_rolo</code>) alinha seis anéis ao longo do eixo X (duas hastes e corpo central) fechados por tampas
    triangulares em leque. A Tabela 1 resume as métricas reais das malhas padrão geradas pelo código.
  </p>
  <table>
    <thead>
      <tr>
        <th>Sólido</th>
        <th>Geometria e Função</th>
        <th class="num">Vértices</th>
        <th class="num">Faces</th>
        <th class="num">Arestas</th>
        <th>Cor Padrão RGB</th>
      </tr>
    </thead>
    <tbody>
      {tabela_solidos_html}
    </tbody>
  </table>
  <pre><code>{code_normais}</code></pre>

  <h3>3.2 Transformações Geométricas 4&times;4 e Composição da Cena no Mundo</h3>
  <p>
    O módulo <code>transformacoes.py</code> define as matrizes homogêneas 4&times;4 de escala
    (<code>escala(sx, sy, sz)</code>), rotações canônicas (<code>rotacao_x</code>, <code>rotacao_y</code>,
    <code>rotacao_z</code>) e translação (<code>translacao(tx, ty, tz)</code>). Para cada sólido na cena,
    aplica-se a transformação composta na ordem <code>M = T &middot; R &middot; S</code> sobre os vértices em
    coordenadas homogêneas <code>(x, y, z, 1)<sup>T</sup></code> em <code>aplicar_transformacao</code>, e as
    normais das faces são recalculadas diretamente após a transformação geométrica em <code>transformar_solido</code>,
    preservando ortogonalidade mesmo sob escalas não uniformes.
  </p>
  <div class="formula-box">
    <p><b>p</b>'<sub>hom</sub> = <b>M</b> &middot; [x, y, z, 1]<sup>T</sup>, &nbsp;&nbsp; <b>M</b> = <b>T</b>(t<sub>x</sub>, t<sub>y</sub>, t<sub>z</sub>) &middot; <b>R</b><sub>&alpha;</sub>(&theta;) &middot; <b>S</b>(s<sub>x</sub>, s<sub>y</sub>, s<sub>z</sub>)</p>
  </div>
  <p>
    Em <code>cena.py</code>, a função <code>montar_cena()</code> posiciona os cinco objetos em regiões distintas
    e executa <code>validar_cena()</code>, que impõe por <code>assert</code> o limite espacial
    <code>max(|x|, |y|, |z|) &le; 10,0</code> e a ausência de sobreposição entre quaisquer pares de caixas
    delimitadoras (<code>verificar_intersecao_aabb</code>).
  </p>
  <pre><code>{code_cena}</code></pre>

  <h3>3.3 Sistema de Coordenadas da Câmera</h3>
  <p>
    Dado o ponto de observação <code>eye</code>, o alvo <code>at</code> e o vetor vertical de referência <code>up</code>,
    a função <code>camera(eye, at, up)</code> em <code>camera.py</code> constrói uma base vetorial ortonormal dextrógira
    <code>(u, v, w)</code> na qual o eixo de visão aponta para <code>&minus;w</code> (<code>&minus;Z<sub>cam</sub></code>):
  </p>
  <div class="formula-box">
    <p><b>w</b> = (<b>eye</b> &minus; <b>at</b>) / &Vert;<b>eye</b> &minus; <b>at</b>&Vert;, &nbsp;&nbsp; <b>u</b> = (<b>up</b> &times; <b>w</b>) / &Vert;<b>up</b> &times; <b>w</b>&Vert;, &nbsp;&nbsp; <b>v</b> = <b>w</b> &times; <b>u</b></p>
    <p><b>M</b><sub>vis</sub> = <b>R</b> &middot; <b>T</b>(&minus;<b>eye</b>), &nbsp;&nbsp; onde as linhas de <b>R</b> são <b>u</b><sup>T</sup>, <b>v</b><sup>T</sup> e <b>w</b><sup>T</sup></p>
  </div>
  <p>
    A função <code>transformar_para_camera</code> transforma os vértices via <code>M<sub>vis</sub></code> e rotaciona as
    normais pela submatriz ortogonal <code>R<sub>3&times;3</sub></code>. A origem do sistema do mundo <code>(0, 0, 0)</code>
    é mapeada para o espaço da câmera por <code>obter_origem_mundo_na_camera(M<sub>vis</sub>)</code> para validação visual.
  </p>
  <pre><code>{code_camera}</code></pre>

  <h3>3.4 Projeção em Perspectiva, <em>Backface Culling</em> e Clipping</h3>
  <p>
    No sistema da câmera, o observador situa-se na origem <code>(0, 0, 0)</code> e a cena visível ocupa o semiespaço
    <code>z &lt; 0</code>. Antes de projetar, <code>descartar_faces_ocultas</code> calcula o baricentro de cada
    triângulo e descarta faces traseiras cujo produto escalar com sua normal seja não negativo. Em seguida,
    <code>projetar</code> aplica o recorte de profundidade entre <code>near</code> e <code>far</code>
    (<code>&minus;far &le; z<sub>cam</sub> &le; &minus;near</code>) e realiza a divisão em perspectiva sobre o plano
    <code>z = &minus;d</code> (com <code>d = {projecao['d_proj']}</code>, <code>near = {projecao['near']}</code>,
    <code>far = {projecao['far']}</code>):
  </p>
  <div class="formula-box">
    <p><strong>Backface Culling:</strong> &nbsp; face visível se &nbsp; <b>n</b>&#770; &middot; ((<b>v</b><sub>0</sub> + <b>v</b><sub>1</sub> + <b>v</b><sub>2</sub>) / 3) &lt; 0</p>
    <p><strong>Projeção Perspectiva:</strong> &nbsp; x<sub>p</sub> = (d &middot; x) / (&minus;z), &nbsp;&nbsp; y<sub>p</sub> = (d &middot; y) / (&minus;z)</p>
  </div>
  <pre><code>{code_projecao}</code></pre>

  <h3>3.5 Iluminação pelo Modelo de Phong</h3>
  <p>
    Para obter transição suave de luminosidade sobre superfícies curvas (sombreamento Gouraud),
    <code>calcular_normais_vertices</code> em <code>iluminacao.py</code> calcula a normal de cada vértice como a média
    normalizada das normais unitárias das faces adjacentes. A função <code>phong</code> avalia, em cada vértice,
    as componentes ambiente, difusa (Lei de Lambert) e especular com fonte de luz branca em
    <code>luz_pos = {_formatar_vetor(iluminacao['luz_pos'], 1)}</code> e parâmetros
    <code>I<sub>a</sub> = {iluminacao['ia']}</code>, <code>I<sub>l</sub> = {iluminacao['il']}</code>,
    <code>K<sub>a</sub> = {iluminacao['ka']}</code>, <code>K<sub>d</sub> = {iluminacao['kd']}</code>,
    <code>K<sub>s</sub> = {iluminacao['ks']}</code> e expoente <code>n = {iluminacao['n_especular']:.0f}</code>:
  </p>
  <div class="formula-box">
    <p><b>L</b> = (<b>P</b><sub>luz</sub> &minus; <b>v</b>) / &Vert;<b>P</b><sub>luz</sub> &minus; <b>v</b>&Vert;, &nbsp;&nbsp; <b>V</b> = (<b>eye</b> &minus; <b>v</b>) / &Vert;<b>eye</b> &minus; <b>v</b>&Vert;, &nbsp;&nbsp; <b>R</b> = 2(<b>N</b> &middot; <b>L</b>)<b>N</b> &minus; <b>L</b></p>
    <p>I = K<sub>a</sub> I<sub>a</sub> <b>C</b><sub>base</sub> + K<sub>d</sub> I<sub>l</sub> max(0, <b>N</b> &middot; <b>L</b>) <b>C</b><sub>base</sub> + K<sub>s</sub> I<sub>l</sub> max(0, <b>R</b> &middot; <b>V</b>)<sup>n</sup> <b>C</b><sub>luz</sub></p>
  </div>
  <pre><code>{code_phong}</code></pre>

  <h3>3.6 Rasterização: Bresenham, Par-Ímpar com Scanline, Interpolação Baricêntrica e Z-buffer</h3>
  <p>
    A etapa final (<code>rasterizacao.py</code>) converte as coordenadas projetadas da janela simétrica
    <code>[&minus;1,0; 1,0] &times; [&minus;1,0; 1,0]</code> para coordenadas contínuas de tela via
    <code>mapear_viewport</code> (com inversão do eixo Y para o padrão de matrizes de imagem). Cada triângulo
    visível é preenchido e contornado manualmente por três mecanismos integrados:
  </p>
  <ul>
    <li><strong>Bresenham (seção 5.2.1):</strong> <code>bresenham(x0, y0, x1, y1)</code> traça segmentos inteiros nos oito octantes com variável de decisão inteira <code>err = dx &minus; dy</code>. A função <code>desenhar_arestas_bresenham</code> projeta os incrementos contínuos sobre cada aresta para interpolar profundidade e testar contra o <em>Z-buffer</em> (<code>tolerancia_z = 1e-3</code>).</li>
    <li><strong>Par-Ímpar com Scanline:</strong> <code>preencher_par_impar</code> varre as linhas horizontais <code>y</code> dentro da caixa delimitadora do triângulo, ignora arestas horizontais e aplica a regra de semi-intervalo <code>y<sub>min</sub> &le; y &lt; y<sub>max</sub></code> para evitar contagem duplicada de vértices.</li>
    <li><strong>Interpolação Baricêntrica e Z-buffer:</strong> Para cada pixel entre pares ordenados de interseções, <code>baricentricas</code> calcula os pesos <code>(&lambda;<sub>0</sub>, &lambda;<sub>1</sub>, &lambda;<sub>2</sub>)</code> usando o determinante <code>det<sub>T</sub></code>. Tanto a cor RGB quanto a profundidade positiva <code>z = &minus;z<sub>cam</sub></code> são interpoladas linearmente, atualizando o pixel somente quando <code>depth &lt; z_buffer[y, x]</code>.</li>
  </ul>
  <div class="formula-box">
    <p>det<sub>T</sub> = (y<sub>b</sub> &minus; y<sub>c</sub>)(x<sub>a</sub> &minus; x<sub>c</sub>) + (x<sub>c</sub> &minus; x<sub>b</sub>)(y<sub>a</sub> &minus; y<sub>c</sub>)</p>
    <p>&lambda;<sub>0</sub> = [(y<sub>b</sub> &minus; y<sub>c</sub>)(x &minus; x<sub>c</sub>) + (x<sub>c</sub> &minus; x<sub>b</sub>)(y &minus; y<sub>c</sub>)] / det<sub>T</sub>, &nbsp;&nbsp; &lambda;<sub>1</sub> = [(y<sub>c</sub> &minus; y<sub>a</sub>)(x &minus; x<sub>c</sub>) + (x<sub>a</sub> &minus; x<sub>c</sub>)(y &minus; y<sub>c</sub>)] / det<sub>T</sub>, &nbsp;&nbsp; &lambda;<sub>2</sub> = 1 &minus; &lambda;<sub>0</sub> &minus; &lambda;<sub>1</sub></p>
  </div>
  <pre><code>{code_raster}</code></pre>

  <!-- 4. SIMULAÇÕES COMPUTACIONAIS -->
  <h2>4. Simulações Computacionais</h2>
  <p>
    Todas as figuras a seguir foram geradas diretamente pela execução do código-fonte do projeto
    (<code>main.py --figuras</code>), respeitando a sequência dos itens exigidos na especificação da disciplina.
  </p>

  <figure>
    <img src="{imagens_b64['fig_1e']}" alt="Figura 1 — Sólidos isolados no sistema do objeto" />
    <figcaption><strong>Figura 1 (Item 1e):</strong> Os cinco sólidos modelados em seus respectivos sistemas de coordenadas de objeto com vetores normais externos.</figcaption>
  </figure>
  <p>
    Na Figura 1 observa-se que cada objeto foi construído em torno de sua própria origem local com eixos proporcionais
    (<code>1:1:1</code>) e setas normais apontando consistentemente para o exterior das faces, validando a orientação
    CCW das malhas antes de qualquer transformação de cena.
  </p>

  <figure>
    <img src="{imagens_b64['fig_2b']}" alt="Figura 2 — Cena composta no sistema do mundo" />
    <figcaption><strong>Figura 2 (Item 2b):</strong> Cena composta no sistema de coordenadas do mundo no domínio [-10, 10]<sup>3</sup>.</figcaption>
  </figure>
  <p>
    A Figura 2 exibe os cinco sólidos posicionados em quadrantes distintos do mundo após escala, rotação e
    translação. A Tabela 2 comprova que todos os vértices obedecem a <code>|coord| &le; 10</code> e que as caixas
    delimitadoras (AABBs) são disjuntas entre si.
  </p>
  <table>
    <thead>
      <tr>
        <th>Sólido na Cena</th>
        <th>BBox Mínima (x, y, z)</th>
        <th>BBox Máxima (x, y, z)</th>
        <th class="num">Máx |coord|</th>
        <th class="num">Faces</th>
      </tr>
    </thead>
    <tbody>
      {tabela_bboxes_html}
    </tbody>
  </table>

  <figure>
    <img src="{imagens_b64['fig_3c']}" alt="Figura 3 — Cena no sistema da câmera com origem do mundo" />
    <figcaption><strong>Figura 3 (Itens 3c e 3d):</strong> Cena transformada para o sistema de coordenadas da câmera (u, v, w) para eye = (12, 8, 14), destacando a câmera na origem (0, 0, 0) e a origem do mundo transformada.</figcaption>
  </figure>
  <p>
    Na Figura 3 verifica-se o alinhamento da cena ao longo de <code>&minus;w</code>, com a origem da câmera marcada em
    <code>(0, 0, 0)</code> e a origem do mundo transladada para <code>{_formatar_vetor(cameras[0]['origem_mundo_cam'], 2)}</code>.
    A Tabela 3 apresenta as bases ortonormais <code>(u, v, w)</code> e a origem do mundo calculadas para os três pontos
    de vista avaliados no projeto.
  </p>
  <table>
    <thead>
      <tr>
        <th>eye (Mundo)</th>
        <th>Base u</th>
        <th>Base v</th>
        <th>Base w</th>
        <th>Origem do Mundo na Câmera</th>
      </tr>
    </thead>
    <tbody>
      {tabela_cameras_html}
    </tbody>
  </table>

  <figure>
    <img src="{imagens_b64['fig_3e']}" alt="Figura 4 — Variação do ponto de vista eye" />
    <figcaption><strong>Figura 4 (Item 3e):</strong> Comparação da cena no sistema da câmera sob três posições distintas de observação (eye).</figcaption>
  </figure>
  <p>
    A Figura 4 demonstra a flexibilidade da função <code>camera(eye, at, up)</code>: ao deslocar o observador para a
    direita (<code>(12, 8, 14)</code>), para a esquerda (<code>(&minus;12, 8, 14)</code>) ou para um plano superior
    central (<code>(0, 14, 16)</code>), a geometria relativa dos objetos na câmera e a posição da origem do mundo
    reorientam-se exatamente conforme esperado.
  </p>

  <figure>
    <img src="{imagens_b64['fig_4a']}" alt="Figura 5 — Projeção perspectiva 3D e janela 2D" />
    <figcaption><strong>Figura 5 (Itens 4 e 4a):</strong> Espaço da câmera com raios projetantes e plano de projeção em z = &minus;1,80 (esquerda) e janela de projeção 2D com faces visíveis após culling (direita).</figcaption>
  </figure>
  <p>
    Na Figura 5 (esquerda), os raios projetantes convergem para o centro óptico em <code>(0, 0, 0)</code> interceptando
    a janela de projeção em <code>z = &minus;1,80</code>. Na janela 2D (direita), cada sólido mantém cor uniforme nas
    arestas e faces, exibindo somente os polígonos que passaram pelo <em>backface culling</em> e pelo recorte de
    <em>frustum</em>, conforme quantificado na Tabela 4 (<code>{total_visiveis}</code> de <code>{total_faces_cena}</code>
    faces totais, redução de {100.0 - perc_total:.1f}%).
  </p>
  <table>
    <thead>
      <tr>
        <th>Sólido</th>
        <th class="num">Faces Totais</th>
        <th class="num">Após Backface Culling</th>
        <th class="num">Visíveis no Frustum</th>
        <th class="num">Taxa Aproveitada</th>
      </tr>
    </thead>
    <tbody>
      {tabela_projecao_html}
    </tbody>
  </table>

  <figure>
    <img src="{imagens_b64['fig_5']}" alt="Figura 6 — Decomposição da iluminação de Phong" />
    <figcaption><strong>Figura 6 (Item 5):</strong> Decomposição do modelo de reflexão de Phong em Ambiente, Difusa, Especular e Soma Total (sombreamento Gouraud).</figcaption>
  </figure>
  <p>
    A Figura 6 evidencia a contribuição isolada de cada termo de Phong: a componente ambiente garante visibilidade
    mínima uniforme; a componente difusa revela o sombreamento direcional em função do ângulo entre <code>N</code> e
    <code>L</code>; a componente especular destaca os reflexos brilhantes brancos sobre as superfícies curvas (especialmente
    boia, prato e rolo); e a soma total combina os três termos com transição suave entre vértices.
  </p>

  <figure>
    <img src="{imagens_b64['fig_6_resolucoes']}" alt="Figura 7 — Comparação de rasterização em três resoluções" />
    <figcaption><strong>Figura 7 (Item 6):</strong> Comparação da rasterização completa via scanline, baricêntricas e Bresenham nas resoluções 200&times;200, 400&times;400 e 800&times;800.</figcaption>
  </figure>
  <p>
    A Figura 7 e a Tabela 5 ilustram o compromisso clássico entre fidelidade visual e custo computacional em
    rasterização por software. A passagem de <code>200&times;200</code> para <code>400&times;400</code> quadruplica o
    número de pixels (4&times;), eliminando o serrilhado mais grosseiro nas curvas da boia, do prato e do rolo. Em
    <code>800&times;800</code> (16&times; mais pixels que <code>200&times;200</code>), as bordas e gradientes de
    Gouraud tornam-se significativamente mais suaves, com aumento de tempo proporcional ao número de pixels varridos
    pelo laço de <em>scanline</em>.
  </p>
  <table>
    <thead>
      <tr>
        <th>Resolução</th>
        <th class="num">Total de Pixels</th>
        <th class="num">Tempo Real Medido</th>
        <th class="num">Fator Relativo (vs. 200&times;200)</th>
      </tr>
    </thead>
    <tbody>
      {tabela_tempos_html}
    </tbody>
  </table>

  <figure>
    <img src="{imagens_b64['fig_6_eyes']}" alt="Figura 8 — Rasterização final sob diferentes valores de eye" />
    <figcaption><strong>Figura 8 (Itens 3e e 6):</strong> Rasterização completa da cena (300&times;300) para três valores distintos do parâmetro eye.</figcaption>
  </figure>
  <p>
    Por fim, a Figura 8 confirma o funcionamento integrado de todo o pipeline <code>render(eye)</code>: a troca do
    ponto de vista atualiza simultaneamente a matriz de visão, o descarte de faces ocultas, a direção de visão
    <code>V</code> no brilho especular de Phong e a rasterização com <em>Z-buffer</em> sem artefatos de oclusão.
  </p>

  <!-- 5. CONCLUSÃO -->
  <h2>5. Conclusão</h2>
  <p>
    A implementação integral do pipeline gráfico 3D em software permitiu consolidar, na prática, os fundamentos
    matemáticos e algorítmicos da Computação Gráfica. Todos os requisitos da especificação foram cumpridos de forma
    modular e reproduzível, com geração automatizada das oito figuras exigidas e validação por testes unitários.
  </p>
  <p>
    Durante o desenvolvimento, três desafios técnicos exigiram atenção especial e motivaram melhorias estruturais no
    código:
  </p>
  <ul>
    <li><strong>Inversão de normais CCW nas malhas:</strong> triângulos com ordem horária produziam normais apontando para o interior dos objetos, causando descarte invertido no <em>backface culling</em> e iluminação escura. A verificação pelo teorema da divergência (volume assinado positivo) e pelo produto escalar externo garantiu consistência geométrica nos cinco sólidos.</li>
    <li><strong>Fechamento sólido do prato de revolução:</strong> a modelagem inicial aberta foi substituída por um perfil com espessura conectando paredes interna e externa, eliminando buracos visíveis sob ângulos elevados e assegurando malha fechada sem bordas livres.</li>
    <li><strong>Triângulos degenerados e oclusão de arestas com Z-buffer:</strong> triângulos quase colineares (<code>|det<sub>T</sub>| &lt; 10<sup>&minus;10</sup></code>) e segmentos de Bresenham sem teste de profundidade geravam vazamentos visuais e auto-oclusão nas arestas. A introdução da interpolação contínua de profundidade na rasterização de triângulos e nas arestas de Bresenham (com tolerância <code>10<sup>&minus;3</sup></code>) eliminou artefatos de sobreposição.</li>
  </ul>
  <p>
    Como principal aprendizado, destaca-se a clareza adquirida sobre como transformações afins, projeção em perspectiva,
    iluminação local e rasterização discreta se articulam em um único fluxo de dados &mdash; conhecimento diretamente
    transferível para programação com shaders em GPUs modernas.
  </p>

  <!-- 6. REFERÊNCIAS -->
  <h2>6. Referências</h2>
  <ol class="refs">
    <li>FOLEY, J. D.; VAN DAM, A.; FEINER, S. K.; HUGHES, J. F. <em>Computer Graphics: Principles and Practice</em>. 2nd/3rd ed. Reading: Addison-Wesley, 1996 / 2013. (Seção 5.2.1: Algoritmo de Bresenham e fundamentos de rasterização).</li>
    <li>SHIRLEY, P.; MARSCHNER, S. <em>Fundamentals of Computer Graphics</em>. 4th ed. Boca Raton: CRC Press, 2015.</li>
    <li>AZEVEDO, E.; CONCI, A. <em>Computação Gráfica: Teoria e Prática</em>. Rio de Janeiro: Elsevier / Campus, 2003.</li>
    <li>ROCHA NETO, A. <em>Notas de Aula da Disciplina de Computação Gráfica</em>. Instituto Federal de Educação, Ciência e Tecnologia do Ceará (IFCE) &ndash; Campus Fortaleza, 2026.2.</li>
    <li>PYTHON SOFTWARE FOUNDATION. <em>Python 3.12 Documentation</em>. Disponível em: <code>https://docs.python.org/3/</code>.</li>
    <li>NUMPY DEVELOPERS. <em>NumPy Reference Manual</em>. Disponível em: <code>https://numpy.org/doc/</code>.</li>
    <li>HUNTER, J. D. et al. <em>Matplotlib: Visualization with Python</em>. Disponível em: <code>https://matplotlib.org/stable/</code>.</li>
    <li>CLARK, A. et al. <em>Pillow (PIL Fork) Documentation</em>. Disponível em: <code>https://pillow.readthedocs.io/</code>.</li>
  </ol>

</body>
</html>
"""


def gerar_relatorio_pdf(
    diretorio_figuras: str = "outputs",
    caminho_pdf: str = "docs/relatorio_trabalho_cg.pdf",
) -> str:
    """
    Executa a coleta de métricas e figuras do pipeline, gera o HTML autocontido
    em arquivo temporário e converte para PDF via navegador headless.
    """
    navegador = encontrar_navegador_headless()
    metricas, caminhos_figuras = coletar_metricas_pipeline(
        diretorio_figuras=diretorio_figuras
    )
    html_conteudo = montar_html_relatorio(metricas, caminhos_figuras)

    pdf_abs = os.path.abspath(caminho_pdf)
    dir_pai = os.path.dirname(pdf_abs)
    if dir_pai:
        os.makedirs(dir_pai, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        html_path = os.path.join(tmp_dir, "relatorio_cg.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_conteudo)

        html_uri = Path(html_path).resolve().as_uri()
        subprocess.run(
            [
                navegador,
                "--headless",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_abs}",
                html_uri,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    if not os.path.isfile(pdf_abs) or os.path.getsize(pdf_abs) == 0:
        raise RuntimeError(f"Falha ao gerar o PDF em: {pdf_abs}")

    with open(pdf_abs, "rb") as f:
        cabecalho = f.read(5)
    if cabecalho != b"%PDF-":
        raise ValueError(f"Arquivo gerado não possui assinatura %PDF-: {pdf_abs}")

    return pdf_abs


if __name__ == "__main__":
    caminho_gerado = gerar_relatorio_pdf()
    print(f"Relatório PDF gerado com sucesso: {caminho_gerado}")
