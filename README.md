# AXINUS core

Colab loader (one cell, fresh runtime):

```python
!rm -rf /content/axc && git clone -q --depth 1 https://github.com/tanveerkarimullashaikh15-bot/axinus-core /content/axc
exec(open('/content/axc/boot.py').read())
```

- `core/` original cells 2-5 (keys, tools, brain, voice page) - Twilio removed
- `addons/` loaded in filename order: ax0 registry (roles, live models, health, token meter), ax1 core/orchestrator, ax2 data, ax3/3b PDF studio v2 + image, ax4 UI/map/sync/phone/recipes/self-test, ax5 server
- Secrets stay in Colab Secrets (GEMINI/GROQ/COHERE/SAMBANOVA/TAVILY/YOUTUBE/GMAIL...). Nothing secret lives in this repo.
- Update = rerun the cell (it re-clones).
