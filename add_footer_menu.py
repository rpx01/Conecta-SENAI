# -*- coding: utf-8 -*-
# Script para adicionar footer consistente e menu "Central de Ajuda" em todas as páginas internas

import os
import re

# Footer template (extraído de selecao-sistema.html)
footer_template = '''
    <!-- Enhanced Footer -->
    <footer class="enhanced-footer mt-5">
        <div class="container">
            <div class="footer-grid">
                <div class="footer-section">
                    <h5>Suporte</h5>
                    <ul>
                        <li><a href="/suporte_ti/abertura.html">Abrir Chamado</a></li>
                        <li><a href="/ajuda.html#faq">Perguntas Frequentes</a></li>
                        <li><a href="/ajuda.html#changelog">Novidades (Changelog)</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h5>Status do Sistema</h5>
                    <div class="service-status">
                        <span class="status-indicator" aria-label="Status: Operacional"></span>
                        <span>Todos os sistemas operacionais</span>
                    </div>
                </div>
                <div class="footer-section">
                    <h5>Sobre</h5>
                    <p class="small text-muted">
                        Portal integrado de sistemas do SENAI para gestão de laboratórios,
                        treinamentos e suporte técnico.
                    </p>
                </div>
            </div>
            <div class="footer-bottom">
                <p>© 2025 Sistema FIEMG | Conecta SENAI · O futuro se faz juntos.</p>
                <p><small>Versão 2.0.0 | Desenvolvido com ❤️ pela Equipe de TI</small></p>
            </div>
        </div>
    </footer>
'''

# Menu item template
help_menu_item = '''                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item" href="/ajuda.html">
                            <i class="bi bi-question-circle"></i> Central de Ajuda
                        </a></li>'''

# Arquivos para modificar
files_to_modify = [
    'templates/laboratorios/calendario.html',
    'templates/treinamentos/index.html',
    'templates/ocupacao/dashboard.html',
    'templates/noticias/index.html',
    'templates/suporte_ti/abertura.html',
    'templates/rateio/dashboard.html'
]

stats = {
    'footer_added': 0,
    'menu_added': 0,
    'errors': []
}

for file_path in files_to_modify:
    try:
        if not os.path.exists(file_path):
            stats['errors'].append(f'{file_path} - Arquivo não encontrado')
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # 1. Adicionar footer se não existir
        if 'enhanced-footer' not in content:
            # Procurar por </body> e inserir footer antes
            if '</body>' in content:
                content = content.replace('</body>', footer_template + '\n</body>')
                stats['footer_added'] += 1
                modified = True
            else:
                stats['errors'].append(f'{file_path} - Tag </body> não encontrada')
        
        # 2. Adicionar item "Central de Ajuda" no menu se não existir
        if 'Central de Ajuda' not in content and 'dropdown-menu' in content:
            # Procurar pelo padrão do menu do usuário e adicionar antes do "Sair"
            # Pattern: procurar por "Retornar à seleção" seguido por "Sair"
            pattern = r'(</a>\s*</li>\s*)(<li><hr class="dropdown-divider"></li>\s*<li><a class="dropdown-item" href="/logout">)'
            
            if re.search(pattern, content):
                content = re.sub(
                    pattern,
                    r'\1' + help_menu_item + r'\n                        \2',
                    content
                )
                stats['menu_added'] += 1
                modified = True
            else:
                # Tentar outro padrão
                pattern2 = r'(<li><a class="dropdown-item" href="/selecao-sistema.html">.*?</a></li>)\s*(<li><hr class="dropdown-divider"></li>\s*<li><a class="dropdown-item" href="/logout">)'
                if re.search(pattern2, content, re.DOTALL):
                    content = re.sub(
                        pattern2,
                        r'\1' + help_menu_item + r'\n                        \2',
                        content,
                        flags=re.DOTALL
                    )
                    stats['menu_added'] += 1
                    modified = True
        
        # Salvar apenas se modificou
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'✅ {os.path.basename(file_path)} - Atualizado com sucesso')
        else:
            print(f'ℹ️  {os.path.basename(file_path)} - Já possui footer e menu')
            
    except Exception as e:
        stats['errors'].append(f'{file_path} - Erro: {str(e)}')
        print(f'❌ {os.path.basename(file_path)} - Erro: {str(e)}')

# Resumo
print(f'\n--- RESUMO ---')
print(f'Footers adicionados: {stats["footer_added"]}/6')
print(f'Menus "Central de Ajuda" adicionados: {stats["menu_added"]}/6')
if stats['errors']:
    print(f'Erros: {len(stats["errors"])}')
    for error in stats['errors']:
        print(f'  - {error}')
else:
    print('Erros: 0')

if stats['footer_added'] == 6 and stats['menu_added'] == 6:
    print('\n🎉 SUCESSO TOTAL! Todas as páginas foram atualizadas!')
