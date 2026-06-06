document.addEventListener("DOMContentLoaded", function () {
  const burgerMenu = document.getElementById("burgerMenu");
  const mobileOverlay = document.getElementById("mobileOverlay");
  const mobileMenu = document.getElementById("mobileMenu");
  const mobileLinks = mobileMenu ? mobileMenu.querySelectorAll(".mobile-link") : [];
  const inspectionFile = document.getElementById("inspectionFile");
  const uploadForm = document.getElementById("uploadForm");
  const selectedFile = document.getElementById("selectedFile");
  const scanOverlay = document.getElementById("scanOverlay");
  const scanText = document.getElementById("scanText");
  const openCameraBtn = document.getElementById("openCameraBtn");
  const openGalleryBtn = document.getElementById("openGalleryBtn");

  function toggleMenu() {
    if (mobileOverlay) {
      mobileOverlay.classList.toggle("show-overlay");
    }
  }

  function closeMenu() {
    if (mobileOverlay) {
      mobileOverlay.classList.remove("show-overlay");
    }
  }

  function openCamera() {
    if (!inspectionFile) return;
    inspectionFile.setAttribute("capture", "environment");
    inspectionFile.click();
  }

  function openGallery() {
    if (!inspectionFile) return;
    inspectionFile.removeAttribute("capture");
    inspectionFile.click();
  }

  if (burgerMenu) {
    burgerMenu.addEventListener("click", toggleMenu);
  }

  if (mobileOverlay) {
    mobileOverlay.addEventListener("click", closeMenu);
  }

  if (mobileMenu) {
    mobileMenu.addEventListener("click", function (event) {
      event.stopPropagation();
    });
  }

  mobileLinks.forEach(function (link) {
    link.addEventListener("click", closeMenu);
  });

  if (openCameraBtn) {
    openCameraBtn.addEventListener("click", openCamera);
  }

  if (openGalleryBtn) {
    openGalleryBtn.addEventListener("click", openGallery);
  }

  if (inspectionFile) {
    inspectionFile.addEventListener("change", function () {
      if (this.files && this.files.length > 0 && selectedFile) {
        selectedFile.innerHTML = "Selected: " + this.files[0].name;
      }
    });
  }

  if (uploadForm) {
    uploadForm.addEventListener("submit", function () {
      if (scanOverlay) {
        scanOverlay.style.display = "flex";
      }

      const messages = [
        "Uploading image...",
        "Scanning construction surface...",
        "Detecting visible defect...",
        "Analyzing root cause...",
        "Matching repair system...",
        "Preparing AI report..."
      ];

      let i = 0;

      setInterval(function () {
        i = (i + 1) % messages.length;
        if (scanText) {
          scanText.innerHTML = messages[i];
        }
      }, 850);
    });
  }
});
