const navToggle = document.querySelector("[data-nav-toggle]");
const navMenu = document.querySelector("[data-nav-menu]");
const yearTarget = document.getElementById("current-year");
const revealItems = document.querySelectorAll("[data-reveal]");
const centeredLayouts = document.querySelectorAll("[data-centered-layout]");
const passwordToggles = document.querySelectorAll("[data-password-toggle]");

if (navToggle && navMenu) {
  const closeMenu = () => {
    navMenu.classList.remove("is-open");
    navToggle.setAttribute("aria-expanded", "false");
  };

  navToggle.addEventListener("click", () => {
    navMenu.classList.toggle("is-open");
    navToggle.setAttribute(
      "aria-expanded",
      navMenu.classList.contains("is-open") ? "true" : "false"
    );
  });

  navMenu.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", closeMenu);
  });

  document.addEventListener("click", (event) => {
    if (!navMenu.contains(event.target) && !navToggle.contains(event.target)) {
      closeMenu();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeMenu();
    }
  });
}

if (yearTarget) {
  yearTarget.textContent = new Date().getFullYear();
}

passwordToggles.forEach((toggle) => {
  const field = toggle.closest(".password-field");
  const input = field ? field.querySelector("[data-password-input]") : null;

  if (!input) return;

  toggle.addEventListener("click", () => {
    const isVisible = input.type === "text";
    input.type = isVisible ? "password" : "text";
    toggle.classList.toggle("is-visible", !isVisible);
    toggle.setAttribute("aria-pressed", isVisible ? "false" : "true");
    toggle.setAttribute("aria-label", isVisible ? "Show password" : "Hide password");
    input.focus({ preventScroll: true });

    if (typeof input.setSelectionRange === "function") {
      input.setSelectionRange(input.value.length, input.value.length);
    }
  });
});

if ("IntersectionObserver" in window && revealItems.length > 0) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.05 }
  );

  revealItems.forEach((item, index) => {
    item.style.transitionDelay = `${index * 70}ms`;
    observer.observe(item);
  });
} else {
  revealItems.forEach((item) => item.classList.add("is-visible"));
}

if (centeredLayouts.length > 0) {
  const syncCenteredLayoutHeight = () => {
    if (window.innerWidth <= 820) {
      centeredLayouts.forEach((layout) => {
        layout.style.removeProperty("--centered-layout-height");
      });
      return;
    }

    const shell = document.querySelector(".site-shell");
    const header = document.querySelector(".topbar");
    const footer = document.querySelector(".footer");
    const flashWrap = document.querySelector(".flash-wrap");

    if (!shell || !header || !footer) return;

    const shellStyles = window.getComputedStyle(shell);
    const shellPaddingTop = parseFloat(shellStyles.paddingTop) || 0;
    const shellPaddingBottom = parseFloat(shellStyles.paddingBottom) || 0;
    const headerHeight = header.getBoundingClientRect().height;
    const footerHeight = footer.getBoundingClientRect().height;
    const flashHeight = flashWrap ? flashWrap.getBoundingClientRect().height : 0;
    const reservedSpace =
      shellPaddingTop +
      shellPaddingBottom +
      headerHeight +
      footerHeight +
      flashHeight +
      48;

    centeredLayouts.forEach((layout) => {
      const availableHeight = Math.max(
        layout.scrollHeight,
        Math.floor(window.innerHeight - reservedSpace)
      );

      if (availableHeight > 0) {
        layout.style.setProperty("--centered-layout-height", `${availableHeight}px`);
      }
    });
  };

  window.addEventListener("load", syncCenteredLayoutHeight);
  window.addEventListener("resize", syncCenteredLayoutHeight);
  window.addEventListener("orientationchange", syncCenteredLayoutHeight);
  syncCenteredLayoutHeight();
}

const contactDock = document.querySelector(".contact-dock");
const contactDockAnchor = document.querySelector(".contact-dock-anchor");
const siteShell = document.querySelector(".site-shell");
const pageFooter = document.querySelector(".footer");

if (contactDock && contactDockAnchor && siteShell && pageFooter) {
  const mobileBreakpoint = 820;
  let dockSyncFrame = null;

  const resetContactDockBelowFooter = () => {
    contactDock.classList.remove("contact-dock--below-footer");
    siteShell.classList.remove("contact-dock-is-below-footer");
    siteShell.style.removeProperty("--contact-dock-anchor-top");
  };

  const syncContactDock = () => {
    dockSyncFrame = null;

    const dockHeight = Math.ceil(contactDock.getBoundingClientRect().height);
    const dockStyles = window.getComputedStyle(contactDock);
    const dockGap = parseFloat(
      dockStyles.getPropertyValue("--contact-dock-mobile-gap")
    ) || 0;

    siteShell.style.setProperty("--contact-dock-height", `${dockHeight}px`);
    siteShell.style.setProperty("--contact-dock-mobile-gap", `${dockGap}px`);

    if (window.innerWidth > mobileBreakpoint) {
      resetContactDockBelowFooter();
      return;
    }

    const footerRect = pageFooter.getBoundingClientRect();
    const dockThreshold = window.innerHeight - dockHeight - dockGap;
    const shouldMoveBelowFooter = footerRect.top <= dockThreshold;

    if (!shouldMoveBelowFooter) {
      resetContactDockBelowFooter();
      return;
    }

    siteShell.style.setProperty(
      "--contact-dock-anchor-top",
      `${contactDockAnchor.offsetTop}px`
    );
    siteShell.classList.add("contact-dock-is-below-footer");
    contactDock.classList.add("contact-dock--below-footer");
  };

  const scheduleContactDockSync = () => {
    if (dockSyncFrame !== null) return;
    dockSyncFrame = window.requestAnimationFrame(syncContactDock);
  };

  window.addEventListener("load", scheduleContactDockSync);
  window.addEventListener("resize", scheduleContactDockSync);
  window.addEventListener("orientationchange", scheduleContactDockSync);
  window.addEventListener("scroll", scheduleContactDockSync, { passive: true });
  scheduleContactDockSync();
}

document.querySelectorAll("[data-gallery-slider]").forEach((slider) => {
  const slides = Array.from(slider.querySelectorAll("[data-gallery-slide]"));
  const copies = Array.from(slider.querySelectorAll("[data-gallery-copy]"));
  const dots = Array.from(slider.querySelectorAll("[data-gallery-dot]"));
  const prevButton = slider.querySelector("[data-gallery-prev]");
  const nextButton = slider.querySelector("[data-gallery-next]");
  const autoplayDelay = Number(slider.dataset.autoplay || 2600);
  let activeIndex = 0;
  let autoplayId = null;

  if (slides.length <= 1) {
    if (prevButton) prevButton.hidden = true;
    if (nextButton) nextButton.hidden = true;
    return;
  }

  const renderSlide = (index) => {
    activeIndex = (index + slides.length) % slides.length;

    slides.forEach((slide, slideIndex) => {
      const isActive = slideIndex === activeIndex;
      slide.classList.toggle("is-active", isActive);
      slide.setAttribute("aria-hidden", isActive ? "false" : "true");
    });

    copies.forEach((copy, copyIndex) => {
      copy.classList.toggle("is-active", copyIndex === activeIndex);
    });

    dots.forEach((dot, dotIndex) => {
      dot.classList.toggle("is-active", dotIndex === activeIndex);
      dot.setAttribute("aria-pressed", dotIndex === activeIndex ? "true" : "false");
    });
  };

  const stopAutoplay = () => {
    if (autoplayId) {
      window.clearInterval(autoplayId);
      autoplayId = null;
    }
  };

  const startAutoplay = () => {
    stopAutoplay();
    autoplayId = window.setInterval(() => {
      renderSlide(activeIndex + 1);
    }, autoplayDelay);
  };

  if (prevButton) {
    prevButton.addEventListener("click", () => {
      renderSlide(activeIndex - 1);
      startAutoplay();
    });
  }

  if (nextButton) {
    nextButton.addEventListener("click", () => {
      renderSlide(activeIndex + 1);
      startAutoplay();
    });
  }

  dots.forEach((dot) => {
    dot.addEventListener("click", () => {
      renderSlide(Number(dot.dataset.galleryIndex || 0));
      startAutoplay();
    });
  });

  slider.addEventListener("mouseenter", stopAutoplay);
  slider.addEventListener("mouseleave", startAutoplay);
  slider.addEventListener("focusin", stopAutoplay);
  slider.addEventListener("focusout", startAutoplay);

  let touchStartX = null;
  slider.addEventListener("touchstart", (e) => {
    touchStartX = e.touches[0].clientX;
  }, { passive: true });
  slider.addEventListener("touchend", (e) => {
    if (touchStartX === null) return;
    const delta = e.changedTouches[0].clientX - touchStartX;
    touchStartX = null;
    if (Math.abs(delta) < 40) return;
    renderSlide(delta < 0 ? activeIndex + 1 : activeIndex - 1);
    startAutoplay();
  }, { passive: true });

  renderSlide(0);
  startAutoplay();
});
