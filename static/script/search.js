function debounce(callback, wait = 250) {
  let timeout = null;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => callback(...args), wait);
  };
}

function createResultItem(item) {
  const link = document.createElement('a');
  link.href = item.url;
  link.className = 'search-result';
  link.innerHTML = `
    <span class="search-result-title">${item.title}</span>
    <span class="search-result-meta">${item.type.charAt(0).toUpperCase() + item.type.slice(1)} · ${item.path}`;
  if (item.population !== null && item.population !== undefined) {
    link.innerHTML += ` · População: ${item.population}`;
  }
  link.innerHTML += `</span>`;
  return link;
}

function renderSearchResults(results, container) {
  container.innerHTML = '';
  if (!results.length) {
    const emptyState = document.createElement('div');
    emptyState.className = 'search-result';
    emptyState.textContent = 'Nenhum resultado encontrado.';
    container.appendChild(emptyState);
    return;
  }

  results.forEach((item) => container.appendChild(createResultItem(item)));
}

function initGlobalSearch() {
  const input = document.getElementById('global-search-input');
  const resultsBox = document.getElementById('global-search-results');
  if (!input || !resultsBox) {
    return;
  }

  const searchAction = debounce((value) => {
    const query = value.trim();
    if (!query) {
      resultsBox.classList.remove('active');
      resultsBox.innerHTML = '';
      return;
    }

    fetch(`/search?q=${encodeURIComponent(query)}`)
      .then((response) => response.json())
      .then((data) => {
        renderSearchResults(data.results || [], resultsBox);
        resultsBox.classList.add('active');
      })
      .catch(() => {
        resultsBox.classList.remove('active');
      });
  }, 250);

  input.addEventListener('input', (event) => searchAction(event.target.value));
  document.addEventListener('click', (event) => {
    if (!resultsBox.contains(event.target) && event.target !== input) {
      resultsBox.classList.remove('active');
    }
  });
}

function initLocalSearch() {
  document.querySelectorAll('.local-search-input').forEach((searchInput) => {
    const tableCard = searchInput.closest('.table-card');
    if (!tableCard) {
      return;
    }

    const rows = Array.from(tableCard.querySelectorAll('tbody tr[data-search]'));
    searchInput.addEventListener('input', (event) => {
      const query = event.target.value.trim().toLowerCase();
      rows.forEach((row) => {
        const text = row.dataset.search.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      });
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initGlobalSearch();
  initLocalSearch();
});
