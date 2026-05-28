const filterForm = document.querySelector('[data-filter-form]');
if (filterForm) {
    const query = filterForm.querySelector('[name="q"]');
    query?.addEventListener('input', () => {
        const term = query.value.toLowerCase();
        document.querySelectorAll('[data-title]').forEach((card) => {
            const haystack = `${card.dataset.title} ${card.dataset.location}`;
            card.style.display = haystack.includes(term) ? '' : 'none';
        });
    });
}
