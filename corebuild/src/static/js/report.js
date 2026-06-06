document.addEventListener("DOMContentLoaded", function () {
  let chatUnlocked = false;
  let questionsLeft = 3;

  const openChatBtn = document.getElementById("openChatBtn");
  const sendChatBtn = document.getElementById("sendChatBtn");
  const openReportModalBtn = document.getElementById("openReportModalBtn");
  const unlockChatBtn = document.getElementById("unlockChatBtn");
  const closeChatModalBtn = document.getElementById("closeChatModalBtn");
  const closeReportModalBtn = document.getElementById("closeReportModalBtn");
  const chatArea = document.getElementById("chatArea");
  const chatModal = document.getElementById("chatModal");
  const reportModal = document.getElementById("reportModal");
  const downloadForm = document.getElementById("downloadForm");
  const downloadName = document.getElementById("downloadName");
  const downloadPhone = document.getElementById("downloadPhone");
  const chatMessages = document.getElementById("chatMessages");
  const chatInput = document.getElementById("chatInput");
  const chatName = document.getElementById("chatName");
  const chatPhone = document.getElementById("chatPhone");
  const questionCounter = document.querySelector(".question-counter");

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  const existingChatName = getCookie("chat_name");
  const existingChatPhone = getCookie("chat_phone");
  if (existingChatName && existingChatPhone) {
    chatUnlocked = true;
  }

  function openChatModal() {
    if (chatUnlocked) {
      if (chatArea) chatArea.style.display = "block";
      return;
    }

    if (chatModal) chatModal.style.display = "flex";
  }

  function closeChatModal() {
    if (chatModal) chatModal.style.display = "none";
  }

  function openReportModal() {
    if (existingChatName && existingChatPhone && downloadForm && downloadName && downloadPhone) {
      downloadName.value = existingChatName;
      downloadPhone.value = existingChatPhone;
      downloadForm.submit();
      return;
    }

    if (reportModal) reportModal.style.display = "flex";
  }

  function closeReportModal() {
    if (reportModal) reportModal.style.display = "none";
  }

  async function unlockChat() {
    if (!chatName || !chatPhone) return;

    const name = chatName.value.trim();
    const phone = chatPhone.value.trim();

    if (!name || !phone) {
      alert("Please enter your details.");
      return;
    }

    try {
      await fetch("/chat-unlock", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name, phone }),
      });

      chatUnlocked = true;
      if (chatModal) chatModal.style.display = "none";
      if (chatArea) chatArea.style.display = "block";
    } catch (error) {
      alert("Unable to unlock CoreBuild AI.");
    }
  }

  async function sendQuestion() {
    if (questionsLeft <= 0) {
      alert("You've used all AI clarifications for this inspection.");
      return;
    }

    if (!chatInput || !chatMessages) return;

    const msg = chatInput.value.trim();
    if (!msg) return;

    chatMessages.innerHTML += `\n<div class="user-msg"><b>You</b> ${msg}</div>`;
    chatInput.value = "";
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: msg }),
      });

      const data = await response.json();
      questionsLeft = data.remaining;

      chatMessages.innerHTML += `\n<div class="ai-msg"><b>CoreBuild AI</b> ${data.reply}</div>`;
      if (questionCounter) {
        questionCounter.innerHTML = `${questionsLeft} / 3 Questions Remaining`;
      }

      if (questionsLeft <= 0) {
        chatMessages.innerHTML += `\n<div class="ai-msg"><b>CoreBuild AI</b> You have used all AI clarifications for this inspection. Please download your report or contact our technical team.</div>`;
      }

      chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (error) {
      chatMessages.innerHTML += `\n<div class="ai-msg"><b>CoreBuild AI</b> Unable to connect. Please try again.</div>`;
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  }

  if (openChatBtn) {
    openChatBtn.addEventListener("click", openChatModal);
  }

  if (sendChatBtn) {
    sendChatBtn.addEventListener("click", sendQuestion);
  }

  if (openReportModalBtn) {
    openReportModalBtn.addEventListener("click", openReportModal);
  }

  if (unlockChatBtn) {
    unlockChatBtn.addEventListener("click", unlockChat);
  }

  if (closeChatModalBtn) {
    closeChatModalBtn.addEventListener("click", closeChatModal);
  }

  if (closeReportModalBtn) {
    closeReportModalBtn.addEventListener("click", closeReportModal);
  }

  window.addEventListener("click", function (event) {
    if (event.target === reportModal) {
      closeReportModal();
    }
    if (event.target === chatModal) {
      closeChatModal();
    }
  });
});
