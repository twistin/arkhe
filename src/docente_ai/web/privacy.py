"""Aviso público del piloto sin acceso a la biblioteca ni a sus sesiones."""
from html import escape
import os
from starlette.responses import HTMLResponse


async def privacy(request):
    responsible = escape(os.environ.get('ARKHE_PRIVACY_RESPONSIBLE', 'Responsable del piloto (pendiente de configurar)'))
    email = escape(os.environ.get('ARKHE_PRIVACY_EMAIL', 'Contacto de privacidad pendiente de configurar'))
    region = escape(os.environ.get('ARKHE_DATA_REGION', 'región UE seleccionada por el administrador'))
    html = '''<!doctype html><html lang="es"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width"><title>Privacidad del piloto · Arkhé</title>
    <link rel="stylesheet" href="/assets/access.css"></head><body><main><h1>Privacidad del piloto Arkhé</h1>
    <p>Acceso privado para evaluar una herramienta de preparación docente. No es una plataforma de alumnado.</p>
    <h2>Qué se guarda</h2><p>Biblioteca y documentos originales, texto extraído, índices de búsqueda,
    preguntas, fragmentos recuperados, respuestas y citas, propuestas, configuración y diario/feedback docente.
    La cuenta tiene un hash scrypt de contraseña. Las sesiones son temporales; los registros técnicos
    no incluyen claves API ni contraseñas.</p>
    <h2>Dónde</h2><p>Instancia y copias del piloto en un droplet de DigitalOcean, ''' + region + '''.
    El administrador debe elegir Frankfurt o Ámsterdam. Este aviso describe el despliegue previsto;
    la aplicación no certifica físicamente la región del servidor. Cada espacio es privado.</p>
    <h2>Proveedor de IA</h2><p>Los embeddings se calculan en Ollama dentro de este servidor UE.
    Mistral recibe la pregunta y los pasajes recuperados, datos de contexto docente y programación necesarios
    para la propuesta, y el diálogo de reparación si hay reintentos. No se envían archivos completos como
    adjuntos ni el diario de sesiones a Mistral. La indexación conserva el texto en la instancia.</p>
    <p>Se utiliza api.eu.mistral.ai. Su documentación describe una región europea UE/AELC;
    una exigencia de UE estricta y las condiciones de retención deben confirmarse contractual y
    operativamente antes de usar el piloto. No se presupone retención cero. El consentimiento en Ajustes
    se exige antes de enviar una consulta.</p>
    <h2>No subas datos del alumnado</h2><p>Está prohibido incorporar nombres, correos, calificaciones,
    expedientes, fotografías, grabaciones identificables, información de salud u otros datos personales del
    alumnado, tanto en fuentes y preguntas como en propuestas o feedback. Usa materiales docentes y ejemplos
    ficticios. La aplicación no detecta automáticamente todos los datos personales.</p>
    <h2>Conservación y borrado</h2><p>Los materiales se conservan durante el piloto o hasta solicitar su
    retirada. Las copias se rotan a los 14 días. Para pedir exportación o borrado del espacio, escribe a
    ''' + email + ''' identificando tu cuenta. El administrador eliminará la cuenta, el volumen y sus copias;
    la retirada de las copias ordinarias se completa en un máximo de 14 días. Una restauración no debe
    reintroducir datos de cuentas ya eliminadas. Las políticas de Mistral deben revisarse aparte.</p>
    <p>Responsable: ''' + responsible + '''. Contacto: ''' + email + '''.</p>
    <p><a href="/login">Volver al acceso</a></p></main></body></html>'''
    return HTMLResponse(html)
