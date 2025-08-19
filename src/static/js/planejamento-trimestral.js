// src/static/js/planejamento-trimestral.js

document.addEventListener("DOMContentLoaded", function () {
    const addButton = document.getElementById("add-button");
    const tableBody = document.getElementById("table-body");
    let groupCounter = 0; // Contador para gerar IDs de grupo únicos

    addButton.addEventListener("click", adicionarNovaLinha);

    function adicionarNovaLinha() {
        // Coleta os valores dos campos do formulário
        const area = document.getElementById("area").value;
        const curso = document.getElementById("curso").value;
        const cargaHoraria = document.getElementById("carga_horaria").value;
        const diasDaSemana = getSelectedDays(); // Pega os dias selecionados
        const horario = document.getElementById("horario").value;
        const dataInicio = document.getElementById("data_inicio").value;

        // Validação simples para garantir que os campos principais estão preenchidos
        if (!area || !curso || !cargaHoraria || !diasDaSemana.length || !horario || !dataInicio) {
            alert("Por favor, preencha todos os campos obrigatórios.");
            return;
        }

        const datas = calcularDatas(dataInicio, diasDaSemana);
        const groupId = `group-${groupCounter++}`; // Cria um ID de grupo único

        // Cria as linhas da tabela para cada data calculada
        datas.forEach((data, index) => {
            const newRow = tableBody.insertRow();
            newRow.setAttribute('data-group-id', groupId); // Adiciona o atributo de grupo

            // Adiciona as células (colunas) à nova linha
            newRow.innerHTML = `
                <td>${area}</td>
                <td>${curso}</td>
                <td>${cargaHoraria}</td>
                <td>${data.diaDaSemana}</td>
                <td>${data.data}</td>
                <td>${horario}</td>
                <td>${index === 0 ? `<button class="btn btn-danger btn-sm" onclick="removerLinha(this, '${groupId}')">Excluir</button>` : ''}</td>
            `;
        });
    }

    window.removerLinha = function (button, groupId) {
        // Seleciona todas as linhas que pertencem ao mesmo grupo
        const rowsToDelete = document.querySelectorAll(`[data-group-id="${groupId}"]`);
        
        // Remove cada uma das linhas encontradas
        rowsToDelete.forEach(row => {
            row.parentNode.removeChild(row);
        });
    }

    function getSelectedDays() {
        const checkboxes = document.querySelectorAll('input[name="dias_da_semana"]:checked');
        const days = [];
        checkboxes.forEach((checkbox) => {
            days.push(parseInt(checkbox.value));
        });
        return days;
    }

    function calcularDatas(startDate, weekDays) {
        const datas = [];
        // Lógica para calcular as datas com base no dia de início e dias da semana
        // (Esta lógica permanece a mesma do seu código original)
        // Exemplo simples:
        let currentDate = new Date(startDate);
        for (let i = 0; i < 5; i++) { // Apenas como exemplo, gere 5 datas
            const dayOfWeek = currentDate.getDay();
            if (weekDays.includes(dayOfWeek)) {
                datas.push({
                    data: currentDate.toLocaleDateString('pt-BR'),
                    diaDaSemana: getDayName(dayOfWeek)
                });
            }
            currentDate.setDate(currentDate.getDate() + 1);
        }
        return datas;
    }

    function getDayName(dayIndex) {
        const days = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"];
        return days[dayIndex];
    }
});

