const chatBody = document.getElementById("chatBody");
const sendBtn = document.getElementById("chatSend");
const input = document.getElementById("chatInput");

const MAX_HISTORY = 50;
const history = [];

let busy = false;

function message(text, role) {
    const wrap = document.createElement("div");

    wrap.className = "chat__msg chat__msg--" + role;

    const bubble = document.createElement("div");

    bubble.className = "chat__bubble";
    bubble.textContent = text;

    wrap.appendChild(bubble);

    chatBody.appendChild(wrap);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function pushHistory(role, content) {
    history.push({ role, content });

    if (history.length > MAX_HISTORY) {
        history.splice(0, history.length - MAX_HISTORY);
    }
}

function resize() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 140) + "px";
}

async function process() {
    const text = input.value.trim();

    if (!text || busy){
        return;
    }

    busy = true;
    sendBtn.disabled = true;

    message(text, "user");
    pushHistory("user", text);

    input.value = "";

    resize();

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: text,
                history: history.slice(0, -1)
            })
        });

        const data = await res.json();

        if (!res.ok){
            throw new Error(data.error || ("HTTP " + res.status));
        }

        message(data.reply, "ai");

        pushHistory("assistant", data.reply);

    } catch (err) {
        message("Ошибка: " + err.message, "ai");
    }

    busy = false;

    sendBtn.disabled = input.value.trim() === "";

    input.focus();
}

input.addEventListener("input", () => {
    resize();

    sendBtn.disabled = input.value.trim() === "" || busy;
});

input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();

        process();
    }
});

sendBtn.addEventListener("click", process);

message("Привет! Я могу ответить на любые вопросы о приложении.", "ai");
resize();
