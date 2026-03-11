import { test, expect } from '@playwright/test'

test.describe('Agents navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('admin')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/(?!login)/)
  })

  test('Agents page renders and has help panel', async ({ page }) => {
    await page.goto('/agents')
    await expect(page.getByRole('heading', { name: /agents/i })).toBeVisible()
    await expect(page.getByText(/what is an agent/i)).toBeVisible()
  })

  test('can toggle help panel', async ({ page }) => {
    await page.goto('/agents')
    await expect(page.getByText(/what is an agent/i)).toBeVisible()
    await page.getByRole('button', { name: /hide help/i }).click()
    await expect(page.getByText(/what is an agent/i)).not.toBeVisible()
  })
})
