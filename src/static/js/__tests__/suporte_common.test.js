const { test, beforeEach } = require('node:test');
const assert = require('node:assert/strict');
const { JSDOM } = require('jsdom');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

let window;
let document;

beforeEach(() => {
    const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
        url: 'http://localhost/suporte-ti/index.html',
        runScripts: 'outside-only'
    });
    window = dom.window;
    document = window.document;
    global.window = window;
    global.document = document;
    global.escapeHTML = (valor) => {
        const div = document.createElement('div');
        div.textContent = String(valor);
        return div.innerHTML;
    };
    const scriptPath = path.resolve(__dirname, '../suporte-ti/common.js');
    const scriptContent = fs.readFileSync(scriptPath, 'utf-8');
    const context = dom.getInternalVMContext();
    vm.runInContext(scriptContent, context);
});

test('formatarStatus devolve rótulos humanizados', () => {
    const { formatarStatus } = window.__suporteTI;
    assert.equal(formatarStatus('aberto'), 'Aberto');
    assert.equal(formatarStatus('RESOLVIDO'), 'Resolvido');
    assert.equal(formatarStatus('status-desconhecido'), 'status-desconhecido');
});

test('obterBadgeStatus retorna classes consistentes', () => {
    const { obterBadgeStatus } = window.__suporteTI;
    assert.equal(obterBadgeStatus('aberto'), 'badge-status-aberto');
    assert.equal(obterBadgeStatus('EM_ANDAMENTO'), 'badge-status-em_andamento');
    assert.equal(obterBadgeStatus('outro'), 'bg-secondary');
});

test('criarBadge sanitiza o conteúdo', () => {
    const { criarBadge } = window.__suporteTI;
    const badge = criarBadge({ texto: '<script>alert(1)</script>', classe: 'badge-test' });
    const container = document.createElement('div');
    container.innerHTML = badge;
    const elemento = container.querySelector('.badge-test');
    assert.ok(elemento, 'Badge deve conter a classe informada');
    assert.equal(elemento.textContent, '<script>alert(1)</script>');
});
