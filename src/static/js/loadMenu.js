document.addEventListener("DOMContentLoaded", function() {
    const menuPlaceholder = document.getElementById('menu-placeholder');
    if (menuPlaceholder) {
        fetch('/_menu.html')
            .then(response => response.text())
            .then(data => {
                menuPlaceholder.innerHTML = data;
            })
            .catch(error => console.error('Erro ao carregar o menu:', error));
    }
});

