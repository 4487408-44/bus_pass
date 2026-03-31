// script.js

document.addEventListener('DOMContentLoaded', () => {

    const emailRegex = /^[a-z0-9._%+-]+@(gmail\.com|yahoo\.com|outlook\.com|hotmail\.com)$/;

    // ===== LOGIN =====
    const loginForm = document.getElementById('loginForm');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('username').value;
            const password = document.getElementById('password')?.value || "123";

            if (!emailRegex.test(email)) {
                alert('Enter valid email');
                return;
            }

            try {
                const res = await fetch('http://localhost:8082/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                const data = await res.json();

                if (res.ok) {
                    // ✅ SAVE USER ID
                    localStorage.setItem("user_id", data.user_id);
                    localStorage.setItem("username", email.split('@')[0]);

                    window.location.href = "dashboard.html";
                } else {
                    alert(data.error);
                }

            } catch (err) {
                alert("Server error");
            }
        });
    }

    // ===== REGISTER =====
    const registerForm = document.getElementById('registerForm');

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('regEmail').value;
            const password = document.getElementById('regPassword')?.value || "123";
            const username = email.split('@')[0];

            if (!emailRegex.test(email)) {
                alert('Enter valid email');
                return;
            }

            try {
                const res = await fetch('http://localhost:8082/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password })
                });

                const data = await res.json();

                if (res.ok) {
                    alert("Registered! Now login.");
                    toggleForms();
                } else {
                    alert(data.error);
                }

            } catch (err) {
                alert("Server error");
            }
        });
    }

});

// ===== TOGGLE FORMS =====
function toggleForms() {
    const loginCard = document.getElementById('loginCard');
    const registerCard = document.getElementById('registerCard');

    if (loginCard && registerCard) {
        loginCard.classList.toggle('hidden');
        registerCard.classList.toggle('hidden');
    }
}

// ===== STORE PASS TYPE =====
function setPassType(type) {
    localStorage.setItem('selectedPassType', type);
}