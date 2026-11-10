# Contribuindo com o GhostEnv 👻

## Como rodar local
```bash
git clone https://github.com/LuizDevkit/ghostenv
cd ghostenv
pip install -e .
ghostenv scan --help
```

## Good First Issues
- [ ] Suporte a Go (`os.Getenv`)
- [ ] Suporte a Rust (`std::env::var`)
- [ ] Suporte a PHP (`$_ENV`, `getenv`)
- [ ] Suporte a Java (`System.getenv`)
- [ ] Suporte a Ruby (`ENV[]`)
- [ ] Detectar `docker-compose.yml` e `Dockerfile` com ENV
- [ ] `ghostenv scan` com saída para GitHub Actions
- [ ] Testes para `scanner.py`

## Regras
1. Um PR = uma linguagem / uma feature
2. Adicione um exemplo em `examples/<linguagem>/`
3. Rode `ghostenv scan` no próprio repo antes de abrir PR
4. Sem segredos reais nos testes — use `change-me`
