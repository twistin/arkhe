import { dialog } from '../ui.js';
// Cierre de diálogos compartido por todas las vistas.

// Acciones y formularios de este módulo; delegación central en main.js.
async function accionCloseDialog() {
  dialog.close();
}

export const actions = {
  'close-dialog': accionCloseDialog,
};
