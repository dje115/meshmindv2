import { test, expect } from '@playwright/test'

test.describe('Ask chat UX', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Username').fill('admin')
    await page.getByLabel('Password').fill('admin')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/(?!login)/)
  })

  test('Ask page has sidebar with New chat', async ({ page }) => {
    await page.goto('/ask')
    await expect(page.getByRole('button', { name: /new chat/i })).toBeVisible()
  })

  test('Ask page shows starter prompts when empty', async ({ page }) => {
    await page.goto('/ask')
    await expect(page.getByText(/ask your knowledge base/i)).toBeVisible()
  })

  test('can create and select chat', async ({ page }) => {
    await page.goto('/ask')
    await page.getByRole('button', { name: /new chat/i }).click()
    await expect(page.getByText(/no chats yet|new chat/i)).toBeVisible()
  })

  test('shows local + web research hint', async ({ page }) => {
    await page.goto('/ask')
    await expect(page.getByText(/local.*optional web|web research/i)).toBeVisible()
  })

  test('Ask input and send button', async ({ page }) => {
    await page.goto('/ask')
    await expect(page.getByLabel(/question/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /send/i })).toBeVisible()
  })
})
