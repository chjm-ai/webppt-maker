#!/usr/bin/env python3
"""离线播放器编辑、演讲备注与保存版本的真实 Chromium 回归。"""
import argparse
import json
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, default=ROOT / 'output/demo.html')
    parser.add_argument('--scratch', type=Path)
    args = parser.parse_args()
    scratch = args.scratch or Path(tempfile.mkdtemp(prefix='deck-edit-check-'))
    scratch.mkdir(parents=True, exist_ok=True)
    report = {'checks': {}, 'errors': [], 'external_requests': []}

    def check(name, condition):
        report['checks'][name] = bool(condition)
        print(name, bool(condition), flush=True)
        assert condition, name

    def download(page, filename, shortcut=None):
        with page.expect_download() as event:
            if shortcut:
                page.keyboard.press(shortcut)
            else:
                page.locator('#save').click()
        target = scratch / filename
        event.value.save_as(target)
        check(f'{filename}/download', target.stat().st_size > 0)
        check(f'{filename}/filename', not any(c in event.value.suggested_filename for c in '/\\:*?"<>|'))
        return target

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        report['browser'] = browser.version
        context = browser.new_context(viewport={'width': 1440, 'height': 960}, accept_downloads=True)
        context.set_default_timeout(30000)
        print('Chromium ready', report['browser'], flush=True)

        def block(route):
            report['external_requests'].append(route.request.url)
            route.abort()

        context.route('http://**/*', block)
        context.route('https://**/*', block)
        context.on('page', lambda page: page.on('pageerror', lambda error: report['errors'].append(str(error))))
        try:
            page = context.new_page()
            page.goto(args.html.resolve().as_uri())
            count = page.locator('.deck-page').count()
            initial_note = page.locator('.deck-page').first.get_attribute('data-note')
            check('starts_read_only', page.locator('[data-player-editable]').count() == 0)
            page.locator('#notes').click()
            check('manifest_note', page.locator('#note-text').input_value() == initial_note)
            note = '演讲备注 "<&>\n</textarea><script>window.injected = true</script>'
            page.locator('#note-text').fill(note)
            page.keyboard.press('ArrowRight')
            check('notes_keys_do_not_navigate', page.evaluate('deckPlayer.current === 0'))
            page.locator('#next').click()
            page.locator('#note-text').fill('第二页独立备注')
            page.locator('#previous').click()
            check('notes_persist_across_pages', page.locator('#note-text').input_value() == note)
            page.locator('#close-notes').click()
            page.locator('#edit').click()
            title = page.locator('.deck-page.active h1,.deck-page.active h2').first
            check('editing_enabled', title.get_attribute('contenteditable') == 'plaintext-only')
            edited = '离线改字 <img src=x onerror=alert(1)>'
            title.fill(edited)
            page.keyboard.press('ArrowRight')
            page.keyboard.press('Space')
            check('text_keys_do_not_navigate', page.evaluate('deckPlayer.current === 0'))
            title.fill(edited)
            check('jump_title_updates', edited in page.locator('#jump option').first.text_content())
            page.evaluate('''() => {
              const target = document.querySelector('.deck');
              const a = new Touch({identifier:1,target,clientX:500,clientY:250});
              const b = new Touch({identifier:1,target,clientX:200,clientY:250});
              target.dispatchEvent(new TouchEvent('touchstart',{touches:[a],bubbles:true}));
              target.dispatchEvent(new TouchEvent('touchend',{changedTouches:[b],bubbles:true}));
            }''')
            check('editing_disables_swipe', page.evaluate('deckPlayer.current === 0'))
            with page.expect_popup() as event:
                page.locator('#presenter').click()
            presenter = event.value
            check('presenter_note_is_plain_text', presenter.locator('#presenter-note').text_content() == note)
            check('presenter_title_is_plain_text', presenter.locator('#presenter-title').text_content() == edited)
            presenter.locator('#presenter-forward').click()
            check('presenter_can_navigate', page.evaluate('deckPlayer.current === 1'))
            check('presenter_tracks_page', presenter.locator('#presenter-note').text_content() == '第二页独立备注')
            presenter.locator('#presenter-previous').click()
            page.locator('#notes').click()
            page.screenshot(path=str(scratch / 'editing-notes-desktop.png'))
            page.locator('#close-notes').click()
            title.focus()
            saved = download(page, 'saved-edit.html', 'Control+s')
            check('save_does_not_change_live_editing', title.get_attribute('contenteditable') == 'plaintext-only')
            page.keyboard.press('Escape')
            check('escape_exits_editing', page.locator('[data-player-editable]').count() == 0)
            page.locator('#overview').click()
            check('overview_read_only', page.locator('[contenteditable]').count() == 0)
            page.evaluate('deckPlayer.go(3)')
            second = download(page, 'saved-overview.html')
            check('save_keeps_live_page', page.evaluate('deckPlayer.current === 3 && document.body.classList.contains("overview")'))
            for filename in [saved, second]:
                reopened = context.new_page()
                reopened.goto(filename.as_uri())
                check(f'{filename.name}/first_page', reopened.evaluate('deckPlayer.current === 0'))
                check(f'{filename.name}/reset_ui', reopened.locator('body.overview,body.editing,[contenteditable]').count() == 0
                      and reopened.locator('#notes-panel').is_hidden())
                check(f'{filename.name}/no_duplicate_options', reopened.locator('#jump option').count() == count)
                check(f'{filename.name}/edited_title', reopened.locator('.deck-page.active h1,.deck-page.active h2').first.text_content() == edited)
                reopened.locator('#notes').click()
                check(f'{filename.name}/note_preserved', reopened.locator('#note-text').input_value() == note)
                check(f'{filename.name}/no_injection', reopened.evaluate('!window.injected') and reopened.locator('.slide img[src="x"]').count() == 0)
                reopened.locator('#next').click()
                check(f'{filename.name}/second_note', reopened.locator('#note-text').input_value() == '第二页独立备注')
                reopened.locator('#close-notes').click()
                reopened.locator('#edit').click()
                check(f'{filename.name}/can_reedit', reopened.locator('[data-player-editable]').count() > 0)
                if filename == saved:
                    third = download(reopened, 'saved-again.html', 'Meta+s')
                    again = context.new_page()
                    again.goto(third.as_uri())
                    again.keyboard.press('ArrowRight')
                    check('second_generation_navigates_once', again.evaluate('deckPlayer.current === 1'))
                    check('second_generation_options', again.locator('#jump option').count() == count)
                    again.close()
                reopened.close()
            presenter.close()
            page.evaluate('deckPlayer.toggleOverview(false)')
            for width, height in [(390, 844), (844, 390)]:
                page.set_viewport_size({'width': width, 'height': height})
                page.locator('#notes').click()
                check(f'mobile-{width}/no_horizontal_overflow', page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                check(f'mobile-{width}/panel_inside_viewport', page.locator('#notes-panel').evaluate(
                    'e => {const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight}'))
                page.screenshot(path=str(scratch / f'notes-mobile-{width}.png'))
                page.locator('#close-notes').click()
                for button in ['edit', 'save', 'notes', 'presenter']:
                    page.locator(f'#{button}').scroll_into_view_if_needed()
                    check(f'mobile-{width}/{button}_reachable', page.locator(f'#{button}').is_visible())
            check('no_script_errors', not report['errors'])
            check('fully_offline', not report['external_requests'])
        finally:
            (scratch / 'editing-check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            context.close()
            browser.close()
    print(json.dumps({'passed': len(report['checks']), 'browser': report['browser'], 'report': str(scratch / 'editing-check.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
