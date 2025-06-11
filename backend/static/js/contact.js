document.addEventListener('DOMContentLoaded', function() {
    // Animate card fade-in
    const card = document.querySelector('.contact-card');
    if (card) {
        card.style.opacity = 0;
        card.style.transform = 'translateY(40px)';
        setTimeout(() => {
            card.style.transition = 'all 0.8s cubic-bezier(.77,0,.18,1)';
            card.style.opacity = 1;
            card.style.transform = 'translateY(0)';
        }, 200);
    }

    // Handle contact form submit with AJAX
    const form = document.getElementById('contactForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(form);
            fetch('/contact/submit/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    // Show thank you modal
                    const modal = new bootstrap.Modal(document.getElementById('thankYouModal'));
                    modal.show();
                    form.reset();
                } else {
                    alert('Something went wrong. Please try again.');
                }
            })
            .catch(() => alert('Something went wrong. Please try again.'));
        });
    }

    // Helper to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
