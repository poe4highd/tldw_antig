import { test, expect, Page } from '@playwright/test';

// Helper to inject Supabase session into localStorage
// This simulates a logged-in user without going through the UI
async function injectSession(page: Page) {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co';

    // Create a mock session object
    const session = {
        access_token: 'mock-access-token',
        token_type: 'bearer',
        expires_in: 3600,
        refresh_token: 'mock-refresh-token',
        user: {
            id: 'mock-user-id',
            email: 'test@example.com',
            app_metadata: { provider: 'email' },
            user_metadata: {},
            aud: 'authenticated',
            role: 'authenticated',
        },
        expires_at: Math.floor(Date.now() / 1000) + 3600,
    };

    const storageKey = `sb-${supabaseUrl.split('//')[1].split('.')[0]}-auth-token`;

    await page.addInitScript(({ key, value }) => {
        window.localStorage.setItem(key, value);
    }, { key: storageKey, value: JSON.stringify(session) });
}

test.describe('Subtitle Interaction & Layout', () => {
    test.beforeEach(async ({ page }) => {
        // Inject session before navigation
        await injectSession(page);
        // Navigate to a known result page (using a placeholder ID from dev env)
        await page.goto('/result/UBE4vkQrSb8');
    });

    test('should show sync button when user scrolls manually', async ({ page }) => {
        // 1. Initially, sync button should not be visible
        await expect(page.locator('button:has-text("同步播放进度")')).not.toBeVisible();

        // 2. Simulate manual scroll
        const scrollContainer = page.getByTestId('subtitle-container');

        await scrollContainer.evaluate(node => node.scrollTop += 100);

        // 3. Verify sync button appears
        await expect(page.locator('button:has-text("同步播放进度")')).toBeVisible();

        // 4. Click sync button
        await page.click('button:has-text("同步播放进度")');

        // 5. Verify it disappears
        await expect(page.locator('button:has-text("同步播放进度")')).not.toBeVisible();
    });

    test('should not have visual gaps between header and navigation', async ({ page }) => {
        // Scroll down to trigger sticky
        await page.evaluate(() => window.scrollTo(0, 500));

        const header = page.locator('main >> .sticky');
        const nav = page.locator('nav.sticky');

        const headerBox = await header.boundingBox();
        const navBox = await nav.boundingBox();

        if (headerBox && navBox) {
            // Expect header to be exactly at the bottom of nav (nav.y + nav.height)
            // Our code uses top-[68px], nav is px-4 py-4 (~72px typically)
            // We check if the distance is minimal
            expect(headerBox.y).toBeLessThanOrEqual(navBox.y + navBox.height + 1);
        }
    });
});
