import { test, expect } from '@playwright/test';
test('overview, all control types, analytics, error handling and visual editor', async ({ page }) => {
  const errors=[]; page.on('pageerror', e=>errors.push(e.message));
  await page.goto('/frontend/demo/');
  await expect(page.getByRole('button',{name:'Output TDS history'})).toContainText('91');
  await page.getByRole('button',{name:'Refresh readings'}).click();
  await expect(page.getByRole('status').filter({hasText:'Readings refreshed'})).toBeVisible();
  await page.getByRole('tab',{name:'Controls'}).click();
  await page.getByLabel('Purification mode',{exact:true}).selectOption('RO + UV');
  await expect(page.locator('#events')).toContainText('select_option');
  await page.getByLabel('Fallback mode',{exact:true}).selectOption('TasteTune 50–100 ppm');
  await page.getByLabel('Input TDS threshold',{exact:true}).fill('230');
  await page.getByLabel('Input TDS threshold',{exact:true}).press('Tab');
  await expect(page.locator('#events')).toContainText('230');
  await page.getByRole('switch',{name:'Display sleep',exact:true}).check();
  await expect(page.getByRole('switch',{name:'Display sleep',exact:true})).toBeChecked();
  await page.getByLabel('Sleep starts',{exact:true}).fill('02:30');
  await page.getByLabel('Sleep starts',{exact:true}).press('Tab');
  await expect(page.locator('#events')).toContainText('02:30:00');
  await page.getByLabel('Sleep ends',{exact:true}).fill('07:30');
  await page.getByLabel('Sleep ends',{exact:true}).press('Tab');
  await expect(page.locator('#events')).toContainText('07:30:00');
  await page.getByRole('switch',{name:'Sleep schedule',exact:true}).uncheck();
  await expect(page.getByLabel('Sleep starts',{exact:true})).toBeDisabled();
  await page.getByRole('tab',{name:'Filters'}).click();
  await expect(page.locator('.filter-item')).toHaveCount(8);
  await expect(page.getByRole('button',{name:'Pre-filter: 78% estimated life remaining',exact:true})).toBeVisible();
  await page.getByText('How filter life is estimated',{exact:true}).click();
  await expect(page.getByText(/Past replacements and the app/)).toBeVisible();
  await expect(page.locator('.updated')).toContainText('every 10 seconds');
  await page.getByRole('tab',{name:'Insights'}).click();
  await expect(page.locator('atomberg-purifier-card')).toContainText('2,100');
  await page.getByText('About these readings',{exact:true}).click();
  await expect(page.getByText(/full refill cycle is still pending/)).toBeVisible();
  await page.getByRole('button',{name:'Service error',exact:true}).click();
  await page.getByRole('button',{name:'Refresh readings'}).click();
  await expect(page.getByRole('alert')).toContainText('did not confirm');
  await page.getByRole('button',{name:'Offline',exact:true}).click();
  await expect(page.getByRole('button',{name:'Refresh readings'})).toBeDisabled();
  await page.getByRole('button',{name:'Connected',exact:true}).click();
  await page.getByRole('button',{name:'Card editor',exact:true}).click();
  await page.getByLabel('Card title',{exact:true}).fill('Kitchen water');
  await page.getByLabel('Card title',{exact:true}).press('Tab');
  await expect(page.getByRole('heading',{name:'Kitchen water',exact:true})).toBeVisible();
  expect(errors).toEqual([]);
});
for (const width of [320,390,768,1440]) test(`fits viewport ${width}px`, async ({page})=>{
  await page.setViewportSize({width,height:1000});
  await page.goto('/frontend/demo/?card');
  await expect(page.getByRole('button',{name:'Output TDS history'})).toBeVisible();
  for (const name of ['Overview','Controls','Filters','Insights']) {
    await page.getByRole('tab',{name,exact:true}).click();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    const overflow=await page.locator('atomberg-purifier-card').evaluate(e=>{
      const root=e.shadowRoot.querySelector('ha-card');return root.scrollWidth>root.clientWidth+1;
    });expect(overflow).toBe(false);
  }
});
