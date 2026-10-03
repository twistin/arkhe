// Módulo local: responsabilidad separada sin alterar el contenido.
import {
  api
} from '../api.js';
import {
  POLYPHONY_LISTENINGS,
  getRunListenings,
  is15thCenturyPolyphony,
  isAncientEgypt,
  renderEgyptListeningsHTML,
  renderListeningCardItem,
  renderStudentDiscographySection
} from './audiciones.js';
import {
  renderEgyptInfographic
} from '../infografias/egipto.js';
import {
  renderStudentInfographic
} from '../infografias/musica.js';
import {
  dialog,
  e,
  formatMarkdown,
  icon,
  modal
} from '../ui.js';

export function studentDocumentHTML(run) {
  const context = run.request?.pedagogy || {},
    plan = run.result?.plan || {},
    claims = run.result?.claims || [];
  const session = context.session;
  const sources = [...new Map((run.evidence || []).map(item => [item.document_id, item.metadata])).values()];
  const title = (run.request?.question || '').charAt(0).toLocaleUpperCase('es') + (run.request?.question ||
    '').slice(1);
  const visuals = run.result?.visualizations || [];
  const isPolyphony = is15thCenturyPolyphony(run);
  const isEgypt = isAncientEgypt(run);
  const listenings = isPolyphony ? POLYPHONY_LISTENINGS : getRunListenings(run);
  let elapsed = 0;

  return [
    `<article class="student-handout">\n    <header class="student-cover">\n      `,
    `<div class="student-brand">\n        <span class="student-pill">ENJAMBRE · `,
    `MATERIAL DE CLASE</span>\n        <span class="student-topic-tag">CUADERNO `,
    `DIDÁCTICO DEL ALUMNADO</span>\n      </div>\n      <h1>${e(title)}`,
    [
      `</h1>\n      <div class="student-meta">\n        <strong>${e(context.group?.name || 'Grupo')}`
    ].join(''),
    [
      `</strong>\n        <span>${e(context.group?.level || 'Conservatorio')}</span>\n        <span>⏱ `
    ].join(''),
    `${context.duration_minutes || 60} minutos</span>\n        `,
    `${session ? `<span>📅 ${e(session.date)}</span>` : ''}`,
    `\n      </div>\n    </header>\n\n    <!-- OBJETIVOS DIDÁCTICOS -->\n    <section `,
    `class="student-section section-intro">\n      <div `,
    `class="student-section-header">\n        <span class="student-section-number">`,
    `🎯</span>\n        <div>\n          <h2>Qué vamos a aprender</h2>\n          <p `,
    `class="student-section-intro">Objetivos y competencias formativas que `,
    `desarrollaremos a lo largo de la sesión.</p>\n        </div>\n      </div>\n     `,
    ` <ol class="student-objectives">\n        `,
    `${(plan.objectives || []).map(item => `<li>${e(item)}</li>`).join('')}`,
    `\n      </ol>\n    </section>\n\n    <!-- SECCIÓN 01: CONTENIDO TEÓRICO DE LAS `,
    `FUENTES -->\n    <section class="student-section section-theory">\n      <div `,
    `class="student-section-header">\n        <span class="student-section-number">`,
    `01</span>\n        <div>\n          <h2>Contenido teórico de las fuentes</h2>\n  `,
    `        <p class="student-section-intro">Análisis musicológico e histórico `,
    `basado en las fuentes documentales autorizadas`,
    [
      `${
        isPolyphony ? ' (Allan Atlas, Gustave Reese y Ulrich Michels)' : isEgypt ?
          ' (Marcelle Duchesne-Guillemin, J. Peter Burkholder y Enrico Fubini)' : ''
      }`
    ].join(''),
    `.</p>\n        </div>\n      </div>\n      <div class="theory-claims-list">\n        `,
    [
      `${
        claims.map((claim, index) => [
          `\n          <div class="student-content theory-claim-card">\n            <span `,
          `class="claim-index-badge">${String(index + 1).padStart(2, '0')}`,
          [
            `</span>\n            <div class="claim-body">\n              ${formatMarkdown(claim.text)}`
          ].join(''),
          `\n              `,
          [
            `${
        claim.evidence?.length ? [
          `<div class="claim-source-badge"><span>📖 Fuente: ${e(claim.evidence[0].source_id)}</span></div>`
        ].join('') : ''
        }`
          ].join(''),
          `\n            </div>\n          </div>\n        `
        ].join('')).join('')
      }`
    ].join(''),
    `\n      </div>\n    </section>\n\n    <!-- SECCIÓN 02: ESQUEMA GRÁFICO (MODELOS `,
    `Y TÉCNICAS) -->\n    <section class="student-section section-infographic">\n     `,
    ` <div class="student-section-header">\n        <span `,
    `class="student-section-number">02</span>\n        <div>\n          <h2>Esquema gráfico: `,
    [
      `${
        isEgypt ? 'Marco histórico, funciones y organología del Antiguo Egipto' : isPolyphony ?
          'Modelos y técnicas de composición del siglo XV' : 'Modelos y estructuras técnicas'
      }`
    ].join(''),
    `</h2>\n          <p class="student-section-intro">`,
    [
      `${
        isEgypt ?
          'Láminas didácticas de contexto, funciones sociales, organología, quironimia y fuentes de estudio.' :
          isPolyphony ? 'Estructuras vocálicas, transformaciones del material y recursos de unificación cíclica.' :
          'Estructuras formales y esquemas comparativos para el aula.'
      }`
    ].join(''),
    `</p>\n        </div>\n      </div>\n      `,
    [
      `${
        isEgypt ? renderEgyptInfographic(run) : (isPolyphony ? renderStudentInfographic(run) : (
          visuals.length ? [
            `\n                <div class="infographic-poster">\n                  <div `,
            `class="infographic-main-head">\n                    <div class="info-tag-row">\n `,
            `                     <span class="info-badge">${e(title.toUpperCase())}`,
            `</span>\n                      <span class="info-badge-sub">ESQUEMAS TÉCNICOS Y `,
            `ESTRUCTURAS FORMALES</span>\n                    </div>\n                    <h2>`,
            `MODELOS Y ANÁLISIS DE TEXTURAS</h2>\n                    <p `,
            `class="info-subtitle">Estructuras formales y esquemas comparativos para el `,
            `aula</p>\n                  </div>\n                  <div class="visual-items">`,
            `${
        visuals.map(v => [
          `\n                    <div class="visual-card">\n                      <h3>${e(v.title)}`,
          `</h3>\n                      ${v.caption ? `<p class="visual-caption">${e(v.caption)}</p>` : ''}`,
          `\n                      <div class="visual-items">`,
          `${
        v.items.map(it => [
          `\n                        <div class="visual-item">\n                          <strong>`,
          `${e(it.label)}</strong>\n                          <span>${e(it.detail)}`,
          `</span>\n                        </div>\n                      `
        ].join('')).join('')
        }`,
          `</div>\n                    </div>\n                  `
        ].join('')).join('')
        }`,
            `</div>\n                </div>\n              `
          ].join('') : [
            `\n          <div class="infographic-poster">\n            <div `,
            [
              `class="infographic-main-head">\n              <div class="info-tag-row"><span class="info-badge">`
            ].join(''),
            `${e(title.toUpperCase())}`,
            `</span></div>\n              <h2>ESQUEMA CONCEPTUAL Y ESTRUCTURAL</h2>\n         `,
            `   </div>\n            <div class="visual-items">`,
            [
              `${
        claims.slice(0, 4).map((c, i) => [
          `\n              <div class="visual-item"><strong>Eje ${i + 1}</strong><span>`,
          `${e(c.text.slice(0, 180))}…</span></div>\n            `
        ].join('')).join('')
        }`
            ].join(''),
            `</div>\n          </div>\n        `
          ].join('')
        ))
      }`
    ].join(''),
    `\n    </section>\n\n    <!-- SECCIÓN 03: CONCEPTOS OBLIGATORIOS PARA APRENDER -->`,
    `\n    <section class="student-section section-concepts">\n      <div `,
    `class="student-section-header">\n        <span class="student-section-number">`,
    `03</span>\n        <div>\n          <h2>Conceptos obligatorios para aprender</h2>`,
    `\n          <p class="student-section-intro">Vocabulario técnico y conceptos `,
    `analíticos indispensables del currículo de conservatorio.</p>\n        </div>\n  `,
    `    </div>\n      <div class="concept-grid">\n        `,
    [
      `${
        isEgypt ? [
          `\n          <div class="concept-card">\n            <div class="concept-head">`,
          `<span class="concept-badge egypt-b-ritual">RITUAL</span><strong>Sistrum `,
          `(Sistro)</strong></div>\n            <p>Instrumento sagrado de percusión con `,
          `marco metálico y varillas sonajas, consagrado al culto de Hathor para ahuyentar `,
          `las fuerzas del caos.</p>\n          </div>\n          <div class="concept-card">`,
          `\n            <div class="concept-head"><span class="concept-badge `,
          `egypt-b-ritual">RITUAL</span><strong>Menat</strong></div>\n            <p>Collar `,
          `ceremonial con cuentas y contrapeso pectoral que las sacerdotisas de Hathor `,
          `agitaban produciendo un suave tintineo purificador.</p>\n          </div>\n      `,
          `    <div class="concept-card">\n            <div class="concept-head"><span `,
          `class="concept-badge egypt-b-gesto">DIRECCIÓN</span><strong>Quironimia</strong>`,
          `</div>\n            <p>Sistema de dirección musical mediante gestos de manos, `,
          `dedos y cuerpo que el cantor/director hacía a los instrumentistas para guiar `,
          `melodía y ritmo.</p>\n          </div>\n          <div class="concept-card">\n   `,
          `         <div class="concept-head"><span class="concept-badge egypt-b-cordas">`,
          `CORDÓFONO</span><strong>Arpa Arqueada</strong></div>\n            <p>Principal `,
          `cordófono del Antiguo Egipto, con cuerpo curvo de madera y cuerdas tensadas `,
          `tañidas por solistas en la corte, banquetes y templos.</p>\n          </div>\n   `,
          `       <div class="concept-card">\n            <div class="concept-head"><span `,
          `class="concept-badge egypt-b-vento">AERÓFONO</span><strong>Clarinete `,
          `Doble</strong></div>\n            <p>Aerófono compuesto por dos tubos paralelos `,
          `de caña provistos de lengüetas batientes, con sonido penetrante usado en `,
          `procesiones y danzas.</p>\n          </div>\n          <div class="concept-card">`,
          `\n            <div class="concept-head"><span class="concept-badge `,
          `egypt-b-liturxia">LITURGIA</span><strong>Canto Ritual</strong></div>\n           `,
          ` <p>Monodia vocal entonada en templos y ritos funerarios, concebida como puente `,
          `directo de comunicación entre el ser humano y las divinidades.</p>\n          `,
          `</div>\n          <div class="concept-card">\n            <div `,
          `class="concept-head"><span class="concept-badge egypt-b-fonte">ICONOGRAFÍA</span>`,
          `<strong>Iconografía Musical</strong></div>\n            <p>Estudio sistemático `,
          `de las fuentes visuales (frescos de tumbas como la de Nebamun y relieves en `,
          `templos) para reconstruir la práctica musical.</p>\n          </div>\n          `,
          `<div class="concept-card">\n            <div class="concept-head"><span `,
          `class="concept-badge egypt-b-arqueo">MÉTODO</span><strong>Arqueología `,
          `Musical</strong></div>\n            <p>Análisis científico de los instrumentos `,
          `materiales conservados en tumbas secas para deducir acústica histórica, `,
          `materiales y afinaciones.</p>\n          </div>\n        `
        ].join('') : isPolyphony ? [
          `\n          <div class="concept-card">\n            <div class="concept-head">`,
          `<span class="concept-badge">TÉCNICA</span><strong>Cantus Firmus</strong></div>\n `,
          `           <p>Melodía preexistente (canto gregoriano o canción profana) empleada `,
          `como eje estructural de una nueva composición polifónica, asignada `,
          `tradicionalmente al Tenor en notas de valores largos.</p>\n          </div>\n    `,
          `      <div class="concept-card">\n            <div class="concept-head"><span `,
          `class="concept-badge">RITMO</span><strong>Aumentación Rítmica</strong></div>\n   `,
          `         <p>Procedimiento consistente en alargar proporcionalmente las `,
          `duraciones de las figuras de la melodía original (duplicar o triplicar su `,
          `valor), confiriendo al Tenor un ritmo lento y solemne.</p>\n          </div>\n   `,
          `       <div class="concept-card">\n            <div class="concept-head"><span `,
          `class="concept-badge">FORMA</span><strong>Misa Cíclica</strong></div>\n          `,
          `  <p>Obra litúrgica polifónica monumental en la que los cinco movimientos del `,
          `Ordinario (Kyrie, Gloria, Credo, Sanctus, Agnus Dei) comparten el mismo material `,
          `temático unificador.</p>\n          </div>\n          <div class="concept-card">`,
          `\n            <div class="concept-head"><span class="concept-badge">`,
          `RECURSO</span><strong>Técnica del Motto</strong></div>\n            <p>Recurso `,
          `de unificación que consiste en iniciar cada uno de los movimientos del Ordinario `,
          `con la misma frase melódica o contrapuntística en las voces superiores (motivo `,
          `de cabeza).</p>\n          </div>\n          <div class="concept-card">\n        `,
          `    <div class="concept-head"><span class="concept-badge">GÉNERO</span><strong>`,
          `Formes Fixes</strong></div>\n            <p>Estructuras poético-musicales `,
          `cerradas del siglo XIV que dominaron la chanson cortesana del XV: rondeau `,
          `(ABaAabAB), ballade (aabC) y virelai / bergerette (AbbaA).</p>\n          </div>`,
          `\n          <div class="concept-card">\n            <div class="concept-head">`,
          `<span class="concept-badge">ESTILO</span><strong>Flujo Continuo y `,
          `Asimetría</strong></div>\n            <p>Técnica polifónica característica de `,
          `Johannes Ockeghem que evita deliberadamente las cesuras cadenciales simultáneas `,
          `mediante la superposición y encabalgamiento de frases melódicas `,
          `independientes.</p>\n          </div>\n          <div class="concept-card">\n    `,
          `        <div class="concept-head"><span class="concept-badge">TÉCNICA</span>`,
          `<strong>Misa Parodia (Imitación)</strong></div>\n            <p>Procedimiento `,
          `compositivo renacentista que toma como modelo una obra polifónica preexistente `,
          `completa a 3 o 4 voces, reelaborando y recombinando sus puntos de imitación y `,
          `texturas.</p>\n          </div>\n          <div class="concept-card">\n          `,
          `  <div class="concept-head"><span class="concept-badge">LENGUAJE</span><strong>`,
          `Diatonicismo Modal</strong></div>\n            <p>Conducción melódica y `,
          `polifónica basada estrictamente en los modos eclesiásticos tradicionales, con `,
          `reducción deliberada de alteraciones cromáticas fictas respecto a la complejidad `,
          `del Ars Subtilior.</p>\n          </div>\n        `
        ].join('') : (
          visuals.flatMap(v => v.items || []).slice(0, 8).map((it, i) => [
            `\n            <div class="concept-card">\n              <div `,
            [
              `class="concept-head"><span class="concept-badge">CONCEPTO ${i + 1}</span><strong>${e(it.label)}`
            ].join(''),
            `</strong></div>\n              <p>${e(it.detail)}</p>\n            </div>\n          `
          ].join('')).join('') || claims.slice(0, 6).map((c, i) => {
            const first = c.text.split('.')[0];
            return [
              `\n              <div class="concept-card">\n                <div `,
              `class="concept-head"><span class="concept-badge">CLAVE ${i + 1}</span><strong>`,
              `${e(first.slice(0, 40))}…</strong></div>\n                <p>${e(c.text)}`,
              `</p>\n              </div>\n            `
            ].join('');
          }).join('')
        )
      }`
    ].join(''),
    `\n      </div>\n    </section>\n\n    <!-- SECCIÓN 04: RELACIÓN DE 4 AUDICIONES `,
    `COMENTADAS -->\n    <section class="student-section section-listenings">\n      `,
    `<div class="student-section-header">\n        <span `,
    `class="student-section-number">04</span>\n        <div>\n          <h2>Relación `,
    `de 4 audiciones comentadas</h2>\n          <p class="student-section-intro">`,
    `Obras maestras y repertorio de audición activa con análisis formal y antologías `,
    [
      `de referencia.</p>\n        </div>\n      </div>\n      <div class="listening-grid">\n        `
    ].join(''),
    [
      `${
        isEgypt ? renderEgyptListeningsHTML(false) : isPolyphony ? POLYPHONY_LISTENINGS.map(l =>
          renderListeningCardItem(l, false)).join('') : (listenings?.length ? listenings.map(l =>
          renderListeningCardItem(l, false)).join('') : (
          [1, 2, 3, 4].map(i => {
            const act = (plan.activities || [])[i - 1] || {};
            const actTitle = act.title || `Obra y audición ${i} de la sesión`;
            return [
              `\n              <div class="listening-card">\n                <div `,
              `class="listening-head">\n                  <span class="listening-badge">AUDICIÓN ${i}`,
              `</span>\n                  <div>\n                    <strong>${e(actTitle)}`,
              `</strong>\n                    <small>Ejemplo práctico y análisis para ${e(title)}`,
              `</small>\n                  </div>\n                </div>\n                <div `,
              `class="listening-anthology">📚 Antología de partituras y fuentes de la `,
              `materia</div>\n                <div class="listening-points">\n                  `,
              [
                `<strong>Puntos clave de escucha activa:</strong>\n                  <ul>\n                    <li>`
              ].join(''),
              [
                `${
        e(act.instructions || 'Identificar la textura predominante y la articulación formal de las frases.')
        }`
              ].join(''),
              `</li>\n                    <li>Seguir la conducción melódica y los puntos de `,
              `tensión y reposo cadencial.</li>\n                    <li>Relacionar los `,
              `procedimientos técnicos escuchados con el marco histórico de la sesión.</li>\n   `,
              `               </ul>\n                </div>\n              </div>\n            `
            ].join('');
          }).join('')
        ))
      }`
    ].join(''),
    `\n      </div>\n    </section>\n\n    <!-- SECCIÓN 05: TRABAJOS PARA EL ALUMNADO `,
    `-->\n    <section class="student-section section-assignments">\n      <div `,
    `class="student-section-header">\n        <span class="student-section-number">`,
    `05</span>\n        <div>\n          <h2>Trabajos para el alumnado</h2>\n         `,
    ` <p class="student-section-intro">Tareas prácticas individuales y en grupo de `,
    `análisis sobre partituras, audición y comparación formal.</p>\n        </div>\n  `,
    `    </div>\n\n      <div class="assignment-grid">\n        `,
    [
      `${
        isEgypt ? [
          `\n          <div class="assignment-card">\n            <div `,
          `class="assignment-head">\n              <span class="assign-tag egypt-tag">`,
          `ACTIVIDAD 1 · FUNCIONES</span>\n              <strong>Diferenciación de usos `,
          `rituales y festivos</strong>\n            </div>\n            <p><strong>`,
          `Objetivo:</strong> Contrastar el papel de la música en el culto sagrado frente a `,
          `los banquetes cortesanos.</p>\n            <div class="assign-instructions">\n   `,
          `           <ul>\n                <li>Completar un cuadro analítico comparando `,
          `los espacios (templo vs. palacio) y los instrumentos utilizados.</li>\n          `,
          `      <li>Explicar qué significaba que una diosa como Hathor fuese señora de la `,
          `música y la danza.</li>\n              </ul>\n            </div>\n          `,
          `</div>\n\n          <div class="assignment-card">\n            <div `,
          `class="assignment-head">\n              <span class="assign-tag egypt-tag">`,
          `ACTIVIDAD 2 · ORGANOLOGÍA</span>\n              <strong>Clasificación de las `,
          `tres familias de instrumentos</strong>\n            </div>\n            <p>`,
          `<strong>Objetivo:</strong> Dominar la organología instrumental del Antiguo `,
          `Egipto.</p>\n            <div class="assign-instructions">\n              <ul>\n `,
          `               <li>Nombrar y describir tres instrumentos de cada familia: `,
          `cordófonos, aerófonos, percusión e idiófonos.</li>\n                <li>Indicar `,
          `con qué materiales se construía cada uno y cuál era su contexto de uso `,
          `habitual.</li>\n              </ul>\n            </div>\n          </div>\n\n    `,
          `      <div class="assignment-card">\n            <div class="assignment-head">\n `,
          `             <span class="assign-tag egypt-tag">ACTIVIDAD 3 · SIMBOLOGÍA</span>`,
          `\n              <strong>El sistrum y el culto sagrado en el templo</strong>\n    `,
          `        </div>\n            <p><strong>Objetivo:</strong> Comprender la relación `,
          `entre timbre metálico, rito y protección divina.</p>\n            <div `,
          `class="assign-instructions">\n              <ul>\n                <li>¿Qué papel `,
          `crees que tenía el sistrum en las ceremonias religiosas? ¿Por qué?</li>\n        `,
          `        <li>Relacionar el sonido de las anillas sonajas con la protección contra `,
          `el caos y las fuerzas malignas.</li>\n              </ul>\n            </div>\n  `,
          `        </div>\n\n          <div class="assignment-card">\n            <div `,
          `class="assignment-head">\n              <span class="assign-tag egypt-tag">`,
          `ACTIVIDAD 4 · ICONOGRAFÍA</span>\n              <strong>Análisis del Fresco de `,
          `la Tumba de Nebamun (c. 1350 a. C.)</strong>\n            </div>\n            <p>`,
          `<strong>Objetivo:</strong> Extraer información musical a partir de `,
          `representaciones pictóricas directas.</p>\n            <div `,
          `class="assign-instructions">\n              <ul>\n                <li>¿Cómo `,
          `sabemos que la música acompañaba a la danza en el Antiguo Egipto a partir de las `,
          `imágenes?</li>\n                <li>Identificar los gestos de las manos de los `,
          `músicos (quironimia) y la disposición de las bailarinas.</li>\n              `,
          `</ul>\n            </div>\n          </div>\n\n          <div `,
          `class="assignment-card">\n            <div class="assignment-head">\n            `,
          `  <span class="assign-tag egypt-tag">ACTIVIDAD 5 · INVESTIGACIÓN</span>\n        `,
          `      <strong>El enigma de la ausencia de partituras completas</strong>\n        `,
          `    </div>\n            <p><strong>Objetivo:</strong> Analizar el método `,
          `histórico-musicológico de aproximación a civilizaciones antiguas.</p>\n          `,
          `  <div class="assign-instructions">\n              <ul>\n                <li>`,
          `¿Por qué no conservamos partituras completas de la música egipcia?</li>\n        `,
          `        <li>Explicar cómo se combinan la iconografía, los textos, la arqueología `,
          `y la comparación.</li>\n              </ul>\n            </div>\n          </div>`,
          `\n\n          <div class="assignment-card">\n            <div `,
          `class="assignment-head">\n              <span class="assign-tag egypt-tag">`,
          `ACTIVIDAD 6 · ARQUEOLOGÍA</span>\n              <strong>Hallazgos arqueológicos `,
          `y reconstrucción sonora</strong>\n            </div>\n            <p><strong>`,
          `Objetivo:</strong> Valorar qué aporta el descubrimiento material de instrumentos `,
          `en tumbas.</p>\n            <div class="assign-instructions">\n              <ul>`,
          `\n                <li>¿Qué información nueva crees que podría aportar un `,
          `hallazgo arqueológico de un instrumento musical? Razona tu respuesta.</li>\n     `,
          `           <li>Mencionar posibles datos sobre maderas, afinación, orificios `,
          `tonales y técnicas constructivas.</li>\n              </ul>\n            </div>`,
          `\n          </div>\n        `
        ].join('') : isPolyphony ? [
          `\n          <div class="assignment-card">\n            <div class="assign-head">`,
          `\n              <span class="assign-tag">TAREA 1 · PARTITURA</span>\n            `,
          `  <strong>Rastreo auditivo y analítico del Cantus Firmus</strong>\n            `,
          `</div>\n            <p><strong>Objetivo:</strong> Seguir en la partitura el `,
          `Kyrie de la <em>Missa Se la face ay pale</em> de Du Fay e identificar con `,
          `precisión el Tenor.</p>\n            <div class="assign-instructions">\n         `,
          `     <ul>\n                <li>Subrayar con rotulador en la partitura los `,
          `compases exactos de entrada del Tenor.</li>\n                <li>Calcular `,
          `cuántos compases dura cada nota del tenor en comparación con el ritmo activo de `,
          `Superius y Altus.</li>\n                <li>Verificar en qué secciones `,
          `secundarias (como el Christe) calla el cantus firmus.</li>\n              </ul>`,
          `\n            </div>\n          </div>\n\n          <div class="assignment-card">`,
          `\n            <div class="assign-head">\n              <span class="assign-tag">`,
          `TAREA 2 · FORMA POÉTICA</span>\n              <strong>Diagramación formal de la `,
          `Chanson cortesana (Rondeau)</strong>\n            </div>\n            <p><strong>`,
          `Objetivo:</strong> Comprender la arquitectura de las formes fixes a partir de `,
          `<em>De plus en plus</em> de Binchois.</p>\n            <div `,
          `class="assign-instructions">\n              <ul>\n                <li>`,
          `Esquematizar el desarrollo formal del rondeau aplicando el molde clásico <code>`,
          `ABaAabAB</code>.</li>\n                <li>Señalar qué secciones reproducen el `,
          `estribillo completo (música y texto idénticos) y cuáles repiten solo la música `,
          `con nuevas rimas poéticas.</li>\n              </ul>\n            </div>\n       `,
          `   </div>\n\n          <div class="assignment-card">\n            <div `,
          `class="assign-head">\n              <span class="assign-tag">TAREA 3 · ESTILO Y `,
          `TEXTURA</span>\n              <strong>Matriz comparativa de estilo: Du Fay vs. `,
          `Ockeghem</strong>\n            </div>\n            <p><strong>Objetivo:</strong> `,
          `Contrastar la estética y técnica de la primera y segunda generación `,
          `franco-flamenca.</p>\n            <div class="assign-instructions">\n            `,
          `  <ul>\n                <li>Completar una tabla comparativa analizando: 1) `,
          `Formación de frases (claras vs. solapadas/flujo continuo), 2) Tesituras y `,
          `registro de voces, 3) Cadencias simultáneas y 4) Imitación contrapuntística.</li>`,
          `\n                <li>Justificar por qué Reese califica el estilo de Ockeghem `,
          `como «evitación deliberada de la articulación de frases».</li>\n              `,
          `</ul>\n            </div>\n          </div>\n\n          <div `,
          `class="assignment-card">\n            <div class="assign-head">\n              `,
          `<span class="assign-tag">TAREA 4 · CONSOLIDACIÓN</span>\n              <strong>`,
          `Cuestionario de conceptos clave del siglo XV</strong>\n            </div>\n      `,
          `      <p><strong>Objetivo:</strong> Afianzar los conceptos teóricos obligatorios `,
          `para el examen y el análisis.</p>\n            <div class="assign-instructions">`,
          `\n              <ul>\n                <li>¿Qué diferencia técnica distingue a `,
          `una misa de cantus firmus de una misa parodia?</li>\n                <li>¿Por `,
          `qué los compositores evitaban emplear melodías del propio Kyrie como cantus `,
          `firmus de la misa cíclica?</li>\n                <li>¿Qué función estructural `,
          `desempeñaba la técnica del <em>motto</em> o motivo de cabeza?</li>\n             `,
          ` </ul>\n            </div>\n          </div>\n        `
        ].join('') : [
          `\n          <div class="assignment-card">\n            <div class="assign-head">`,
          `\n              <span class="assign-tag">TAREA 1 · PARTITURA</span>\n            `,
          `  <strong>Análisis auditivo y sobre partitura</strong>\n            </div>\n     `,
          `       <p><strong>Objetivo:</strong> Localizar en la partitura los elementos `,
          `constructivos y técnicos trabajados en la sesión de ${e(title)}`,
          `.</p>\n            <div class="assign-instructions">\n              <ul>\n       `,
          `         <li>Marcar las entradas motívicas, cesuras y cambios de textura `,
          `musical.</li>\n                <li>Identificar los puntos de articulación formal `,
          `y las cadencias principales.</li>\n              </ul>\n            </div>\n     `,
          `     </div>\n\n          <div class="assignment-card">\n            <div `,
          `class="assign-head">\n              <span class="assign-tag">TAREA 2 · FORMA Y `,
          `ESTRUCTURA</span>\n              <strong>Diagramación formal y esquema `,
          `estructural</strong>\n            </div>\n            <p><strong>`,
          `Objetivo:</strong> Diseñar un mapa visual de la arquitectura formal de las obras `,
          `estudiadas.</p>\n            <div class="assign-instructions">\n              `,
          `<ul>\n                <li>Esquematizar las secciones principales (exposición, `,
          `desarrollo, reexposiciones o estribillos).</li>\n                <li>Indicar la `,
          `modulación o centros tonales/modales de cada sección.</li>\n              </ul>`,
          `\n            </div>\n          </div>\n\n          <div class="assignment-card">`,
          `\n            <div class="assign-head">\n              <span class="assign-tag">`,
          `TAREA 3 · ESTILO Y TEXTURA</span>\n              <strong>Matriz comparativa de `,
          `estilo</strong>\n            </div>\n            <p><strong>Objetivo:</strong> `,
          `Contrastar dos pasajes o ejemplos musicales analizando sus rasgos `,
          `diferenciales.</p>\n            <div class="assign-instructions">\n              `,
          `<ul>\n                <li>Elaborar una tabla analítica comparando textura `,
          `(homofonía vs. contrapunto), ritmo armónico y perfil melódico.</li>\n            `,
          `    <li>Justificar las conclusiones utilizando vocabulario técnico de `,
          `conservatorio.</li>\n              </ul>\n            </div>\n          </div>`,
          `\n\n          <div class="assignment-card">\n            <div `,
          `class="assign-head">\n              <span class="assign-tag">TAREA 4 · `,
          `CONSOLIDACIÓN</span>\n              <strong>Cuestionario de conceptos `,
          `clave</strong>\n            </div>\n            <p><strong>Objetivo:</strong> `,
          `Afianzar el dominio de los conceptos obligatorios de la unidad.</p>\n            `,
          `<div class="assign-instructions">\n              <ul>\n                <li>`,
          `Definir con precisión técnica los términos obligatorios de la sesión.</li>\n     `,
          `           <li>Redactar una síntesis razonada ilustrando cada concepto con un `,
          [
            `ejemplo musical concreto.</li>\n              </ul>\n            </div>\n          </div>\n        `
          ].join('')
        ].join('')
      }`
    ].join(''),
    `\n      </div>\n\n      <!-- SECUENCIA DE TRABAJO EN EL AULA -->\n      <div `,
    `class="class-session-work">\n        <h3 class="session-work-title">⏱ Secuencia `,
    [
      `de trabajo y actividades en el aula</h3>\n        <div class="student-activities">\n          `
    ].join(''),
    [
      `${
        (plan.activities || []).map((activity, index) => {
          const mins = Number(activity.minutes) || 0;
          const start = elapsed;
          elapsed += mins;
          return [
            `\n                    <div class="student-activity">\n                      <span>${start}–`,
            `${elapsed} min</span>\n                      <div>\n                        <h3>${index + 1}. `,
            `${e(activity.title)}</h3>\n                        <p>${e(activity.instructions)}`,
            `</p>\n                      </div>\n                    </div>\n                  `
          ].join('');
        }).join('')
      }`
    ].join(''),
    `\n        </div>\n      </div>\n    </section>\n\n    <!-- SECCIÓN 06: FUENTES Y `,
    `BIBLIOGRAFÍA DE CONSULTA -->\n    <section class="student-section `,
    `section-sources">\n      <div class="student-section-header">\n        <span `,
    `class="student-section-number">06</span>\n        <div>\n          <h2>Fuentes y `,
    `antologías de consulta</h2>\n          <p class="student-section-intro">`,
    `Bibliografía autorizada y ediciones de partituras utilizadas para elaborar este `,
    [
      `material.</p>\n        </div>\n      </div>\n      <div class="sources-pills-list">\n        `
    ].join(''),
    [
      `${
        isEgypt ? [
          `\n                <div class="source-pill-card">\n                  <span `,
          `class="source-pill-icon">📖</span>\n                  <div>\n                    `,
          `<strong>Music in Ancient Mesopotamia and Egypt</strong>\n                    `,
          `<small>Marcelle Duchesne-Guillemin · World of Music / Garland</small>\n          `,
          `        </div>\n                </div>\n                <div `,
          `class="source-pill-card">\n                  <span class="source-pill-icon">`,
          `📖</span>\n                  <div>\n                    <strong>Norton Anthology `,
          `of Western Music (Ancient to Baroque)</strong>\n                    <small>J. `,
          `Peter Burkholder & Claude V. Palisca · W. W. Norton</small>\n                  `,
          `</div>\n                </div>\n                <div class="source-pill-card">\n `,
          `                 <span class="source-pill-icon">📖</span>\n                  <div>`,
          `\n                    <strong>Historia de la estética musical: desde la `,
          `Antigüedad hasta el siglo XX</strong>\n                    <small>Enrico Fubini `,
          `· Alianza Música</small>\n                  </div>\n                </div>\n     `,
          `           <div class="source-pill-card">\n                  <span `,
          `class="source-pill-icon">🏺</span>\n                  <div>\n                    `,
          `<strong>Iconografía y textos de las tumbas de Nebamun, Ti y Tutankamón</strong>`,
          `\n                    <small>Museo Británico (Londres) / Museo de El `,
          `Cairo</small>\n                  </div>\n                </div>\n              `
        ].join('') : isPolyphony ? [
          `\n                <div class="source-pill-card">\n                  <span `,
          `class="source-pill-icon">📖</span>\n                  <div>\n                    `,
          `<strong>La música del Renacimiento & Antología de la música del `,
          `Renacimiento</strong>\n                    <small>Allan W. Atlas · Ediciones `,
          `Akal / Norton</small>\n                  </div>\n                </div>\n        `,
          `        <div class="source-pill-card">\n                  <span `,
          `class="source-pill-icon">📖</span>\n                  <div>\n                    `,
          `<strong>La música en el Renacimiento</strong>\n                    <small>`,
          `Gustave Reese · Alianza Música</small>\n                  </div>\n               `,
          ` </div>\n                <div class="source-pill-card">\n                  <span `,
          `class="source-pill-icon">📖</span>\n                  <div>\n                    `,
          `<strong>Atlas de la Música (Vol. 1)</strong>\n                    <small>Ulrich `,
          `Michels · Alianza Editorial</small>\n                  </div>\n                `,
          `</div>\n                <div class="source-pill-card">\n                  <span `,
          `class="source-pill-icon">🎼</span>\n                  <div>\n                    `,
          `<strong>Manuscrito Chigi C.VIII.234</strong>\n                    <small>`,
          `Biblioteca Apostólica Vaticana · Misas y motetes de Johannes Ockeghem</small>\n  `,
          `                </div>\n                </div>\n              `
        ].join('') : ''
      }`
    ].join(''),
    `\n        `,
    [
      `${
        sources.filter(s => s.title && !s.title.includes('Atlas') && !s.title.includes('Reese') && !s.title.includes(
          'Duchesne')).map(meta => [
          `\n          <div class="source-pill-card">\n            <span `,
          [
            `class="source-pill-icon">📄</span>\n            <div>\n              <strong>${e(meta.title)}`
          ].join(''),
          `</strong>\n              <small>${e(meta.authors?.join(', ') || 'Biblioteca Enjambre')}`,
          [
            `${meta.year ? ` · ${meta.year}` : ''}</small>\n            </div>\n          </div>\n        `
          ].join('')
        ].join('')).join('')
      }`
    ].join(''),
    [
      `\n      </div>\n    </section>\n\n    ${renderStudentDiscographySection(run)}\n  </article>`
    ].join('')
  ].join('');
}

export function printStudentDocument() {
  const handout = document.querySelector('.student-dialog .student-handout');
  if (!handout) {
    document.body.classList.add('student-printing');
    window.addEventListener('afterprint', () => document.body.classList.remove('student-printing'), {
      once: true
    });
    window.print();
    return;
  }

  // Clone handout content so the on-screen modal stays intact
  const clone = handout.cloneNode(true);

  // For Ancient Egypt sheets: remove interactive tabs and show both sheets sequentially
  clone.querySelectorAll('.egypt-sheet-tabs').forEach(el => el.remove());
  clone.querySelectorAll('.egypt-sheet').forEach(el => {
    el.style.display = 'block';
  });

  // Remove buttons and interactive elements
  clone.querySelectorAll('.button, button, [data-action]').forEach(el => el.remove());

  // Use an isolated hidden iframe for 100% clean, non-modal browser printing
  let iframe = document.getElementById('student-print-frame');
  if (iframe) iframe.remove();

  iframe = document.createElement('iframe');
  iframe.id = 'student-print-frame';
  iframe.style.position = 'fixed';
  iframe.style.right = '0';
  iframe.style.bottom = '0';
  iframe.style.width = '0';
  iframe.style.height = '0';
  iframe.style.border = '0';
  iframe.style.visibility = 'hidden';
  document.body.appendChild(iframe);

  const doc = iframe.contentWindow.document;
  const docTitle = document.querySelector('.student-cover h1')?.textContent?.trim() ||
    'Material para el alumnado';

  doc.open();
  doc.write('<!doctype html><html lang="es"><head><meta charset="utf-8"><title>' + docTitle +
    ' · Enjambre</title></head><body class="print-isolated-body"></body></html>');
  doc.close();

  // Copy all style elements and stylesheets so custom typography, colors, and layout apply
  document.querySelectorAll('link[rel="stylesheet"], style').forEach(node => {
    doc.head.appendChild(node.cloneNode(true));
  });

  doc.body.appendChild(clone);

  setTimeout(() => {
    try {
      iframe.contentWindow.focus();
      iframe.contentWindow.print();
    } catch (e) {
      document.body.classList.add('student-printing');
      window.addEventListener('afterprint', () => document.body.classList.remove('student-printing'), {
        once: true
      });
      window.print();
    }
  }, 250);
}

export async function studentMaterialModal(id) {
  const run = await api('/runs/' + encodeURIComponent(id));
  if (!run.request?.pedagogy || !run.result?.plan) throw new Error(
    'Esta propuesta todavía no tiene material válido para el alumnado.');
  modal('Material para el alumnado', [
    `${studentDocumentHTML(run)}`,
    `<div class="student-share-actions"><div><strong>Listo para compartir</strong><p>`,
    `Copia el contenido en Google Classroom o guárdalo como PDF.</p></div><button `,
    `class="button" data-copy-student="${e(id)}">${icon('copy')}`,
    `Copiar para Classroom</button><button class="button" data-download-student="${e(id)}">`,
    `${icon('download')}Descargar Markdown</button><button class="button primary" `,
    `data-action="print-student">${icon('document')}Imprimir / Guardar PDF</button></div>`
  ].join(''));
  dialog.classList.add('student-dialog');
}
