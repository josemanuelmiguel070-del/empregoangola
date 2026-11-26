(function () {
  "use strict";

  const body = document.body;
  const menuToggle = document.querySelector(".mobile-nav-toggle");
  const navigation = document.querySelector("#navmenu");
  const scrollTop = document.querySelector(".scroll-top");
  const themeToggle = document.querySelector(".theme-toggle");
  const themeStorageKey = "emprego-angola-theme";

  function getInitialTheme() {
    const savedTheme = window.localStorage.getItem(themeStorageKey);
    if (savedTheme === "light" || savedTheme === "dark") {
      return savedTheme;
    }
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function updateThemeControl(theme) {
    if (!themeToggle) {
      return;
    }
    const isDark = theme === "dark";
    const icon = themeToggle.querySelector("i");
    themeToggle.setAttribute("aria-label", isDark ? "Activar modo claro" : "Activar modo escuro");
    themeToggle.setAttribute("title", isDark ? "Modo claro" : "Modo escuro");
    themeToggle.setAttribute("aria-pressed", String(isDark));
    if (icon) {
      icon.classList.toggle("bi-moon-stars", !isDark);
      icon.classList.toggle("bi-sun", isDark);
    }
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    updateThemeControl(theme);
  }

  applyTheme(getInitialTheme());

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      const nextTheme =
        document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      window.localStorage.setItem(themeStorageKey, nextTheme);
      applyTheme(nextTheme);
    });
  }

  function setMenuOpen(isOpen) {
    body.classList.toggle("mobile-nav-active", isOpen);
    if (menuToggle) {
      menuToggle.setAttribute("aria-expanded", String(isOpen));
      menuToggle.setAttribute("aria-label", isOpen ? "Fechar menu" : "Abrir menu");
      const icon = menuToggle.querySelector("i");
      if (icon) {
        icon.classList.toggle("bi-list", !isOpen);
        icon.classList.toggle("bi-x", isOpen);
      }
    }
  }

  if (menuToggle && navigation) {
    menuToggle.addEventListener("click", function () {
      setMenuOpen(menuToggle.getAttribute("aria-expanded") !== "true");
    });

    navigation.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        setMenuOpen(false);
      });
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && body.classList.contains("mobile-nav-active")) {
        setMenuOpen(false);
        menuToggle.focus();
      }
    });

    document.addEventListener("click", function (event) {
      if (body.classList.contains("mobile-nav-active") &&
          !navigation.contains(event.target) &&
          !menuToggle.contains(event.target)) {
        setMenuOpen(false);
      }
    });
  }

  function updateScrollTop() {
    if (scrollTop) {
      scrollTop.classList.toggle("active", window.scrollY > 320);
    }
  }

  if (scrollTop) {
    window.addEventListener("scroll", updateScrollTop, { passive: true });
    updateScrollTop();
  }

  const year = document.querySelector("#current-year");
  if (year) {
    year.textContent = String(new Date().getFullYear());
  }

  const listingSearch = document.querySelector(".listing-search");
  const listingInput = document.querySelector("#listing-query");
  const searchStatus = document.querySelector(".search-status");
  const searchableCards = Array.from(document.querySelectorAll(".searchable-card"));

  if (listingSearch && listingInput && searchStatus && searchableCards.length) {
    const queryFromUrl = new URLSearchParams(window.location.search).get("q") || "";
    listingInput.value = queryFromUrl;

    function filterListings(query) {
      const normalizedQuery = query.trim().toLocaleLowerCase("pt");
      let visibleCount = 0;

      searchableCards.forEach(function (card) {
        const matches = !normalizedQuery ||
          card.textContent.toLocaleLowerCase("pt").includes(normalizedQuery);
        card.hidden = !matches;
        if (matches) {
          visibleCount += 1;
        }
      });

      if (!normalizedQuery) {
        searchStatus.textContent = "";
      } else if (visibleCount === 0) {
        searchStatus.textContent = "Não foram encontrados conteúdos para esta pesquisa.";
      } else {
        searchStatus.textContent = visibleCount === 1
          ? "1 conteúdo encontrado."
          : visibleCount + " conteúdos encontrados.";
      }
    }

    listingSearch.addEventListener("submit", function (event) {
      event.preventDefault();
      const query = listingInput.value.trim();
      const url = new URL(window.location.href);
      if (query) {
        url.searchParams.set("q", query);
      } else {
        url.searchParams.delete("q");
      }
      window.history.replaceState({}, "", url);
      filterListings(query);
    });

    filterListings(queryFromUrl);
  }
})();
