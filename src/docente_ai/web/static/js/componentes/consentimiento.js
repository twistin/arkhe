// Módulo local: responsabilidad separada sin alterar el contenido.
import { api } from '../api.js';
import { refresh } from './trabajos.js';
import { store } from '../state.js';

export async function ensureRemoteConsent(mode='ask') {
  const info=(mode==='pedagogy'?store.state.pedagogy_provider_info:null)||store.state.provider_info;
  if(!info?.is_remote||info.remote_confirmed)return true;
  const accepted=confirm(`Enviar a ${info.name} (${info.data_residency}) en ${info.base_url}: pregunta y fragmentos recuperados, con título, autor, año y tipo de fuente. Para propuestas también se envían nivel, idioma, duración, criterios que escribas y la unidad seleccionada. Nunca se envían documentos completos, registros del diario ni feedback de sesiones. También se usa este proveedor para reformular la búsqueda y ordenar pasajes. ¿Confirmas este envío?`);
  if(!accepted)return false;
  await api('/provider/confirm',{confirmed:true,consent_scope:info.consent_scope,mode});
  await refresh(false);
  return true;
}
