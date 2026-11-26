"""
Transcrição de reuniões com faster-whisper.

Estrutura (pasta Whisper):
  Gravações\   -> coloque aqui os áudios das reuniões (pendentes)
  Reuniões\    -> uma pasta por reunião: áudio + transcrição + transcrição com timestamps
  sistema\     -> este script e o instalador

Uso:
  transcrever.bat                 -> transcreve tudo que estiver pendente em Gravações
  arrastar áudio(s) no .bat       -> transcreve só esses arquivos
  python transcrever.py [arquivos] [--modelo turbo] [--idioma pt]
"""
import argparse
import ctypes
import datetime as dt
import os
import re
import shutil
import sys
import time

from faster_whisper import WhisperModel
from tqdm import tqdm

PASTA_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_GRAVACOES = os.path.join(PASTA_RAIZ, "Gravações")
PASTA_REUNIOES = os.path.join(PASTA_RAIZ, "Reuniões")

EXTENSOES = {".mp3", ".wav", ".m4a", ".ogg", ".opus", ".flac", ".aac", ".wma",
             ".mp4", ".mkv", ".mov", ".webm"}


# ---------- utilidades ----------

def formatar_hms(seg):
    seg = int(seg)
    h, r = divmod(seg, 3600)
    m, s = divmod(r, 60)
    return f"{h:02}:{m:02}:{s:02}"


def formatar_duracao(seg):
    seg = int(seg)
    h, r = divmod(seg, 3600)
    m, s = divmod(r, 60)
    return f"{h}h{m:02}m{s:02}s" if h else f"{m}m{s:02}s"


def data_da_gravacao(caminho):
    """Tenta ler a data do nome (ex.: 2026-10-09 14-24-17); senão usa a data do arquivo."""
    nome = os.path.basename(caminho)
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})[ _T]?(\d{2})-(\d{2})(?:-(\d{2}))?", nome)
    if m:
        try:
            return dt.datetime(*(int(x) for x in m.groups(default="0")))
        except ValueError:
            pass
    return dt.datetime.fromtimestamp(os.path.getmtime(caminho))


def pasta_livre(base):
    """Evita sobrescrever: 'Nome', 'Nome (2)', 'Nome (3)'..."""
    destino, n = base, 2
    while os.path.exists(destino):
        destino = f"{base} ({n})"
        n += 1
    return destino


def manter_acordado(ligado):
    """Impede o Windows de suspender enquanto transcreve."""
    if os.name != "nt":
        return
    ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
    flags = ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if ligado else 0)
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(flags)
    except Exception:
        pass


def avisar_fim():
    if os.name == "nt":
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass


def pendentes():
    os.makedirs(PASTA_GRAVACOES, exist_ok=True)
    arquivos = [os.path.join(PASTA_GRAVACOES, f) for f in os.listdir(PASTA_GRAVACOES)]
    arquivos = [a for a in arquivos
                if os.path.isfile(a) and os.path.splitext(a)[1].lower() in EXTENSOES]
    return sorted(arquivos, key=os.path.getmtime)


# ---------- transcrição ----------

def transcrever(model, modelo_nome, caminho, idioma):
    caminho = os.path.abspath(caminho)
    nome = os.path.basename(caminho)
    nome_sem_ext = os.path.splitext(nome)[0]
    data = data_da_gravacao(caminho)
    inicio = time.time()

    segments, info = model.transcribe(
        caminho,
        language=idioma,
        beam_size=5,
        vad_filter=True,                   # pula silêncios
        condition_on_previous_text=False,  # evita repetições em áudios longos
    )
    total = round(info.duration, 1)
    print(f"Arquivo: {nome}  (duração: {formatar_duracao(total)})")

    linhas_txt, linhas_ts = [], []
    with tqdm(
        total=total,
        unit="s",
        desc="Transcrevendo",
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n:.0f}/{total:.0f}s  "
                   "[decorrido {elapsed} | falta ~{remaining}]",
        dynamic_ncols=True,
    ) as barra:
        for seg in segments:
            texto = seg.text.strip()
            if not texto:
                continue
            linhas_txt.append(texto)
            linhas_ts.append(f"[{formatar_hms(seg.start)} - {formatar_hms(seg.end)}] {texto}")
            barra.update(min(seg.end, total) - barra.n)
        barra.update(total - barra.n)

    gasto = time.time() - inicio
    cabecalho = (
        f"Reunião: {nome_sem_ext}\n"
        f"Data: {data:%d/%m/%Y} às {data:%H:%M}\n"
        f"Duração: {formatar_duracao(total)}\n"
        f"Modelo: {modelo_nome} | Transcrito em {dt.datetime.now():%d/%m/%Y %H:%M} "
        f"(levou {formatar_duracao(gasto)})\n"
        + "-" * 60 + "\n\n"
    )

    os.makedirs(PASTA_REUNIOES, exist_ok=True)
    pasta = pasta_livre(os.path.join(PASTA_REUNIOES, nome_sem_ext))
    os.makedirs(pasta)
    with open(os.path.join(pasta, f"{nome_sem_ext} - transcrição.txt"), "w", encoding="utf-8") as f:
        f.write(cabecalho + "\n".join(linhas_txt) + "\n")
    with open(os.path.join(pasta, f"{nome_sem_ext} - com timestamps.txt"), "w", encoding="utf-8") as f:
        f.write(cabecalho + "\n".join(linhas_ts) + "\n")

    # só move o áudio depois que as transcrições foram salvas
    shutil.move(caminho, os.path.join(pasta, nome))

    print(f"Pronto em {formatar_duracao(gasto)} -> {pasta}")
    return pasta


def main():
    p = argparse.ArgumentParser(description="Transcrição de reuniões")
    p.add_argument("arquivos", nargs="*", help="áudios (vazio = tudo em Gravações)")
    p.add_argument("--modelo", default="turbo",
                   help="tiny, base, small, medium, large-v3, turbo (padrão: turbo)")
    p.add_argument("--idioma", default="pt", help="código do idioma (padrão: pt)")
    args = p.parse_args()

    os.makedirs(PASTA_GRAVACOES, exist_ok=True)
    os.makedirs(PASTA_REUNIOES, exist_ok=True)

    arquivos = args.arquivos or pendentes()
    if not arquivos:
        print("Nenhuma gravação pendente em:")
        print(f"  {PASTA_GRAVACOES}")
        return 0

    print(f"{len(arquivos)} gravação(ões) para transcrever.")
    print(f"Carregando modelo '{args.modelo}'... (na primeira vez ele é baixado, pode demorar)")
    model = WhisperModel(args.modelo, device="cpu", compute_type="int8",
                         cpu_threads=os.cpu_count() or 4)

    feitas, erros = [], []
    manter_acordado(True)
    try:
        for i, caminho in enumerate(arquivos, 1):
            print(f"\n=== Reunião {i} de {len(arquivos)} ===")
            if not os.path.isfile(caminho):
                print(f"Arquivo não encontrado: {caminho}")
                erros.append(caminho)
                continue
            try:
                feitas.append(transcrever(model, args.modelo, caminho, args.idioma))
            except Exception as e:
                print(f"ERRO ao transcrever {os.path.basename(caminho)}: {e}")
                print("O áudio continua onde estava.")
                erros.append(caminho)
    finally:
        manter_acordado(False)

    print("\n" + "=" * 60)
    print(f"Concluído: {len(feitas)} transcrita(s), {len(erros)} com erro.")
    print(f"Resultados em: {PASTA_REUNIOES}")
    avisar_fim()
    if feitas and os.name == "nt":
        os.startfile(feitas[0] if len(feitas) == 1 else PASTA_REUNIOES)
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
