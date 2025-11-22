# -*- coding: utf-8 -*-
# Script para expandir ajuda.html com seções específicas de cada módulo

# Ler o arquivo original
with open('templates/ajuda.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Encontrar a posição para inserir (antes do Changelog)
insert_marker = '        <!-- Changelog Section -->'
insert_position = content.find(insert_marker)

if insert_position == -1:
    print("❌ Erro: Marcador não encontrado!")
    exit(1)

# Conteúdo das seções de módulos
module_sections = '''
        <!-- Module-Specific Documentation Sections -->
        
        <!-- Laborat\u00f3rios Section -->
        <section id="laboratorios" class="help-section">
            <h2 class="mb-4"><i class="bi bi-calendar-check me-2"></i>Agenda de Laborat\u00f3rios</h2>
            <div class="card">
                <div class="card-body">
                    <h5>Como usar o M\u00f3dulo</h5>
                    <p>O m\u00f3dulo de Agenda de Laborat\u00f3rios permite gerenciar reservas de espa\u00e7os, visualizar disponibilidade em tempo real e controlar o uso dos laborat\u00f3rios do SENAI.</p>
                    
                    <h6 class="mt-4">Principais Funcionalidades:</h6>
                    <ul>
                        <li><strong>Visualiza\u00e7\u00e3o em Calend\u00e1rio:</strong> Veja todos osagendamentos em uma interface intuitiva</li>
                        <li><strong>Novo Agendamento:</strong> Reserve laborat\u00f3rios com poucos cliques</li>
                        <li><strong>Gerenciamento de Turmas:</strong> Associe turmas aos agendamentos</li>
                        <li><strong>Controle de Salas:</strong> Visualize status e disponibilidade</li>
                    </ul>

                    <h6 class="mt-4">Primeiros Passos:</h6>
                    <ol>
                        <li>Acesse o m\u00f3dulo pela tela de sele\u00e7\u00e3o de sistemas</li>
                        <li>Visualize o calend\u00e1rio com agendamentos existentes</li>
                        <li>Clique em "Novo Agendamento" para criar uma reserva</li>
                        <li>Preencha os campos obrigat\u00f3rios e confirme</li>
                    </ol>
                </div>
            </div>
        </section>

        <!-- Treinamentos Section -->
        <section id="treinamentos" class="help-section">
            <h2 class="mb-4"><i class="bi bi-easel2 me-2"></i>Agenda de Treinamentos</h2>
            <div class="card">
                <div class="card-body">
                    <h5>Como usar o M\u00f3dulo</h5>
                    <p>O m\u00f3dulo de Agenda de Treinamentos facilita a programa\u00e7\u00e3o e gest\u00e3o de cursos t\u00e9cnicos, permitindo controle completo sobre inscri\u00e7\u00f5es, turmas e hist\u00f3rico.</p>
                    
                    <h6 class="mt-4">Principais Funcionalidades:</h6>
                    <ul>
                        <li><strong>Cat\u00e1logo de Cursos:</strong> Visualize e gerencie todos os cursos dispon\u00edveis</li>
                        <li><strong>Gest\u00e3o de Turmas:</strong> Crie e administre turmas de treinamento</li>
                        <li><strong>Controle de Inscri\u00e7\u00f5es:</strong> Gerencie inscri\u00e7\u00f5es de participantes</li>
                        <li><strong>Hist\u00f3rico de Treinamentos:</strong> Acesse registros de cursos anteriores</li>
                    </ul>

                    <h6 class="mt-4">Dica Importante:</h6>
                    <p class="alert alert-info">
                        <i class="bi bi-lightbulb me-2"></i>
                        Use os filtros de data e \u00e1rea para localizar rapidamente os treinamentos desejados.
                    </p>
                </div>
            </div>
        </section>

        <!-- Ocupa\u00e7\u00e3o de Salas Section -->
        <section id="ocupacao" class="help-section">
            <h2 class="mb-4"><i class="bi bi-building me-2"></i>Controle de Ocupa\u00e7\u00e3o de Salas</h2>
            <div class="card">
                <div class="card-body">
                    <h5>Como usar o M\u00f3dulo</h5>
                    <p>O m\u00f3dulo de Controle de Ocupa\u00e7\u00e3o monitora e registra o uso das salas de aula, gerando estat\u00edsticas de utiliza\u00e7\u00e3o para otimizar a gest\u00e3o de espa\u00e7os.</p>
                    
                    <h6 class="mt-4">Principais Funcionalidades:</h6>
                    <ul>
                        <li><strong>Dashboard de Ocupa\u00e7\u00e3o:</strong> Visualize estat\u00edsticas em tempo real</li>
                        <li><strong>Registro de Ocupa\u00e7\u00f5es:</strong> Controle entrada e sa\u00edda de turmas</li>
                        <li><strong>Relat\u00f3rios de Utiliza\u00e7\u00e3o:</strong> Gere relat\u00f3rios em PDF, Excel ou CSV</li>
                        <li><strong>Base de Dados:</strong> Gerencie salas, turmas e corpo docente</li>
                    </ul>

                    <h6 class="mt-4">Como Exportar Relat\u00f3rios:</h6>
                    <ol>
                        <li>Acesse o Dashboard de Ocupa\u00e7\u00e3o</li>
                        <li>Utilize os filtros de data para selecionar o per\u00edodo</li>
                        <li>Clique nos bot\u00f5es de exporta\u00e7\u00e3o (PDF/Excel/CSV) nos cards</li>
                    </ol>
                </div>
            </div>
        </section>

        <!-- Portal de Not\u00edcias Section -->
        <section id="noticias" class="help-section">
            <h2 class="mb-4"><i class="bi bi-newspaper me-2"></i>Portal de Not\u00edcias</h2>
            <div class="card">
                <div class="card-body">
                    <h5>Como usar o M\u00f3dulo</h5>
                    <p>O Portal de Not\u00edcias centraliza comunicados institucionais, destaques e aniversariantes, mantendo todos informados sobre eventos e novidades do SENAI.</p>
                    
                    <h6 class="mt-4">Principais Funcionalidades:</h6>
                    <ul>
                        <li><strong>Visualiza\u00e7\u00e3o de Not\u00edcias:</strong> Acesse comunicados importantes</li>
                        <li><strong>Filtros por Categoria:</strong> Encontre not\u00edcias por tipo ou data</li>
                        <li><strong>Aniversariantes do M\u00eas:</strong> Veja quem est\u00e1 de anivers\u00e1rio</li>
                        <li><strong>Gerenciamento (Admin):</strong> Publique e edite not\u00edcias</li>
                    </ul>

                    <h6 class="mt-4">Para Administradores:</h6>
                    <p>Para publicar uma not\u00edcia, acesse "Gerenciar" no menu lateral, clique em "Nova Not\u00edcia" e preencha os campos de t\u00edtulo, conte\u00fado e categoria.</p>
                </div>
            </div>
        </section>

        <!-- Suporte de TI Section -->
        <section id="suporte-ti" class="help-section">
            <h2 class="mb-4"><i class="bi bi-headset me-2"></i>Suporte de TI</h2>
            <div class="card">
                <div class="card-body">
                    <h5>Como usar o M\u00f3dulo</h5>
                    <p>O m\u00f3dulo de Suporte de TI permite abrir chamados t\u00e9cnicos e acompanhar solicita\u00e7\u00f5es de suporte ao parque de TI do SENAI.</p>
                    
                    <h6 class="mt-4">Principais Funcionalidades:</h6>
                    <ul>
                        <li><strong>Abertura de Chamados:</strong> Registre problemas t\u00e9cnicos</li>
                        <li><strong>Acompanhamento:</strong> Veja status dos seus chamados</li>
                        <li><strong>Hist\u00f3rico:</strong> Consulte chamados anteriores</li>
                        <li><strong>Indicadores (Admin):</strong> Visualize m\u00e9tricas de atendimento</li>
                    </ul>

                    <h6 class="mt-4">Como Abrir um Chamado:</h6>
                    <ol>
                        <li>Clique em "Abrir Chamado"</li>
                        <li>Selecione a categoria do problema</li>
                        <li>Descreva detalhadamente o ocorrido</li>
                        <li>Adicione capturas de tela se relevante</li>
                        <li>Clique em "Enviar Chamado"</li>
                    </ol>

                    <p class="alert alert-warning mt-3">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        <strong>Dica:</strong> Antes de abrir um chamado, consulte o FAQ acima - sua d\u00favida pode j\u00e1 estar respondida!
                    </p>
                </div>
            </div>
        </section>

        <!-- Controle de Rateio Section -->
        <section id="rateio" class="help-section">
            <h2 class="mb-4"><i class="bi bi-coin me-2"></i>Controle de Rateio</h2>
            <div class="card">
                <div class="card-body">
                    <h5>Como usar o M\u00f3dulo</h5>
                    <p>O m\u00f3dulo de Controle de Rateio permite a apura\u00e7\u00e3o de horas de instrutores e rateio de custos entre diferentes \u00e1reas e projetos.</p>
                    
                    <h6 class="mt-4">Principais Funcionalidades:</h6>
                    <ul>
                        <li><strong>Dashboard Financeiro:</strong> Visualize m\u00e9tricas de custos e aloca\u00e7\u00f5es</li>
                        <li><strong>Apura\u00e7\u00e3o de Horas:</strong> Registre e calcule horas trabalhadas</li>
                        <li><strong>Relat\u00f3rios de Rateio:</strong> Gere relat\u00f3rios detalhados por per\u00edodo</li>
                        <li><strong>Gest\u00e3o de Instrutores:</strong> Controle cadastro e dados de instrutores</li>
                    </ul>

                    <h6 class="mt-4">Gloss\u00e1rio de Termos:</h6>
                    <dl>
                        <dt>Rateio:</dt>
                        <dd>Distribui\u00e7\u00e3o proporcional de custos entre diferentes centros de custo.</dd>
                        
                        <dt>Apura\u00e7\u00e3o de Horas:</dt>
                        <dd>Processo de contabiliza\u00e7\u00e3o das horas trabalhadas por instrutores.</dd>
                        
                        <dt>Centro de Custo:</dt>
                        <dd>Unidade organizacional \u00e0 qual os custos s\u00e3o alocados.</dd>
                    </dl>
                </div>
            </div>
        </section>

        <!-- Gerenciamento de Usu\u00e1rios Section -->
        <section id="usuarios" class="help-section">
            <h2 class="mb-4"><i class="bi bi-person-gear me-2"></i>Gerenciamento de Usu\u00e1rios</h2>
            <div class="card">
                <div class="card-body">
                    <h5>Como usar o M\u00f3dulo</h5>
                    <p>O m\u00f3dulo de Gerenciamento de Usu\u00e1rios permite cadastrar, editar e controlar permiss\u00f5es de acesso ao sistema Conecta SENAI. <strong>Acesso restrito a administradores.</strong></p>
                    
                    <h6 class="mt-4">Principais Funcionalidades:</h6>
                    <ul>
                        <li><strong>Cadastro de Usu\u00e1rios:</strong> Crie novos usu\u00e1rios no sistema</li>
                        <li><strong>Controle de Permiss\u00f5es:</strong> Defina quais m\u00f3dulos cada usu\u00e1rio pode acessar</li>
                        <li><strong>Edi\u00e7\u00e3o de Perfis:</strong> Atualize dados e permiss\u00f5es</li>
                        <li><strong>Inativa\u00e7\u00e3o/Reativa\u00e7\u00e3o:</strong> Gerencie status de usu\u00e1rios</li>
                    </ul>

                    <h6 class="mt-4">N\u00edveis de Permiss\u00e3o:</h6>
                    <ul>
                        <li><strong>Administrador:</strong> Acesso completo a todos os m\u00f3dulos</li>
                        <li><strong>Gestor:</strong> Acesso a m\u00f3dulos operacionais e relat\u00f3rios</li>
                        <li><strong>Usu\u00e1rio Padr\u00e3o:</strong> Acesso b\u00e1sico aos m\u00f3dulos permitidos</li>
                    </ul>

                    <p class="alert alert-danger mt-3">
                        <i class="bi bi-shield-exclamation me-2"></i>
                        <strong>Importante:</strong> Altera\u00e7\u00f5es em permiss\u00f5es t\u00eam efeito imediato. Sempre confirme as mudan\u00e7as antes de salvar.
                    </p>
                </div>
            </div>
        </section>

'''

# Inserir as seções antes do Changelog
new_content = content[:insert_position] + module_sections + content[insert_position:]

# Salvar o arquivo
with open('templates/ajuda.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("\u2705 Se\u00e7\u00f5es espec\u00edficas de m\u00f3dulos adicionadas ao ajuda.html!")
print(f"Tamanho anterior: {len(content)} bytes")
print(f"Tamanho novo: {len(new_content)} bytes")
print(f"Se\u00e7\u00f5es adicionadas: {len(new_content) - len(content)} bytes")
