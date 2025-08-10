# Design System FIEMG

Este documento descreve os padrões de interface aprovados pela FIEMG.
Use-o como referência e atualize-o sempre que novos componentes forem introduzidos.

## Tipografia

- **Gibson** – títulos e elementos de destaque.
- **Exo 2** – corpo de texto e formulários.

```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gibson&family=Exo+2:wght@400;600&display=swap">
<h1 class="fiemg-heading">Título de Exemplo</h1>
<p class="fiemg-body">Parágrafo com o corpo de texto.</p>
```

```css
body {
  font-family: "Gibson", "Exo 2", sans-serif;
}

h1, h2, h3, h4, h5, h6 {
  font-family: "Gibson", sans-serif;
}

p, input, textarea {
  font-family: "Exo 2", sans-serif;
}
```

## Paleta de Cores

| Nome            | Hex      | Uso sugerido                         |
|-----------------|----------|-------------------------------------|
| Azul FIEMG      | `#164194`| Botões primários, cabeçalhos        |
| Vermelho FIEMG  | `#D50032`| Ações destrutivas e alertas         |
| Verde FIEMG     | `#006837`| Mensagens de sucesso                |
| Amarelo FIEMG   | `#FFB612`| Avisos e destaques                 |

```css
.bg-fiemg-blue   { background-color: #164194; color: #fff; }
.bg-fiemg-red    { background-color: #D50032; color: #fff; }
.bg-fiemg-green  { background-color: #006837; color: #fff; }
.bg-fiemg-yellow { background-color: #FFB612; color: #000; }
.text-fiemg-blue { color: #164194; }
```

## Botões

```html
<button class="btn btn-primary">Primário</button>
<button class="btn btn-danger">Perigo</button>
<button class="btn btn-success">Sucesso</button>
<button class="btn btn-warning">Aviso</button>
```

```css
.btn-primary { background-color: #164194; border-color: #164194; }
.btn-danger  { background-color: #D50032; border-color: #D50032; }
.btn-success { background-color: #006837; border-color: #006837; }
.btn-warning { background-color: #FFB612; border-color: #FFB612; color: #000; }
```

## Formulários

```html
<form>
  <label for="nome">Nome</label>
  <input id="nome" type="text" class="form-control" placeholder="Digite seu nome">

  <label for="mensagem" class="mt-3">Mensagem</label>
  <textarea id="mensagem" class="form-control" rows="3"></textarea>

  <button type="submit" class="btn btn-primary mt-3">Enviar</button>
</form>
```

```css
.form-control {
  font-family: "Exo 2", sans-serif;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
  padding: 0.375rem 0.75rem;
}
```

## Modais

```html
<div class="modal" id="demoModal" tabindex="-1" role="dialog">
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header bg-fiemg-blue text-white">
        <h5 class="modal-title">Título do Modal</h5>
      </div>
      <div class="modal-body">
        <p>Conteúdo do modal...</p>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">Fechar</button>
        <button type="button" class="btn btn-primary">Salvar</button>
      </div>
    </div>
  </div>
</div>
```

```css
.modal-header { border-bottom: 1px solid #dee2e6; }
.modal-footer { border-top: 1px solid #dee2e6; }
```

## Tabelas

```html
<table class="table table-striped">
  <caption class="visually-hidden">Tabela de exemplo do design system</caption>
  <thead class="table-primary">
    <tr>
      <th scope="col">Coluna 1</th>
      <th scope="col">Coluna 2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Valor 1</td>
      <td>Valor 2</td>
    </tr>
  </tbody>
</table>
```

```css
.table th, .table td {
  font-family: "Exo 2", sans-serif;
}
```

## Iconografia

O projeto utiliza os [Lucide Icons](https://lucide.dev/) para manter um estilo linear consistente.

```html
<script src="https://unpkg.com/lucide@latest"></script>
<script>lucide.createIcons({attrs:{strokeWidth:1.75}})</script>
<i data-lucide="calendar"></i>
```

Os ícones herdam a cor do texto e evitam preenchimentos pesados.

Atualize este documento sempre que novos componentes visuais forem adicionados ao sistema.
