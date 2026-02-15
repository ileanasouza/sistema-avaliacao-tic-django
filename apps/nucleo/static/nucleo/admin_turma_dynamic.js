(function () {
  function qs(sel) {
    return document.querySelector(sel);
  }

  function setSelectOptions(selectEl, placeholderText, items, selectedValue) {
    if (!selectEl) return;

    // limpa
    while (selectEl.firstChild) selectEl.removeChild(selectEl.firstChild);

    // placeholder
    const opt0 = document.createElement("option");
    opt0.value = "";
    opt0.textContent = placeholderText;
    selectEl.appendChild(opt0);

    // opções
    (items || []).forEach((it) => {
      const opt = document.createElement("option");
      opt.value = it.value;
      opt.textContent = it.label;
      selectEl.appendChild(opt);
    });

    if (selectedValue) {
      selectEl.value = selectedValue;
    }
  }

  async function fetchOptions(baseUrl, tipo, ciclo) {
    const url = new URL(baseUrl, window.location.origin);
    if (tipo) url.searchParams.set("tipo", tipo);
    if (ciclo) url.searchParams.set("ciclo", ciclo);
    const resp = await fetch(url.toString(), { headers: { "X-Requested-With": "XMLHttpRequest" } });
    if (!resp.ok) throw new Error("Falha ao obter opções");
    return await resp.json();
  }

  function findDynamicUrl() {
    // Admin: URL base atual termina com /add/ ou /<id>/change/
    // Nosso endpoint está em ../dynamic-options/
    // Ex.: /admin/nucleo/turma/add/ -> /admin/nucleo/turma/dynamic-options/
    const href = window.location.href;
    if (href.includes("/add/")) return href.replace("/add/", "/dynamic-options/");
    if (href.includes("/change/")) return href.replace(/\/\d+\/change\/.*/, "/dynamic-options/");
    return null;
  }

  document.addEventListener("DOMContentLoaded", async function () {
    const tipoEl = qs("#id_tipo_contexto");
    const cicloEl = qs("#id_ciclo");
    const anoEl = qs("#id_ano_escolaridade");

    if (!tipoEl || !cicloEl || !anoEl) return;

    const dynamicUrl = findDynamicUrl();
    if (!dynamicUrl) return;

    async function updateCicloEAno({ preserveCiclo = true, preserveAno = true } = {}) {
      const tipo = tipoEl.value || "";
      let ciclo = cicloEl.value || "";

      // Sem tipo -> placeholders
      if (!tipo) {
        setSelectOptions(cicloEl, "— Selecione o Tipo de contexto primeiro —", [], "");
        setSelectOptions(anoEl, "— Selecione o Ciclo primeiro —", [], "");
        cicloEl.disabled = true;
        anoEl.disabled = true;
        return;
      }

      cicloEl.disabled = false;

      const data = await fetchOptions(dynamicUrl, tipo, ciclo);

      // popula ciclo
      const cicloSelecionado = preserveCiclo ? (cicloEl.value || data.ciclo || "") : (data.ciclo || "");
      setSelectOptions(cicloEl, "— Selecione —", data.ciclos, cicloSelecionado);

      // se ciclo foi forçado (secundário), trava
      cicloEl.disabled = !!data.ciclo_forcado;

      // define ciclo final para buscar anos
      ciclo = cicloEl.value || data.ciclo || "";

      // popula anos
      const anoSelecionado = preserveAno ? (anoEl.value || "") : "";
      setSelectOptions(anoEl, ciclo ? "— Selecione —" : "— Selecione o Ciclo primeiro —", data.anos, anoSelecionado);

      anoEl.disabled = !ciclo;
    }

    // 1) Estado inicial (add/change)
    try {
      await updateCicloEAno({ preserveCiclo: true, preserveAno: true });
    } catch (e) {
      // se der erro, não bloqueia a página
      console.warn(e);
    }

    // 2) Mudou tipo -> atualiza ciclo e limpa ano
    tipoEl.addEventListener("change", async function () {
      try {
        // ao mudar tipo, resetamos ciclo/ano
        cicloEl.value = "";
        anoEl.value = "";
        await updateCicloEAno({ preserveCiclo: false, preserveAno: false });
      } catch (e) {
        console.warn(e);
      }
    });

    // 3) Mudou ciclo -> atualiza anos
    cicloEl.addEventListener("change", async function () {
      try {
        anoEl.value = "";
        await updateCicloEAno({ preserveCiclo: true, preserveAno: false });
      } catch (e) {
        console.warn(e);
      }
    });
  });
})();


