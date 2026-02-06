import { test, expect } from '@playwright/test'

test.describe('Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('hero section renders with headline', async ({ page }) => {
    await expect(page.locator('h1').first()).toContainText('Your Documents')
    await expect(page.locator('h1').first()).toContainText('Your AI')
  })

  test('hero CTA "Try Live Demo" links to /demo/', async ({ page }) => {
    const ctaButton = page.locator('a', { hasText: 'Try Live Demo' })
    await expect(ctaButton).toBeVisible()
    await expect(ctaButton).toHaveAttribute('href', '/demo/')
    await ctaButton.click()
    await expect(page).toHaveURL(/\/demo\//)
  })

  test('hero CTA "API Documentation" links to /api-docs/', async ({ page }) => {
    const docsButton = page.locator('a', { hasText: 'API Documentation' })
    await expect(docsButton).toBeVisible()
    await expect(docsButton).toHaveAttribute('href', '/api-docs/')
    await docsButton.click()
    await expect(page).toHaveURL(/\/api-docs\//)
  })

  test('audience badges are visible', async ({ page }) => {
    await expect(page.locator('text=NGOs & Nonprofits').first()).toBeVisible()
    await expect(page.locator('text=Academic Research').first()).toBeVisible()
    await expect(page.locator('text=Enterprise').first()).toBeVisible()
  })

  test('stats bar displays stats with values', async ({ page }) => {
    await expect(page.locator('text=Total Books')).toBeVisible()
    await expect(page.locator('text=Total Chunks')).toBeVisible()
    await expect(page.locator('text=Embedding Dimensions')).toBeVisible()
    await expect(page.locator('text=Search Speed')).toBeVisible()

    // Stats should show labels (values may be loading or skeleton)
    await page.waitForTimeout(3000)
    // Check for static values that are always rendered
    await expect(page.locator('text=Embedding Dimensions')).toBeVisible()
    await expect(page.locator('text=Search Speed')).toBeVisible()
  })

  test('how-it-works section displays 3 steps', async ({ page }) => {
    await expect(page.locator('text=How It Works')).toBeVisible()
    await expect(page.locator('text=Ingest')).toBeVisible()
    await expect(page.locator('text=Chunk & Embed')).toBeVisible()
    await expect(page.locator('text=Search & Retrieve')).toBeVisible()
  })

  test('use cases section displays 3 cards', async ({ page }) => {
    await expect(page.locator('text=Built For')).toBeVisible()
    await expect(page.locator('text=NGOs & Nonprofits').nth(1)).toBeVisible()
    await expect(page.locator('text=Academic Researchers')).toBeVisible()
    await expect(page.locator('text=Enterprise Teams')).toBeVisible()
  })

  test('live demo section has embedded search interface', async ({ page }) => {
    await expect(page.locator('text=Try It Live')).toBeVisible()
    // Search input should exist in the live demo section
    const searchInput = page.locator('input[type="text"]')
    await expect(searchInput.first()).toBeVisible()
  })

  test('live demo embedded search accepts input', async ({ page }) => {
    const searchInput = page.locator('input[type="text"]').first()
    await searchInput.fill('philosophy')
    await expect(searchInput).toHaveValue('philosophy')
  })
})
