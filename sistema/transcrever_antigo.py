"""
Transcreve áudio/vídeo com faster-whisper e mostra uma barra de progresso.

Uso:
  python transcrever.py arquivo.mp3 [outro.m4a ...] [--modelo small] [--idioma pt]
  (sem arquivos: abre uma janela para escolher)

Cria uma pasta com o nome do arquivo (ao lado dele) contendo:
  <nome> - transcrição.txt      -> só o texto
  <nome> - com timestamps.txt   -> texto com [início - fim] de cada trecho
"""
import argparse
import os
import sys
import time

from faster_whisper import WhisperModel
from tqdm import tqdm


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


def escolher_arquivos():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        arquivos = filedialog.askopenfilenames(
            title="Escolha o(s) áudio(s) para transcrever",
            filetypes=[("Áudio e vídeo", "*.mp3 *.wav *.m4a *.ogg *.opus *.flac *.aac *.wma *.mp4 *.mkv *.mov *.webm"),
                       ("Todos os arquivos", "*.*")],
        )
        root.destroy()
        return list(arquivos)
    except Exception:
        return []


def transcrever(model, caminho, idioma):
    caminho = os.path.abspath(caminho)
    nome = os.path.basename(caminho)
    nome_sem_ext = os.path.splitext(nome)[0]
    pasta = os.path.join(os.path.dirname(caminho), nome_sem_ext)
    inicio = time.time()

    segments, info = model.transcribe(
        caminho, language=idioma, beam_size=5, vad_filter=True
    )
    total = round(info.duration, 1)
    print(f"\nArquivo: {nome}  (duração: {formatar_duracao(total)})")

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
            linhas_txt.append(texto)
            linhas_ts.append(f"[{formatar_hms(seg.start)} - {formatar_hms(seg.end)}] {texto}")
            barra.update(min(seg.end, total) - barra.n)
        barra.update(total - barra.n)  # completa 100% no fim

    os.makedirs(pasta, exist_ok=True)
    arq_texto = os.path.join(pasta, f"{nome_sem_ext} - transcrição.txt")
    arq_ts = os.path.join(pasta, f"{nome_sem_ext} - com timestamps.txt")
    with open(arq_texto, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_txt) + "\n")
    with open(arq_ts, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_ts) + "\n")

    gasto = time.time() - inicio
    print(f"Pronto em {formatar_duracao(gasto)}. Arquivos salvos em:")
    print(f"  {pasta}")
    print(f"    - {os.path.basename(arq_texto)}")
    print(f"    - {os.path.basename(arq_ts)}")


def main():
    p = argparse.ArgumentParser(description="Transcrição com faster-whisper")
    p.add_argument("arquivos", nargs="*", help="arquivos de áudio/vídeo")
    p.add_argument("--modelo", default="small",
                   help="tiny, base, small, medium, large-v3, turbo (padrão: small)")
    p.add_argument("--idioma", default="pt", help="código do idioma (padrão: pt)")
    args = p.parse_args()

    arquivos = args.arquivos or escolher_arquivos()
    if not arquivos:
        print("Nenhum arquivo escolhido.")
        return 1

    print(f"Carregando modelo '{args.modelo}'... "
          "(na primeira vez ele é baixado, pode demorar)")
    model = WhisperModel(args.modelo, device="cpu", compute_type="int8",
                         cpu_threads=os.cpu_count() or 4)

    for caminho in arquivos:
        if not os.path.isfile(caminho):
            print(f"\nArquivo não encontrado: {caminho}")
            continue
        try:
            transcrever(model, caminho, args.idioma)
        except Exception as e:
            print(f"\nErro ao transcrever {caminho}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
