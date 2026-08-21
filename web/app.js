const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const sendButton = document.getElementById("send");
const messages = document.getElementById("messages");

const statusText = document.getElementById("status");
const lifeTime = document.getElementById("life-time");
const lifeActivity = document.getElementById("life-activity");
const lifeEnergy = document.getElementById("life-energy");
const lifeFatigue = document.getElementById("life-fatigue");
const virtualMemoryCount = document.getElementById("virtual-memory-count");

function addMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  wrapper.appendChild(bubble);
  messages.appendChild(wrapper);
  messages.scrollTop = messages.scrollHeight;
}

function setStatus(text) {
  statusText.textContent = text;
}

function updateMemoryCounts(counts) {
  if (!counts) {
    return;
  }

  virtualMemoryCount.textContent = counts.virtual_life ?? 0;
}

function updateLifeState(lifeState) {
  if (!lifeState) {
    return;
  }

  lifeTime.textContent = lifeState.current_time ?? "-";
  lifeActivity.textContent = lifeState.current_activity ?? "-";
  lifeEnergy.textContent = lifeState.energy ?? "-";
  lifeFatigue.textContent = lifeState.fatigue ?? "-";
}

async function loadStatus() {
  try {
    const response = await fetch("/api/status");

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    updateLifeState(data.life_state);
    updateMemoryCounts(data.memory_counts);
    setStatus("在线");
  } catch (error) {
    console.error(error);
    setStatus("连接失败");
  }
}


async function loadProactive() {
  try {
    const response = await fetch("/api/proactive");

    if (!response.ok) {
      return;
    }

    const data = await response.json();

    if (!data.messages) {
      return;
    }

    data.messages.forEach((msg) => {
      if (msg.content) {
        addMessage(
          "assistant",
          msg.content,
        );
      }
    });

  } catch (error) {
    console.error(error);
  }
}

async function sendMessage(text) {
  sendButton.disabled = true;
  input.disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: text,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }

    addMessage("assistant", data.reply);
    updateLifeState(data.life_state);
    updateMemoryCounts(data.memory_counts);
    setStatus("在线");
  } catch (error) {
    console.error(error);
    addMessage(
      "assistant",
      `抱歉，刚才出了点问题：${error.message}`,
    );
    setStatus("连接异常");
  } finally {
    sendButton.disabled = false;
    input.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const text = input.value.trim();

  if (!text) {
    return;
  }

  addMessage("user", text);
  input.value = "";

  await sendMessage(text);
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

addMessage(
  "assistant",
  "嗨～我是小七。过来陪我聊聊天吧。",
);

loadStatus();
input.focus();

setInterval(loadStatus, 5000);
setInterval(loadProactive, 5000);
