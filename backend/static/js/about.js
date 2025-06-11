document.addEventListener('DOMContentLoaded', function() {
    // Animate card fade-in
    const card = document.querySelector('.about-card');
    if (card) {
        card.style.opacity = 0;
        card.style.transform = 'translateY(40px)';
        setTimeout(() => {
            card.style.transition = 'all 0.8s cubic-bezier(.77,0,.18,1)';
            card.style.opacity = 1;
            card.style.transform = 'translateY(0)';
        }, 200);
    }
});
