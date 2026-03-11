import { test, expect } from '@playwright/test'

test.describe('Create source flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('admin')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/(?!login)/)
  })

  test('can navigate to Add Source and see form', async ({ page }) => {
    await page.goto('/sources')
    await page.getByRole('link', { name: /add source/i }).click()
    await expect(page).toHaveURL(/\/sources\/add/)
    await expect(page.getByLabel(/source name/i)).toBeVisible()
    await expect(page.getByLabel(/workspace/i)).toBeVisible()
    await expect(page.getByLabel(/path/i)).toBeVisible()
  })

  test('Add Source form has Save and Cancel', async ({ page }) => {
    await page.goto('/sources/add')
    await expect(page.getByRole('button', { name: /save/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /cancel/i })).toBeVisible()
  })
})
