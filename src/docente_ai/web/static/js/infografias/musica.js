// Módulo local: responsabilidad separada sin alterar el contenido.

export function renderStaffSvg(type) {
  const lines = [8, 14, 20, 26, 32].map(y => [
    `<line x1="24" y1="${y}" x2="315" y2="${y}" stroke="#cbd5e1" stroke-width="1.2"/>`
  ].join('')).join('');
  let content = '';
  switch (type) {
    case 'superius_cf':
      content = [
        `\n        <text x="6" y="27" font-size="22" font-family="serif" fill="#475569">`,
        `𝄞</text>\n        <ellipse cx="48" cy="20" rx="4.5" ry="3.5" fill="#1e293b" `,
        `transform="rotate(-15 48 20)"/><line x1="52" y1="20" x2="52" y2="6" `,
        `stroke="#1e293b" stroke-width="1.5"/>\n        <ellipse cx="78" cy="14" rx="4.5" `,
        `ry="3.5" fill="#1e293b" transform="rotate(-15 78 14)"/><line x1="82" y1="14" `,
        `x2="82" y2="2" stroke="#1e293b" stroke-width="1.5"/>\n        <ellipse cx="108" `,
        `cy="17" rx="4.5" ry="3.5" fill="#1e293b" transform="rotate(-15 108 17)"/><line `,
        `x1="112" y1="17" x2="112" y2="4" stroke="#1e293b" stroke-width="1.5"/>\n        `,
        `<ellipse cx="138" cy="23" rx="4.5" ry="3.5" fill="#1e293b" transform="rotate(-15 `,
        `138 23)"/><line x1="142" y1="23" x2="142" y2="9" stroke="#1e293b" `,
        `stroke-width="1.5"/>\n        <ellipse cx="172" cy="20" rx="4.5" ry="3.5" `,
        `fill="#1e293b" transform="rotate(-15 172 20)"/><line x1="176" y1="20" x2="176" `,
        `y2="6" stroke="#1e293b" stroke-width="1.5"/>\n        <ellipse cx="206" cy="14" `,
        `rx="4.5" ry="3.5" fill="#1e293b" transform="rotate(-15 206 14)"/><line x1="210" `,
        `y1="14" x2="210" y2="2" stroke="#1e293b" stroke-width="1.5"/>\n        <ellipse `,
        `cx="240" cy="8" rx="5" ry="4" fill="#ffffff" stroke="#1e293b" stroke-width="1.8" `,
        `transform="rotate(-15 240 8)"/><line x1="244" y1="8" x2="244" y2="-4" `,
        `stroke="#1e293b" stroke-width="1.5"/>\n        <ellipse cx="280" cy="14" `,
        `rx="5.5" ry="4" fill="#ffffff" stroke="#1e293b" stroke-width="2"/>\n      `
      ].join('');
      break;
    case 'altus_cf':
      content = [
        `\n        <text x="6" y="25" font-size="18" font-family="serif" fill="#475569">`,
        `𝄡</text>\n        <ellipse cx="54" cy="26" rx="4.5" ry="3.5" fill="#334155" `,
        `transform="rotate(-15 54 26)"/><line x1="58" y1="26" x2="58" y2="12" `,
        `stroke="#334155" stroke-width="1.5"/>\n        <ellipse cx="94" cy="20" rx="4.5" `,
        `ry="3.5" fill="#334155" transform="rotate(-15 94 20)"/><line x1="98" y1="20" `,
        `x2="98" y2="6" stroke="#334155" stroke-width="1.5"/>\n        <ellipse cx="134" `,
        `cy="23" rx="4.5" ry="3.5" fill="#334155" transform="rotate(-15 134 23)"/><line `,
        `x1="138" y1="23" x2="138" y2="9" stroke="#334155" stroke-width="1.5"/>\n        `,
        `<ellipse cx="180" cy="26" rx="5" ry="4" fill="#ffffff" stroke="#334155" `,
        `stroke-width="1.8"/>\n        <ellipse cx="230" cy="20" rx="5" ry="4" `,
        `fill="#ffffff" stroke="#334155" stroke-width="1.8"/>\n        <ellipse cx="280" `,
        `cy="23" rx="5.5" ry="4" fill="#ffffff" stroke="#334155" stroke-width="2"/>\n      `
      ].join('');
      break;
    case 'tenor_cf':
      content = [
        `\n        <text x="6" y="25" font-size="18" font-family="serif" fill="#b45309">`,
        `𝄡</text>\n        <rect x="55" y="16" width="16" height="8" fill="#ffffff" `,
        `stroke="#b45309" stroke-width="2.2" rx="1.5"/><line x1="71" y1="16" x2="71" `,
        `y2="35" stroke="#b45309" stroke-width="2.2"/>\n        <rect x="135" y="13" `,
        `width="16" height="8" fill="#ffffff" stroke="#b45309" stroke-width="2.2" `,
        `rx="1.5"/><line x1="151" y1="13" x2="151" y2="32" stroke="#b45309" `,
        `stroke-width="2.2"/>\n        <rect x="215" y="19" width="16" height="8" `,
        `fill="#ffffff" stroke="#b45309" stroke-width="2.2" rx="1.5"/><line x1="231" `,
        `y1="19" x2="231" y2="38" stroke="#b45309" stroke-width="2.2"/>\n        <rect `,
        `x="280" y="16" width="20" height="8" fill="#ffffff" stroke="#b45309" `,
        `stroke-width="2.5" rx="1.5"/><line x1="300" y1="16" x2="300" y2="35" `,
        `stroke="#b45309" stroke-width="2.2"/>\n      `
      ].join('');
      break;
    case 'bassus_cf':
      content = [
        `\n        <text x="6" y="24" font-size="18" font-family="serif" fill="#475569">`,
        `𝄢</text>\n        <ellipse cx="60" cy="26" rx="5" ry="4" fill="#ffffff" `,
        `stroke="#334155" stroke-width="1.8"/><line x1="56" y1="26" x2="56" y2="40" `,
        `stroke="#334155" stroke-width="1.5"/>\n        <ellipse cx="120" cy="32" rx="5" `,
        `ry="4" fill="#ffffff" stroke="#334155" stroke-width="1.8"/><line x1="116" `,
        `y1="32" x2="116" y2="44" stroke="#334155" stroke-width="1.5"/>\n        <ellipse `,
        `cx="180" cy="26" rx="5" ry="4" fill="#ffffff" stroke="#334155" `,
        `stroke-width="1.8"/><line x1="176" y1="26" x2="176" y2="40" stroke="#334155" `,
        `stroke-width="1.5"/>\n        <ellipse cx="250" cy="20" rx="5.5" ry="4" `,
        `fill="#ffffff" stroke="#334155" stroke-width="2"/>\n      `
      ].join('');
      break;
    case 'paraphrase_s':
      content = [
        `\n        <text x="6" y="27" font-size="22" font-family="serif" fill="#dc2626">`,
        `𝄞</text>\n        <rect x="42" y="3" width="76" height="30" fill="rgba(239, 68, `,
        `68, 0.12)" stroke="#ef4444" stroke-width="1.2" stroke-dasharray="3,2" rx="4"/>\n `,
        `       <text x="47" y="12" font-size="8" font-weight="bold" fill="#dc2626">`,
        `Fragmento A</text>\n        <ellipse cx="62" cy="20" rx="4" ry="3" `,
        `fill="#dc2626"/><ellipse cx="82" cy="14" rx="4" ry="3" fill="#dc2626"/><ellipse `,
        `cx="102" cy="17" rx="4" ry="3" fill="#dc2626"/>\n        <ellipse cx="150" `,
        `cy="14" rx="4" ry="3" fill="#334155"/><ellipse cx="180" cy="20" rx="4" ry="3" `,
        `fill="#334155"/><ellipse cx="230" cy="26" rx="4.5" ry="3.5" fill="#ffffff" `,
        `stroke="#334155" stroke-width="1.5"/>\n      `
      ].join('');
      break;
    case 'paraphrase_a':
      content = [
        `\n        <text x="6" y="25" font-size="18" font-family="serif" fill="#d97706">`,
        `𝄡</text>\n        <rect x="95" y="3" width="76" height="30" fill="rgba(245, 158, `,
        `11, 0.12)" stroke="#f59e0b" stroke-width="1.2" stroke-dasharray="3,2" rx="4"/>\n `,
        `       <text x="100" y="12" font-size="8" font-weight="bold" fill="#b45309">↳ `,
        `Imitación</text>\n        <ellipse cx="115" cy="26" rx="4" ry="3" `,
        `fill="#d97706"/><ellipse cx="135" cy="20" rx="4" ry="3" fill="#d97706"/><ellipse `,
        `cx="155" cy="23" rx="4" ry="3" fill="#d97706"/>\n        <ellipse cx="200" `,
        `cy="20" rx="4" ry="3" fill="#334155"/><ellipse cx="240" cy="14" rx="4.5" `,
        `ry="3.5" fill="#ffffff" stroke="#334155" stroke-width="1.5"/>\n      `
      ].join('');
      break;
    case 'paraphrase_t':
      content = [
        `\n        <text x="6" y="25" font-size="18" font-family="serif" fill="#059669">`,
        `𝄡</text>\n        <rect x="145" y="3" width="76" height="30" fill="rgba(16, 185, `,
        `129, 0.12)" stroke="#10b981" stroke-width="1.2" stroke-dasharray="3,2" rx="4"/>`,
        `\n        <text x="150" y="12" font-size="8" font-weight="bold" fill="#047857">↳ `,
        `Imitación</text>\n        <ellipse cx="165" cy="20" rx="4" ry="3" `,
        `fill="#059669"/><ellipse cx="185" cy="14" rx="4" ry="3" fill="#059669"/><ellipse `,
        `cx="205" cy="17" rx="4" ry="3" fill="#059669"/>\n        <ellipse cx="250" `,
        `cy="20" rx="4.5" ry="3.5" fill="#ffffff" stroke="#334155" stroke-width="1.5"/>\n      `
      ].join('');
      break;
    case 'paraphrase_b':
      content = [
        `\n        <text x="6" y="24" font-size="18" font-family="serif" fill="#2563eb">`,
        `𝄢</text>\n        <rect x="195" y="3" width="76" height="30" fill="rgba(37, 99, `,
        `235, 0.12)" stroke="#2563eb" stroke-width="1.2" stroke-dasharray="3,2" rx="4"/>`,
        `\n        <text x="200" y="12" font-size="8" font-weight="bold" fill="#1d4ed8">↳ `,
        `Imitación</text>\n        <ellipse cx="215" cy="26" rx="4" ry="3" `,
        `fill="#2563eb"/><ellipse cx="235" cy="20" rx="4" ry="3" fill="#2563eb"/><ellipse `,
        `cx="255" cy="23" rx="4" ry="3" fill="#2563eb"/>\n      `
      ].join('');
      break;
    case 'motto':
      content = [
        `\n        <text x="6" y="27" font-size="22" font-family="serif" fill="#6366f1">`,
        `𝄞</text>\n        <circle cx="50" cy="20" r="4.2" fill="#6366f1"/><line x1="54" `,
        `y1="20" x2="54" y2="7" stroke="#6366f1" stroke-width="1.5"/>\n        <circle `,
        `cx="85" cy="14" r="4.2" fill="#6366f1"/><line x1="89" y1="14" x2="89" y2="2" `,
        `stroke="#6366f1" stroke-width="1.5"/>\n        <circle cx="120" cy="17" r="4.2" `,
        `fill="#6366f1"/><line x1="124" y1="17" x2="124" y2="4" stroke="#6366f1" `,
        `stroke-width="1.5"/>\n        <circle cx="155" cy="20" r="4.2" fill="#6366f1"/>`,
        `<line x1="159" y1="20" x2="159" y2="7" stroke="#6366f1" stroke-width="1.5"/>\n   `,
        `     <text x="180" y="22" font-size="10" font-weight="bold" fill="#4338ca">Kyrie `,
        `/ Gloria / Credo...</text>\n      `
      ].join('');
      break;
    case 'cadence':
      content = [
        `\n        <text x="6" y="27" font-size="22" font-family="serif" fill="#0f766e">`,
        `𝄞</text>\n        <ellipse cx="55" cy="23" rx="4" ry="3" fill="#0f766e"/>`,
        `<ellipse cx="55" cy="14" rx="4" ry="3" fill="#0f766e"/>\n        <text x="80" `,
        `y="21" font-size="9" fill="#64748b">➔ 6ª a 8ª (Landini) ➔</text>\n        `,
        `<ellipse cx="200" cy="26" rx="5.5" ry="4" fill="#ffffff" stroke="#0f766e" `,
        `stroke-width="2"/>\n        <ellipse cx="200" cy="8" rx="5.5" ry="4" `,
        `fill="#ffffff" stroke="#0f766e" stroke-width="2"/>\n        <text x="216" y="20" `,
        `font-size="8.5" font-weight="bold" fill="#0f766e">8ª sin 3ª</text>\n      `
      ].join('');
      break;
    default:
      content = `<text x="6" y="27" font-size="22" font-family="serif" fill="#64748b">𝄞</text>`;
  }
  return [
    `<svg class="staff-svg" viewBox="0 0 320 38" preserveAspectRatio="none">${lines}${content}</svg>`
  ].join('');
}

export function renderStudentInfographic(run) {
  return [
    `\n    <div class="infographic-poster">\n      <div class="infographic-main-head">`,
    `\n        <div class="info-tag-row">\n          <span class="info-badge">`,
    `POLIFONÍA DEL SIGLO XV</span>\n          <span class="info-badge-sub">MODELOS DE `,
    `MISA Y TÉCNICAS COMPOSITIVAS</span>\n        </div>\n        <h2>ARTE, FE Y `,
    `MÚSICA EN EL RENACIMIENTO</h2>\n        <p class="info-subtitle">Del material `,
    `preexistente a la misa cíclica · Dufay · Binchois · Ockeghem · Busnois · `,
    `Josquin</p>\n      </div>\n\n      <div class="infographic-grid">\n        <!-- `,
    `PANEL 1: DISTRIBUCIÓN VOCÁLICA Y EJEMPLOS DE NOTACIÓN -->\n        <div `,
    `class="infographic-panel panel-left">\n          <div class="panel-header-bar">`,
    `\n            <span class="panel-number">1</span>\n            <div>\n           `,
    `   <h3>DISTRIBUCIÓN VOCÁLICA Y EJEMPLOS DE NOTACIÓN</h3>\n              <span `,
    `class="panel-sub">Modelos de misa del siglo XV · Una melodía, tres caminos de `,
    `creación</span>\n            </div>\n          </div>\n\n          <!-- MODELO `,
    `1: MISA DE CANTUS FIRMUS -->\n          <div class="model-block">\n            `,
    `<div class="model-header-row">\n              <div class="model-title-group">\n  `,
    `              <span class="model-circle-badge">1</span>\n                <div>\n `,
    `                 <h4>MISA DE CANTUS FIRMUS</h4>\n                  <small `,
    `class="model-meta">Estructura rígida</small>\n                </div>\n           `,
    `   </div>\n              <span class="model-quote">«La melodía permanece fija `,
    `como eje de la misa»</span>\n            </div>\n\n            <div `,
    `class="model-body-grid">\n              <div class="voice-staves-box">\n         `,
    `       <div class="voice-row"><span class="voice-tag">Superius (Soprano)</span>`,
    `${renderStaffSvg('superius_cf')}`,
    [
      `</div>\n                <div class="voice-row"><span class="voice-tag">Altus (Contralto)</span>`
    ].join(''),
    `${renderStaffSvg('altus_cf')}`,
    `</div>\n                <div class="voice-row voice-tenor-highlight">\n          `,
    [
      `        <span class="voice-tag voice-tenor-badge">Tenor (Cantus Firmus)</span>\n                  `
    ].join(''),
    [
      `${renderStaffSvg('tenor_cf')}\n                </div>\n                <div class="voice-row"><span `
    ].join(''),
    `class="voice-tag">Bassus (Bajo)</span>${renderStaffSvg('bassus_cf')}`,
    `</div>\n              </div>\n\n              <div class="model-side-info">\n    `,
    `            <div class="model-chars-card">\n                  <strong>`,
    `CARACTERÍSTICAS</strong>\n                  <ul>\n                    <li>La `,
    `melodía preexistente se presenta en valores largos (aumentación).</li>\n         `,
    `           <li>Normalmente situada en el Tenor.</li>\n                    <li>`,
    `Las otras voces desarrollan contrapunto libre o imitativo.</li>\n                `,
    `    <li>Estructura solemne y estable.</li>\n                  </ul>\n            `,
    `    </div>\n                <div class="model-example-card">\n                  `,
    `<span class="ex-badge">EJEMPLO</span>\n                  <strong>L'homme `,
    `armé</strong>\n                  <p>Melodía del cantus firmus en el Tenor (en `,
    `valores de longa y máxima).</p>\n                </div>\n              </div>\n  `,
    `          </div>\n          </div>\n\n          <!-- MODELO 2: MISA DE `,
    `PARÁFRASIS -->\n          <div class="model-block">\n            <div `,
    `class="model-header-row">\n              <div class="model-title-group">\n       `,
    `         <span class="model-circle-badge accent-amber">2</span>\n                `,
    `<div>\n                  <h4>MISA DE PARÁFRASIS</h4>\n                  <small `,
    `class="model-meta">Estructura fluida e imitativa</small>\n                </div>`,
    `\n              </div>\n              <span class="model-quote">«La melodía `,
    `viaja, se adorna y se transforma»</span>\n            </div>\n\n            <div `,
    `class="model-body-grid">\n              <div class="voice-staves-box">\n         `,
    `       <div class="voice-row"><span class="voice-tag">Superius (Soprano)</span>`,
    `${renderStaffSvg('paraphrase_s')}`,
    [
      `</div>\n                <div class="voice-row"><span class="voice-tag">Altus (Contralto)</span>`
    ].join(''),
    `${renderStaffSvg('paraphrase_a')}`,
    `</div>\n                <div class="voice-row"><span class="voice-tag">Tenor</span>`,
    `${renderStaffSvg('paraphrase_t')}`,
    [
      `</div>\n                <div class="voice-row"><span class="voice-tag">Bassus (Bajo)</span>`
    ].join(''),
    `${renderStaffSvg('paraphrase_b')}`,
    `</div>\n              </div>\n\n              <div class="model-side-info">\n    `,
    `            <div class="model-chars-card">\n                  <strong>`,
    `CARACTERÍSTICAS</strong>\n                  <ul>\n                    <li>La `,
    `melodía original se mantiene reconocible, pero con adornos (glosas).</li>\n      `,
    `              <li>Se reparte entre todas las voces mediante imitación.</li>\n    `,
    `                <li>Hay mayor libertad rítmica y melódica.</li>\n                `,
    `    <li>Textura más dinámica y expresiva.</li>\n                  </ul>\n        `,
    `        </div>\n                <div class="model-example-card">\n               `,
    `   <span class="ex-badge">EJEMPLO</span>\n                  <strong>Pange `,
    `Lingua</strong>\n                  <p>Fragmento del himno gregoriano con `,
    `ornamentos y tratamiento imitativo entre voces.</p>\n                </div>\n    `,
    `          </div>\n            </div>\n          </div>\n\n          <!-- MODELO `,
    `3: MISA PARODIA / IMITACIÓN -->\n          <div class="model-block">\n           `,
    ` <div class="model-header-row">\n              <div class="model-title-group">\n `,
    `               <span class="model-circle-badge accent-green">3</span>\n          `,
    `      <div>\n                  <h4>MISA PARODIA / IMITACIÓN</h4>\n               `,
    `   <small class="model-meta">Estructura en bloque</small>\n                </div>`,
    `\n              </div>\n              <span class="model-quote">«Se toma el `,
    `tejido polifónico completo y se reelabora»</span>\n            </div>\n\n        `,
    `    <div class="model-body-grid">\n              <div class="parody-diagram-box">`,
    `\n                <div class="parody-box-side original-piece">\n                 `,
    ` <span class="parody-box-title">Obra original (Motete / Chanson a 4 voces)</span>`,
    `\n                  <div class="p-voice v1">Voz 1 (Superius)</div>\n             `,
    `     <div class="p-voice v2">Voz 2 (Altus)</div>\n                  <div `,
    `class="p-voice v3">Voz 3 (Tenor)</div>\n                  <div class="p-voice `,
    `v4">Voz 4 (Bassus)</div>\n                </div>\n\n                <div `,
    `class="parody-arrow-center">\n                  <span>↳ Se copia, se adapta y se `,
    `transforma ➔</span>\n                </div>\n\n                <div `,
    `class="parody-box-side new-mass">\n                  <span `,
    `class="parody-box-title">Misa nueva (Kyrie, Gloria, Credo...)</span>\n           `,
    `       <div class="p-voice v1">Superius</div>\n                  <div `,
    `class="p-voice v2">Altus</div>\n                  <div class="p-voice v3">`,
    `Tenor</div>\n                  <div class="p-voice v4">Bassus</div>\n            `,
    `    </div>\n              </div>\n\n              <div class="model-side-info">`,
    `\n                <div class="model-chars-card">\n                  <strong>`,
    `CARACTERÍSTICAS</strong>\n                  <ul>\n                    <li>Se `,
    `toma la obra original completa (las cuatro voces).</li>\n                    <li>`,
    `Puede mantenerse el orden, invertirse o variar el ritmo.</li>\n                  `,
    `  <li>Alternancia de texturas: contrapunto imitativo y pasajes más `,
    `homofónicos.</li>\n                    <li>Inserción de nuevos motivos y `,
    `adaptaciones al texto litúrgico.</li>\n                  </ul>\n                `,
    `</div>\n                <div class="model-example-card">\n                  `,
    `<span class="ex-badge">EJEMPLO</span>\n                  <strong>Je ne vis `,
    `oncques la / Se la face ay pale</strong>\n                  <p>Inicio en `,
    `imitación de las cuatro voces de la chanson en el Kyrie de la misa.</p>\n        `,
    `        </div>\n              </div>\n            </div>\n          </div>\n     `,
    `   </div>\n\n        <!-- PANEL 2: TÉCNICAS DE COMPOSICIÓN DEL SIGLO XV -->\n    `,
    `    <div class="infographic-panel panel-right">\n          <div `,
    `class="panel-header-bar accent-wine">\n            <span class="panel-number">`,
    `2</span>\n            <div>\n              <h3>TÉCNICAS DE COMPOSICIÓN DEL SIGLO `,
    `XV</h3>\n              <span class="panel-sub">Del material preexistente a la `,
    `misa cíclica · Tradición · Invención · Unidad</span>\n            </div>\n       `,
    `   </div>\n\n          <!-- PASO 1 -->\n          <div class="step-card">\n      `,
    `      <div class="step-title-row">\n              <span class="step-badge">PASO `,
    `1</span>\n              <div>\n                <strong>SELECCIÓN DEL MATERIAL `,
    `PREEXISTENTE</strong>\n                <p>El compositor parte de una melodía o `,
    `de una obra ya conocida.</p>\n              </div>\n            </div>\n\n       `,
    `     <div class="source-branches-grid">\n              <div `,
    `class="source-branch-card sacred">\n                <div class="branch-head">\n  `,
    `                <span class="branch-icon">📜</span>\n                  <div>\n    `,
    `                <strong>ORIGEN SACRO</strong>\n                    <small>Canto `,
    `Llano / Gregoriano</small>\n                  </div>\n                </div>\n   `,
    `             <ul>\n                  <li>Himnos</li>\n                  <li>`,
    `Antífonas</li>\n                  <li>Cantos litúrgicos</li>\n                `,
    `</ul>\n                <div class="branch-examples">\n                  <em>`,
    `Ejemplos:</em> Ave Maris Stella, Pange Lingua, Veni Creator Spiritus\n           `,
    `     </div>\n              </div>\n\n              <div `,
    `class="source-branch-card secular">\n                <div class="branch-head">\n `,
    `                 <span class="branch-icon">🪕</span>\n                  <div>\n   `,
    `                 <strong>ORIGEN PROFANO</strong>\n                    <small>`,
    `Chansons, canciones populares</small>\n                  </div>\n                `,
    `</div>\n                <ul>\n                  <li>Chansons cortesanas</li>\n   `,
    `               <li>Canciones de tradición oral</li>\n                  <li>`,
    `Melodías de gran difusión</li>\n                </ul>\n                <div `,
    `class="branch-examples">\n                  <em>Ejemplos:</em> L'homme armé, Se `,
    `la face ay pale, Belle, bonne, sage\n                </div>\n              </div>`,
    `\n            </div>\n          </div>\n\n          <div class="flow-arrow-down">`,
    `⬇</div>\n\n          <!-- PASO 2 -->\n          <div class="step-card">\n        `,
    `    <div class="step-title-row">\n              <span class="step-badge">PASO `,
    `2</span>\n              <div>\n                <strong>ELECCIÓN DE LA TÉCNICA DE `,
    `TRATAMIENTO</strong>\n                <p>Diferentes maneras de integrar el `,
    `material en la misa.</p>\n              </div>\n            </div>\n\n           `,
    ` <div class="treatment-cols-grid">\n              <div class="treatment-box `,
    `col-cf">\n                <div class="treatment-icon">𝄡</div>\n                `,
    `<strong>CANTUS FIRMUS</strong>\n                <ul>\n                  <li>`,
    `Aislar la melodía.</li>\n                  <li>Estirar las notas `,
    `(aumentación).</li>\n                  <li>Normalmente en el Tenor.</li>\n       `,
    `           <li>Otras voces en contrapunto libre.</li>\n                  <li>`,
    `Estructura solemne.</li>\n                </ul>\n                <div `,
    `class="treatment-res">\n                  <small>Resultado:</small>\n            `,
    `      <span>Melodía fija como columna vertebral de la obra.</span>\n             `,
    `   </div>\n              </div>\n\n              <div class="treatment-box `,
    `col-pf">\n                <div class="treatment-icon">〰</div>\n                `,
    `<strong>PARÁFRASIS</strong>\n                <ul>\n                  <li>Alterar `,
    `intervalos.</li>\n                  <li>Añadir ornamentos (glosas).</li>\n       `,
    `           <li>Repartir la melodía entre todas las voces (imitación).</li>\n     `,
    `             <li>Mayor libertad rítmica y melódica.</li>\n                  <li>`,
    `Textura más fluida.</li>\n                </ul>\n                <div `,
    `class="treatment-res">\n                  <small>Resultado:</small>\n            `,
    `      <span>Melodía transformada y en constante movimiento.</span>\n             `,
    `   </div>\n              </div>\n\n              <div class="treatment-box `,
    `col-pd">\n                <div class="treatment-icon">♫</div>\n                `,
    `<strong>PARODIA / IMITACIÓN</strong>\n                <ul>\n                  `,
    `<li>Tomar el tejido polifónico completo.</li>\n                  <li>Variar el `,
    `orden, el ritmo o la textura.</li>\n                  <li>Alternar contrapunto y `,
    `pasajes homofónicos.</li>\n                  <li>Inserción de nuevos `,
    `motivos.</li>\n                </ul>\n                <div class="treatment-res">`,
    `\n                  <small>Resultado:</small>\n                  <span>Una nueva `,
    `obra a partir de todo el material original.</span>\n                </div>\n     `,
    `         </div>\n            </div>\n          </div>\n\n          <div `,
    `class="flow-arrow-down">⬇</div>\n\n          <!-- PASO 3 -->\n          <div `,
    `class="step-card">\n            <div class="step-title-row">\n              `,
    `<span class="step-badge">PASO 3</span>\n              <div>\n                `,
    `<strong>UNIFICACIÓN DE LA MISA CÍCLICA</strong>\n                <p>Recursos `,
    `para dar coherencia a toda la obra (Kyrie, Gloria, Credo, Sanctus, Agnus `,
    `Dei).</p>\n              </div>\n            </div>\n\n            <div `,
    `class="unification-cards-grid">\n              <div class="unification-card `,
    `motto">\n                <div class="u-card-head">\n                  <strong>`,
    `TÉCNICA DEL MOTTO</strong>\n                  <small>(Motivo de cabeza)</small>`,
    `\n                </div>\n                ${renderStaffSvg('motto')}`,
    `\n                <ul>\n                  <li>Todas las partes de la misa `,
    `comienzan con las mismas 3 o 4 notas o células.</li>\n                  <li>`,
    `Refuerza la unidad arquitectónica de la obra.</li>\n                  <li>Muy `,
    `utilizada por Dufay, Josquin y sus contemporáneos.</li>\n                </ul>\n `,
    `             </div>\n\n              <div class="unification-card cadence">\n    `,
    `            <div class="u-card-head">\n                  <strong>CADENCIAS `,
    `RENACENTISTAS</strong>\n                  <small>(Landini y borgoñonas)</small>`,
    `\n                </div>\n                ${renderStaffSvg('cadence')}`,
    `\n                <ul>\n                  <li>Uso de la cadencia de Landini o `,
    `cadencias borgoñonas.</li>\n                  <li>Caracterizadas por la octava `,
    `sin tercera (conducción 6ª a 8ª).</li>\n                  <li>Cierran secciones `,
    `y articulan el texto litúrgico.</li>\n                </ul>\n              </div>`,
    `\n            </div>\n          </div>\n        </div>\n      </div>\n\n      `,
    `<div class="infographic-footer-banner">\n        <span>⚜ MISMA MÚSICA, NUEVOS `,
    `SIGNIFICADOS: DEL MUNDO PROFANO AL ESPACIO SAGRADO ⚜</span>\n        <span `,
    `class="footer-composers">DUFAY · BINCHOIS · OCKEGHEM · BUSNOIS · JOSQUIN</span>`,
    `\n      </div>\n    </div>\n  `
  ].join('');
}
