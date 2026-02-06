import { test, expect } from '@playwright/test'

test.describe('API Documentation Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/api-docs/')
  })

  test('page loads with title', async ({ page }) => {
    await expect(page.locator('h1')).toContainText(/API/i)
  })

  test('endpoint groups are displayed', async ({ page }) => {
    await expect(page.locator('text=/Health|System/i').first()).toBeVisible()
    await expect(page.locator('text=/Books/i').first()).toBeVisible()
    await expect(page.locator('text=/Search/i').first()).toBeVisible()
    await expect(page.locator('text=/Mobile|Shortcuts/i').first()).toBeVisible()
  })

  test('endpoint cards show method and path', async ({ page }) => {
    // GET badges should exist
    await expect(page.locator('text=GET').first()).toBeVisible()

    // Endpoint paths should exist
    await expect(page.locator('text=/\\/api\\/health/').first()).toBeVisible()
    await expect(page.locator('text=/\\/api\\/books/').first()).toBeVisible()
    await expect(page.locator('text=/\\/api\\/search/').first()).toBeVisible()
  })

  test('Try It buttons exist on endpoint cards', async ({ page }) => {
    const tryItButtons = page.getByRole('button', { name: /Try It/i })
    const count = await tryItButtons.count()
    expect(count).toBeGreaterThan(0)
  })

  test('Try It button opens panel', async ({ page }) => {
    // Click the first Try It button
    const tryItBtn = page.getByRole('button', { name: /Try It/i }).first()
    await tryItBtn.click()
    await page.waitForTimeout(500)

    // TryItPanel modal should appear
    const panel = page.locator('[class*="fixed"]').filter({ hasText: /Send Request/i })
    await expect(panel).toBeVisible()

    // Should have Send Request button
    await expect(page.getByRole('button', { name: /Send Request/i })).toBeVisible()

    // Should have code tabs
    await expect(page.getByRole('button', { name: /cURL/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /Python/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /JavaScript/i })).toBeVisible()
  })

  test('Try It panel sends request and shows response', async ({ page }) => {
    // Open first Try It panel
    const tryItBtn = page.getByRole('button', { name: /Try It/i }).first()
    await tryItBtn.click()
    await page.waitForTimeout(500)

    // Send button should be visible
    const sendBtn = page.getByRole('button', { name: /Send Request/i })
    await expect(sendBtn).toBeVisible()

    // Click Send Request
    await sendBtn.click()

    // Wait for response (the button text changes during loading)
    await page.waitForTimeout(5000)

    // After sending, a <pre> block with JSON response should appear
    await expect(page.locator('pre').last()).toBeVisible({ timeout: 10000 })
  })

  test('code tab switching works', async ({ page }) => {
    // Open any Try It panel
    const tryItBtn = page.getByRole('button', { name: /Try It/i }).first()
    await tryItBtn.click()
    await page.waitForTimeout(500)

    // Code tabs should be visible
    const curlTab = page.getByRole('button', { name: 'cURL' })
    const pythonTab = page.getByRole('button', { name: 'Python' })
    const jsTab = page.getByRole('button', { name: 'JavaScript' })

    await expect(curlTab).toBeVisible()
    await expect(pythonTab).toBeVisible()
    await expect(jsTab).toBeVisible()

    // Click Python tab
    await pythonTab.click()
    await page.waitForTimeout(300)
    await expect(pythonTab).toHaveClass(/text-model-technical/)

    // Click JavaScript tab
    await jsTab.click()
    await page.waitForTimeout(300)
    await expect(jsTab).toHaveClass(/text-model-technical/)

    // Click cURL tab
    await curlTab.click()
    await page.waitForTimeout(300)
    await expect(curlTab).toHaveClass(/text-model-technical/)
  })

  test('Try It panel close button works', async ({ page }) => {
    const tryItBtn = page.getByRole('button', { name: /Try It/i }).first()
    await tryItBtn.click()
    await page.waitForTimeout(500)

    // Find and click close button (X icon)
    const closeBtn = page.locator('button[aria-label="Close panel"]')
    if (await closeBtn.isVisible()) {
      await closeBtn.click()
      await page.waitForTimeout(500)
      // Panel should be gone
      await expect(page.getByRole('button', { name: /Send Request/i })).toBeHidden()
    }
  })

  test('parameters section expands and collapses', async ({ page }) => {
    // Find a Parameters toggle button
    const paramsToggle = page.getByRole('button', { name: /Parameters/i }).first()
    if (await paramsToggle.isVisible()) {
      await paramsToggle.click()
      await page.waitForTimeout(300)

      // Parameter table should be visible
      await expect(page.locator('text=/Name|Type|Required/i').first()).toBeVisible()

      // Click again to collapse
      await paramsToggle.click()
      await page.waitForTimeout(300)
    }
  })

  test('example response section expands and collapses', async ({ page }) => {
    const responseToggle = page.getByRole('button', { name: /Example Response/i }).first()
    if (await responseToggle.isVisible()) {
      await responseToggle.click()
      await page.waitForTimeout(300)

      // JSON code should be visible
      await expect(page.locator('pre').first()).toBeVisible()

      // Collapse
      await responseToggle.click()
      await page.waitForTimeout(300)
    }
  })

  test('code snippet copy button exists', async ({ page }) => {
    // Open an endpoint's example response
    const responseToggle = page.getByRole('button', { name: /Example Response/i }).first()
    if (await responseToggle.isVisible()) {
      await responseToggle.click()
      await page.waitForTimeout(300)

      // Copy button should exist in the expanded section
      const copyBtn = page.getByRole('button', { name: /Copy/i }).first()
      await expect(copyBtn).toBeVisible()
      // Click it
      await copyBtn.click()
      await page.waitForTimeout(500)
    }
  })
})
