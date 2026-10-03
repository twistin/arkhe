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

// SSE mediante fetch: el token permanece en la cabecera, nunca en la URL.
export async function jobEvents(id, after, receive, signal) {
  const response = await request('/api/jobs/' + encodeURIComponent(id) + '/events', {
    headers: {'Accept': 'text/event-stream', 'Last-Event-ID': String(after)}, signal
  });
  if (!response.ok || !response.body) throw new Error('No se pudo abrir el canal de progreso.');
  const reader = response.body.getReader(), decoder = new TextDecoder();
  let buffer = '';
  try {
    while (true) {
      const {value, done} = await reader.read();
      buffer += decoder.decode(value, {stream: !done}).replace(/\r/g, '');
      let end;
      while ((end = buffer.indexOf('\n\n')) >= 0) {
        const block = buffer.slice(0, end);
        buffer = buffer.slice(end + 2);
        const lines = block.split('\n');
        const data = lines.filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart());
        if (data.length) receive({
          id: Number(lines.find(line => line.startsWith('id:'))?.slice(3) || 0),
          event: lines.find(line => line.startsWith('event:'))?.slice(6).trim() || 'message',
          data: JSON.parse(data.join('\n'))
        });
      }
      if (done) return;
    }
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
