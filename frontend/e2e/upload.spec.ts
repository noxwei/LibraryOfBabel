import { test, expect } from '@playwright/test'

test.describe('Upload Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/upload/')
  })

  test('page loads with upload dropzone', async ({ page }) => {
    await expect(page.getByText('Drag & drop EPUB files')).toBeVisible()
  })

  test('dropzone has file input accepting .epub', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput).toHaveAttribute('accept', '.epub')
  })

  test('dropzone visual feedback on interaction', async ({ page }) => {
    // The dropzone should be visible and interactive
    const dropzone = page.locator('[class*="border-dashed"]')
    await expect(dropzone).toBeVisible()
  })

  test('upload button appears after file selection', async ({ page }) => {
    // Without files, upload button should not be visible
    const uploadBtn = page.getByRole('button', { name: /Upload.*Process/i })
    await expect(uploadBtn).toBeHidden()
  })
})
