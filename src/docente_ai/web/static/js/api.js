// Módulo local: responsabilidad separada sin alterar el contenido.

export const token = document.querySelector('meta[name="docente-token"]').content;
export async function api(path, data, options = {}) {
  const response = await fetch('/api' + path, {
    method: data === undefined ? 'GET' : 'POST',
    headers: {
      'X-Docente-Token': token,
      ...(data === undefined ? {} : {
        'Content-Type': 'application/json'
      }),
      ...options.headers
    },
    ...(data === undefined ? {} : {
      body: JSON.stringify(data)
    }),
    ...options
  });
  if (!response.ok) {
    let message = 'No se pudo completar la operación.';
    try {
      message = (await response.json()).error || message;
    } catch {}
    throw new Error(message);
  }
  return response.json();
}

export async function request(url, options = {}) {
  return fetch(url, {
    ...options,
    headers: {
      'X-Docente-Token': token,
      ...options.headers
    }
  });
}
