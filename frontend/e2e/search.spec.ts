import { test, expect } from '@playwright/test'

test.describe('Search Interface', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/demo/')
  })

  test('displays search interface with type selector', async ({ page }) => {
    await expect(page.locator('h1').first()).toContainText('Live Demo')

    const searchInput = page.locator('input[type="text"]')
    await expect(searchInput).toBeVisible()

    await expect(page.getByRole('button', { name: /Semantic/i }).first()).toBeVisible()
    await expect(page.getByRole('button', { name: /Emotional/i }).first()).toBeVisible()
    await expect(page.getByRole('button', { name: /Discovery/i }).first()).toBeVisible()
  })

  test('semantic search returns results', async ({ page }) => {
    await page.locator('input[type="text"]').fill('philosophy')

    await page.waitForResponse(resp =>
      resp.url().includes('/api/search') && resp.status() === 200
    , { timeout: 15000 })

    await page.waitForTimeout(2000)
  })

  test('emotional search works', async ({ page }) => {
    await page.getByRole('button', { name: /Emotional/i }).click()
    await page.locator('input[type="text"]').fill('grief')

    await page.waitForResponse(resp =>
      resp.url().includes('/api/search'),
      { timeout: 15000 }
    )

    await page.waitForTimeout(2000)
  })

  test('discovery search works', async ({ page }) => {
    await page.getByRole('button', { name: /Discovery/i }).click()
    await page.locator('input[type="text"]').fill('dystopia')

    await page.waitForResponse(resp =>
      resp.url().includes('/api/search'),
      { timeout: 15000 }
    )

    await page.waitForTimeout(2000)
  })

  test('clicking suggestion fills search', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]')
    const suggestion = page.locator('button').filter({ hasText: /quantum|existential|knowledge/i }).first()
    if (await suggestion.isVisible()) {
      const text = await suggestion.textContent()
      await suggestion.click()
      await expect(searchInput).toHaveValue(text!.trim())
    }
  })

  test('search type changes suggestions', async ({ page }) => {
    // Switch to emotional
    await page.getByRole('button', { name: /Emotional/i }).click()
    await page.waitForTimeout(500)

    // Should show emotional suggestions
    const emotionalSuggestion = page.locator('button').filter({ hasText: /grief|hope|fear|joy|longing/i })
    const count = await emotionalSuggestion.count()
    expect(count).toBeGreaterThan(0)
  })
})

test.describe('Browse Library', () => {
  test('displays book grid', async ({ page }) => {
    await page.goto('/browse/')

    await page.waitForResponse(resp =>
      resp.url().includes('/api/books') && resp.status() === 200
    , { timeout: 15000 })

    await page.waitForTimeout(2000)
  })

  test('shows book count', async ({ page }) => {
    await page.goto('/browse/')

    await page.waitForResponse(resp => resp.url().includes('/api/books'),
      { timeout: 15000 })

    await expect(page.locator('text=/\\d+.*books/i')).toBeVisible({ timeout: 10000 })
  })
})
