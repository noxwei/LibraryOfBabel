import { test, expect } from '@playwright/test'

test.describe('Header Navigation - Desktop', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('logo links to homepage', async ({ page }) => {
    const logo = page.locator('a[href="/"]').filter({ hasText: 'LibraryOfBabel' })
    await expect(logo).toBeVisible()
    await logo.click()
    await expect(page).toHaveURL(/\/$/)
  })

  test('Demo nav link navigates to /demo/', async ({ page }) => {
    await page.locator('nav a[href="/demo/"]').first().click()
    await expect(page).toHaveURL(/\/demo\//)
    await expect(page.locator('h1').first()).toContainText('Live Demo')
  })

  test('Browse nav link navigates to /browse/', async ({ page }) => {
    await page.locator('nav a[href="/browse/"]').click()
    await expect(page).toHaveURL(/\/browse\//)
  })

  test('API nav link navigates to /api-docs/', async ({ page }) => {
    await page.locator('nav a[href="/api-docs/"]').click()
    await expect(page).toHaveURL(/\/api-docs\//)
  })

  test('Upload nav link navigates to /upload/', async ({ page }) => {
    await page.locator('nav a[href="/upload/"]').click()
    await expect(page).toHaveURL(/\/upload\//)
  })
})

test.describe('Header Navigation - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } })

  test('mobile menu button toggles menu', async ({ page }) => {
    await page.goto('/')

    // Desktop nav should be hidden
    const desktopNav = page.locator('nav.hidden.md\\:flex')
    await expect(desktopNav).toBeHidden()

    // Mobile menu button should be visible
    const menuButton = page.locator('button.md\\:hidden')
    await expect(menuButton).toBeVisible()

    // Click to open
    await menuButton.click()

    // Mobile nav links should appear
    const mobileNav = page.locator('nav.md\\:hidden')
    await expect(mobileNav).toBeVisible()
    await expect(mobileNav.locator('a[href="/demo/"]')).toBeVisible()
    await expect(mobileNav.locator('a[href="/browse/"]')).toBeVisible()
    await expect(mobileNav.locator('a[href="/api-docs/"]')).toBeVisible()
    await expect(mobileNav.locator('a[href="/upload/"]')).toBeVisible()

    // Click to close
    await menuButton.click()
    await expect(mobileNav).toBeHidden()
  })

  test('mobile menu closes on link click', async ({ page }) => {
    await page.goto('/')
    const menuButton = page.locator('button.md\\:hidden')
    await menuButton.click()

    const mobileNav = page.locator('nav.md\\:hidden')
    await expect(mobileNav).toBeVisible()

    // Click a link
    await mobileNav.locator('a[href="/demo/"]').click()
    await expect(page).toHaveURL(/\/demo\//)
  })
})
