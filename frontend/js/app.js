const $ = (sel) => document.querySelector(sel);

function toggleApiKey() {
    const provider = $("#provider-select").value;
    $("#api-key-group").style.display = provider === "groq" ? "none" : "flex";
}

function setStatus(text, show = true) {
    $("#status-text").textContent = text;
    $("#status-bar").style.display = show ? "flex" : "none";
}

function addArgumentCard(side, round) {
    const container = $(`#${side}-arguments`);
    const card = document.createElement("div");
    card.className = "argument-card typing-cursor";
    card.id = `${side}-round-${round}`;
    card.innerHTML = `<div class="argument-round">Round ${round}</div><span class="arg-text"></span>`;
    container.appendChild(card);
    // auto-scroll the panel to the new card
    container.scrollTop = container.scrollHeight;
}

function appendChunk(side, round, text) {
    if (!$(`#${side}-round-${round}`)) {
        addArgumentCard(side, round);
    }
    const span = $(`#${side}-round-${round} .arg-text`);
    if (span) {
        span.textContent += text;
        const container = $(`#${side}-arguments`);
        container.scrollTop = container.scrollHeight;
    }
}

function finishCard(side, round) {
    const card = $(`#${side}-round-${round}`);
    if (card) card.classList.remove("typing-cursor");
}

function renderVerdict(markdown) {
    let html = markdown
        .replace(/## (.+)/g, "<h2>$1</h2>")
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n\n/g, "</p><p>")
        .replace(/\n/g, "<br>");
    $("#verdict-content").innerHTML = "<p>" + html + "</p>";
    $("#verdict-section").style.display = "block";
    $("#verdict-section").scrollIntoView({ behavior: "smooth" });
}

async function startDebate() {
    const topic = $("#topic-input").value.trim();
    if (!topic) {
        $("#topic-input").focus();
        return;
    }

    const provider = $("#provider-select").value;
    const roundsRaw = parseInt($("#rounds-input").value) || 3;
    const numRounds = Math.max(1, Math.min(10, roundsRaw));
    $("#rounds-input").value = numRounds;
    const apiKey = $("#api-key-input").value.trim() || null;

    if (provider !== "groq" && !apiKey) {
        alert("Please enter your API key for this provider.");
        return;
    }

    // reset
    $("#pro-arguments").innerHTML = "";
    $("#con-arguments").innerHTML = "";
    $("#verdict-content").innerHTML = "";
    $("#verdict-section").style.display = "none";
    $("#arena").style.display = "grid";
    $("#start-btn").disabled = true;
    setStatus("Starting debate...");

    const body = { topic, num_rounds: numRounds, provider };
    if (apiKey) body.api_key = apiKey;

    try {
        const response = await fetch("/api/debate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.startsWith("data:")) continue;
                const raw = line.slice(5).trim();
                if (!raw) continue;

                let ev;
                try { ev = JSON.parse(raw); } catch { continue; }

                switch (ev.type) {
                    case "round_start":
                        setStatus(`Round ${ev.round}, PRO is arguing...`);
                        break;

                    case "pro_chunk":
                        appendChunk("pro", ev.round, ev.content);
                        break;

                    case "con_chunk":
                        if (!$(`#con-round-${ev.round}`)) {
                            setStatus(`Round ${ev.round}, CON is responding...`);
                        }
                        appendChunk("con", ev.round, ev.content);
                        break;

                    case "round_end":
                        finishCard("pro", ev.round);
                        finishCard("con", ev.round);
                        setStatus(`Round ${ev.round} complete`);
                        break;

                    case "judge":
                        setStatus("Judge is evaluating...");
                        renderVerdict(ev.content);
                        break;

                    case "error":
                        setStatus(`Error: ${ev.content}`);
                        $("#start-btn").disabled = false;
                        return;

                    case "done":
                        setStatus("", false);
                        break;
                }
            }
        }
    } catch (err) {
        setStatus(`Connection error: ${err.message}`);
    }

    $("#start-btn").disabled = false;
}

document.addEventListener("DOMContentLoaded", () => {
    $("#topic-input").focus();
    $("#topic-input").addEventListener("keydown", (e) => {
        if (e.key === "Enter") startDebate();
    });
});
