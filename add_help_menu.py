# -*- coding: utf-8 -*-
# Script corrigido para adicionar  menu "Central de Ajuda"

import os
import re

# Arquivos para modificar
files_to_modify = [
    'templates/laboratorios/calendario.html',
    'templates/treinamentos/index.html',
    'templates/ocupacao/dashboard.html',
    'templates/noticias/index.html',
    'templates/suporte_ti/abertura.html',
    'templates/rateio/dashboard.html'
]

stats = {'menu_added': 0, 'errors': []}

for file_path in files_to_modify:
    try:
        if not os.path.exists(file_path):
            stats['errors'].append(f'{file_path} - Arquivo não encontrado')
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Verificar se já possui "Central de Ajuda"
        if 'Central de Ajuda' in content or 'ajuda.html' in content:
            print(f'ℹ️  {os.path.basename(file_path)} - Já possui Central de Ajuda')
            continue
        
        # Padrão 1: Menu só com "Meu Perfil" e "Sair" (sem "Retornar")
        # Inserir entre "Meu Perfil" e o divisor do "Sair"
        pattern1 = r'(<li><a class="dropdown-item" href="[^"]*perfil.html">.*?</a></li>\s*)(<li>\s*<hr class="dropdown-divider">\s*</li>\s*<li><a class="dropdown-item" href="[^"]*logout)'
        
        if re.search(pattern1, content, re.DOTALL):
            new_menu = r'''\1<li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="/ajuda.html"><i class="bi bi-question-circle me-2"></i>Central de Ajuda</a></li>
                            <li><a class="dropdown-item" href="/selecao-sistema.html"><i class="bi bi-grid-3x3 me-2"></i>Trocar de Sistema</a></li>
                            \2'''
            
            content = re.sub(pattern1, new_menu, content, flags=re.DOTALL)
            stats['menu_added'] += 1
            
            # Salvar
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'✅ {os.path.basename(file_path)} - Menu atualizado!')
        else:
            stats['errors'].append(f'{file_path} - Padrão de menu não encontrado')
            print(f'❌ {os.path.basename(file_path)} - Padrão não encontrado')
            
    except Exception as e:
        stats['errors'].append(f'{file_path} - Erro: {str(e)}')
        print(f'❌ {os.path.basename(file_path)} - Erro: {str(e)}')

# Resumo
print(f'\n--- RESUMO ---')
print(f'Menus "Central de Ajuda" adicionados: {stats["menu_added"]}/6')
if stats['errors']:
    print(f'Erros/Pulos: {len(stats["errors"])}')
else:
    print('Erros: 0')

if stats['menu_added'] == 6:
    print('\n🎉 Todos os menus foram atualizados!')
