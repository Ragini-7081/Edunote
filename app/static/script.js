// ==================================================
// MULTI-TAB AUTHENTICATION & LOGIN SCRIPT
// ==================================================

// Channel for cross-tab communication
const authChannel = typeof BroadcastChannel !== "undefined" ? new BroadcastChannel("edunote_auth") : null;

// Broadcast auth event to all other tabs and persist in localStorage
function notifyAuthChange(type, data) {
    const payload = { type: type, data: data, timestamp: Date.now() };
    if (authChannel) {
        authChannel.postMessage(payload);
    }
    try {
        localStorage.setItem("edunote_auth_event", JSON.stringify(payload));
    } catch (e) {}
}

// Check if user is currently logged in on the server
async function checkAuthStatus() {
    try {
        const response = await fetch("/api/auth/status", {
            headers: { "Accept": "application/json" },
            cache: "no-store"
        });
        if (response.ok) {
            const data = await response.json();
            if (data.logged_in && data.dashboard_url) {
                // Already logged in in this browser session, redirect to dashboard
                window.location.replace(data.dashboard_url);
                return true;
            }
        }
    } catch (err) {
        console.warn("Auth status check failed:", err);
    }
    return false;
}

// UI Alert Helpers
function showAlert(message, isAlreadyLoggedIn, dashboardUrl) {
    const alertBox = document.getElementById("authAlert");
    const messageEl = document.getElementById("alertMessage");
    const actionsEl = document.getElementById("alertActions");
    const dashboardLink = document.getElementById("dashboardLink");

    if (!alertBox || !messageEl) {
        alert(message);
        return;
    }

    messageEl.textContent = message;
    if (isAlreadyLoggedIn) {
        alertBox.classList.add("info");
        if (actionsEl && dashboardLink) {
            if (dashboardUrl) {
                dashboardLink.href = dashboardUrl;
            }
            actionsEl.style.display = "flex";
        }
    } else {
        alertBox.classList.remove("info");
        if (actionsEl) {
            actionsEl.style.display = "none";
        }
    }
    alertBox.style.display = "block";
}

function hideAlert() {
    const alertBox = document.getElementById("authAlert");
    if (alertBox) {
        alertBox.style.display = "none";
    }
}

// Listen for cross-tab login events
if (authChannel) {
    authChannel.onmessage = (event) => {
        if (event.data?.type === "LOGIN" && event.data?.data?.dashboard_url) {
            // Another tab just logged in: automatically redirect this tab to dashboard!
            window.location.replace(event.data.data.dashboard_url);
        } else if (event.data?.type === "LOGOUT") {
            window.location.reload();
        }
    };
}

// Storage event listener fallback (for older browsers or iframe contexts)
window.addEventListener("storage", (event) => {
    if (event.key === "edunote_auth_event" && event.newValue) {
        try {
            const payload = JSON.parse(event.newValue);
            if (payload.type === "LOGIN" && payload.data?.dashboard_url) {
                window.location.replace(payload.data.dashboard_url);
            } else if (payload.type === "LOGOUT") {
                window.location.reload();
            }
        } catch (e) {}
    }
});

// Re-verify auth status when page is shown (handles Back/Forward bfcache navigations)
window.addEventListener("pageshow", () => {
    checkAuthStatus();
});

// Main login form handling
document.addEventListener("DOMContentLoaded", () => {
    // Initial check on load
    checkAuthStatus();

    const form = document.getElementById("loginForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideAlert();

        const submitBtn = form.querySelector("button[type='submit']");
        const originalText = submitBtn ? submitBtn.innerText : "Login";
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerText = "Logging in...";
        }

        try {
            const formData = new FormData(form);
            const response = await fetch("/login", {
                method: "POST",
                headers: {
                    "Accept": "application/json"
                },
                body: formData
            });

            // If browser followed a 303 Redirect to dashboard
            if (response.redirected) {
                notifyAuthChange("LOGIN", { dashboard_url: response.url });
                window.location.href = response.url;
                return;
            }

            const contentType = response.headers.get("content-type") || "";
            if (contentType.includes("application/json")) {
                const result = await response.json();

                if (result.success && result.redirect_url) {
                    notifyAuthChange("LOGIN", { dashboard_url: result.redirect_url });
                    window.location.href = result.redirect_url;
                    return;
                }

                if (result.already_logged_in) {
                    showAlert(
                        result.message || "Another account is already logged in on this browser. Please log out first.",
                        true,
                        result.dashboard_url
                    );
                } else {
                    showAlert(result.message || "Invalid email or password", false);
                }
            } else {
                // If HTML response was returned
                if (response.status === 200) {
                    window.location.reload();
                } else {
                    showAlert("Invalid email or password", false);
                }
            }
        } catch (err) {
            console.error("Login submission error:", err);
            showAlert("An error occurred during login. Please try again.", false);
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerText = originalText;
            }
        }
    });
});