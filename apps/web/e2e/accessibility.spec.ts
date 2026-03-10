import { test, expect } from '@playwright/test'

test.describe('Accessibility smoke checks', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('admin')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/(?!login)/)
  })

  test('main content has heading', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  })

  test('form inputs have labels', async ({ page }) => {
    await page.goto('/search')
    const input = page.getByPlaceholder(/search your knowledge/i)
    await expect(input).toHaveAttribute('aria-label', 'Search query')
  })

  test('buttons have accessible names', async ({ page }) => {
    await page.goto('/search')
    const btn = page.getByRole('button', { name: /search/i })
    await expect(btn).toBeVisible()
  })
})
