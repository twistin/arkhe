// Módulo local: responsabilidad separada sin alterar el contenido.


export function renderStaffSvg(type) {
  const lines = [8, 14, 20, 26, 32].map(y => `<line x1="24" y1="${y}" x2="315" y2="${y}" stroke="#cbd5e1" stroke-width="1.2"/>`).join('');
  let content = '';
  switch(type) {
    case 'superius_cf':
      content = `
        <text x="6" y="27" font-size="22" font-family="serif" fill="#475569">𝄞</text>
        <ellipse cx="48" cy="20" rx="4.5" ry="3.5" fill="#1e293b" transform="rotate(-15 48 20)"/><line x1="52" y1="20" x2="52" y2="6" stroke="#1e293b" stroke-width="1.5"/>
        <ellipse cx="78" cy="14" rx="4.5" ry="3.5" fill="#1e293b" transform="rotate(-15 78 14)"/><line x1="82" y1="14" x2="82" y2="2" stroke="#1e293b" stroke-width="1.5"/>
        <ellipse cx="108" cy="17" rx="4.5" ry="3.5" fill="#1e293b" transform="rotate(-15 108 17)"/><line x1="112" y1="17" x2="112" y2="4" stroke="#1e293b" stroke-width="1.5"/>
        <ellipse cx="138" cy="23" rx="4.5" ry="3.5" fill="#1e293b" transform="rotate(-15 138 23)"/><line x1="142" y1="23" x2="142" y2="9" stroke="#1e293b" stroke-width="1.5"/>
        <ellipse cx="172" cy="20" rx="4.5" ry="3.5" fill="#1e293b" transform="rotate(-15 172 20)"/><line x1="176" y1="20" x2="176" y2="6" stroke="#1e293b" stroke-width="1.5"/>
        <ellipse cx="206" cy="14" rx="4.5" ry="3.5" fill="#1e293b" transform="rotate(-15 206 14)"/><line x1="210" y1="14" x2="210" y2="2" stroke="#1e293b" stroke-width="1.5"/>
        <ellipse cx="240" cy="8" rx="5" ry="4" fill="#ffffff" stroke="#1e293b" stroke-width="1.8" transform="rotate(-15 240 8)"/><line x1="244" y1="8" x2="244" y2="-4" stroke="#1e293b" stroke-width="1.5"/>
        <ellipse cx="280" cy="14" rx="5.5" ry="4" fill="#ffffff" stroke="#1e293b" stroke-width="2"/>
      `;
      break;
    case 'altus_cf':
      content = `
        <text x="6" y="25" font-size="18" font-family="serif" fill="#475569">𝄡</text>
        <ellipse cx="54" cy="26" rx="4.5" ry="3.5" fill="#334155" transform="rotate(-15 54 26)"/><line x1="58" y1="26" x2="58" y2="12" stroke="#334155" stroke-width="1.5"/>
        <ellipse cx="94" cy="20" rx="4.5" ry="3.5" fill="#334155" transform="rotate(-15 94 20)"/><line x1="98" y1="20" x2="98" y2="6" stroke="#334155" stroke-width="1.5"/>
        <ellipse cx="134" cy="23" rx="4.5" ry="3.5" fill="#334155" transform="rotate(-15 134 23)"/><line x1="138" y1="23" x2="138" y2="9" stroke="#334155" stroke-width="1.5"/>
        <ellipse cx="180" cy="26" rx="5" ry="4" fill="#ffffff" stroke="#334155" stroke-width="1.8"/>
        <ellipse cx="230" cy="20" rx="5" ry="4" fill="#ffffff" stroke="#334155" stroke-width="1.8"/>
        <ellipse cx="280" cy="23" rx="5.5" ry="4" fill="#ffffff" stroke="#334155" stroke-width="2"/>
      `;
      break;
    case 'tenor_cf':
      content = `
        <text x="6" y="25" font-size="18" font-family="serif" fill="#b45309">𝄡</text>
        <rect x="55" y="16" width="16" height="8" fill="#ffffff" stroke="#b45309" stroke-width="2.2" rx="1.5"/><line x1="71" y1="16" x2="71" y2="35" stroke="#b45309" stroke-width="2.2"/>
        <rect x="135" y="13" width="16" height="8" fill="#ffffff" stroke="#b45309" stroke-width="2.2" rx="1.5"/><line x1="151" y1="13" x2="151" y2="32" stroke="#b45309" stroke-width="2.2"/>
        <rect x="215" y="19" width="16" height="8" fill="#ffffff" stroke="#b45309" stroke-width="2.2" rx="1.5"/><line x1="231" y1="19" x2="231" y2="38" stroke="#b45309" stroke-width="2.2"/>
        <rect x="280" y="16" width="20" height="8" fill="#ffffff" stroke="#b45309" stroke-width="2.5" rx="1.5"/><line x1="300" y1="16" x2="300" y2="35" stroke="#b45309" stroke-width="2.2"/>
      `;
      break;
    case 'bassus_cf':
      content = `
        <text x="6" y="24" font-size="18" font-family="serif" fill="#475569">𝄢</text>
        <ellipse cx="60" cy="26" rx="5" ry="4" fill="#ffffff" stroke="#334155" stroke-width="1.8"/><line x1="56" y1="26" x2="56" y2="40" stroke="#334155" stroke-width="1.5"/>
        <ellipse cx="120" cy="32" rx="5" ry="4" fill="#ffffff" stroke="#334155" stroke-width="1.8"/><line x1="116" y1="32" x2="116" y2="44" stroke="#334155" stroke-width="1.5"/>
        <ellipse cx="180" cy="26" rx="5" ry="4" fill="#ffffff" stroke="#334155" stroke-width="1.8"/><line x1="176" y1="26" x2="176" y2="40" stroke="#334155" stroke-width="1.5"/>
        <ellipse cx="250" cy="20" rx="5.5" ry="4" fill="#ffffff" stroke="#334155" stroke-width="2"/>
      `;
      break;
    case 'paraphrase_s':
      content = `
        <text x="6" y="27" font-size="22" font-family="serif" fill="#dc2626">𝄞</text>
        <rect x="42" y="3" width="76" height="30" fill="rgba(239, 68, 68, 0.12)" stroke="#ef4444" stroke-width="1.2" stroke-dasharray="3,2" rx="4"/>
        <text x="47" y="12" font-size="8" font-weight="bold" fill="#dc2626">Fragmento A</text>
        <ellipse cx="62" cy="20" rx="4" ry="3" fill="#dc2626"/><ellipse cx="82" cy="14" rx="4" ry="3" fill="#dc2626"/><ellipse cx="102" cy="17" rx="4" ry="3" fill="#dc2626"/>
        <ellipse cx="150" cy="14" rx="4" ry="3" fill="#334155"/><ellipse cx="180" cy="20" rx="4" ry="3" fill="#334155"/><ellipse cx="230" cy="26" rx="4.5" ry="3.5" fill="#ffffff" stroke="#334155" stroke-width="1.5"/>
      `;
      break;
    case 'paraphrase_a':
      content = `
        <text x="6" y="25" font-size="18" font-family="serif" fill="#d97706">𝄡</text>
        <rect x="95" y="3" width="76" height="30" fill="rgba(245, 158, 11, 0.12)" stroke="#f59e0b" stroke-width="1.2" stroke-dasharray="3,2" rx="4"/>
        <text x="100" y="12" font-size="8" font-weight="bold" fill="#b45309">↳ Imitación</text>
        <ellipse cx="115" cy="26" rx="4" ry="3" fill="#d97706"/><ellipse cx="135" cy="20" rx="4" ry="3" fill="#d97706"/><ellipse cx="155" cy="23" rx="4" ry="3" fill="#d97706"/>
        <ellipse cx="200" cy="20" rx="4" ry="3" fill="#334155"/><ellipse cx="240" cy="14" rx="4.5" ry="3.5" fill="#ffffff" stroke="#334155" stroke-width="1.5"/>
      `;
      break;
    case 'paraphrase_t':
      content = `
        <text x="6" y="25" font-size="18" font-family="serif" fill="#059669">𝄡</text>
        <rect x="145" y="3" width="76" height="30" fill="rgba(16, 185, 129, 0.12)" stroke="#10b981" stroke-width="1.2" stroke-dasharray="3,2" rx="4"/>
        <text x="150" y="12" font-size="8" font-weight="bold" fill="#047857">↳ Imitación</text>
        <ellipse cx="165" cy="20" rx="4" ry="3" fill="#059669"/><ellipse cx="185" cy="14" rx="4" ry="3" fill="#059669"/><ellipse cx="205" cy="17" rx="4" ry="3" fill="#059669"/>
        <ellipse cx="250" cy="20" rx="4.5" ry="3.5" fill="#ffffff" stroke="#334155" stroke-width="1.5"/>
      `;
      break;
    case 'paraphrase_b':
      content = `
        <text x="6" y="24" font-size="18" font-family="serif" fill="#2563eb">𝄢</text>
        <rect x="195" y="3" width="76" height="30" fill="rgba(37, 99, 235, 0.12)" stroke="#2563eb" stroke-width="1.2" stroke-dasharray="3,2" rx="4"/>
        <text x="200" y="12" font-size="8" font-weight="bold" fill="#1d4ed8">↳ Imitación</text>
        <ellipse cx="215" cy="26" rx="4" ry="3" fill="#2563eb"/><ellipse cx="235" cy="20" rx="4" ry="3" fill="#2563eb"/><ellipse cx="255" cy="23" rx="4" ry="3" fill="#2563eb"/>
      `;
      break;
    case 'motto':
      content = `
        <text x="6" y="27" font-size="22" font-family="serif" fill="#6366f1">𝄞</text>
        <circle cx="50" cy="20" r="4.2" fill="#6366f1"/><line x1="54" y1="20" x2="54" y2="7" stroke="#6366f1" stroke-width="1.5"/>
        <circle cx="85" cy="14" r="4.2" fill="#6366f1"/><line x1="89" y1="14" x2="89" y2="2" stroke="#6366f1" stroke-width="1.5"/>
        <circle cx="120" cy="17" r="4.2" fill="#6366f1"/><line x1="124" y1="17" x2="124" y2="4" stroke="#6366f1" stroke-width="1.5"/>
        <circle cx="155" cy="20" r="4.2" fill="#6366f1"/><line x1="159" y1="20" x2="159" y2="7" stroke="#6366f1" stroke-width="1.5"/>
        <text x="180" y="22" font-size="10" font-weight="bold" fill="#4338ca">Kyrie / Gloria / Credo...</text>
      `;
      break;
    case 'cadence':
      content = `
        <text x="6" y="27" font-size="22" font-family="serif" fill="#0f766e">𝄞</text>
        <ellipse cx="55" cy="23" rx="4" ry="3" fill="#0f766e"/><ellipse cx="55" cy="14" rx="4" ry="3" fill="#0f766e"/>
        <text x="80" y="21" font-size="9" fill="#64748b">➔ 6ª a 8ª (Landini) ➔</text>
        <ellipse cx="200" cy="26" rx="5.5" ry="4" fill="#ffffff" stroke="#0f766e" stroke-width="2"/>
        <ellipse cx="200" cy="8" rx="5.5" ry="4" fill="#ffffff" stroke="#0f766e" stroke-width="2"/>
        <text x="216" y="20" font-size="8.5" font-weight="bold" fill="#0f766e">8ª sin 3ª</text>
      `;
      break;
    default:
      content = `<text x="6" y="27" font-size="22" font-family="serif" fill="#64748b">𝄞</text>`;
  }
  return `<svg class="staff-svg" viewBox="0 0 320 38" preserveAspectRatio="none">${lines}${content}</svg>`;
}

export function renderStudentInfographic(run) {
  return `
    <div class="infographic-poster">
      <div class="infographic-main-head">
        <div class="info-tag-row">
          <span class="info-badge">POLIFONÍA DEL SIGLO XV</span>
          <span class="info-badge-sub">MODELOS DE MISA Y TÉCNICAS COMPOSITIVAS</span>
        </div>
        <h2>ARTE, FE Y MÚSICA EN EL RENACIMIENTO</h2>
        <p class="info-subtitle">Del material preexistente a la misa cíclica · Dufay · Binchois · Ockeghem · Busnois · Josquin</p>
      </div>

      <div class="infographic-grid">
        <!-- PANEL 1: DISTRIBUCIÓN VOCÁLICA Y EJEMPLOS DE NOTACIÓN -->
        <div class="infographic-panel panel-left">
          <div class="panel-header-bar">
            <span class="panel-number">1</span>
            <div>
              <h3>DISTRIBUCIÓN VOCÁLICA Y EJEMPLOS DE NOTACIÓN</h3>
              <span class="panel-sub">Modelos de misa del siglo XV · Una melodía, tres caminos de creación</span>
            </div>
          </div>

          <!-- MODELO 1: MISA DE CANTUS FIRMUS -->
          <div class="model-block">
            <div class="model-header-row">
              <div class="model-title-group">
                <span class="model-circle-badge">1</span>
                <div>
                  <h4>MISA DE CANTUS FIRMUS</h4>
                  <small class="model-meta">Estructura rígida</small>
                </div>
              </div>
              <span class="model-quote">«La melodía permanece fija como eje de la misa»</span>
            </div>

            <div class="model-body-grid">
              <div class="voice-staves-box">
                <div class="voice-row"><span class="voice-tag">Superius (Soprano)</span>${renderStaffSvg('superius_cf')}</div>
                <div class="voice-row"><span class="voice-tag">Altus (Contralto)</span>${renderStaffSvg('altus_cf')}</div>
                <div class="voice-row voice-tenor-highlight">
                  <span class="voice-tag voice-tenor-badge">Tenor (Cantus Firmus)</span>
                  ${renderStaffSvg('tenor_cf')}
                </div>
                <div class="voice-row"><span class="voice-tag">Bassus (Bajo)</span>${renderStaffSvg('bassus_cf')}</div>
              </div>

              <div class="model-side-info">
                <div class="model-chars-card">
                  <strong>CARACTERÍSTICAS</strong>
                  <ul>
                    <li>La melodía preexistente se presenta en valores largos (aumentación).</li>
                    <li>Normalmente situada en el Tenor.</li>
                    <li>Las otras voces desarrollan contrapunto libre o imitativo.</li>
                    <li>Estructura solemne y estable.</li>
                  </ul>
                </div>
                <div class="model-example-card">
                  <span class="ex-badge">EJEMPLO</span>
                  <strong>L'homme armé</strong>
                  <p>Melodía del cantus firmus en el Tenor (en valores de longa y máxima).</p>
                </div>
              </div>
            </div>
          </div>

          <!-- MODELO 2: MISA DE PARÁFRASIS -->
          <div class="model-block">
            <div class="model-header-row">
              <div class="model-title-group">
                <span class="model-circle-badge accent-amber">2</span>
                <div>
                  <h4>MISA DE PARÁFRASIS</h4>
                  <small class="model-meta">Estructura fluida e imitativa</small>
                </div>
              </div>
              <span class="model-quote">«La melodía viaja, se adorna y se transforma»</span>
            </div>

            <div class="model-body-grid">
              <div class="voice-staves-box">
                <div class="voice-row"><span class="voice-tag">Superius (Soprano)</span>${renderStaffSvg('paraphrase_s')}</div>
                <div class="voice-row"><span class="voice-tag">Altus (Contralto)</span>${renderStaffSvg('paraphrase_a')}</div>
                <div class="voice-row"><span class="voice-tag">Tenor</span>${renderStaffSvg('paraphrase_t')}</div>
                <div class="voice-row"><span class="voice-tag">Bassus (Bajo)</span>${renderStaffSvg('paraphrase_b')}</div>
              </div>

              <div class="model-side-info">
                <div class="model-chars-card">
                  <strong>CARACTERÍSTICAS</strong>
                  <ul>
                    <li>La melodía original se mantiene reconocible, pero con adornos (glosas).</li>
                    <li>Se reparte entre todas las voces mediante imitación.</li>
                    <li>Hay mayor libertad rítmica y melódica.</li>
                    <li>Textura más dinámica y expresiva.</li>
                  </ul>
                </div>
                <div class="model-example-card">
                  <span class="ex-badge">EJEMPLO</span>
                  <strong>Pange Lingua</strong>
                  <p>Fragmento del himno gregoriano con ornamentos y tratamiento imitativo entre voces.</p>
                </div>
              </div>
            </div>
          </div>

          <!-- MODELO 3: MISA PARODIA / IMITACIÓN -->
          <div class="model-block">
            <div class="model-header-row">
              <div class="model-title-group">
                <span class="model-circle-badge accent-green">3</span>
                <div>
                  <h4>MISA PARODIA / IMITACIÓN</h4>
                  <small class="model-meta">Estructura en bloque</small>
                </div>
              </div>
              <span class="model-quote">«Se toma el tejido polifónico completo y se reelabora»</span>
            </div>

            <div class="model-body-grid">
              <div class="parody-diagram-box">
                <div class="parody-box-side original-piece">
                  <span class="parody-box-title">Obra original (Motete / Chanson a 4 voces)</span>
                  <div class="p-voice v1">Voz 1 (Superius)</div>
                  <div class="p-voice v2">Voz 2 (Altus)</div>
                  <div class="p-voice v3">Voz 3 (Tenor)</div>
                  <div class="p-voice v4">Voz 4 (Bassus)</div>
                </div>

                <div class="parody-arrow-center">
                  <span>↳ Se copia, se adapta y se transforma ➔</span>
                </div>

                <div class="parody-box-side new-mass">
                  <span class="parody-box-title">Misa nueva (Kyrie, Gloria, Credo...)</span>
                  <div class="p-voice v1">Superius</div>
                  <div class="p-voice v2">Altus</div>
                  <div class="p-voice v3">Tenor</div>
                  <div class="p-voice v4">Bassus</div>
                </div>
              </div>

              <div class="model-side-info">
                <div class="model-chars-card">
                  <strong>CARACTERÍSTICAS</strong>
                  <ul>
                    <li>Se toma la obra original completa (las cuatro voces).</li>
                    <li>Puede mantenerse el orden, invertirse o variar el ritmo.</li>
                    <li>Alternancia de texturas: contrapunto imitativo y pasajes más homofónicos.</li>
                    <li>Inserción de nuevos motivos y adaptaciones al texto litúrgico.</li>
                  </ul>
                </div>
                <div class="model-example-card">
                  <span class="ex-badge">EJEMPLO</span>
                  <strong>Je ne vis oncques la / Se la face ay pale</strong>
                  <p>Inicio en imitación de las cuatro voces de la chanson en el Kyrie de la misa.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- PANEL 2: TÉCNICAS DE COMPOSICIÓN DEL SIGLO XV -->
        <div class="infographic-panel panel-right">
          <div class="panel-header-bar accent-wine">
            <span class="panel-number">2</span>
            <div>
              <h3>TÉCNICAS DE COMPOSICIÓN DEL SIGLO XV</h3>
              <span class="panel-sub">Del material preexistente a la misa cíclica · Tradición · Invención · Unidad</span>
            </div>
          </div>

          <!-- PASO 1 -->
          <div class="step-card">
            <div class="step-title-row">
              <span class="step-badge">PASO 1</span>
              <div>
                <strong>SELECCIÓN DEL MATERIAL PREEXISTENTE</strong>
                <p>El compositor parte de una melodía o de una obra ya conocida.</p>
              </div>
            </div>

            <div class="source-branches-grid">
              <div class="source-branch-card sacred">
                <div class="branch-head">
                  <span class="branch-icon">📜</span>
                  <div>
                    <strong>ORIGEN SACRO</strong>
                    <small>Canto Llano / Gregoriano</small>
                  </div>
                </div>
                <ul>
                  <li>Himnos</li>
                  <li>Antífonas</li>
                  <li>Cantos litúrgicos</li>
                </ul>
                <div class="branch-examples">
                  <em>Ejemplos:</em> Ave Maris Stella, Pange Lingua, Veni Creator Spiritus
                </div>
              </div>

              <div class="source-branch-card secular">
                <div class="branch-head">
                  <span class="branch-icon">🪕</span>
                  <div>
                    <strong>ORIGEN PROFANO</strong>
                    <small>Chansons, canciones populares</small>
                  </div>
                </div>
                <ul>
                  <li>Chansons cortesanas</li>
                  <li>Canciones de tradición oral</li>
                  <li>Melodías de gran difusión</li>
                </ul>
                <div class="branch-examples">
                  <em>Ejemplos:</em> L'homme armé, Se la face ay pale, Belle, bonne, sage
                </div>
              </div>
            </div>
          </div>

          <div class="flow-arrow-down">⬇</div>

          <!-- PASO 2 -->
          <div class="step-card">
            <div class="step-title-row">
              <span class="step-badge">PASO 2</span>
              <div>
                <strong>ELECCIÓN DE LA TÉCNICA DE TRATAMIENTO</strong>
                <p>Diferentes maneras de integrar el material en la misa.</p>
              </div>
            </div>

            <div class="treatment-cols-grid">
              <div class="treatment-box col-cf">
                <div class="treatment-icon">𝄡</div>
                <strong>CANTUS FIRMUS</strong>
                <ul>
                  <li>Aislar la melodía.</li>
                  <li>Estirar las notas (aumentación).</li>
                  <li>Normalmente en el Tenor.</li>
                  <li>Otras voces en contrapunto libre.</li>
                  <li>Estructura solemne.</li>
                </ul>
                <div class="treatment-res">
                  <small>Resultado:</small>
                  <span>Melodía fija como columna vertebral de la obra.</span>
                </div>
              </div>

              <div class="treatment-box col-pf">
                <div class="treatment-icon">〰</div>
                <strong>PARÁFRASIS</strong>
                <ul>
                  <li>Alterar intervalos.</li>
                  <li>Añadir ornamentos (glosas).</li>
                  <li>Repartir la melodía entre todas las voces (imitación).</li>
                  <li>Mayor libertad rítmica y melódica.</li>
                  <li>Textura más fluida.</li>
                </ul>
                <div class="treatment-res">
                  <small>Resultado:</small>
                  <span>Melodía transformada y en constante movimiento.</span>
                </div>
              </div>

              <div class="treatment-box col-pd">
                <div class="treatment-icon">♫</div>
                <strong>PARODIA / IMITACIÓN</strong>
                <ul>
                  <li>Tomar el tejido polifónico completo.</li>
                  <li>Variar el orden, el ritmo o la textura.</li>
                  <li>Alternar contrapunto y pasajes homofónicos.</li>
                  <li>Inserción de nuevos motivos.</li>
                </ul>
                <div class="treatment-res">
                  <small>Resultado:</small>
                  <span>Una nueva obra a partir de todo el material original.</span>
                </div>
              </div>
            </div>
          </div>

          <div class="flow-arrow-down">⬇</div>

          <!-- PASO 3 -->
          <div class="step-card">
            <div class="step-title-row">
              <span class="step-badge">PASO 3</span>
              <div>
                <strong>UNIFICACIÓN DE LA MISA CÍCLICA</strong>
                <p>Recursos para dar coherencia a toda la obra (Kyrie, Gloria, Credo, Sanctus, Agnus Dei).</p>
              </div>
            </div>

            <div class="unification-cards-grid">
              <div class="unification-card motto">
                <div class="u-card-head">
                  <strong>TÉCNICA DEL MOTTO</strong>
                  <small>(Motivo de cabeza)</small>
                </div>
                ${renderStaffSvg('motto')}
                <ul>
                  <li>Todas las partes de la misa comienzan con las mismas 3 o 4 notas o células.</li>
                  <li>Refuerza la unidad arquitectónica de la obra.</li>
                  <li>Muy utilizada por Dufay, Josquin y sus contemporáneos.</li>
                </ul>
              </div>

              <div class="unification-card cadence">
                <div class="u-card-head">
                  <strong>CADENCIAS RENACENTISTAS</strong>
                  <small>(Landini y borgoñonas)</small>
                </div>
                ${renderStaffSvg('cadence')}
                <ul>
                  <li>Uso de la cadencia de Landini o cadencias borgoñonas.</li>
                  <li>Caracterizadas por la octava sin tercera (conducción 6ª a 8ª).</li>
                  <li>Cierran secciones y articulan el texto litúrgico.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="infographic-footer-banner">
        <span>⚜ MISMA MÚSICA, NUEVOS SIGNIFICADOS: DEL MUNDO PROFANO AL ESPACIO SAGRADO ⚜</span>
        <span class="footer-composers">DUFAY · BINCHOIS · OCKEGHEM · BUSNOIS · JOSQUIN</span>
      </div>
    </div>
  `;
}
