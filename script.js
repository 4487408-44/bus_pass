// script.js
// Handles global interactions and auth mocks
document.addEventListener('DOMContentLoaded', () => {
    // Setup login/register listeners if on index.html
    const loginForm = document.getElementById('loginForm');
    // Strict lowercase case-sensitive email validation regex (allows numbers e.g. xyz1234@gmail.com)
    const emailRegex = /^[a-z0-9._%+-]+@(gmail\.com|yahoo\.com|outlook\.com|hotmail\.com)$/;
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const emailInput = document.getElementById('username').value;
            if (!emailRegex.test(emailInput)) {
                alert('Please enter a valid lowercase email address with a proper domain (e.g., xyz1234@gmail.com).');
                return;
            }
            const btn = e.target.querySelector('button');
            const ogText = btn.textContent;
            btn.textContent = "Verifying...";
            btn.style.opacity = '0.8';
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 800);
        });
    }
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const emailInput = document.getElementById('regEmail').value;
            if (!emailRegex.test(emailInput)) {
                alert('Please use a valid email address with a proper domain (e.g., @gmail.com, @yahoo.com) for registration.');
                return;
            }
            alert('Registration Successful! Please login.');
            toggleForms();
        });
    }
});
function toggleForms() {
    const loginCard = document.getElementById('loginCard');
    const registerCard = document.getElementById('registerCard');
    if (loginCard && registerCard) {
        loginCard.classList.toggle('hidden');
        registerCard.classList.toggle('hidden');
    }
}
// Store the pass type choice to display correctly on the next page
function setPassType(type) {
    localStorage.setItem('selectedPassType', type);
}
