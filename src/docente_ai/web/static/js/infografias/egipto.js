// Módulo local: responsabilidad separada sin alterar el contenido.


export function switchEgyptTab(btn, tabId) {
  const poster = btn.closest('.egypt-infographic-poster');
  if (!poster) return;
  poster.querySelectorAll('.egypt-tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const p1 = poster.querySelector('#egypt-page-1');
  const p2 = poster.querySelector('#egypt-page-2');
  if (p1) p1.style.display = (tabId === 'egypt-page-1') ? 'block' : 'none';
  if (p2) p2.style.display = (tabId === 'egypt-page-2') ? 'block' : 'none';
}

export function renderEgyptInfographic(run) {
  return `
    <div class="infographic-poster egypt-infographic-poster">
      <!-- CONTROL DE PÁGINAS DE LÁMINAS -->
      <div class="egypt-page-tabs">
        <span class="egypt-tab-label">LÁMINAS DIDÁCTICAS · HISTORIA DA MÚSICA I:</span>
        <button type="button" class="egypt-tab-btn active" data-tab="egypt-page-1">
          📜 Lámina 1: Contexto, funciones y rasgos
        </button>
        <button type="button" class="egypt-tab-btn" data-tab="egypt-page-2">
          𓏢 Lámina 2: Instrumentos, práctica y fuentes
        </button>
      </div>

      <!-- ==================== PÁGINA 1 ==================== -->
      <div id="egypt-page-1" class="egypt-sheet">
        <header class="egypt-sheet-header">
          <div class="egypt-header-top">
            <div class="egypt-header-icon">𓏢</div>
            <div class="egypt-header-center">
              <h1>LA MÚSICA EN EL ANTIGUO EGIPTO</h1>
              <span class="egypt-sheet-sub">APUNTES PARA EL ALUMNADO</span>
              <span class="egypt-sheet-page-indicator">Página 1: contexto, funciones y rasgos generales</span>
            </div>
            <div class="egypt-header-side">
              <span>MÚSICA</span>
              <span>CULTURA</span>
              <span>MEMORIA</span>
              <span>SOCIEDAD</span>
            </div>
          </div>
        </header>

        <!-- SECCIÓN 1: MARCO HISTÓRICO -->
        <section class="egypt-block block-historical">
          <div class="egypt-block-title-row">
            <span class="egypt-num-badge">1</span>
            <div>
              <h3>MARCO HISTÓRICO</h3>
              <small>Una civilización, un río, una música milenaria</small>
            </div>
          </div>
          <div class="egypt-hist-body">
            <div class="egypt-hist-text">
              <p>La civilización egipcia se desarrolló a lo largo del valle del Nilo, un entorno que favoreció la estabilidad, la agricultura y una gran continuidad cultural desde el Imperio Antiguo (hacia 2700 a. C.) hasta el período grecorromano (siglos IV a. C. – IV d. C.).</p>
              <p>La música está presente en tumbas, relieves, pinturas y textos, lo que demuestra su importancia en la vida religiosa, política, social y cotidiana. <strong>No se conservan partituras completas</strong> como en la tradición occidental, por lo que nuestro conocimiento procede principalmente de fuentes iconográficas (imágenes), textuales (inscripciones y textos) y arqueológicas (instrumentos, objetos y contextos materiales).</p>
            </div>
            <div class="egypt-nile-card">
              <div class="nile-illustration">
                <svg viewBox="0 0 200 80" class="nile-svg">
                  <path d="M0,60 Q50,45 100,55 T200,50 L200,80 L0,80 Z" fill="#38bdf8" opacity="0.35"/>
                  <path d="M0,65 Q50,55 100,62 T200,58 L200,80 L0,80 Z" fill="#0284c7" opacity="0.4"/>
                  <polygon points="120,48 145,15 170,48" fill="#e2b170"/>
                  <polygon points="145,15 170,48 185,48" fill="#c69251"/>
                  <polygon points="90,50 110,24 130,50" fill="#edd09b"/>
                  <path d="M30,58 Q32,35 34,22" stroke="#78350f" stroke-width="2" fill="none"/>
                  <circle cx="34" cy="22" r="8" fill="#15803d" opacity="0.8"/>
                  <path d="M22,59 Q25,40 26,28" stroke="#78350f" stroke-width="1.8" fill="none"/>
                  <circle cx="26" cy="28" r="7" fill="#166534" opacity="0.8"/>
                  <polygon points="65,56 75,56 80,52 60,52" fill="#78350f"/>
                  <polygon points="70,52 70,30 82,48" fill="#ffffff" stroke="#cbd5e1" stroke-width="0.8"/>
                </svg>
              </div>
              <p class="nile-quote">«El Nilo no solo dio vida a Egipto, también inspiró su música.»</p>
              <span class="nile-tag">EL NILO, UNA CIVILIZACIÓN DE MIL SONIDOS</span>
            </div>
          </div>
        </section>

        <!-- SECCIÓN 2: FUNCIONES DE LA MÚSICA -->
        <section class="egypt-block block-functions">
          <div class="egypt-block-title-row">
            <span class="egypt-num-badge">2</span>
            <div>
              <h3>FUNCIONES DE LA MÚSICA</h3>
              <small>Una misma música para los dioses, la muerte, la fiesta y la vida cotidiana</small>
            </div>
          </div>
          <div class="egypt-functions-grid">
            <!-- 1. RELIGIOSA Y RITUAL -->
            <div class="fn-card fn-religious">
              <div class="fn-header">
                <span class="fn-symbol">☥</span>
                <h4>RELIGIOSA Y RITUAL</h4>
              </div>
              <div class="fn-scene">
                <div class="scene-badge">Templo y Ceremonia</div>
                <div class="scene-desc">Sacerdotisas con arpas e himnos sagrados</div>
              </div>
              <ul class="fn-points">
                <li>La música formaba parte del culto a los dioses, con himnos, cantos, procesiones y ceremonias en los templos.</li>
                <li>Divinidades como <strong>Hathor</strong> (alegría, música y danza) e <strong>Isis</strong> (magia y protección) estaban especialmente vinculadas a la música.</li>
                <li>Sacerdotisas y músicos del templo desempeñaban un papel fundamental en los rituales y ofrendas.</li>
              </ul>
              <div class="fn-footer">
                <span>𓆸 Hathor, señora de la música, la danza y la alegría.</span>
              </div>
            </div>

            <!-- 2. FUNERARIA -->
            <div class="fn-card fn-funerary">
              <div class="fn-header">
                <span class="fn-symbol">𓂀</span>
                <h4>FUNERARIA</h4>
              </div>
              <div class="fn-scene">
                <div class="scene-badge">Viaje al Más Allá</div>
                <div class="scene-desc">Cortejo fúnebre, flautas y lamento ritual</div>
              </div>
              <ul class="fn-points">
                <li>La música estaba presente en los ritos funerarios, acompañando al difunto en su tránsito al Más Allá.</li>
                <li>Se interpretaban cantos y piezas instrumentales en ceremonias de enterramiento y ofrendas.</li>
                <li>Dimensión ritual y conmemorativa para honrar la memoria del difunto y desear su renacimiento eterno.</li>
              </ul>
              <div class="fn-footer">
                <span>𓂀 La música acompañaba al difunto en su viaje eterno.</span>
              </div>
            </div>

            <!-- 3. CORTESANA Y FESTIVA -->
            <div class="fn-card fn-court">
              <div class="fn-header">
                <span class="fn-symbol">🪷</span>
                <h4>CORTESANA Y FESTIVA</h4>
              </div>
              <div class="fn-scene">
                <div class="scene-badge">Palacios y Banquetes</div>
                <div class="scene-desc">Arpistas, danzas y recepciones de la élite</div>
              </div>
              <ul class="fn-points">
                <li>La música sonaba en banquetes, recepciones y celebraciones de la élite y la familia real.</li>
                <li>Acompañaba la danza, el entretenimiento y la vida social en los palacios.</li>
                <li>Piezas instrumentales y canciones con una clara función lúdica y de prestigio cortesano.</li>
              </ul>
              <div class="fn-footer">
                <span>🪷 Música y danza en los jardines del palacio.</span>
              </div>
            </div>

            <!-- 4. POPULAR Y LABORAL -->
            <div class="fn-card fn-popular">
              <div class="fn-header">
                <span class="fn-symbol">🌾</span>
                <h4>POPULAR Y LABORAL</h4>
              </div>
              <div class="fn-scene">
                <div class="scene-badge">Campo y Talleres</div>
                <div class="scene-desc">Remeros, agricultores y canciones de faena</div>
              </div>
              <ul class="fn-points">
                <li>Canciones vinculadas al trabajo: agricultores, constructores o remeros en el río.</li>
                <li>Acompañaba las tareas colectivas, marcando el pulso rítmico y facilitando la coordinación.</li>
                <li>Presente en la vida cotidiana del pueblo: coplas de amor, juegos y celebraciones festivas.</li>
              </ul>
              <div class="fn-footer">
                <span>🌾 El ritmo también movía la vida diaria.</span>
              </div>
            </div>
          </div>
        </section>

        <!-- SECCIÓN 3: RASGOS GENERALES -->
        <section class="egypt-block block-traits">
          <div class="egypt-block-title-row">
            <span class="egypt-num-badge">3</span>
            <div>
              <h3>RASGOS GENERALES</h3>
              <small>Más que sonido: un lenguaje total</small>
            </div>
          </div>
          <div class="egypt-traits-body">
            <div class="traits-text">
              <p>En el Antiguo Egipto, <strong>la música, la poesía y la danza estaban estrechamente unidas</strong> y formaban parte de un mismo lenguaje artístico y simbólico. La música no se entendía solo como sonido acústico, sino como una experiencia integral que incluía gesto, movimiento corporal, palabra poética y contexto ceremonial.</p>
              <p>Se practicaba tanto el canto monódico como la interpretación instrumental. El ritmo y la expresividad gestual eran elementos esenciales. Las representaciones pictóricas muestran una <strong>participación femenina muy visible</strong>, tanto como cantantes, instrumentistas y bailarinas, como en roles rituales sacerdotales junto a músicos varones.</p>
            </div>
            <div class="traits-badge-card">
              <span class="traits-badge-title">ARTE TOTAL</span>
              <p>«Música, danza y palabra, unidas en armonía.»</p>
              <div class="traits-symbols">𓏢 · 𓀤 · 𓀥 · 𓀠</div>
            </div>
          </div>
        </section>

        <!-- SECCIONES 4 Y 5: IDEAS PARA ESTUDIAR Y VOCABULARIO BÁSICO -->
        <div class="egypt-dual-grid">
          <!-- SECCIÓN 4: IDEAS PARA ESTUDIAR -->
          <section class="egypt-block block-study-keys">
            <div class="egypt-block-title-row">
              <span class="egypt-num-badge">4</span>
              <div>
                <h3>IDEAS PARA ESTUDIAR</h3>
                <small>Cinco claves para recordar</small>
              </div>
            </div>
            <ol class="study-keys-list">
              <li><span>1</span><div>Egipto tuvo una larga continuidad cultural desde el Imperio Antiguo hasta el período grecorromano.</div></li>
              <li><span>2</span><div>La música aparece en tumbas, relieves, pinturas y textos; no se conservan partituras completas.</div></li>
              <li><span>3</span><div>Cumplía cuatro funciones esenciales: religiosa, funeraria, cortesana y popular/laboral.</div></li>
              <li><span>4</span><div>Estaba unida a la poesía, la danza, el gesto ritual y el contexto ceremonial (arte total).</div></li>
              <li><span>5</span><div>Las mujeres tuvieron un papel protagonista y sumamente visible en la práctica musical.</div></li>
            </ol>
          </section>

          <!-- SECCIÓN 5: VOCABULARIO BÁSICO -->
          <section class="egypt-block block-vocabulary">
            <div class="egypt-block-title-row">
              <span class="egypt-num-badge">5</span>
              <div>
                <h3>VOCABULARIO BÁSICO</h3>
                <small>Términos esenciales</small>
              </div>
            </div>
            <div class="vocab-table">
              <div class="vocab-row"><strong>Canto ritual</strong><span>Canto en contextos religiosos dirigido a los dioses, vinculado a ofrendas y liturgia.</span></div>
              <div class="vocab-row"><strong>Iconografía</strong><span>Representaciones visuales (pinturas, relieves) que documentan instrumentos y músicos.</span></div>
              <div class="vocab-row"><strong>Relieve</strong><span>Escultura mural en muros de templos o tumbas mostrando escenas musicales y rituales.</span></div>
              <div class="vocab-row"><strong>Aerófono</strong><span>Instrumento de viento por vibración de columna de aire (flauta, clarinete doble, trompeta).</span></div>
              <div class="vocab-row"><strong>Cordófono</strong><span>Instrumento de cuerda que suena al pulsar cuerdas tensadas (arpa arqueada, laúd, lira).</span></div>
              <div class="vocab-row"><strong>Idiófono</strong><span>Instrumento cuyo propio cuerpo vibra al agitarse o golpearse (sistro, menat, crótalos).</span></div>
            </div>
            <div class="egypt-remember-box">
              <span class="rem-icon">☥ 𓂀</span>
              <p><strong>Recuerda:</strong> en Egipto la música no era solo entretenimiento; también era religión, rito, memoria y representación social.</p>
            </div>
          </section>
        </div>

        <footer class="egypt-sheet-footer">
          <span>UN RÍO. UNA CIVILIZACIÓN. INFINITAS MELODÍAS.</span>
        </footer>
      </div>

      <!-- ==================== PÁGINA 2 ==================== -->
      <div id="egypt-page-2" class="egypt-sheet" style="display:none;">
        <header class="egypt-sheet-header">
          <div class="egypt-header-top">
            <div class="egypt-header-icon">𓏢</div>
            <div class="egypt-header-center">
              <h1>LA MÚSICA EN EL ANTIGUO EGIPTO</h1>
              <span class="egypt-sheet-sub">APUNTES PARA EL ALUMNADO</span>
              <span class="egypt-sheet-page-indicator">Página 2 de 2: instrumentos, práctica musical y fuentes</span>
            </div>
            <div class="egypt-header-side">
              <span>ORGANOLOGÍA</span>
              <span>PRÁCTICA</span>
              <span>FUENTES</span>
              <span>HISTORIA</span>
            </div>
          </div>
          <p class="egypt-banner-motto">La música, un legado sonoro de una gran civilización</p>
        </header>

        <!-- SECCIÓN 1: PRINCIPALES INSTRUMENTOS -->
        <section class="egypt-block block-instruments">
          <div class="egypt-block-title-row">
            <span class="egypt-num-badge">1</span>
            <div>
              <h3>PRINCIPALES INSTRUMENTOS</h3>
              <small>Diversos timbres y funciones para la vida religiosa, social y cortesana</small>
            </div>
          </div>
          <div class="instruments-columns-grid">
            <!-- CORDÓFONOS -->
            <div class="inst-col inst-chordophones">
              <div class="inst-col-head">
                <h4>CORDÓFONOS</h4>
                <small>Cuerdas que se hacen sonar al ser pulsadas</small>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Arpa arqueada</strong><span class="inst-pill">Cortesano</span></div>
                <p>Muy representada en pinturas y relieves. Asociada a banquetes, templos y acompañamiento de cantos. Sonido claro y envolvente.</p>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Laúd</strong><span class="inst-pill">Vida cotidiana</span></div>
                <p>Mástil largo y pequeña caja de resonancia. Común en escenas festivas del Imperio Nuevo. Timbre cálido y suave.</p>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Lira</strong><span class="inst-pill">Religioso y profano</span></div>
                <p>Estructura en forma de U con cuerdas paralelas. Importada de Asia anterior y adoptada en ceremonias. Timbre brillante.</p>
              </div>
            </div>

            <!-- AERÓFONOS -->
            <div class="inst-col inst-aerophones">
              <div class="inst-col-head">
                <h4>AERÓFONOS</h4>
                <small>Viento que se transforma en sonido</small>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Flautas rectas</strong><span class="inst-pill">Caña / Madera</span></div>
                <p>Varios orificios tonales. Usadas en la corte, pastoreo y ritos religiosos. Producían sonoridades dulces y expresivas.</p>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Clarinetes dobles</strong><span class="inst-pill">Lengüeta batiente</span></div>
                <p>Dos tubos de caña paralelos que sonaban simultáneamente. Sonido penetrante y nasal, empleado en procesiones y danzas.</p>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Trompetas</strong><span class="inst-pill">Bronce / Plata</span></div>
                <p>Asociadas al ejército, audiencias del faraón y ritos solemnes (como las de Tutankamón). Toques sonoros para marcar momentos clave.</p>
              </div>
            </div>

            <!-- PERCUSIÓN E IDIÓFONOS -->
            <div class="inst-col inst-idiophones">
              <div class="inst-col-head">
                <h4>PERCUSIÓN E IDIÓFONOS</h4>
                <small>Golpeados, agitados o entrechocados</small>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Sistros</strong><span class="inst-pill">Sagrado (Hathor)</span></div>
                <p>Marco de metal con varillas y anillas sonajas. Al agitarse emitía un brillo metálico para ahuyentar el mal en procesiones.</p>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Menat</strong><span class="inst-pill">Collar ritual</span></div>
                <p>Collar de cuentas con contrapeso tañido por sacerdotisas de Hathor. Producía un tintineo rítmico asociado a la fertilidad.</p>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Tambores y Crótalos</strong><span class="inst-pill">Pulso y Danza</span></div>
                <p>Tambores de mano o doble parche y palillos/crótalos entrechocados de madera o marfil para guiar el movimiento corporal.</p>
              </div>
            </div>
          </div>
        </section>

        <!-- SECCIÓN 2: AGRUPACIONES Y PRÁCTICA MUSICAL -->
        <section class="egypt-block block-practice">
          <div class="egypt-block-title-row">
            <span class="egypt-num-badge">2</span>
            <div>
              <h3>AGRUPACIONES Y PRÁCTICA MUSICAL</h3>
              <small>Música en solitario, en conjunto y en movimiento</small>
            </div>
          </div>
          <div class="practice-body-grid">
            <div class="practice-formats-list">
              <div class="pf-item"><strong>Solistas:</strong> Músicos y músicas actuando en solitario (arpistas y cantantes) en la corte y escenas íntimas.</div>
              <div class="pf-item"><strong>Pequeños conjuntos:</strong> Combinación habitual de cámara: arpa, flauta doble y percusión rítmica.</div>
              <div class="pf-item"><strong>Música y danza:</strong> La música guiaba la coreografía en banquetes y templos mediante sistros y tambores.</div>
              <div class="pf-item"><strong>Canto e instrumentos:</strong> Alternancia antifonal entre solista y coro, con instrumentos respondiendo a las frases.</div>
              <div class="pf-item"><strong>Coordinación y Quironimia:</strong> Gestualidad consciente de manos y miradas del director para marcar alturas y giros melódicos.</div>
            </div>
            <div class="practice-mural-card">
              <div class="mural-visual-box">
                <div class="mural-scene-tag">Fresco de la Tumba de Nebamun (c. 1350 a. C.)</div>
                <div class="mural-caption">Música, danza y coordinación entre intérpretes</div>
              </div>
              <div class="mural-quotes">
                <p>«La música acompaña la vida: en el templo, en la corte, en la fiesta y en el trabajo.»</p>
                <p>«Diferentes instrumentos, una misma finalidad: expresar, comunicar, celebrar y conectar con lo divino.»</p>
              </div>
            </div>
          </div>
        </section>

        <!-- SECCIÓN 3: FUENTES PARA SU ESTUDIO -->
        <section class="egypt-block block-sources">
          <div class="egypt-block-title-row">
            <span class="egypt-num-badge">3</span>
            <div>
              <h3>FUENTES PARA SU ESTUDIO</h3>
              <small>Un pasado que se reconstruye a través de sus huellas</small>
            </div>
          </div>
          <div class="egypt-sources-grid">
            <div class="src-card">
              <span class="src-icon">🎨</span>
              <strong>Iconografía</strong>
              <p>Pinturas murales, relieves en tumbas y templos, estatuas y cerámicas que revelan posturas, conjuntos y usos sociales.</p>
            </div>
            <div class="src-card">
              <span class="src-icon">📜</span>
              <strong>Textos</strong>
              <p>Himnos litúrgicos, inscripciones jeroglíficas, documentos administrativos y poemas que describen a los músicos.</p>
            </div>
            <div class="src-card">
              <span class="src-icon">🏺</span>
              <strong>Arqueología</strong>
              <p>Instrumentos conservados en ajuares funerarios secos (arpa, sistro, trompeta) que permiten analizar acústica y materiales.</p>
            </div>
            <div class="src-card">
              <span class="src-icon">⚖️</span>
              <strong>Comparación</strong>
              <p>Estudio etnomusicológico comparado con tradiciones del Próximo Oriente y monodia mediterránea posterior.</p>
            </div>
          </div>
        </section>

        <!-- SECCIÓN 4: COMENTARIO HISTÓRICO-MUSICAL -->
        <section class="egypt-block block-commentary">
          <div class="egypt-block-title-row">
            <span class="egypt-num-badge">4</span>
            <div>
              <h3>COMENTARIO HISTÓRICO-MUSICAL</h3>
              <small>Sonido, ritual y sociedad en perspectiva</small>
            </div>
          </div>
          <div class="commentary-content">
            <p>La música en el Antiguo Egipto es fundamental para comprender cómo el sonido actuaba como un <strong>puente entre lo humano y lo divino</strong>. Presente en la religión, la corte, el trabajo y las celebraciones fúnebres, reflejaba el orden cósmico (<em>Maat</em>) y la cohesión de la sociedad egipcia. Aunque no conservamos partituras completas con notación cifrada, la convergencia de la iconografía, los instrumentos conservados y los textos poéticos demuestra una sofisticada cultura musical con más de tres milenios de evolución ininterrumpida.</p>
          </div>
        </section>

        <!-- SECCIONES 5 Y 6: ACTIVIDADES DE REPASO Y GLOSARIO -->
        <div class="egypt-dual-grid">
          <!-- SECCIÓN 5: ACTIVIDADES DE REPASO -->
          <section class="egypt-block block-review-tasks">
            <div class="egypt-block-title-row">
              <span class="egypt-num-badge">5</span>
              <div>
                <h3>ACTIVIDADES DE REPASO</h3>
                <small>Comprueba y aplica lo aprendido</small>
              </div>
            </div>
            <ol class="review-questions-list">
              <li><span>1</span><div>¿En qué se diferencian los usos rituales y los usos festivos de la música egipcia?</div></li>
              <li><span>2</span><div>Nombra al menos tres instrumentos de cada familia (cordófonos, aerófonos, percusión e idiófonos).</div></li>
              <li><span>3</span><div>¿Qué papel crees que tenía el sistrum en las ceremonias religiosas? ¿Por qué?</div></li>
              <li><span>4</span><div>¿Cómo sabemos que la música acompañaba a la danza en el Antiguo Egipto?</div></li>
              <li><span>5</span><div>¿Por qué no conservamos partituras completas de la música egipcia?</div></li>
              <li><span>6</span><div>¿Qué información nueva crees que podría aportar un hallazgo arqueológico de un instrumento musical? Razona tu respuesta.</div></li>
            </ol>
          </section>

          <!-- SECCIÓN 6: GLOSARIO COMPLEMENTARIO -->
          <section class="egypt-block block-glossary">
            <div class="egypt-block-title-row">
              <span class="egypt-num-badge">6</span>
              <div>
                <h3>GLOSARIO COMPLEMENTARIO</h3>
                <small>Términos clave para tu estudio</small>
              </div>
            </div>
            <div class="glossary-items-list">
              <div class="gl-item"><strong>Sistrum:</strong> Instrumento de metal con anillas sagrado de Hathor en contextos rituales.</div>
              <div class="gl-item"><strong>Menat:</strong> Collar ritual con cuentas y contrapeso que emitía un suave tintineo.</div>
              <div class="gl-item"><strong>Arqueología musical:</strong> Estudio material y acústico de restos de instrumentos antiguos.</div>
              <div class="gl-item"><strong>Organología:</strong> Disciplina que clasifica, construye y estudia los instrumentos musicales.</div>
              <div class="gl-item"><strong>Canto llano (comparación):</strong> Monodia vocal litúrgica sin acompañamiento instrumental.</div>
              <div class="gl-item"><strong>Reconstrucción histórica:</strong> Formulación de hipótesis sonoras a partir de las fuentes conservadas.</div>
            </div>
          </section>
        </div>

        <footer class="egypt-sheet-footer">
          <span class="egypt-key-idea">Idea clave: estudiamos la música egipcia a través de imágenes, objetos, textos y comparaciones, no a través de partituras completas.</span>
          <span class="egypt-final-motto">«EL PASADO TAMBIÉN SUENA CUANDO SABEMOS ESCUCHARLO.»</span>
        </footer>
      </div>
    </div>
  `;
}
