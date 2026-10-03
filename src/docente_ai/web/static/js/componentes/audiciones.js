import { e } from '../ui.js';
// Módulo local: responsabilidad separada sin alterar el contenido.

export function is15thCenturyPolyphony(run) {
  const text = ((run.request?.question || '') + ' ' + (run.request?.pedagogy?.teacher_criteria || '') + ' ' +
    (run.result?.claims || []).map(c => c.text).join(' ')).toLowerCase();
  return text.includes('xv') || text.includes('ockeghem') || text.includes('dufay') || text.includes(
    'binchois') || text.includes('busnois') || text.includes('cantus firmus') || text.includes(
    'formes fixes') || text.includes('chanson') || text.includes('misa');
}

export function isAncientEgypt(run) {
  const q = (run.request?.question || '').toLowerCase();
  const criteria = (run.request?.pedagogy?.teacher_criteria || '').toLowerCase();
  const claims = (run.result?.claims || []).map(c => c.text).join(' ').toLowerCase();
  const unitTitle = (run.request?.pedagogy?.unit?.title || '').toLowerCase();
  const unitId = run.request?.pedagogy?.unit?.id || run.request?.pedagogy?.unit_id || '';
  const text = `${q} ${criteria} ${claims} ${unitTitle}`;
  return text.includes('egipt') || text.includes('nilo') || text.includes('hathor') || text.includes(
      'sistro') || text.includes('menat') || text.includes('nebamun') || text.includes('mesopotamia') || text
    .includes('antigüedad') || text.includes('antiga') || unitId === 'unit-h1-1';
}

export const POLYPHONY_LISTENINGS = [{
  index: 1,
  composer: 'Guillaume Du Fay',
  title: 'Missa Se la face ay pale',
  subtitle: 'Kyrie y Gloria · Misa de cantus firmus secular a 4 voces sobre su propia chanson balada',
  performer: 'Early Music Consort of London, dir. David Munrow',
  anthology: 'Allan Atlas (Antología Norton, nº 14) / Gustave Reese',
  links: [{
    label: 'Escuchar el Kyrie en YouTube',
    url: 'https://www.youtube.com/watch?v=izy4bDPp23k'
  }, {
    label: 'Escuchar el Gloria en YouTube',
    url: 'https://www.youtube.com/watch?v=McyAlOZ4JjQ'
  }],
  teacher_note: 'Son especialmente útiles porque pertenecen a la misma grabación y mantienen una ' +
    'interpretación homogénea.',
  points: [
    'Identificar la entrada del Tenor en valores aumentados (proporción 3:1 en el Gloria).',
    'Observar el contraste tímbrico entre las notas sostenidas del Tenor y el contrapunto ágil de Superius y Altus.',
    'Detectar la articulación cadencial Landini (salto melódico de sexta a octava).'
  ]
}, {
  index: 2,
  composer: 'Gilles Binchois',
  title: 'De plus en plus se renouvelle',
  subtitle: 'Chanson cortesana borgoñona a 3 voces (Forme Fixe: Rondeau)',
  performer: 'Ensemble Gilles Binchois, dir. Dominique Vellard',
  anthology: 'Allan Atlas (Antología Norton, nº 11) / Gustave Reese',
  links: [{
    label: 'Escuchar De plus en plus en YouTube',
    url: 'https://www.youtube.com/watch?v=cw_V53noTUg'
  }],
  teacher_note: 'Esta versión me parece particularmente apropiada para apreciar el carácter ' +
    'lírico de la chanson y la claridad de las tres voces.',
  points: [
    'Seguir la melodía lírica y transparente del Superius en ritmo ternario suave.',
    'Apreciar la sonoridad dulce de terceras y sextas imperfectas (contenance angloise).',
    'Distinguir la claridad meridiana de las frases musicales delimitadas por cadencias nítidas.'
  ]
}, {
  index: 3,
  composer: 'Johannes Ockeghem',
  title: "Missa L'homme armé",
  subtitle: 'Kyrie y Agnus Dei · Misa de cantus firmus a 4 voces sobre la popular melodía borgoñona',
  performer: 'Oxford Camerata, dir. Jeremy Summerly',
  anthology: 'Manuscrito Chigi C.VIII.234 (Vaticano) / Gustave Reese',
  links: [{
    label: 'Escuchar el Kyrie en YouTube',
    url: 'https://www.youtube.com/watch?v=KgV3cxc1NEI'
  }, {
    label: 'Escuchar el Agnus Dei en YouTube',
    url: 'https://www.youtube.com/watch?v=xDFKOKWzpI0'
  }],
  teacher_note: 'También aquí tienes la ventaja de utilizar la misma interpretación para ambos movimientos.',
  points: [
    'Percibir el registro vocal más profundo y homogéneo (el Bassus desciende a graves inusuales en Du Fay).',
    'Comprobar cómo las frases se solapan en un flujo polifónico continuo sin pausas colectivas.',
    'Escuchar los apéndices ornamentales añadidos al cantus firmus en el Tenor.'
  ]
}, {
  index: 4,
  composer: 'Johannes Ockeghem',
  title: 'Mort, tu as navré (Déploration sur la mort de Binchois)',
  subtitle: 'Motete-chanson funerario bilingüe a 4 voces (1460)',
  performer: 'Graindelavoix, dir. Björn Schmelzer',
  anthology: 'Allan Atlas (Cap. XI-XII) / Gustave Reese',
  links: [{
    label: 'Escuchar Mort, tu as navré en YouTube',
    url: 'https://www.youtube.com/watch?v=R9tcg1VfKPs'
  }],
  teacher_note: 'Esta grabación funciona muy bien para clase por el contraste con las audiciones ' +
    'anteriores y por el carácter expresivo y sombrío de la obra.',
  points: [
    'Reconocer la textura bilingüe: Superius canta en francés la balada y el Tenor canta en latín el Pie Jhesu Domine.',
    'Identificar la paráfrasis litúrgica del canto llano del Dies Irae en el Tenor.',
    'Sentir el austero diatonicismo modal y el clima sombrío de homenaje al maestro borgoñón.'
  ]
}];

export const EGYPT_LISTENINGS = [{
  index: '1A',
  composer: 'Michael Levy',
  title: 'Ancient Harps of Kemet',
  subtitle: 'Arpa arqueada · Recreación tímbrica e improvisación moderna (2011)',
  performer: 'Michael Levy (arpa arqueada de tipo arcaico)',
  anthology: 'Reconstrucción organológica / Arqueomusicología experimental',
  links: [{
    label: 'Escuchar en YouTube (Levy – Ancient Harps of Kemet)',
    url: 'https://www.youtube.com/watch?v=mqxB34z4tyw'
  }],
  teacher_note: 'No es una pieza transmitida desde el Egipto faraónico: es una improvisación ' +
    'moderna sobre un arpa arqueada de tipo arcaico. Resulta útil para que el ' +
    'alumnado escuche un modelo de sonoridad próximo a la iconografía y para ' +
    'plantear cómo se reconstruye un paisaje sonoro cuando faltan partituras.',
  points: [
    'El ataque de la cuerda pulsada y la resonancia corta del instrumento.',
    'La ausencia de progresiones armónicas funcionales propias de la tonalidad moderna.',
    'La repetición y variación de células breves como recurso para construir continuidad.',
    'La diferencia entre escuchar el timbre de un instrumento reconstruido y afirmar que conocemos la música original.'
  ]
}, {
  index: '1B',
  composer: 'Michael Levy',
  title: 'Reconstructed Ancient Egyptian Melody',
  subtitle: 'Arreglo para lira de propuesta reconstructiva vinculada a escena de banquete tebano',
  performer: 'Michael Levy (lira; melodía basada en De Organographia y flauta vertical)',
  anthology: 'Escena de banquete tebano / Ensemble De Organographia',
  links: [{
    label: 'Escuchar en YouTube (Levy – Reconstructed Melody)',
    url: 'https://www.youtube.com/watch?v=nBmWXmn11YE'
  }],
  teacher_note: 'Levy explica que tomó la melodía de De Organographia y que la escala se ' +
    'relacionó con una flauta vertical egipcia conservada. La utilidad didáctica ' +
    'está en observar el procedimiento de reconstrucción, no en tomar el resultado ' +
    'como una transcripción segura de 1400 a. C.',
  points: [
    'El perfil melódico: movimiento conjunto, fórmulas breves y clara sensación modal.',
    'La repetición ornamental y la ausencia de una dirección armónica tonal fuerte.',
    'Cómo una fuente iconográfica puede convertirse en hipótesis sonora.',
    'Qué partes de lo que oímos son dato arqueológico y cuáles son decisión del intérprete moderno.'
  ]
}, {
  index: '2',
  composer: 'De Organographia',
  title: 'Isis Sistrum Rhythm, after Apuleius',
  subtitle: 'Reconstrucción breve de ritmo ritual de sistro (0:31) a partir de Apuleyo (época romana)',
  performer: 'Ensemble De Organographia (Music of the Ancient Sumerians, Egyptians & Greeks)',
  anthology: 'Apuleyo (Metamorfosis) / Culto de Isis y Hathor',
  links: [{
    label: 'Escuchar en YouTube (De Organographia – Isis Sistrum Rhythm)',
    url: 'https://www.youtube.com/watch?v=599YEae4DYA'
  }],
  teacher_note: 'Sustitución más segura para el aula: reconstruye un ritmo de sistro asociado a ' +
    'Isis a partir de Apuleyo, permitiendo trabajar el instrumento y su función ' +
    'ritual sin presentar como auténtica una melodía no conservada.',
  points: [
    'El timbre metálico y brillante del sistro (sejem/sesheshet) producido por el movimiento de sus varillas móviles.',
    'La función del pulso y del gesto repetido más que el desarrollo de una melodía.',
    'La relación del sistro y el menat con el culto ritual y divinidades como Hathor e Isis.',
    'La diferencia entre un ritmo reconstruido desde una fuente literaria tardía y una música faraónica conservada.'
  ]
}, {
  index: '3',
  composer: 'Descarte metodológico razonado',
  title: 'Canto colectivo de labor (Descartada deliberadamente)',
  subtitle: 'Módulo de análisis crítico de fuentes iconográficas en lugar de audición especulativa',
  performer: 'Sin grabación musical: rigor epistemológico en el aula',
  anthology: 'Escenas parietales de trabajo agrícola y navegación (Tumbas del Reino Antiguo y Nuevo)',
  links: [],
  teacher_note: 'Descartada como audición: existen escenas y textos que sugieren canto durante ' +
    'el trabajo, pero no conservamos melodía ni ritmo que permitan identificar con ' +
    'rigor un ejemplo faraónico. Se trabaja en el aula como análisis crítico de ' +
    'fuentes iconográficas.',
  points: [
    'Observar una escena parietal de trabajo colectivo (siega, molienda o remeros en el Nilo).',
    'Describir qué información objetiva aporta la imagen y separar lo que sabemos de lo que inferimos.',
    'Comprender por qué la ausencia de notación exige cautela metodológica frente a audiciones especulativas.'
  ]
}, {
  index: '4',
  composer: 'Grabación histórica BBC (1939)',
  title: "King Tutankhamun's Trumpets (Trompetas de Tutankamón)",
  subtitle: 'Instrumentos originales (c. 1323 a. C.); interpretación de James Tappern (El Cairo)',
  performer: 'James Tappern (trompetista militar), retransmisión oficial BBC El Cairo (1939)',
  anthology: 'Tumba KV62 de Tutankamón / Museo de El Cairo / BBC & Society of Antiquaries',
  links: [{
    label: 'Escuchar en YouTube (King Tutankhamun\'s Trumpets – Grabación BBC 1939)',
    url: 'https://www.youtube.com/watch?v=Qt9AyV3hnlc'
  }, {
    label: 'BBC Ghost Music (Documental sobre las trompetas)',
    url: 'https://www.bbc.co.uk/programmes/b010dp0s'
  }],
  teacher_note: 'Audición más excepcional del conjunto: en 1939 se hicieron sonar dos trompetas ' +
    'auténticas de la tumba de Tutankamón. Documenta el sonido posible de esos ' +
    'objetos, pero con técnica militar moderna del siglo XX y boquilla adaptada.',
  points: [
    'El timbre directo, metálico y de gran proyección al aire libre.',
    'La limitada disponibilidad de alturas sonoras, propia de un tubo natural sin válvulas ni llaves.',
    'La emisión de sonidos relacionados con la serie de armónicos naturales.',
    'La diferencia crucial entre hacer sonar un instrumento antiguo y reconstruir su práctica musical original.'
  ]
}];

export function getRunListenings(run) {
  if (is15thCenturyPolyphony(run)) {
    return POLYPHONY_LISTENINGS;
  }
  if (isAncientEgypt(run)) {
    return EGYPT_LISTENINGS;
  }
  const criteria = run.request?.pedagogy?.teacher_criteria || '';
  const ytRegex =
    /\[([^\]]+)\]\((https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)[\w\-_&?=]+)\)/gi;
  const matches = [...criteria.matchAll(ytRegex)];
  if (matches.length > 0) {
    return matches.map((m, idx) => ({
      index: idx + 1,
      composer: 'Referencia aportada por el profesor',
      title: m[1],
      subtitle: 'Grabación de apoyo indicada en los criterios docentes',
      anthology: 'Material audiovisual aportado por el profesor',
      links: [{
        label: m[1],
        url: m[2]
      }],
      teacher_note: 'Enlace de audición suministrado directamente en los criterios docentes.',
      points: [
        'Audición atenta del fragmento musical seleccionado.',
        'Vinculación de los rasgos audibles con los contenidos de la sesión.'
      ]
    }));
  }
  return null;
}

export function renderListeningCardItem(l, isProposal = false) {
  const linksHTML = (l.links || []).map(link => [
    `\n    <a href="${e(link.url)}`,
    `" target="_blank" rel="noopener noreferrer" class="yt-link-btn" title="Abrir `,
    `audición en YouTube">\n      <svg class="icon yt-icon" viewBox="0 0 24 24" `,
    `width="16" height="16" style="vertical-align:-3px;margin-right:4px;"><path `,
    `fill="#dc2626" d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.5 12 3.5 `,
    `12 3.5s-7.505 0-9.377.55a3.016 3.016 0 0 0-2.122 2.136C0 8.07 0 12 0 12s0 `,
    `3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.55 9.376.55 9.376.55s7.505 0 `,
    `9.377-.55a3.016 3.016 0 0 0 2.122-2.136C24 15.93 24 12 24 `,
    `12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>\n      <span>`,
    `${e(link.label)}</span>\n      <svg class="icon" viewBox="0 0 25 25" `,
    `style="width:12px;height:12px;margin-left:4px;opacity:0.8"><path d="M13 `,
    `4h7v7m0-7L10 14M9 4H4v16h16v-5" stroke="currentColor" fill="none" `,
    `stroke-width="2"/></svg>\n    </a>\n  `
  ].join('')).join(' ');

  return [
    `\n    <div class="listening-card ${isProposal ? 'proposal-listening-card' : ''}`,
    [
      `">\n      <div class="listening-head">\n        <span class="listening-badge">AUDICIÓN ${e(l.index)}`
    ].join(''),
    [
      `</span>\n        <div>\n          <strong>${e(l.composer ? l.composer + ' · ' : '')}${e(l.title)}`
    ].join(''),
    `</strong>\n          ${l.subtitle ? `<small>${e(l.subtitle)}</small>` : ''}`,
    `\n        </div>\n      </div>\n      `,
    [
      `${
        l.performer ? [
          `<div class="listening-performer">🎙 <strong>Grabación de referencia:</strong> ${e(l.performer)}</div>`
        ].join('') : ''
      }`
    ].join(''),
    `\n      ${linksHTML ? `<div class="listening-links">${linksHTML}</div>` : ''}\n      `,
    [
      `${
        l.teacher_note ? [
          `<div class="listening-teacher-note">💡 <strong>Criterio y comentario docente:</strong> `,
          `${e(l.teacher_note)}</div>`
        ].join('') : ''
      }`
    ].join(''),
    `\n      ${
      l.anthology ? `<div class="listening-anthology">📚 ${e(l.anthology)}</div>` : ''
    }`,
    `\n      <div class="listening-points">\n        <strong>Puntos clave de escucha `,
    `activa:</strong>\n        <ul>\n          `,
    `${(l.points || []).map(pt => `<li>${e(pt)}</li>`).join('')}`,
    `\n        </ul>\n      </div>\n    </div>\n  `
  ].join('');
}

export function renderEgyptListeningsHTML(isProposal = false) {
  return EGYPT_LISTENINGS.map(l => renderListeningCardItem(l, isProposal)).join('');
}

export function renderStudentDiscographySection(run) {
  const isPolyphony = is15thCenturyPolyphony(run);
  const isEgypt = isAncientEgypt(run);
  const listenings = isPolyphony ? POLYPHONY_LISTENINGS : isEgypt ? EGYPT_LISTENINGS : getRunListenings(run);
  if (!listenings || !listenings.length) return '';
  return [
    `\n    <section class="student-section section-discography">\n      <div `,
    `class="student-section-header">\n        <span class="student-section-number">`,
    `07</span>\n        <div>\n          <h2>Discografía recomendada y enlaces `,
    `directos de audición</h2>\n          <p class="student-section-intro">Relación `,
    `detallada de grabaciones de referencia con enlaces directos a YouTube y `,
    `comentarios analíticos del profesor para el trabajo autónomo del alumnado.</p>\n `,
    `       </div>\n      </div>\n      <div class="table-wrapper">\n        <table `,
    `class="discography-table">\n          <thead>\n            <tr>\n              `,
    `<th style="width: 25%;">Obra y movimientos</th>\n              <th style="width: `,
    `25%;">Grabación e intérpretes</th>\n              <th style="width: 24%;">`,
    `Enlaces a YouTube</th>\n              <th style="width: 26%;">Comentario `,
    `didáctico</th>\n            </tr>\n          </thead>\n          <tbody>\n            `,
    [
      `${
        listenings.map(item => [
          [
            `\n              <tr>\n                <td><strong>${e(item.composer || '')}</strong><br><em>`
          ].join(''),
          `${e(item.title)}</em>`,
          `${
              item.subtitle ? `<br><small class="muted-small">${e(item.subtitle)}</small>` : ''
              }`,
          `</td>\n                <td><span class="disco-performer">🎙 `,
          `${e(item.performer || 'Grabación recomendada')}`,
          `</span></td>\n                <td>\n                  <div class="disco-links">`,
          `\n                    `,
          [
            `${
        (item.links && item.links.length > 0) ? (item.links.map(l => [
          `\n                      <a href="${e(l.url)}`,
          `" target="_blank" rel="noopener noreferrer" class="yt-link-btn yt-link-table">\n `,
          `                       <svg class="icon yt-icon" viewBox="0 0 24 24" width="14" `,
          `height="14" style="vertical-align:-2px;margin-right:2px;"><path fill="#dc2626" `,
          `d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.5 12 3.5 12 3.5s-7.505 `,
          `0-9.377.55a3.016 3.016 0 0 0-2.122 2.136C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 `,
          `3.016 0 0 0 2.122 2.136c1.871.55 9.376.55 9.376.55s7.505 0 9.377-.55a3.016 3.016 `,
          `0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 `,
          [
            `15.568V8.432L15.818 12l-6.273 3.568z"/></svg>\n                        <span>${e(l.label)}`
          ].join(''),
          `</span>\n                      </a>\n                    `
        ].join('')).join('')) :
        '<span class="muted-small"><em>(Descarte deliberado · Análisis iconográfico)</em></span>'
        }`
          ].join(''),
          [
            `\n                  </div>\n                </td>\n                <td><small class="disco-note">`
          ].join(''),
          `${e(item.teacher_note || 'Audición de referencia para la unidad.')}`,
          `</small></td>\n              </tr>\n            `
        ].join('')).join('')
      }`
    ].join(''),
    `\n          </tbody>\n        </table>\n      </div>\n    </section>\n  `
  ].join('');
}

// Acciones y formularios de este módulo; delegación central en main.js.


export const actions = {};
