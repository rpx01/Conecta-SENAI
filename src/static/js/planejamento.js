// app/static/js/planejamento.js
(() => {
  const API = "/planejamento/api/planejamento";

  function semanaStr(d){ return ["Domingo","Segunda","Terça-feira","Quarta-feira","Quinta-feira","Sexta-feira","Sábado"][d.getDay()]; }

  async function fetchDados(params={}) {
    const qs = new URLSearchParams(params).toString();
    const r = await fetch(`${API}?${qs}`); return r.json();
  }

  // Colorir por status
  function statusClass(s){
    if (s==="Confirmado") return "bg-success-subtle";
    if (s==="Cancelado") return "bg-danger-subtle";
    return "bg-warning-subtle"; // Planejado
  }

  // LISTA
  window.loadLista = async function(){
    const mes = document.querySelector("#mes").value;
    const status = document.querySelector("#filtroStatus")?.value || "";
    const data = await fetchDados({mes, status});
    const tbody = document.querySelector("#tbodyLista");
    tbody.innerHTML = "";
    data.forEach(p=>{
      const d = new Date(p.data+"T00:00:00");
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${d.toLocaleDateString()}</td>
        <td>${semanaStr(d)}</td>
        <td>${p.turno}</td>
        <td>${p.instrutor||""}</td>
        <td>${p.treinamento}</td>
        <td>${p.carga_horas||""}</td>
        <td>${p.modalidade||""}</td>
        <td>${p.local||""}</td>
        <td>${p.cliente||""}</td>
        <td><span class="badge ${p.status==='Confirmado'?'text-bg-success':p.status==='Cancelado'?'text-bg-danger':'text-bg-warning'}">${p.status}</span></td>
        ${window.userCanEdit ? `<td class="text-end">
          <button class="btn btn-sm btn-outline-primary" data-id="${p.id}" onclick="editar(${p.id})">Editar</button>
          <button class="btn btn-sm btn-outline-danger" data-id="${p.id}" onclick="remover(${p.id})">Excluir</button>
        </td>`:""}
      `;
      tbody.appendChild(tr);
    });
  }

  // MATRIZ (linhas = dias*turnos; colunas = instrutores)
  window.loadMatriz = async function(){
    const mes = document.querySelector("#mes").value;
    const data = await fetchDados({mes});
    // agrupar por instrutor
    const instrutores = [...new Set(data.map(p=>p.instrutor))].sort();
    // gerar cabeçalho extra
    const thead = document.querySelector("thead tr");
    // remove cols antigas
    thead.querySelectorAll("th:not(:nth-child(-n+3))").forEach(el=>el.remove());
    instrutores.forEach(i=>{
      const th = document.createElement("th"); th.textContent=i||"—"; th.style.minWidth="180px";
      thead.appendChild(th);
    });

    // construir mapa: chave = data|turno|instrutor
    const map = new Map();
    data.forEach(p => map.set(`${p.data}|${p.turno}|${p.instrutor}`, p));

    const tbody = document.querySelector("#tbodyMatriz"); tbody.innerHTML="";
    const [y,m] = mes.split("-").map(Number);
    const start = new Date(y, m-1, 1);
    const end   = new Date(y, m, 0);
    const turnos = ["MANHA","TARDE","NOITE"];

    for(let d=new Date(start); d<=end; d.setDate(d.getDate()+1)){
      turnos.forEach(t=>{
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${d.toLocaleDateString()}</td>
          <td>${semanaStr(d)}</td>
          <td>${t}</td>`;
        instrutores.forEach(i=>{
          const key = `${d.toISOString().slice(0,10)}|${t}|${i}`;
          const p = map.get(key);
          const c = document.createElement("td");
          c.className = "align-top";
          if (p){
            c.classList.add(statusClass(p.status));
            c.innerHTML = `<div class="fw-semibold">${p.treinamento}</div>
                           <div class="small text-muted">${p.modalidade||""} ${p.carga_horas?`• ${p.carga_horas}h`:""} ${p.local?`• ${p.local}`:""}</div>`;
            if (window.userCanEdit){
              c.style.cursor="pointer";
              c.onclick=()=>editar(p.id);
            }
          } else if (window.userCanEdit){
            c.innerHTML = `<button class="btn btn-sm btn-outline-primary" onclick="novoSlot('${d.toISOString().slice(0,10)}','${t}','${i}')">Adicionar</button>`;
          }
          tr.appendChild(c);
        });
        tbody.appendChild(tr);
      });
    }
  }

  // Ações CRUD (snippets)
  window.novoSlot = function(data, turno, instrutor){
    // abre modal com valores presetados; salvar via POST
    // ... preencher inputs; mostrar modal
  };
  window.editar = async function(id){ /* carregar via /api/planejamento e abrir modal */ };
  window.remover = async function(id){ /* DELETE e recarregar */ };

  // bind botões
  document.querySelector("#btnCarregar")?.addEventListener("click", ()=>loadMatriz());
  document.querySelector("#btnAplicar")?.addEventListener("click", ()=>loadLista());

  // auto-load
  if (document.querySelector("#tbodyMatriz")) loadMatriz();
  if (document.querySelector("#tbodyLista"))  loadLista();
})();
