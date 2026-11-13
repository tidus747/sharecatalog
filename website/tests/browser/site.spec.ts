import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('desktop: presentation, theme persistence and documentation navigation', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1050 });
  await page.goto('/sharecatalog/');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Your documents.Connected.');
  await expect(page.getByRole('img')).toBeVisible();
  await page.getByRole('button', { name: 'Switch to Paper color mode' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await page.getByRole('link', { name: 'Get started', exact: false }).first().click();
  await expect(page).toHaveURL(/\/sharecatalog\/docs\/getting-started\/$/);
  await expect(page.getByRole('heading', { name: 'Install ShareCatalog', exact: true })).toBeVisible();
});

test('mobile: no horizontal overflow and guides remain reachable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  for (const route of ['/sharecatalog/', '/sharecatalog/docs/getting-started/']) {
    await page.goto(route);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await expect(page.getByRole('link', { name: 'Documentation', exact: true }).first()).toBeVisible();
  }
  await page.getByRole('link', { name: 'Library mappings', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Mapping libraries safely' })).toBeVisible();
});

test('copy button puts the install command on the clipboard', async ({ page, context }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('/sharecatalog/');
  await page.getByRole('button', { name: 'Copy code to clipboard' }).click();
  await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toContain('python.exe -m sharecatalog');
});

for (const theme of ['dark', 'light']) {
  test(`automated accessibility: home and installation in ${theme} mode`, async ({ page }) => {
    for (const route of ['/sharecatalog/', '/sharecatalog/docs/getting-started/']) {
      await page.goto(route);
      if (theme === 'light') {
        const toggle = page.getByRole('button', { name: 'Switch to Paper color mode' });
        if (await toggle.count()) await toggle.click();
      }
      const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
      expect(result.violations).toEqual([]);
    }
  });
}
