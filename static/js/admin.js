(function () {
  "use strict";

  const sidebar = document.querySelector("#admin-sidebar");
  const menuToggle = document.querySelector(".admin-menu-toggle");
  const sidebarOverlay = document.querySelector(".admin-sidebar-overlay");
  const toast = document.querySelector("#admin-toast");
  let toastTimer;

  function showToast(message) {
    if (!toast) {
      return;
    }
    toast.textContent = message;
    toast.classList.add("is-visible");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(function () {
      toast.classList.remove("is-visible");
    }, 3500);
  }

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

  const modal = document.querySelector("#admin-record-modal");
  const form = document.querySelector("#admin-record-form");
  const table = document.querySelector("#admin-record-table");
  const rows = document.querySelector("#admin-record-rows");
  const search = document.querySelector("#admin-list-search");
  const count = document.querySelector("#admin-record-count");
  const emptyRow = document.querySelector("#admin-empty-row");
  let opener = null;
  let editingId = null;
  let records = [];
  let columns = [];

  if (table && rows && form && modal) {
    const dataElement = document.querySelector("#admin-record-data");
    records = dataElement ? JSON.parse(dataElement.textContent) : [];
    columns = JSON.parse(table.dataset.columns || "[]");

    function openModal(record, trigger) {
      opener = trigger || document.activeElement;
      editingId = record ? record.id : null;
      form.reset();
      form.elements.id.value = record ? record.id : "";
      form.querySelectorAll("[name]").forEach(function (field) {
        if (field.name === "id" || field.type === "file") {
          return;
        }
        field.value = record && record[field.name] !== undefined ? record[field.name] : "";
      });

      const fileName = document.querySelector("#admin-file-name");
      if (fileName) {
        fileName.textContent = record && record.file
          ? "Ficheiro de demonstração: " + record.file + ". O upload não está activo."
          : "Selecção visual apenas; o ficheiro não será enviado.";
      }

      const modalTitle = document.querySelector("#admin-modal-title");
      if (modalTitle) {
        modalTitle.textContent = record ? "Editar conteúdo" : "Adicionar conteúdo";
      }
      modal.hidden = false;
      document.body.classList.add("admin-modal-open");
      const firstField = form.querySelector("input:not([type='hidden']), select, textarea");
      if (firstField) {
        firstField.focus();
      }
    }

    function closeModal() {
      if (!modal || modal.hidden) {
        return;
      }
      modal.hidden = true;
      document.body.classList.remove("admin-modal-open");
      if (opener && typeof opener.focus === "function") {
        opener.focus();
      }
    }

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closeModal();
      }
    });

    function buildCell(record, column) {
      const cell = document.createElement("td");
      const value = record[column.key] === undefined ? "" : record[column.key];

      if (column.key === "title" || column.key === "name") {
        const title = document.createElement("span");
        title.className = "admin-cell-title";
        title.textContent = String(value);
        const subtitle = document.createElement("span");
        subtitle.className = "admin-cell-subtitle";
        subtitle.textContent = record.description || record.excerpt || record.category || record.slug || "";
        cell.append(title, subtitle);
      } else if (column.key === "status") {
        const status = document.createElement("span");
        status.className = "admin-status status-" + String(value).toLocaleLowerCase("pt").replaceAll(" ", "-");
        status.textContent = String(value);
        cell.append(status);
      } else {
        cell.textContent = String(value);
      }
      return cell;
    }

    function renderRecords(query) {
      const normalizedQuery = (query || "").trim().toLocaleLowerCase("pt");
      const filtered = records.filter(function (record) {
        return Object.values(record).join(" ").toLocaleLowerCase("pt").includes(normalizedQuery);
      });

      rows.replaceChildren(emptyRow);
      emptyRow.hidden = filtered.length !== 0;
      count.textContent = String(filtered.length);

      filtered.forEach(function (record) {
        const row = document.createElement("tr");
        row.dataset.id = String(record.id);
        columns.forEach(function (column) {
          row.append(buildCell(record, column));
        });

        const actions = document.createElement("td");
        actions.className = "admin-row-actions";
        const edit = document.createElement("button");
        edit.className = "admin-icon-button";
        edit.type = "button";
        edit.dataset.action = "edit";
        edit.dataset.id = String(record.id);
        edit.setAttribute("aria-label", "Editar " + (record.title || record.name || ""));
        edit.title = "Editar";
        edit.innerHTML = '<i class="bi bi-pencil" aria-hidden="true"></i>';

        const remove = document.createElement("button");
        remove.className = "admin-icon-button admin-icon-danger";
        remove.type = "button";
        remove.dataset.action = "delete";
        remove.dataset.id = String(record.id);
        remove.setAttribute("aria-label", "Remover " + (record.title || record.name || ""));
        remove.title = "Remover";
        remove.innerHTML = '<i class="bi bi-trash3" aria-hidden="true"></i>';
        actions.append(edit, remove);
        row.append(actions);
        rows.insertBefore(row, emptyRow);
      });
    }

    rows.addEventListener("click", function (event) {
      const button = event.target.closest("button[data-action]");
      if (!button) {
        return;
      }
      const record = records.find(function (item) {
        return String(item.id) === button.dataset.id;
      });
      if (!record) {
        return;
      }
      if (button.dataset.action === "edit") {
        openModal(record, button);
      } else if (button.dataset.action === "delete" && window.confirm("Remover este item apenas da demonstração actual?")) {
        records = records.filter(function (item) {
          return String(item.id) !== button.dataset.id;
        });
        renderRecords(search ? search.value : "");
        showToast("Item removido apenas desta demonstração. Nada foi gravado.");
      }
    });

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      const formData = new FormData(form);
      const record = {};
      formData.forEach(function (value, key) {
        if (key !== "id") {
          record[key] = value;
        }
      });

      const fileInput = form.querySelector('input[type="file"]');
      if (fileInput) {
        const selectedFile = fileInput.files && fileInput.files[0];
        const previousRecord = records.find(function (item) {
          return String(item.id) === String(editingId);
        });
        record.file = selectedFile ? selectedFile.name : (previousRecord ? previousRecord.file : "");
      }

      if (editingId !== null) {
        record.id = editingId;
        const index = records.findIndex(function (item) {
          return String(item.id) === String(editingId);
        });
        if (index !== -1) {
          records[index] = Object.assign({}, records[index], record, {updated: "Agora"});
        }
      } else {
        record.id = records.reduce(function (max, item) {
          return Math.max(max, Number(item.id) || 0);
        }, 0) + 1;
        record.updated = "Agora";
        if (columns.some(function (column) { return column.key === "status"; })) {
          record.status = "Rascunho";
        }
        if (columns.some(function (column) { return column.key === "count"; })) {
          record.count = 0;
        }
        records.unshift(record);
      }

      // Replace this in-memory demo update with authenticated CRUD/API calls when a backend is introduced.
      renderRecords(search ? search.value : "");
      closeModal();
      showToast("Demonstração actualizada neste navegador. Recarregar restaura os dados de exemplo.");
    });

    if (search) {
      search.addEventListener("input", function () {
        renderRecords(search.value);
      });
    }

    modal.addEventListener("click", function (event) {
      if (event.target.closest("[data-close-modal]")) {
        closeModal();
      }
    });

    const fileInput = form.querySelector('input[type="file"]');
    if (fileInput) {
      fileInput.addEventListener("change", function () {
        const fileName = document.querySelector("#admin-file-name");
        if (fileName && fileInput.files && fileInput.files[0]) {
          fileName.textContent = "Ficheiro seleccionado: " + fileInput.files[0].name + ". Não será enviado nesta demonstração.";
        }
      });
    }

    renderRecords("");
    if (modal.dataset.open === "true") {
      const initialRecord = modal.dataset.initialRecord
        ? JSON.parse(modal.dataset.initialRecord)
        : null;
      openModal(initialRecord, null);
    }
  }

  const settingsForm = document.querySelector("#admin-settings-form");
  if (settingsForm) {
    settingsForm.addEventListener("submit", function (event) {
      event.preventDefault();
      showToast("Alterações de demonstração mantidas apenas até recarregar a página.");
    });
  }
})();
