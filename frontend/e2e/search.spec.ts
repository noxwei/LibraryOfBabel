import { test, expect } from '@playwright/test'

test.describe('Search Interface', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('displays search interface with type selector', async ({ page }) => {
    // Check header
    await expect(page.locator('h1')).toContainText('LibraryOfBabel')

    // Check search input exists
    const searchInput = page.locator('input[type="text"]')
    await expect(searchInput).toBeVisible()

    // Check search type buttons exist
    await expect(page.getByRole('button', { name: /Semantic/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /Emotional/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /Discovery/i })).toBeVisible()
  })

  test('semantic search returns results', async ({ page }) => {
    // Type search query
    await page.locator('input[type="text"]').fill('philosophy')

    // Wait for results to load
    await page.waitForResponse(resp =>
      resp.url().includes('/api/search') && resp.status() === 200
    )

    // Check results appear
    await expect(page.locator('[class*="bg-bg-card"]').first()).toBeVisible({ timeout: 10000 })
  })

  test('emotional search shows emotion badges', async ({ page }) => {
    // Select emotional search type
    await page.getByRole('button', { name: /Emotional/i }).click()

    // Check placeholder updated
    await expect(page.locator('input[type="text"]')).toHaveAttribute('placeholder', /grief|hope|fear|joy/i)

    // Search for an emotion
    await page.locator('input[type="text"]').fill('grief')

    // Wait for results
    await page.waitForResponse(resp =>
      resp.url().includes('/api/search') && resp.url().includes('emotional')
    )

    // Results should load
    await expect(page.locator('[class*="bg-bg-card"]').first()).toBeVisible({ timeout: 10000 })
  })

  test('discovery search works', async ({ page }) => {
    // Select discovery search type
    await page.getByRole('button', { name: /Discovery/i }).click()

    // Search
    await page.locator('input[type="text"]').fill('dystopia')

    // Wait for results
    await page.waitForResponse(resp =>
      resp.url().includes('/api/search') && resp.url().includes('discovery')
    )

    await expect(page.locator('[class*="bg-bg-card"]').first()).toBeVisible({ timeout: 10000 })
  })

  test('clicking suggestion fills search', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]')

    // Click a suggestion button
    await page.getByRole('button', { name: 'quantum consciousness' }).click()

    // Check input was filled
    await expect(searchInput).toHaveValue('quantum consciousness')
  })

  test('search type changes suggestions', async ({ page }) => {
    // Default semantic suggestions
    await expect(page.getByRole('button', { name: 'quantum consciousness' })).toBeVisible()

    // Switch to emotional
    await page.getByRole('button', { name: /Emotional/i }).click()

    // Should show emotional suggestions
    await expect(page.getByRole('button', { name: 'grief' })).toBeVisible()
  })
})

test.describe('Browse Library', () => {
  test('displays book grid', async ({ page }) => {
    await page.goto('/browse')

    // Wait for books to load
    await page.waitForResponse(resp =>
      resp.url().includes('/api/books') && resp.status() === 200
    )

    // Check books appear
    await expect(page.locator('[class*="bg-bg-card"]').first()).toBeVisible({ timeout: 10000 })
  })

  test('shows book count', async ({ page }) => {
    await page.goto('/browse')

    // Wait for load
    await page.waitForResponse(resp => resp.url().includes('/api/books'))

    // Should show total count
    await expect(page.locator('text=/\\d+.*books/i')).toBeVisible({ timeout: 10000 })
  })
})
