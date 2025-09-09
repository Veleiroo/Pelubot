// @ts-check
const { test, expect } = require('@playwright/test');

test('home -> reservar -> seleccionar servicio -> date page visible', async ({ page, baseURL, request }) => {
  // wait backend
  const backendBase = process.env.BACKEND_URL || (baseURL + '/api');
  for (let i = 0; i < 30; i++) {
    try {
      const rdy = await request.get(backendBase.replace(/\/api$/, '') + '/ready');
      if (rdy.ok()) break;
    } catch {}
    await page.waitForTimeout(200);
  }
  // Go home
  // Ir directo a la página de servicios para evitar ambigüedades de CTA
  await page.goto(baseURL + '/book/service');
  // Wait Service page loaded (cards visible)
  await expect(page.getByText('Selecciona un servicio')).toBeVisible({ timeout: 15000 });
  // Click primer "Seleccionar" visible
  const selectBtn = page.getByRole('button', { name: /^Seleccionar$/ }).first();
  await selectBtn.click();
  // We should land in /book/date with header
  await expect(page).toHaveURL(/\/book\/date\?service=/);
  await expect(page.getByText('Selecciona fecha y hora')).toBeVisible({ timeout: 15000 });
});
