document.addEventListener('DOMContentLoaded', function() {
    const card = document.querySelector('.login-card, .register-card');
    if (card) {
        card.style.opacity = 0;
        card.style.transform = 'translateY(40px)';
        setTimeout(() => {
            card.style.transition = 'all 0.7s cubic-bezier(.77,0,.18,1)';
            card.style.opacity = 1;
            card.style.transform = 'translateY(0)';
        }, 200);
    }
});
