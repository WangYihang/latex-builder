FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-xetex \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-lang-chinese \
    texlive-bibtex-extra \
    biber \
    latexdiff \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app
COPY . .
RUN uv sync

ENTRYPOINT ["uv", "run", "latex-builder"]
