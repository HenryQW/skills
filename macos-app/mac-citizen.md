# Mac citizen checklist

The release gate for any UI change. Each line is true, or it has a requirement line in `docs/requirements.md` that says why not.

## Menus and keyboard

- [ ] Standard menus that apply: App, File, Edit, View, Window, Help. Primary tasks near the top; destructive items grouped and labeled.
- [ ] Settings is in the App menu and opens with ⌘,.
- [ ] Menu items enable and disable with focus and selection.
- [ ] Every primary command has a menu item; frequent ones have a shortcut. Standard shortcuts (⌘N, ⌘O, ⌘F, ⌘C, ⌘V, ⌘Z) work where they apply.
- [ ] Menus, shortcuts and toolbar buttons call the same command code.
- [ ] Everything works without a mouse: Tab order, focus rings on custom controls.

## Windows and text

- [ ] The window model fits the archetype (document, library + detail, utility, menu bar).
- [ ] Resizing is smooth and the layout adapts; the window never resizes itself.
- [ ] Close, minimize, zoom, full screen and tabs behave as the system does.
- [ ] Text surfaces use system text components: selection, undo/redo, Services, context menu.
- [ ] Copy, paste and drag and drop work where the user would expect them. ⌘C on a selected table row copies it (`.copyable`).
- [ ] Tables sort by their column headers (`Table(sortOrder:)` with `KeyPathComparator`).
- [ ] A search with no result shows `ContentUnavailableView.search`, not an empty list.
- [ ] Choose a file or folder with `.fileImporter`, not a custom panel.
- [ ] Every popover and hover card is Liquid Glass: a native popover, or a card with `.glassEffect`.

## Look

- [ ] System text styles, colours and materials only; no custom backgrounds or borders for emphasis.
- [ ] Liquid Glass only on the floating layer (toolbar, sidebar, popovers, panels); no glass on content; no glass on glass.
- [ ] Toolbar grouped by function and frequency; one prominent primary action; secondary actions in a "more" menu.
- [ ] SF Symbols for system concepts; custom symbols match them.
- [ ] Motion only explains a change.
- [ ] Light and dark checked (`--args -AppleInterfaceStyle Dark`).
- [ ] App icon layered and checked in default, dark, clear and tinted appearances.

## Accessibility

- [ ] VoiceOver: every interactive element has a name, and a value or hint where needed. A VoiceOver user can do the core task.
- [ ] Colour is never the only cue (add a shape or text).
- [ ] Usable with Reduce Motion, Reduce Transparency and Increase Contrast.
- [ ] Longer localized strings fit.

## Performance and stability

- [ ] Heavy data: open, scroll and resize stay smooth.
- [ ] No work that blocks the main thread; no unbounded caches; windows close cleanly with no leaks.
