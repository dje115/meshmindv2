import { test, expect } from '@playwright/test'

test.describe('Dashboards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('admin')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/(?!login)/)
  })

  test('Dashboards page renders', async ({ page }) => {
    await page.goto('/dashboards')
    await expect(page.getByRole('heading', { name: /dashboards/i })).toBeVisible()
  })

  test('can open create dashboard', async ({ page }) => {
    await page.goto('/dashboards')
    await page.getByRole('button', { name: /create dashboard/i }).click()
    await expect(page).toHaveURL(/\/dashboards\/new/)
    await expect(page.getByText(/create dashboard/i)).toBeVisible()
  })
})
