document.addEventListener('DOMContentLoaded', function() {
    // Animate the title with a glow effect
    const title = document.querySelector('.animated-title');
    if (title) {
        setInterval(() => {
            title.classList.toggle('glow');
        }, 1200);
    }

    // Animate the slogan
    const slogan = document.querySelector('.slogan');
    if (slogan) {
        slogan.style.opacity = 0;
        slogan.style.transition = "opacity 1.2s cubic-bezier(.77,0,.18,1)";
        setTimeout(() => {
            slogan.style.opacity = 1;
        }, 600);
    }
});

// Optional: Add CSS for the glow effect dynamically
const style = document.createElement('style');
style.innerHTML = `
.animated-title.glow {
    text-shadow:
        0 0 16px #00e6e6,
        0 0 32px #fff176,
        0 4px 24px #000,
        0 1px 0 #fff;
}
`;
document.head.appendChild(style);

// Add ripple effect to animated buttons
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.btn-animated').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            let ripple = document.createElement('span');
            ripple.className = 'ripple';
            ripple.style.left = (e.offsetX) + 'px';
            ripple.style.top = (e.offsetY) + 'px';
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });
});

// Optional: Animate title letters
document.addEventListener('DOMContentLoaded', function() {
    const title = document.querySelector('.home-title');
    if (title) {
        let html = '';
        title.textContent.split('').forEach((char, i) => {
            if (char === ' ') html += ' ';
            else html += `<span style="display:inline-block;animation:popIn 0.7s cubic-bezier(.77,0,.18,1) both;animation-delay:${i*0.04}s">${char}</span>`;
        });
        title.innerHTML = html;
    }
});

// Add ripple effect style
const style2 = document.createElement('style');
style2.innerHTML = `
.ripple {
    position: absolute;
    border-radius: 50%;
    background: rgba(0,230,230,0.4);
    width: 60px;
    height: 60px;
    transform: translate(-50%, -50%);
    pointer-events: none;
    animation: ripple-effect 0.6s linear;
    z-index: 10;
}
@keyframes ripple-effect {
    from { opacity: 1; transform: scale(0);}
    to { opacity: 0; transform: scale(2);}
}
@keyframes popIn {
    from { opacity: 0; transform: scale(0.7) translateY(-30px);}
    to { opacity: 1; transform: scale(1) translateY(0);}
}
`;
document.head.appendChild(style2);
