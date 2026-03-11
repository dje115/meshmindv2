import { test, expect } from '@playwright/test'

test.describe('Accessibility smoke', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('admin')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/(?!login)/)
  })

  test('Overview has heading', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  })

  test('Sources has Add source button', async ({ page }) => {
    await page.goto('/sources')
    const addBtn = page.getByRole('link', { name: /add source/i })
    await expect(addBtn).toBeVisible()
  })

  test('Ask has question input', async ({ page }) => {
    await page.goto('/ask')
    await expect(page.getByLabel(/question/i)).toBeVisible()
  })
})
