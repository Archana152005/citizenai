// Mobile menu toggle
document.addEventListener("DOMContentLoaded", () => {
  const menuBtn = document.getElementById("mobileMenuBtn");
  const mobileMenu = document.getElementById("mobileMenuPanel");
  
  if (menuBtn && mobileMenu) {
    const panel = mobileMenu.querySelector("div");
    const closeBtn = mobileMenu.querySelector("#closeMobileMenu");
    
    function openMenu() {
      mobileMenu.classList.remove("hidden");
      panel.classList.remove("translate-x-full");
    }
    
    function closeMenu() {
      panel.classList.add("translate-x-full");
      setTimeout(() => {
        mobileMenu.classList.add("hidden");
      }, 300);
    }
    
    menuBtn.addEventListener("click", openMenu);
    closeBtn.addEventListener("click", closeMenu);
    mobileMenu.addEventListener("click", (e) => {
      if (e.target === mobileMenu) closeMenu();
    });
    
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeMenu();
    });
  }
});