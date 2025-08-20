// Popula a tabela de planejamento de treinamentos

function formatarData(iso) {
    if (!iso) return '';
    const [ano, mes, dia] = iso.split('-');
    return `${dia}/${mes}/${ano}`;
}

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/planejamento/');
        if (!response.ok) {
            throw new Error('Falha ao carregar planejamento');
        }
        const dados = await response.json();
        const tbody = document.getElementById('corpo-tabela-planejamento');
        dados.forEach(planejamento => {
            const tr = document.createElement('tr');
            const celulas = [
                formatarData(planejamento.data_inicio),
                formatarData(planejamento.data_termino),
                '',
                planejamento.horario || '',
                planejamento.treinamento?.carga_horaria || '',
                planejamento.modalidade || '',
                planejamento.treinamento?.nome || '',
                planejamento.local || '',
                ''
            ];
            celulas.forEach(texto => {
                const td = document.createElement('td');
                td.textContent = texto;
                tr.appendChild(td);
            });
            const tdLink = document.createElement('td');
            if (planejamento.link_inscricao) {
                const a = document.createElement('a');
                a.href = planejamento.link_inscricao;
                a.textContent = 'Inscrição';
                a.target = '_blank';
                tdLink.appendChild(a);
            }
            tr.appendChild(tdLink);
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Erro ao buscar planejamentos:', error);
    }
});
