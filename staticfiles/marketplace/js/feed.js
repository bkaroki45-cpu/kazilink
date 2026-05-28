const nextLink = document.querySelector('[data-next-page]');
const feed = document.querySelector('[data-feed]');

if (nextLink && feed) {
    const observer = new IntersectionObserver(async (entries) => {
        if (!entries[0].isIntersecting) return;
        observer.disconnect();
        nextLink.textContent = 'Loading...';
        const response = await fetch(nextLink.href);
        const text = await response.text();
        const doc = new DOMParser().parseFromString(text, 'text/html');
        const cards = doc.querySelectorAll('.feed-card');
        cards.forEach((card) => feed.insertBefore(card, nextLink));
        const replacement = doc.querySelector('[data-next-page]');
        if (replacement) {
            nextLink.href = replacement.href;
            nextLink.textContent = 'Load more jobs';
            observer.observe(nextLink);
        } else {
            nextLink.remove();
        }
    }, { rootMargin: '300px' });
    observer.observe(nextLink);
}
