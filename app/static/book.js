/* ============================================================
   EduNote — Book Writer v3
   Fixes: author_id detection, AI chat, save/publish
============================================================ */

// ===========================
// AUTHOR ID — triple fallback
// ===========================

function getAuthorId() {
    // 1. Server-injected via Jinja2
    if (window.AUTHOR_ID && Number(window.AUTHOR_ID) > 0) {
        return Number(window.AUTHOR_ID);
    }
    // 2. URL query param  /write-book?author_id=3
    const urlParams = new URLSearchParams(window.location.search);
    const fromUrl = parseInt(urlParams.get("author_id"));
    if (fromUrl > 0) return fromUrl;
    // 3. sessionStorage (set when navigating from dashboard)
    const stored = parseInt(sessionStorage.getItem("edunote_author_id"));
    if (stored > 0) return stored;
    return 0;
}

// Persist author_id to sessionStorage immediately
(function () {
    const id = getAuthorId();
    if (id > 0) sessionStorage.setItem("edunote_author_id", id);
    console.log("[EduNote] Resolved AUTHOR_ID:", id);
})();

// ===========================
// QUILL EDITOR
// ===========================

const quill = new Quill("#editor", {
    theme: "snow",
    placeholder: "Start writing your book here...",
    modules: {
        toolbar: [
            [{ header: [1, 2, 3, 4, false] }],
            ["bold", "italic", "underline", "strike"],
            [{ list: "ordered" }, { list: "bullet" }],
            ["blockquote", "code-block"],
            [{ color: [] }, { background: [] }],
            [{ align: [] }],
            ["link", "image"],
            ["clean"]
        ]
    }
});

// ===========================
// BACK BUTTON
// ===========================

(function () {
    const authorId = getAuthorId();
    const backBtn  = document.getElementById("backToDashboard");
    if (backBtn) backBtn.href = authorId > 0 ? `/author/${authorId}` : "/";
})();

// ===========================
// COVER IMAGE PREVIEW
// ===========================

document.getElementById("cover").addEventListener("change", function () {
    document.getElementById("cover-name").innerText =
        this.files.length > 0 ? this.files[0].name : "No image selected";
});

// ===========================
// BUTTONS
// ===========================

document.querySelector(".draft-btn").addEventListener("click",   () => saveBook("Draft"));
document.querySelector(".publish-btn").addEventListener("click", () => saveBook("Published"));

// ===========================
// SAVE / PUBLISH
// ===========================

async function saveBook(status) {
    const title       = (document.getElementById("title").value       || "").trim();
    const category    = (document.getElementById("category").value    || "").trim();
    const description = (document.getElementById("description").value || "").trim();
    const price       = parseFloat(document.getElementById("price").value) || 0;
    const content     = quill.root.innerHTML;
    const author_id   = getAuthorId();

    // Validation
    if (!title) {
        showToast("⚠️ Please enter a book title.", "error");
        document.getElementById("title").focus();
        return;
    }
    if (author_id <= 0) {
        showToast("⚠️ Cannot identify your account. Please log in again.", "error");
        console.error("[EduNote] author_id is", author_id, "— window.AUTHOR_ID:", window.AUTHOR_ID);
        return;
    }

    const payload = { title, description, content, category, price, status, author_id };
    console.log("[EduNote] Saving book:", payload);

    const btn = status === "Draft"
        ? document.querySelector(".draft-btn")
        : document.querySelector(".publish-btn");
    const origText = btn.innerText;
    btn.innerText  = status === "Draft" ? "⏳ Saving..." : "⏳ Publishing...";
    btn.disabled   = true;

    try {
        const res = await fetch("/books", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify(payload)
        });

        let result;
        try   { result = await res.json(); }
        catch { result = { success: false, message: "Invalid server response" }; }

        console.log("[EduNote] Save result:", result);

        if (!res.ok) {
            showToast("❌ Server error " + res.status + ". Check console.", "error");
            return;
        }

        if (result.success) {
            showToast(
                status === "Draft" ? "✅ Draft saved!" : "🚀 Book published!",
                "success"
            );
            setTimeout(() => {
                window.location.href = `/my-books?author_id=${author_id}`;
            }, 1800);
        } else {
            showToast("❌ " + (result.message || "Save failed"), "error");
        }

    } catch (err) {
        showToast("❌ Network error — is the server running?", "error");
        console.error("[EduNote] Fetch error:", err);
    } finally {
        btn.innerText = origText;
        btn.disabled  = false;
    }
}

// ===========================
// TOAST
// ===========================

function showToast(message, type = "success") {
    let t = document.getElementById("__toast");
    if (!t) {
        t        = document.createElement("div");
        t.id     = "__toast";
        t.style.cssText = [
            "position:fixed", "bottom:28px", "right:28px", "z-index:99999",
            "padding:14px 24px", "border-radius:14px", "font-size:14px",
            "font-weight:600", "color:#fff", "font-family:Poppins,sans-serif",
            "max-width:340px", "line-height:1.5", "box-shadow:0 10px 30px rgba(0,0,0,.25)",
            "transition:all .4s ease", "opacity:0", "transform:translateY(20px)"
        ].join(";");
        document.body.appendChild(t);
    }
    t.innerText        = message;
    t.style.background = type === "success" ? "#10b981" : "#ef4444";
    t.style.opacity    = "1";
    t.style.transform  = "translateY(0)";
    clearTimeout(t._tid);
    t._tid = setTimeout(() => {
        t.style.opacity   = "0";
        t.style.transform = "translateY(20px)";
    }, 3800);
}

// ===========================
// AI CHAT
// ===========================

const chatBox = document.getElementById("chat-box");
const aiInput = document.getElementById("ai-message");
const sendBtn = document.getElementById("send-ai");

sendBtn.addEventListener("click", sendAI);
aiInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendAI(); }
});

async function sendAI() {
    const msg = aiInput.value.trim();
    if (!msg) return;
    addUserBubble(msg);
    aiInput.value = "";

    const tid = showTyping();
    try {
        const bookTitle = (document.getElementById("title")?.value || "").trim();
        const bookCategory = document.getElementById("category")?.value || "";
        const res = await fetch("/ai-chat", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({
                message: msg,
                context: {
                    title: bookTitle,
                    category: bookCategory
                }
            })
        });
        if (!res.ok) throw new Error("HTTP " + res.status);
        const data = await res.json();
        removeTyping(tid);
        addAIBubble(data.reply || "No reply received.");
    } catch (err) {
        removeTyping(tid);
        addAIBubble("⚠️ Could not connect to AI. Please try again.");
        console.error("[AI]", err);
    }
}

// Enter to send
if (aiInput) {
    aiInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendAI();
        }
    });
}

// Quick buttons with context
document.querySelectorAll(".quick-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const text = btn.innerText.trim();
        const bookTitle = (document.getElementById("title")?.value || "").trim();
        const bookCategory = document.getElementById("category")?.value || "";
        const topic = bookTitle || bookCategory || "my book";

        let prompt = text;
        if (text.includes("Suggest Title")) {
            prompt = `Suggest titles for a book about ${topic}`;
        } else if (text.includes("Improve Writing")) {
            const selectedText = quill.getText(quill.getSelection()?.index || 0, quill.getSelection()?.length || 0).trim();
            prompt = selectedText ? `Improve this writing:\n${selectedText}` : `Give me writing tips to improve my chapter`;
        } else if (text.includes("Continue Paragraph")) {
            prompt = `Continue paragraph for a chapter on ${topic}`;
        } else if (text.includes("Fix Grammar")) {
            prompt = `Fix grammar and polish style for writing`;
        } else if (text.includes("Generate Summary")) {
            prompt = `Generate summary and key takeaways for a chapter on ${topic}`;
        } else if (text.includes("Create Quiz")) {
            prompt = `Create a 5-question quiz on ${topic}`;
        }

        aiInput.value = prompt;
        sendAI();
    });
});

// ---- Chat UI helpers ----

function addUserBubble(text) {
    const d = document.createElement("div");
    d.className = "user-message";
    d.innerText = text;
    chatBox.appendChild(d);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function addAIBubble(text) {
    const d = document.createElement("div");
    d.className = "ai-message";
    
    // Markdown formatting helper
    const formattedHtml = text
        .replace(/### (.*?)\n/g, '<h4 style="margin:8px 0 4px;font-size:14px;color:#1e293b;">$1</h4>')
        .replace(/#### (.*?)\n/g, '<h5 style="margin:6px 0 2px;font-size:13px;color:#334155;">$1</h5>')
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>")
        .replace(/\n•/g, "<br>•")
        .replace(/\n/g, "<br>");

    const bubbleId = "ai_msg_" + Date.now();
    d.id = bubbleId;

    d.innerHTML = `
      <div class="ai-label">🤖 EduNote AI</div>
      <div class="ai-text" style="line-height:1.6;font-size:13px;">${formattedHtml}</div>
      <div style="display:flex;gap:8px;margin-top:10px;padding-top:8px;border-top:1px dashed #e2e8f0;">
        <button type="button" class="ai-act-btn" onclick="insertAIIntoBook('${bubbleId}')" style="background:#dbeafe;color:#1d4ed8;border:none;padding:5px 10px;border-radius:6px;font-size:11px;font-weight:600;cursor:pointer;">
          📥 Insert into Book
        </button>
        <button type="button" class="ai-act-btn" onclick="copyAIText('${bubbleId}')" style="background:#f1f5f9;color:#475569;border:none;padding:5px 10px;border-radius:6px;font-size:11px;font-weight:600;cursor:pointer;">
          📋 Copy
        </button>
      </div>`;
    
    d._rawText = text;
    chatBox.appendChild(d);
    chatBox.scrollTop = chatBox.scrollHeight;
}

window.insertAIIntoBook = function(bubbleId) {
    const el = document.getElementById(bubbleId);
    if (!el || !el._rawText) return;
    const textToInsert = el._rawText;
    
    // Insert into Quill editor
    const range = quill.getSelection() || { index: quill.getLength() };
    const htmlToInsert = "<p><br></p>" + textToInsert
        .replace(/### (.*?)\n/g, "<h3>$1</h3>")
        .replace(/#### (.*?)\n/g, "<h4>$1</h4>")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>")
        .replace(/\n/g, "<br>");
    
    quill.clipboard.dangerouslyPasteHTML(range.index, htmlToInsert);
    showToast("✅ Content inserted into book editor!");
};

window.copyAIText = function(bubbleId) {
    const el = document.getElementById(bubbleId);
    if (!el || !el._rawText) return;
    navigator.clipboard.writeText(el._rawText).then(() => {
        showToast("📋 Copied to clipboard!");
    }).catch(() => {
        showToast("Copied text!");
    });
};

function showTyping() {
    const id = "typ_" + Date.now();
    const d  = document.createElement("div");
    d.id        = id;
    d.className = "ai-message";
    d.innerHTML = `
      <div class="ai-label">🤖 EduNote AI</div>
      <div class="ai-text" style="color:#94a3b8;font-style:italic">Thinking<span id="${id}_dots">.</span></div>`;
    chatBox.appendChild(d);
    chatBox.scrollTop = chatBox.scrollHeight;
    // Animate dots
    let n = 1;
    d._itv = setInterval(() => {
        const el = document.getElementById(id + "_dots");
        if (el) { n = (n % 3) + 1; el.innerText = ".".repeat(n); }
    }, 400);
    return id;
}

function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) { clearInterval(el._itv); el.remove(); }
}

// ===========================
// AUTO SAVE (every 2 min)
// ===========================

setInterval(() => {
    const title     = (document.getElementById("title").value || "").trim();
    const author_id = getAuthorId();
    if (title && author_id > 0) {
        silentSave();
    }
}, 120000);

async function silentSave() {
    const author_id = getAuthorId();
    if (author_id <= 0) return;
    try {
        await fetch("/books", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title:       (document.getElementById("title").value || "Untitled").trim(),
                description: (document.getElementById("description").value || "").trim(),
                content:     quill.root.innerHTML,
                category:    document.getElementById("category").value || "",
                price:       parseFloat(document.getElementById("price").value) || 0,
                status:      "Draft",
                author_id
            })
        });
        console.log("[EduNote AutoSave] Draft saved:", new Date().toLocaleTimeString());
    } catch (e) { /* silent */ }
}
