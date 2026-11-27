(function () {
  "use strict";

  const sidebar = document.querySelector("#admin-sidebar");
  const menuToggle = document.querySelector(".admin-menu-toggle");
  const sidebarOverlay = document.querySelector(".admin-sidebar-overlay");

  function setSidebarOpen(isOpen) {
    if (!sidebar || !menuToggle || !sidebarOverlay) {
      return;
    }
    sidebar.classList.toggle("is-open", isOpen);
    sidebarOverlay.hidden = !isOpen;
    menuToggle.setAttribute("aria-expanded", String(isOpen));
    menuToggle.setAttribute("aria-label", isOpen ? "Fechar menu administrativo" : "Abrir menu administrativo");
  }

  if (menuToggle) {
    menuToggle.addEventListener("click", function () {
      setSidebarOpen(menuToggle.getAttribute("aria-expanded") !== "true");
    });
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", function () {
      setSidebarOpen(false);
    });
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      setSidebarOpen(false);
    }
  });

  const search = document.querySelector("#admin-list-search");
  const rows = document.querySelectorAll("[data-record-row]");
  const count = document.querySelector("#admin-record-count");
  const emptyRow = document.querySelector("#admin-empty-row");

  if (search && count) {
    search.addEventListener("input", function () {
      const query = search.value.trim().toLocaleLowerCase("pt");
      let visible = 0;
      rows.forEach(function (row) {
        const matches = row.textContent.toLocaleLowerCase("pt").includes(query);
        row.hidden = !matches;
        if (matches) {
          visible += 1;
        }
      });
      count.textContent = String(visible);
      if (emptyRow) {
        emptyRow.hidden = visible !== 0 || rows.length === 0;
      }
    });
  }
})();
