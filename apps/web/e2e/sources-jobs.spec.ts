import { test, expect } from '@playwright/test'

test.describe('Sources and Jobs', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('admin')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/(?!login)/)
  })

  test('Sources page renders', async ({ page }) => {
    await page.goto('/sources')
    await expect(page.getByRole('heading', { name: /sources/i })).toBeVisible()
  })

  test('Jobs page renders', async ({ page }) => {
    await page.goto('/jobs')
    await expect(page.getByRole('heading', { name: /jobs/i })).toBeVisible()
  })

  test(' navigation works', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: /sources/i }).first().click()
    await expect(page).toHaveURL(/\/sources/)
  })
})
