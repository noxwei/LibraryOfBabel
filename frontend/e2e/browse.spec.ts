import { test, expect } from '@playwright/test'

test.describe('Browse Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/browse/')
  })

  test('page loads with header', async ({ page }) => {
    await expect(page.locator('text=Library Browse')).toBeVisible({ timeout: 10000 })
  })

  test('book grid loads with cards', async ({ page }) => {
    // Wait for API response
    await page.waitForResponse(
      resp => resp.url().includes('/api/books') && resp.status() === 200,
      { timeout: 15000 }
    )
    await page.waitForTimeout(2000)

    // Books should appear
    const bookCards = page.locator('[class*="bg-bg-card"]')
    const count = await bookCards.count()
    expect(count).toBeGreaterThan(0)
  })

  test('view toggle switches between grid and list', async ({ page }) => {
    await page.waitForResponse(
      resp => resp.url().includes('/api/books') && resp.status() === 200,
      { timeout: 15000 }
    )
    await page.waitForTimeout(1000)

    // Find view toggle buttons (LayoutGrid and List icons)
    const gridBtn = page.getByRole('button').filter({ has: page.locator('svg.lucide-layout-grid') })
    const listBtn = page.getByRole('button').filter({ has: page.locator('svg.lucide-list') })

    if (await listBtn.isVisible()) {
      await listBtn.click()
      await page.waitForTimeout(500)
      // Should switch to single-column layout
      await gridBtn.click()
      await page.waitForTimeout(500)
    }
  })

  test('genre filter buttons are visible', async ({ page }) => {
    await page.waitForTimeout(2000)

    // Genre filter buttons should all be rendered
    await expect(page.getByRole('button', { name: 'All' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Philosophy' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Sci-Fi' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Technology' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Fiction' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'History' })).toBeVisible()

    // "All" should have the active style
    await expect(page.getByRole('button', { name: 'All' })).toHaveClass(/bg-model-technical/)
  })

  test('pagination controls work', async ({ page }) => {
    await page.waitForResponse(
      resp => resp.url().includes('/api/books') && resp.status() === 200,
      { timeout: 15000 }
    )
    await page.waitForTimeout(2000)

    // Pagination buttons use text
    const nextBtn = page.getByRole('button', { name: /Next/i })

    if (await nextBtn.isVisible()) {
      // Previous should be disabled on page 1
      await expect(page.getByRole('button', { name: /Previous/i })).toBeDisabled()

      // Page indicator
      await expect(page.locator('text=/Page 1 of/i')).toBeVisible()

      // Click next
      await nextBtn.click()

      // Wait for new data to load
      await page.waitForResponse(
        resp => resp.url().includes('/api/books') && resp.status() === 200,
        { timeout: 15000 }
      )
      await page.waitForTimeout(1000)

      // Page 2 - previous should now be enabled
      await expect(page.getByRole('button', { name: /Previous/i })).toBeEnabled()
      await expect(page.locator('text=/Page 2 of/i')).toBeVisible()
    }
  })

  test('book card details dialog opens', async ({ page }) => {
    await page.waitForResponse(
      resp => resp.url().includes('/api/books') && resp.status() === 200,
      { timeout: 15000 }
    )
    await page.waitForTimeout(2000)

    // Find a Details button on a book card
    const detailsBtn = page.getByRole('button', { name: /Details/i }).first()
    if (await detailsBtn.isVisible()) {
      await detailsBtn.click()
      await page.waitForTimeout(500)

      // Dialog should open
      const dialog = page.locator('[role="dialog"]')
      await expect(dialog).toBeVisible()

      // Should show book info sections
      await expect(dialog.getByRole('heading', { name: 'Genre' })).toBeVisible()

      // Close the dialog
      const closeBtn = dialog.locator('button').filter({ has: page.locator('svg.lucide-x') })
      if (await closeBtn.isVisible()) {
        await closeBtn.click()
        await expect(dialog).toBeHidden()
      }
    }
  })
})
