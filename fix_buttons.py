import re

# Read the file
with open(r'c:\Conecta-SENAI\Conecta-SENAI\templates\selecao-sistema.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Define replacements with unique context before each button
replacements = [
    # Notícias
    (r'(aria-label="Entrar no Portal de Notícias">.*?)\s*<a href="#" class="btn-module-secondary"',
     r'\1\n                                                    <a href="/ajuda.html#noticias" class="btn-module-secondary"',
     re.DOTALL),
    # Suporte TI
    (r'(aria-label="Entrar no módulo Suporte de TI">.*?)\s*<a href="#" class="btn-module-secondary"',
     r'\1\n                                                    <a href="/ajuda.html#suporte-ti" class="btn-module-secondary"',
     re.DOTALL),
    # Rateio
    (r'(aria-label="Entrar no módulo Controle de Rateio">.*?)\s*<a href="#" class="btn-module-secondary"',
     r'\1\n                                                    <a href="/ajuda.html#rateio" class="btn-module-secondary"',
     re.DOTALL),
    # Usuários
    (r'(aria-label="Entrar no módulo Gerenciamento de Usuários">.*?)\s*<a href="#" class="btn-module-secondary"',
     r'\1\n                                                    <a href="/ajuda.html#usuarios" class="btn-module-secondary"',
     re.DOTALL),
]

# Apply replacements
for pattern, replacement, flags in replacements:
    content = re.sub(pattern, replacement, content, flags=flags)

# Write back
with open(r'c:\Conecta-SENAI\Conecta-SENAI\templates\selecao-sistema.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Todos os 4 botões de documentação restantes foram corrigidos!")
