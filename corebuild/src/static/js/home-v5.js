(() => {
  "use strict";

  const fileInput = document.getElementById("inspectionFile");
  const cameraBtn = document.getElementById("openCameraBtn");
  const galleryBtn = document.getElementById("openGalleryBtn");
  const changePhotoBtn = document.getElementById("changePhotoBtn");
  const pickerState = document.getElementById("pickerState");
  const previewState = document.getElementById("previewState");
  const previewImage = document.getElementById("previewImage");
  const selectedFileName = document.getElementById("selectedFileName");
  const uploadForm = document.getElementById("uploadForm");
  const analyzeButton = document.getElementById("analyzeButton");
  const mobileDock = document.getElementById("mobileDock");
  const dockAnalyze = document.getElementById("dockAnalyze");
  const scanOverlay = document.getElementById("scanOverlay");
  const scanText = document.getElementById("scanText");
  const burgerMenu = document.getElementById("burgerMenu");
  const closeMenuBtn = document.getElementById("closeMenuBtn");
  const mobileOverlay = document.getElementById("mobileOverlay");
  const mobileLinks = document.querySelectorAll(".mobile-link");
  let objectUrl = null;

  function setMenu(open) {
    if (!mobileOverlay || !burgerMenu) return;
    mobileOverlay.classList.toggle("open", open);
    mobileOverlay.setAttribute("aria-hidden", String(!open));
    burgerMenu.setAttribute("aria-expanded", String(open));
    document.body.classList.toggle("menu-open", open);
  }

  burgerMenu?.addEventListener("click", () => setMenu(true));
  closeMenuBtn?.addEventListener("click", () => setMenu(false));
  mobileOverlay?.addEventListener("click", (event) => {
    if (event.target === mobileOverlay) setMenu(false);
  });
  mobileLinks.forEach((link) => link.addEventListener("click", () => setMenu(false)));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setMenu(false);
  });

  function openPicker(useCamera) {
    if (!fileInput) return;
    if (useCamera) fileInput.setAttribute("capture", "environment");
    else fileInput.removeAttribute("capture");
    fileInput.value = "";
    fileInput.click();
  }

  cameraBtn?.addEventListener("click", () => openPicker(true));
  galleryBtn?.addEventListener("click", () => openPicker(false));
  changePhotoBtn?.addEventListener("click", () => openPicker(false));

  function showSelectedFile(file) {
    if (!file || !previewImage || !pickerState || !previewState) return;
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = URL.createObjectURL(file);
    previewImage.src = objectUrl;
    if (selectedFileName) selectedFileName.textContent = file.name || "Selected photo";
    pickerState.hidden = true;
    pickerState.style.display = "none";
    previewState.classList.add("active");
    mobileDock?.classList.add("photo-ready");

    window.setTimeout(() => {
      previewState.scrollIntoView({ behavior: "smooth", block: "center" });
      analyzeButton?.focus({ preventScroll: true });
    }, 120);
  }

  fileInput?.addEventListener("change", () => {
    const file = fileInput.files?.[0];
    if (file) showSelectedFile(file);
  });

  dockAnalyze?.addEventListener("click", () => {
    if (fileInput?.files?.[0]) analyzeButton?.click();
    else document.getElementById("corebuild-ai")?.scrollIntoView({ behavior: "smooth" });
  });

  uploadForm?.addEventListener("submit", (event) => {
    const file = fileInput?.files?.[0];
    if (!file) {
      event.preventDefault();
      openPicker(false);
      return;
    }

    scanOverlay?.classList.add("active");
    scanOverlay?.setAttribute("aria-hidden", "false");
    const messages = [
      "Preparing image…",
      "Checking visible defect patterns…",
      "Building preliminary diagnosis…",
      "Preparing repair direction…"
    ];
    let index = 0;
    if (scanText) scanText.textContent = messages[0];
    window.setInterval(() => {
      index = Math.min(index + 1, messages.length - 1);
      if (scanText) scanText.textContent = messages[index];
    }, 1550);
  });
})();
