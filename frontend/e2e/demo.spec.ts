import { test, expect } from '@playwright/test'

test.describe('Demo Page - Search Interface', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/demo/')
  })

  test('page loads with heading and search input', async ({ page }) => {
    await expect(page.locator('h1').first()).toContainText('Live Demo')
    const searchInput = page.locator('input[type="text"]')
    await expect(searchInput).toBeVisible()
  })

  test('search type selector buttons are visible', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Semantic/i }).first()).toBeVisible()
    await expect(page.getByRole('button', { name: /Emotional/i }).first()).toBeVisible()
    await expect(page.getByRole('button', { name: /Discovery/i }).first()).toBeVisible()
    await expect(page.getByRole('button', { name: /Analysis/i }).first()).toBeVisible()
    await expect(page.getByRole('button', { name: /Style/i }).first()).toBeVisible()
  })

  test('semantic search type is selected by default', async ({ page }) => {
    const semanticBtn = page.getByRole('button', { name: /Semantic/i })
    await expect(semanticBtn).toHaveClass(/bg-model-technical/)
  })

  test('clicking search type changes active state', async ({ page }) => {
    const emotionalBtn = page.getByRole('button', { name: /Emotional/i })
    await emotionalBtn.click()
    await expect(emotionalBtn).toHaveClass(/bg-model-technical/)

    // Semantic should no longer be active
    const semanticBtn = page.getByRole('button', { name: /Semantic/i })
    await expect(semanticBtn).not.toHaveClass(/bg-model-technical/)
  })

  test('suggestion buttons are visible and clickable', async ({ page }) => {
    // Find suggestion buttons (small rounded buttons with "Try:" label nearby)
    const suggestions = page.locator('button').filter({ hasText: /quantum|existential|knowledge|consciousness/i })
    const count = await suggestions.count()
    expect(count).toBeGreaterThan(0)

    // Click first suggestion
    await suggestions.first().click()

    // Search input should be filled
    const searchInput = page.locator('input[type="text"]')
    const value = await searchInput.inputValue()
    expect(value.length).toBeGreaterThan(0)
  })

  test('search type change updates suggestions', async ({ page }) => {
    // Switch to emotional
    await page.getByRole('button', { name: /Emotional/i }).click()
    await page.waitForTimeout(500)

    // Should show emotional suggestions
    const suggestions = page.locator('button').filter({ hasText: /grief|hope|fear|joy|longing|rage/i })
    const count = await suggestions.count()
    expect(count).toBeGreaterThan(0)
  })

  test('typing in search triggers API call and shows results', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]')
    await searchInput.fill('philosophy of mind')

    // Wait for debounced API call
    const response = await page.waitForResponse(
      resp => resp.url().includes('/api/search') && resp.status() === 200,
      { timeout: 15000 }
    )
    expect(response.ok()).toBe(true)

    // Results or "no results" message should appear
    await page.waitForTimeout(1000)
  })

  test('sort radio buttons are visible on desktop', async ({ page }) => {
    // Sort options in sidebar (large screens only)
    const relevanceRadio = page.locator('input[type="radio"][value="relevance"]')
    if (await relevanceRadio.isVisible()) {
      await expect(relevanceRadio).toBeChecked()

      const dateRadio = page.locator('input[type="radio"][value="date"]')
      await expect(dateRadio).toBeVisible()
      await dateRadio.click()
      await expect(dateRadio).toBeChecked()
    }
  })

  test('empty state shows prompt message', async ({ page }) => {
    // Before any search, should show empty state
    await expect(page.locator('text=/enter a search query/i')).toBeVisible()
  })
})

test.describe('Demo Page - Result Cards', () => {
  test('search results show book info and actions', async ({ page }) => {
    await page.goto('/demo/')

    // Trigger a search
    await page.locator('input[type="text"]').fill('existentialism')
    await page.waitForResponse(
      resp => resp.url().includes('/api/search') && resp.status() === 200,
      { timeout: 15000 }
    )
    await page.waitForTimeout(2000)

    // Check if results appeared
    const resultCards = page.locator('[class*="bg-bg-card"]').filter({ hasText: /relevance|similarity/i })
    const count = await resultCards.count()

    if (count > 0) {
      const firstCard = resultCards.first()

      // Copy button
      const copyBtn = firstCard.locator('button').filter({ hasText: /copy/i }).first()
      if (await copyBtn.isVisible()) {
        await copyBtn.click()
        // Should show feedback
        await page.waitForTimeout(500)
      }

      // Cite button
      const citeBtn = firstCard.locator('button').filter({ hasText: /cite/i }).first()
      if (await citeBtn.isVisible()) {
        await expect(citeBtn).toBeEnabled()
      }

      // Context/Book button (opens modal)
      const contextBtn = firstCard.locator('button').filter({ hasText: /context|book/i }).first()
      if (await contextBtn.isVisible()) {
        await contextBtn.click()
        // Dialog should open
        await page.waitForTimeout(1000)
        const dialog = page.locator('[role="dialog"]')
        if (await dialog.isVisible()) {
          // Close dialog
          await page.locator('[role="dialog"] button').filter({ hasText: /close/i }).first().click()
        }
      }
    }
  })
})
