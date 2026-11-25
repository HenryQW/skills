# Design language

How __APP_NAME__ should feel, and the ideas behind each screen. Specific rules (sizes, controls, colours, labels) are in `docs/requirements.md` with their IDs. When a new screen or control is not covered there, decide it from this file.

## Character

TODO(scaffold): two or three sentences. What the app is to the user, when it speaks, and what comes first (for example: "A quiet tool. It works in the background and speaks only when something needs attention. Data first, chrome second.").

## Principles

1. **Native first.** System controls, fonts, colours and materials with their default look. Custom drawing only where the data needs it, and then with system colours, fonts and hit areas, so it reads as part of the system.
2. **Minimal.** Every element earns its place. Hierarchy comes from layout and grouping, not from decoration: no custom backgrounds, borders, gradients or shadows for emphasis. A crowded toolbar is a signal to remove or demote actions.
3. **Not flashy.** Normal is quiet: no colour and no motion. Motion explains a change and never decorates. Reduce Motion turns it off.
4. **Colour is information.** Three roles, never mixed:
   - Status: yellow for a warning, red for an error, only when something is wrong.
   - Interaction: the system accent marks the selection.
   - Identity (only if the app needs it): stable per item, never red or yellow.
   Colour is never the only cue; a shape or text goes with it.
5. **Overview first, details on demand.** The main view gives the shape at a glance; a selection shows details; a double-click goes one level deeper.
6. **Stable.** The window never resizes itself, controls do not jump, numbers keep their column.
7. **Honest data.** Missing data says so and is never a zero. An estimate says "About". Old data says when it is from.
8. **Reachable without a mouse.** Every command has a menu item and, if frequent, a shortcut. Every hover or drag action also has a menu item or an accessibility action.

## Surfaces

- Liquid Glass is for what floats: toolbar items, sidebars, popovers, panels. System glass only, so Reduce Transparency and Increase Contrast work.
- Content is never glass: lists, tables, documents and charts sit on the window background.
- No glass on glass.
- Toolbar: items grouped by function and frequency; one primary action is prominent; secondary actions go in a "more" menu. Do not put a text button next to an icon button.
- One layout grid: 8 pt insets and gaps, system default spacing inside controls.
- Density is compact and aligned. No boxes for decoration.

## Type, symbols and numbers

- System text styles only. Numbers that change use monospaced digits.
- SF Symbols for system concepts. A custom symbol only when the domain needs it, drawn to match SF Symbols.
- The app icon is layered and checked in the default, dark, clear and tinted appearances.

## Mac citizen

- Menus: the standard App, File, Edit, View, Window and Help menus that apply. Settings is in the App menu with ⌘,. Menu items enable and disable with the selection.
- Standard shortcuts work (⌘N, ⌘O, ⌘F, ⌘C, ⌘V, ⌘Z) where they apply. Undo and redo work where the user edits.
- Text uses system text components, so selection, Services and the context menu work.
- Windows resize smoothly; the layout adapts.
- Accessibility: VoiceOver names for every control; full keyboard use; usable with Reduce Motion, Reduce Transparency and Increase Contrast; longer localized strings fit.

## Voice

- Simplified Technical English, with no em or en dashes.
- Labels and hints say the action and the result, and name the real target ("Delete 3 entries", not "Delete").
- Errors say what failed and what to do next.

## Changing this file

Change it only when the language changes: a new principle, a new colour role, a new interaction. A new size, control or label is a requirement line, not a line here.
