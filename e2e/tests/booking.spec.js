// @ts-check
const { test, expect } = require('@playwright/test');

test('flow via /debug to confirm reservation', async ({ page, baseURL, request }) => {
  // 0) Discover a valid day via API to avoid flaky parsing
  const toYmd = (d) => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  const today = new Date();
  const start = new Date(today.getFullYear(), today.getMonth(), 1);
  const end = new Date(today.getFullYear(), today.getMonth()+1, 0);
  const serviceId = 'corte';
  const backendBase = process.env.BACKEND_URL || (baseURL + '/api');
  // Wait for backend ready
  for (let i = 0; i < 30; i++) {
    try {
      const rdy = await request.get(backendBase.replace(/\/api$/, '') + '/ready');
      const ok = rdy.ok();
      if (ok) break;
    } catch {}
    await page.waitForTimeout(500);
  }
  const r = await request.post(backendBase + '/slots/days', {
    data: { service_id: serviceId, start: toYmd(start), end: toYmd(end) }
  });
  const fs = require('fs');
  const path = require('path');
  const outDir = path.join(__dirname, '..', 'artifacts-out');
  try { fs.mkdirSync(outDir, { recursive: true }); } catch {}
  let text = await r.text();
  try { fs.writeFileSync(path.join(outDir, 'slots-days.txt'), text); } catch {}
  let body = {};
  try { body = JSON.parse(text); } catch (e) { try { fs.writeFileSync(path.join(outDir, 'parse-error.txt'), String(e)); } catch {} }
  const day = (body && body.available_days && body.available_days[0]) || null;
  test.skip(!day, 'No available days found');

  // 1) Go to debug page
  await page.goto(baseURL + '/debug');
  // Wait a bit for lazy route content (ES/EN)
  const h1es = page.getByText('Configuración de Debug');
  const h1en = page.getByText('Debug Config');
  await Promise.race([
    h1es.waitFor({ state: 'visible', timeout: 15000 }),
    h1en.waitFor({ state: 'visible', timeout: 15000 }),
  ]);

  // 2) Set service and fetch slots for discovered day
  await page.getByPlaceholder('corte').fill(serviceId);
  await page.locator('input[placeholder*="-"]').first().fill(day);
  // Ensure use_gcal is off to avoid external dependencies
  try {
    const gcalSwitch = page.locator('#dbg-use-gcal');
    if (await gcalSwitch.isVisible({ timeout: 2000 })) {
      if (await gcalSwitch.isChecked()) await gcalSwitch.click();
    }
  } catch {}
  await page.getByRole('button', { name: '/slots' }).click();

  // Wait for at least one slot button
  const firstSlotBtn = page.getByRole('button', { name: /\d{2}:\d{2}/ }).first();
  await expect(firstSlotBtn).toBeVisible({ timeout: 15000 });

  // 3) Click a slot -> Debug page seeds store and navigates to Confirm
  await firstSlotBtn.click();

  // 4) Confirm page
  await expect(page).toHaveURL(/\/book\/confirm/);
  await expect(page.getByText('Confirmar reserva')).toBeVisible();

  // 5) Click Confirmar
  const confirmBtn = page.getByRole('button', { name: 'Confirmar' });
  await confirmBtn.click();

  // 6) Expect success message
  await expect(page.getByText('¡Reserva creada!')).toBeVisible({ timeout: 15000 });
});
