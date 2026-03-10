import { test, expect } from '@playwright/test'

test.describe('Search and Ask', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('admin')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/(?!login)/)
  })

  test('Search page renders', async ({ page }) => {
    await page.goto('/search')
    await expect(page.getByPlaceholder(/search your knowledge/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /search/i })).toBeVisible()
  })

  test('Ask page renders', async ({ page }) => {
    await page.goto('/ask')
    await expect(page.getByPlaceholder(/ask a question/i)).toBeVisible()
  })
})
