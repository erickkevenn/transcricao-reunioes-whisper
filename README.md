# Transcrição de reuniões (Whisper)

Transcreve gravações de reuniões em português no próprio computador, sem internet depois da primeira execução, usando o [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

## Como funciona

```
Whisper/
├── Gravações/        ← coloque aqui os áudios a transcrever
├── Reuniões/         ← resultado: uma pasta por reunião
├── sistema/
│   ├── instalar.bat      instala as dependências (rodar uma vez)
│   └── transcrever.py    o script de transcrição
├── transcrever.bat   ← dois cliques para transcrever
└── LEIA-ME.txt
```

1. Salve o áudio da reunião em `Gravações/`.
2. Dê dois cliques em `transcrever.bat`.
3. O resultado aparece em `Reuniões/<nome da gravação>/`:

| Arquivo | Conteúdo |
|---|---|
| `<nome>.mp3` | o áudio original (movido de `Gravações`) |
| `<nome> - transcrição.txt` | só o texto |
| `<nome> - com timestamps.txt` | texto com `[início - fim]` de cada trecho |

Ele transcreve todas as gravações pendentes, uma por vez, com barra de progresso. O computador não entra em suspensão durante a transcrição, e no fim toca um aviso e abre a pasta do resultado. Se uma gravação der erro, o áudio continua em `Gravações/` para tentar de novo.

Também dá para arrastar um ou mais áudios de qualquer lugar para cima do `transcrever.bat`.

Formatos aceitos: mp3, wav, m4a, ogg, opus, flac, aac, wma, mp4, mkv, mov, webm.

## Instalação em um computador novo

Requisitos: Windows, [Python 3](https://www.python.org/downloads/) (marque "Add Python to PATH" na instalação) e Git.

```powershell
git clone https://github.com/erickkevenn/transcricao-reunioes-whisper.git $HOME\Whisper
```

Depois, dê dois cliques em `sistema\instalar.bat` (só na primeira vez). Pronto: já pode usar o `transcrever.bat`.

Na primeira transcrição o modelo é baixado automaticamente (~1,6 GB no modelo padrão).

## Opções

Rodando de dentro da pasta `Whisper`:

```powershell
python sistema\transcrever.py --modelo small
python sistema\transcrever.py --idioma en
python sistema\transcrever.py "C:\caminho\reuniao.mp3"
```

| Modelo | Observação |
|---|---|
| `turbo` | padrão, mais preciso |
| `small`, `base`, `tiny` | mais rápidos, menos precisos |
| `medium`, `large-v3` | alternativas maiores |

## Privacidade

O repositório guarda só o sistema e a estrutura de pastas. O `.gitignore` impede que áudios e transcrições de `Gravações/` e `Reuniões/` sejam enviados ao GitHub.
