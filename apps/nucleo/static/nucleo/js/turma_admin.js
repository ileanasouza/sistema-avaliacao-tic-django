(function () {
  function byId(id) {
    return document.getElementById(id);
  }

  function setOptionVisibility(selectEl, allowedValues) {
    const allowed = new Set(allowedValues);

    // percorre options e esconde/desabilita as não permitidas
    Array.from(selectEl.options).forEach((opt) => {
      if (!opt.value) {
        // mantém placeholder sempre visível
        opt.hidden = false;
        opt.disabled = false;
        return;
      }
      const ok = allowed.has(opt.value) || allowed.has(Number(opt.value));
      opt.hidden = !ok;
      opt.disabled = !ok;
    });

    // se o valor atual não é permitido, limpa
    const current = selectEl.value;
    if (current && !allowed.has(current) && !allowed.has(Number(current))) {
      selectEl.value = "";
    }
  }

  function applyRules() {
    const tipo = byId("id_tipo_contexto");
    const ciclo = byId("id_ciclo");
    const ano = byId("id_ano_escolaridade");

    if (!tipo || !ciclo || !ano) return;

    const t = tipo.value;

    // Defaults: nada liberado até selecionar Tipo
    let ciclosPermitidos = [];
    let anosPermitidos = [];

    if (!t) {
      setOptionVisibility(ciclo, []);
      setOptionVisibility(ano, []);
      return;
    }

    if (t === "ENSINO_BASICO_TIC") {
      ciclosPermitidos = ["2C", "3C"];
    } else if (t === "ENSINO_SECUNDARIO") {
      ciclosPermitidos = ["SEC"];
      // força ciclo para SEC
      ciclo.value = "SEC";
    } else if (t === "ENSINO_PROFISSIONAL_UFCD") {
      ciclosPermitidos = ["2C", "3C", "SEC"];
    }

    setOptionVisibility(ciclo, ciclosPermitidos);

    const c = ciclo.value;

    if (!c) {
      setOptionVisibility(ano, []);
      return;
    }

    if (c === "2C") anosPermitidos = [5, 6];
    if (c === "3C") anosPermitidos = [7, 8, 9];
    if (c === "SEC") anosPermitidos = [10, 11, 12];

    setOptionVisibility(ano, anosPermitidos);
  }

  document.addEventListener("DOMContentLoaded", function () {
    const tipo = byId("id_tipo_contexto");
    const ciclo = byId("id_ciclo");

    if (tipo) {
      tipo.addEventListener("change", function () {
        // ao mudar tipo, limpa ciclo e ano e reaplica regras
        const c = byId("id_ciclo");
        const a = byId("id_ano_escolaridade");
        if (c) c.value = "";
        if (a) a.value = "";
        applyRules();
      });
    }

    if (ciclo) {
      ciclo.addEventListener("change", function () {
        // ao mudar ciclo, limpa ano e reaplica
        const a = byId("id_ano_escolaridade");
        if (a) a.value = "";
        applyRules();
      });
    }

    // aplica na carga inicial (GET) e também quando volta com erros (POST)
    applyRules();
  });
})();

