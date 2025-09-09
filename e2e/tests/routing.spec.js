// @ts-check
const { test, expect } = require('@playwright/test');

test('navigates to /book/date with service param without redirect loop', async ({ page, baseURL, request }) => {
  // Ensure backend is ready
  const backendBase = process.env.BACKEND_URL || (baseURL + '/api');
  for (let i = 0; i < 30; i++) {
    try {
      const rdy = await request.get(backendBase.replace(/\/api$/, '') + '/ready');
      if (rdy.ok()) break;
    } catch {}
    await page.waitForTimeout(300);
  }
  await page.goto(baseURL + '/book/date?service=corte');
  await expect(page).toHaveURL(/\/book\/date\?service=corte/);
  // Espera por el encabezado o por el fallback de carga
  const header = page.getByText('Selecciona fecha y hora');
  const fallback = page.getByText('Cargando calendario…');
  await Promise.race([
    header.waitFor({ state: 'visible', timeout: 12000 }),
    fallback.waitFor({ state: 'visible', timeout: 12000 }),
  ]);
});
