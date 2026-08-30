document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("loginForm");

    form.addEventListener("submit", async (e) => {

        e.preventDefault();

        const formData = new FormData(form);

        const response = await fetch("/login", {
            method: "POST",
            body: formData
        });

        if (response.redirected) {

            window.location.href = response.url;

            return;
        }

        const result = await response.json();

        alert(result.message);

    });

});