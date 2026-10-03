// Módulo local: responsabilidad separada sin alterar el contenido.
import { api } from '../api.js';
import { POLYPHONY_LISTENINGS, getRunListenings, is15thCenturyPolyphony, isAncientEgypt, renderEgyptListeningsHTML, renderListeningCardItem, renderStudentDiscographySection } from './audiciones.js';
import { renderEgyptInfographic } from '../infografias/egipto.js';
import { renderStudentInfographic } from '../infografias/musica.js';
import { dialog, e, formatMarkdown, icon, modal } from '../ui.js';

export function studentDocumentHTML(run) {
  const context = run.request?.pedagogy || {}, plan = run.result?.plan || {}, claims = run.result?.claims || [];
  const session = context.session;
  const sources = [...new Map((run.evidence || []).map(item => [item.document_id, item.metadata])).values()];
  const title = (run.request?.question || '').charAt(0).toLocaleUpperCase('es') + (run.request?.question || '').slice(1);
  const visuals = run.result?.visualizations || [];
  const isPolyphony = is15thCenturyPolyphony(run);
  const isEgypt = isAncientEgypt(run);
  const listenings = isPolyphony ? POLYPHONY_LISTENINGS : getRunListenings(run);
  let elapsed = 0;

  return `<article class="student-handout">
    <header class="student-cover">
      <div class="student-brand">
        <span class="student-pill">ENJAMBRE · MATERIAL DE CLASE</span>
        <span class="student-topic-tag">CUADERNO DIDÁCTICO DEL ALUMNADO</span>
      </div>
      <h1>${e(title)}</h1>
      <div class="student-meta">
        <strong>${e(context.group?.name || 'Grupo')}</strong>
        <span>${e(context.group?.level || 'Conservatorio')}</span>
        <span>⏱ ${context.duration_minutes || 60} minutos</span>
        ${session ? `<span>📅 ${e(session.date)}</span>` : ''}
      </div>
    </header>

    <!-- OBJETIVOS DIDÁCTICOS -->
    <section class="student-section section-intro">
      <div class="student-section-header">
        <span class="student-section-number">🎯</span>
        <div>
          <h2>Qué vamos a aprender</h2>
          <p class="student-section-intro">Objetivos y competencias formativas que desarrollaremos a lo largo de la sesión.</p>
        </div>
      </div>
      <ol class="student-objectives">
        ${(plan.objectives || []).map(item => `<li>${e(item)}</li>`).join('')}
      </ol>
    </section>

    <!-- SECCIÓN 01: CONTENIDO TEÓRICO DE LAS FUENTES -->
    <section class="student-section section-theory">
      <div class="student-section-header">
        <span class="student-section-number">01</span>
        <div>
          <h2>Contenido teórico de las fuentes</h2>
          <p class="student-section-intro">Análisis musicológico e histórico basado en las fuentes documentales autorizadas${isPolyphony ? ' (Allan Atlas, Gustave Reese y Ulrich Michels)' : isEgypt ? ' (Marcelle Duchesne-Guillemin, J. Peter Burkholder y Enrico Fubini)' : ''}.</p>
        </div>
      </div>
      <div class="theory-claims-list">
        ${claims.map((claim, index) => `
          <div class="student-content theory-claim-card">
            <span class="claim-index-badge">${String(index + 1).padStart(2, '0')}</span>
            <div class="claim-body">
              ${formatMarkdown(claim.text)}
              ${claim.evidence?.length ? `<div class="claim-source-badge"><span>📖 Fuente: ${e(claim.evidence[0].source_id)}</span></div>` : ''}
            </div>
          </div>
        `).join('')}
      </div>
    </section>

    <!-- SECCIÓN 02: ESQUEMA GRÁFICO (MODELOS Y TÉCNICAS) -->
    <section class="student-section section-infographic">
      <div class="student-section-header">
        <span class="student-section-number">02</span>
        <div>
          <h2>Esquema gráfico: ${isEgypt ? 'Marco histórico, funciones y organología del Antiguo Egipto' : isPolyphony ? 'Modelos y técnicas de composición del siglo XV' : 'Modelos y estructuras técnicas'}</h2>
          <p class="student-section-intro">${isEgypt ? 'Láminas didácticas de contexto, funciones sociales, organología, quironimia y fuentes de estudio.' : isPolyphony ? 'Estructuras vocálicas, transformaciones del material y recursos de unificación cíclica.' : 'Estructuras formales y esquemas comparativos para el aula.'}</p>
        </div>
      </div>
      ${isEgypt ? renderEgyptInfographic(run) : (isPolyphony ? renderStudentInfographic(run) : (
        visuals.length ? `
          <div class="infographic-poster">
            <div class="infographic-main-head">
              <div class="info-tag-row">
                <span class="info-badge">${e(title.toUpperCase())}</span>
                <span class="info-badge-sub">ESQUEMAS TÉCNICOS Y ESTRUCTURAS FORMALES</span>
              </div>
              <h2>MODELOS Y ANÁLISIS DE TEXTURAS</h2>
              <p class="info-subtitle">Estructuras formales y esquemas comparativos para el aula</p>
            </div>
            <div class="visual-items">${visuals.map(v => `
              <div class="visual-card">
                <h3>${e(v.title)}</h3>
                ${v.caption ? `<p class="visual-caption">${e(v.caption)}</p>` : ''}
                <div class="visual-items">${v.items.map(it => `
                  <div class="visual-item">
                    <strong>${e(it.label)}</strong>
                    <span>${e(it.detail)}</span>
                  </div>
                `).join('')}</div>
              </div>
            `).join('')}</div>
          </div>
        ` : `
          <div class="infographic-poster">
            <div class="infographic-main-head">
              <div class="info-tag-row"><span class="info-badge">${e(title.toUpperCase())}</span></div>
              <h2>ESQUEMA CONCEPTUAL Y ESTRUCTURAL</h2>
            </div>
            <div class="visual-items">${claims.slice(0, 4).map((c, i) => `
              <div class="visual-item"><strong>Eje ${i + 1}</strong><span>${e(c.text.slice(0, 180))}…</span></div>
            `).join('')}</div>
          </div>
        `
      ))}
    </section>

    <!-- SECCIÓN 03: CONCEPTOS OBLIGATORIOS PARA APRENDER -->
    <section class="student-section section-concepts">
      <div class="student-section-header">
        <span class="student-section-number">03</span>
        <div>
          <h2>Conceptos obligatorios para aprender</h2>
          <p class="student-section-intro">Vocabulario técnico y conceptos analíticos indispensables del currículo de conservatorio.</p>
        </div>
      </div>
      <div class="concept-grid">
        ${isEgypt ? `
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-ritual">RITUAL</span><strong>Sistrum (Sistro)</strong></div>
            <p>Instrumento sagrado de percusión con marco metálico y varillas sonajas, consagrado al culto de Hathor para ahuyentar las fuerzas del caos.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-ritual">RITUAL</span><strong>Menat</strong></div>
            <p>Collar ceremonial con cuentas y contrapeso pectoral que las sacerdotisas de Hathor agitaban produciendo un suave tintineo purificador.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-gesto">DIRECCIÓN</span><strong>Quironimia</strong></div>
            <p>Sistema de dirección musical mediante gestos de manos, dedos y cuerpo que el cantor/director hacía a los instrumentistas para guiar melodía y ritmo.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-cordas">CORDÓFONO</span><strong>Arpa Arqueada</strong></div>
            <p>Principal cordófono del Antiguo Egipto, con cuerpo curvo de madera y cuerdas tensadas tañidas por solistas en la corte, banquetes y templos.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-vento">AERÓFONO</span><strong>Clarinete Doble</strong></div>
            <p>Aerófono compuesto por dos tubos paralelos de caña provistos de lengüetas batientes, con sonido penetrante usado en procesiones y danzas.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-liturxia">LITURGIA</span><strong>Canto Ritual</strong></div>
            <p>Monodia vocal entonada en templos y ritos funerarios, concebida como puente directo de comunicación entre el ser humano y las divinidades.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-fonte">ICONOGRAFÍA</span><strong>Iconografía Musical</strong></div>
            <p>Estudio sistemático de las fuentes visuales (frescos de tumbas como la de Nebamun y relieves en templos) para reconstruir la práctica musical.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-arqueo">MÉTODO</span><strong>Arqueología Musical</strong></div>
            <p>Análisis científico de los instrumentos materiales conservados en tumbas secas para deducir acústica histórica, materiales y afinaciones.</p>
          </div>
        ` : isPolyphony ? `
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">TÉCNICA</span><strong>Cantus Firmus</strong></div>
            <p>Melodía preexistente (canto gregoriano o canción profana) empleada como eje estructural de una nueva composición polifónica, asignada tradicionalmente al Tenor en notas de valores largos.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">RITMO</span><strong>Aumentación Rítmica</strong></div>
            <p>Procedimiento consistente en alargar proporcionalmente las duraciones de las figuras de la melodía original (duplicar o triplicar su valor), confiriendo al Tenor un ritmo lento y solemne.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">FORMA</span><strong>Misa Cíclica</strong></div>
            <p>Obra litúrgica polifónica monumental en la que los cinco movimientos del Ordinario (Kyrie, Gloria, Credo, Sanctus, Agnus Dei) comparten el mismo material temático unificador.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">RECURSO</span><strong>Técnica del Motto</strong></div>
            <p>Recurso de unificación que consiste en iniciar cada uno de los movimientos del Ordinario con la misma frase melódica o contrapuntística en las voces superiores (motivo de cabeza).</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">GÉNERO</span><strong>Formes Fixes</strong></div>
            <p>Estructuras poético-musicales cerradas del siglo XIV que dominaron la chanson cortesana del XV: rondeau (ABaAabAB), ballade (aabC) y virelai / bergerette (AbbaA).</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">ESTILO</span><strong>Flujo Continuo y Asimetría</strong></div>
            <p>Técnica polifónica característica de Johannes Ockeghem que evita deliberadamente las cesuras cadenciales simultáneas mediante la superposición y encabalgamiento de frases melódicas independientes.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">TÉCNICA</span><strong>Misa Parodia (Imitación)</strong></div>
            <p>Procedimiento compositivo renacentista que toma como modelo una obra polifónica preexistente completa a 3 o 4 voces, reelaborando y recombinando sus puntos de imitación y texturas.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">LENGUAJE</span><strong>Diatonicismo Modal</strong></div>
            <p>Conducción melódica y polifónica basada estrictamente en los modos eclesiásticos tradicionales, con reducción deliberada de alteraciones cromáticas fictas respecto a la complejidad del Ars Subtilior.</p>
          </div>
        ` : (
          visuals.flatMap(v => v.items || []).slice(0, 8).map((it, i) => `
            <div class="concept-card">
              <div class="concept-head"><span class="concept-badge">CONCEPTO ${i + 1}</span><strong>${e(it.label)}</strong></div>
              <p>${e(it.detail)}</p>
            </div>
          `).join('') || claims.slice(0, 6).map((c, i) => {
            const first = c.text.split('.')[0];
            return `
              <div class="concept-card">
                <div class="concept-head"><span class="concept-badge">CLAVE ${i + 1}</span><strong>${e(first.slice(0, 40))}…</strong></div>
                <p>${e(c.text)}</p>
              </div>
            `;
          }).join('')
        )}
      </div>
    </section>

    <!-- SECCIÓN 04: RELACIÓN DE 4 AUDICIONES COMENTADAS -->
    <section class="student-section section-listenings">
      <div class="student-section-header">
        <span class="student-section-number">04</span>
        <div>
          <h2>Relación de 4 audiciones comentadas</h2>
          <p class="student-section-intro">Obras maestras y repertorio de audición activa con análisis formal y antologías de referencia.</p>
        </div>
      </div>
      <div class="listening-grid">
        ${isEgypt ? renderEgyptListeningsHTML(false) : isPolyphony ? POLYPHONY_LISTENINGS.map(l => renderListeningCardItem(l, false)).join('') : (listenings?.length ? listenings.map(l => renderListeningCardItem(l, false)).join('') : (
          [1, 2, 3, 4].map(i => {
            const act = (plan.activities || [])[i - 1] || {};
            const actTitle = act.title || `Obra y audición ${i} de la sesión`;
            return `
              <div class="listening-card">
                <div class="listening-head">
                  <span class="listening-badge">AUDICIÓN ${i}</span>
                  <div>
                    <strong>${e(actTitle)}</strong>
                    <small>Ejemplo práctico y análisis para ${e(title)}</small>
                  </div>
                </div>
                <div class="listening-anthology">📚 Antología de partituras y fuentes de la materia</div>
                <div class="listening-points">
                  <strong>Puntos clave de escucha activa:</strong>
                  <ul>
                    <li>${e(act.instructions || 'Identificar la textura predominante y la articulación formal de las frases.')}</li>
                    <li>Seguir la conducción melódica y los puntos de tensión y reposo cadencial.</li>
                    <li>Relacionar los procedimientos técnicos escuchados con el marco histórico de la sesión.</li>
                  </ul>
                </div>
              </div>
            `;
          }).join('')
        ))}
      </div>
    </section>

    <!-- SECCIÓN 05: TRABAJOS PARA EL ALUMNADO -->
    <section class="student-section section-assignments">
      <div class="student-section-header">
        <span class="student-section-number">05</span>
        <div>
          <h2>Trabajos para el alumnado</h2>
          <p class="student-section-intro">Tareas prácticas individuales y en grupo de análisis sobre partituras, audición y comparación formal.</p>
        </div>
      </div>

      <div class="assignment-grid">
        ${isEgypt ? `
          <div class="assignment-card">
            <div class="assignment-head">
              <span class="assign-tag egypt-tag">ACTIVIDAD 1 · FUNCIONES</span>
              <strong>Diferenciación de usos rituales y festivos</strong>
            </div>
            <p><strong>Objetivo:</strong> Contrastar el papel de la música en el culto sagrado frente a los banquetes cortesanos.</p>
            <div class="assign-instructions">
              <ul>
                <li>Completar un cuadro analítico comparando los espacios (templo vs. palacio) y los instrumentos utilizados.</li>
                <li>Explicar qué significaba que una diosa como Hathor fuese señora de la música y la danza.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assignment-head">
              <span class="assign-tag egypt-tag">ACTIVIDAD 2 · ORGANOLOGÍA</span>
              <strong>Clasificación de las tres familias de instrumentos</strong>
            </div>
            <p><strong>Objetivo:</strong> Dominar la organología instrumental del Antiguo Egipto.</p>
            <div class="assign-instructions">
              <ul>
                <li>Nombrar y describir tres instrumentos de cada familia: cordófonos, aerófonos, percusión e idiófonos.</li>
                <li>Indicar con qué materiales se construía cada uno y cuál era su contexto de uso habitual.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assignment-head">
              <span class="assign-tag egypt-tag">ACTIVIDAD 3 · SIMBOLOGÍA</span>
              <strong>El sistrum y el culto sagrado en el templo</strong>
            </div>
            <p><strong>Objetivo:</strong> Comprender la relación entre timbre metálico, rito y protección divina.</p>
            <div class="assign-instructions">
              <ul>
                <li>¿Qué papel crees que tenía el sistrum en las ceremonias religiosas? ¿Por qué?</li>
                <li>Relacionar el sonido de las anillas sonajas con la protección contra el caos y las fuerzas malignas.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assignment-head">
              <span class="assign-tag egypt-tag">ACTIVIDAD 4 · ICONOGRAFÍA</span>
              <strong>Análisis del Fresco de la Tumba de Nebamun (c. 1350 a. C.)</strong>
            </div>
            <p><strong>Objetivo:</strong> Extraer información musical a partir de representaciones pictóricas directas.</p>
            <div class="assign-instructions">
              <ul>
                <li>¿Cómo sabemos que la música acompañaba a la danza en el Antiguo Egipto a partir de las imágenes?</li>
                <li>Identificar los gestos de las manos de los músicos (quironimia) y la disposición de las bailarinas.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assignment-head">
              <span class="assign-tag egypt-tag">ACTIVIDAD 5 · INVESTIGACIÓN</span>
              <strong>El enigma de la ausencia de partituras completas</strong>
            </div>
            <p><strong>Objetivo:</strong> Analizar el método histórico-musicológico de aproximación a civilizaciones antiguas.</p>
            <div class="assign-instructions">
              <ul>
                <li>¿Por qué no conservamos partituras completas de la música egipcia?</li>
                <li>Explicar cómo se combinan la iconografía, los textos, la arqueología y la comparación.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assignment-head">
              <span class="assign-tag egypt-tag">ACTIVIDAD 6 · ARQUEOLOGÍA</span>
              <strong>Hallazgos arqueológicos y reconstrucción sonora</strong>
            </div>
            <p><strong>Objetivo:</strong> Valorar qué aporta el descubrimiento material de instrumentos en tumbas.</p>
            <div class="assign-instructions">
              <ul>
                <li>¿Qué información nueva crees que podría aportar un hallazgo arqueológico de un instrumento musical? Razona tu respuesta.</li>
                <li>Mencionar posibles datos sobre maderas, afinación, orificios tonales y técnicas constructivas.</li>
              </ul>
            </div>
          </div>
        ` : isPolyphony ? `
          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 1 · PARTITURA</span>
              <strong>Rastreo auditivo y analítico del Cantus Firmus</strong>
            </div>
            <p><strong>Objetivo:</strong> Seguir en la partitura el Kyrie de la <em>Missa Se la face ay pale</em> de Du Fay e identificar con precisión el Tenor.</p>
            <div class="assign-instructions">
              <ul>
                <li>Subrayar con rotulador en la partitura los compases exactos de entrada del Tenor.</li>
                <li>Calcular cuántos compases dura cada nota del tenor en comparación con el ritmo activo de Superius y Altus.</li>
                <li>Verificar en qué secciones secundarias (como el Christe) calla el cantus firmus.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 2 · FORMA POÉTICA</span>
              <strong>Diagramación formal de la Chanson cortesana (Rondeau)</strong>
            </div>
            <p><strong>Objetivo:</strong> Comprender la arquitectura de las formes fixes a partir de <em>De plus en plus</em> de Binchois.</p>
            <div class="assign-instructions">
              <ul>
                <li>Esquematizar el desarrollo formal del rondeau aplicando el molde clásico <code>ABaAabAB</code>.</li>
                <li>Señalar qué secciones reproducen el estribillo completo (música y texto idénticos) y cuáles repiten solo la música con nuevas rimas poéticas.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 3 · ESTILO Y TEXTURA</span>
              <strong>Matriz comparativa de estilo: Du Fay vs. Ockeghem</strong>
            </div>
            <p><strong>Objetivo:</strong> Contrastar la estética y técnica de la primera y segunda generación franco-flamenca.</p>
            <div class="assign-instructions">
              <ul>
                <li>Completar una tabla comparativa analizando: 1) Formación de frases (claras vs. solapadas/flujo continuo), 2) Tesituras y registro de voces, 3) Cadencias simultáneas y 4) Imitación contrapuntística.</li>
                <li>Justificar por qué Reese califica el estilo de Ockeghem como «evitación deliberada de la articulación de frases».</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 4 · CONSOLIDACIÓN</span>
              <strong>Cuestionario de conceptos clave del siglo XV</strong>
            </div>
            <p><strong>Objetivo:</strong> Afianzar los conceptos teóricos obligatorios para el examen y el análisis.</p>
            <div class="assign-instructions">
              <ul>
                <li>¿Qué diferencia técnica distingue a una misa de cantus firmus de una misa parodia?</li>
                <li>¿Por qué los compositores evitaban emplear melodías del propio Kyrie como cantus firmus de la misa cíclica?</li>
                <li>¿Qué función estructural desempeñaba la técnica del <em>motto</em> o motivo de cabeza?</li>
              </ul>
            </div>
          </div>
        ` : `
          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 1 · PARTITURA</span>
              <strong>Análisis auditivo y sobre partitura</strong>
            </div>
            <p><strong>Objetivo:</strong> Localizar en la partitura los elementos constructivos y técnicos trabajados en la sesión de ${e(title)}.</p>
            <div class="assign-instructions">
              <ul>
                <li>Marcar las entradas motívicas, cesuras y cambios de textura musical.</li>
                <li>Identificar los puntos de articulación formal y las cadencias principales.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 2 · FORMA Y ESTRUCTURA</span>
              <strong>Diagramación formal y esquema estructural</strong>
            </div>
            <p><strong>Objetivo:</strong> Diseñar un mapa visual de la arquitectura formal de las obras estudiadas.</p>
            <div class="assign-instructions">
              <ul>
                <li>Esquematizar las secciones principales (exposición, desarrollo, reexposiciones o estribillos).</li>
                <li>Indicar la modulación o centros tonales/modales de cada sección.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 3 · ESTILO Y TEXTURA</span>
              <strong>Matriz comparativa de estilo</strong>
            </div>
            <p><strong>Objetivo:</strong> Contrastar dos pasajes o ejemplos musicales analizando sus rasgos diferenciales.</p>
            <div class="assign-instructions">
              <ul>
                <li>Elaborar una tabla analítica comparando textura (homofonía vs. contrapunto), ritmo armónico y perfil melódico.</li>
                <li>Justificar las conclusiones utilizando vocabulario técnico de conservatorio.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 4 · CONSOLIDACIÓN</span>
              <strong>Cuestionario de conceptos clave</strong>
            </div>
            <p><strong>Objetivo:</strong> Afianzar el dominio de los conceptos obligatorios de la unidad.</p>
            <div class="assign-instructions">
              <ul>
                <li>Definir con precisión técnica los términos obligatorios de la sesión.</li>
                <li>Redactar una síntesis razonada ilustrando cada concepto con un ejemplo musical concreto.</li>
              </ul>
            </div>
          </div>
        `}
      </div>

      <!-- SECUENCIA DE TRABAJO EN EL AULA -->
      <div class="class-session-work">
        <h3 class="session-work-title">⏱ Secuencia de trabajo y actividades en el aula</h3>
        <div class="student-activities">
          ${(plan.activities || []).map((activity, index) => {
            const mins = Number(activity.minutes) || 0;
            const start = elapsed;
            elapsed += mins;
            return `
              <div class="student-activity">
                <span>${start}–${elapsed} min</span>
                <div>
                  <h3>${index + 1}. ${e(activity.title)}</h3>
                  <p>${e(activity.instructions)}</p>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    </section>

    <!-- SECCIÓN 06: FUENTES Y BIBLIOGRAFÍA DE CONSULTA -->
    <section class="student-section section-sources">
      <div class="student-section-header">
        <span class="student-section-number">06</span>
        <div>
          <h2>Fuentes y antologías de consulta</h2>
          <p class="student-section-intro">Bibliografía autorizada y ediciones de partituras utilizadas para elaborar este material.</p>
        </div>
      </div>
      <div class="sources-pills-list">
        ${isEgypt ? `
          <div class="source-pill-card">
            <span class="source-pill-icon">📖</span>
            <div>
              <strong>Music in Ancient Mesopotamia and Egypt</strong>
              <small>Marcelle Duchesne-Guillemin · World of Music / Garland</small>
            </div>
          </div>
          <div class="source-pill-card">
            <span class="source-pill-icon">📖</span>
            <div>
              <strong>Norton Anthology of Western Music (Ancient to Baroque)</strong>
              <small>J. Peter Burkholder & Claude V. Palisca · W. W. Norton</small>
            </div>
          </div>
          <div class="source-pill-card">
            <span class="source-pill-icon">📖</span>
            <div>
              <strong>Historia de la estética musical: desde la Antigüedad hasta el siglo XX</strong>
              <small>Enrico Fubini · Alianza Música</small>
            </div>
          </div>
          <div class="source-pill-card">
            <span class="source-pill-icon">🏺</span>
            <div>
              <strong>Iconografía y textos de las tumbas de Nebamun, Ti y Tutankamón</strong>
              <small>Museo Británico (Londres) / Museo de El Cairo</small>
            </div>
          </div>
        ` : isPolyphony ? `
          <div class="source-pill-card">
            <span class="source-pill-icon">📖</span>
            <div>
              <strong>La música del Renacimiento & Antología de la música del Renacimiento</strong>
              <small>Allan W. Atlas · Ediciones Akal / Norton</small>
            </div>
          </div>
          <div class="source-pill-card">
            <span class="source-pill-icon">📖</span>
            <div>
              <strong>La música en el Renacimiento</strong>
              <small>Gustave Reese · Alianza Música</small>
            </div>
          </div>
          <div class="source-pill-card">
            <span class="source-pill-icon">📖</span>
            <div>
              <strong>Atlas de la Música (Vol. 1)</strong>
              <small>Ulrich Michels · Alianza Editorial</small>
            </div>
          </div>
          <div class="source-pill-card">
            <span class="source-pill-icon">🎼</span>
            <div>
              <strong>Manuscrito Chigi C.VIII.234</strong>
              <small>Biblioteca Apostólica Vaticana · Misas y motetes de Johannes Ockeghem</small>
            </div>
          </div>
        ` : ''}
        ${sources.filter(s => s.title && !s.title.includes('Atlas') && !s.title.includes('Reese') && !s.title.includes('Duchesne')).map(meta => `
          <div class="source-pill-card">
            <span class="source-pill-icon">📄</span>
            <div>
              <strong>${e(meta.title)}</strong>
              <small>${e(meta.authors?.join(', ') || 'Biblioteca Enjambre')}${meta.year ? ` · ${meta.year}` : ''}</small>
            </div>
          </div>
        `).join('')}
      </div>
    </section>

    ${renderStudentDiscographySection(run)}
  </article>`;
}

export function printStudentDocument() {
  const handout = document.querySelector('.student-dialog .student-handout');
  if (!handout) {
    document.body.classList.add('student-printing');
    window.addEventListener('afterprint', () => document.body.classList.remove('student-printing'), { once: true });
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
  const docTitle = document.querySelector('.student-cover h1')?.textContent?.trim() || 'Material para el alumnado';

  doc.open();
  doc.write('<!doctype html><html lang="es"><head><meta charset="utf-8"><title>' + docTitle + ' · Enjambre</title></head><body class="print-isolated-body"></body></html>');
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
      window.addEventListener('afterprint', () => document.body.classList.remove('student-printing'), { once: true });
      window.print();
    }
  }, 250);
}

export async function studentMaterialModal(id) {
  const run=await api('/runs/'+encodeURIComponent(id));
  if(!run.request?.pedagogy||!run.result?.plan)throw new Error('Esta propuesta todavía no tiene material válido para el alumnado.');
  modal('Material para el alumnado',`${studentDocumentHTML(run)}<div class="student-share-actions"><div><strong>Listo para compartir</strong><p>Copia el contenido en Google Classroom o guárdalo como PDF.</p></div><button class="button" data-copy-student="${e(id)}">${icon('copy')}Copiar para Classroom</button><button class="button" data-download-student="${e(id)}">${icon('download')}Descargar Markdown</button><button class="button primary" data-action="print-student">${icon('document')}Imprimir / Guardar PDF</button></div>`);
  dialog.classList.add('student-dialog');
}
