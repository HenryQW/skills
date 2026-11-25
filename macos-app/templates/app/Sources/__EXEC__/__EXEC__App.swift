import __EXEC__Core
import Observation
import SwiftUI

// Command Line Tools have no SwiftUI macro plugin: no @State, @Entry or #Preview (ADR 0001).
// View state lives in an @Observable model that the app owns; views bind it with @Bindable.

@MainActor @Observable
final class AppModel {
    var list = ItemList()
    /// The search text: view state, kept here because a view struct cannot own it without @State.
    var query = ""

    /// The one code path for "New Item": the menu, ⌘N and the toolbar button call it.
    func addItem() {
        list.add("Item \(list.items.count + 1)")
    }
}

@main
struct __EXEC__App: App {
    private let model = AppModel()

    var body: some Scene {
        WindowGroup("__APP_NAME__", id: "main") {
            ContentView(model: model)
                .frame(minWidth: 480, minHeight: 320)
        }
        .commands {
            CommandGroup(replacing: .newItem) {
                Button("New Item") { model.addItem() }
                    .keyboardShortcut("n")
            }
        }
        Settings {
            SettingsView()
        }
    }
}

struct ContentView: View {
    @Bindable var model: AppModel

    var body: some View {
        let items = model.list.filtered(by: model.query)
        Group {
            if items.isEmpty {
                ContentUnavailableView(model.query.isEmpty ? "No Items" : "No Matches",
                                       systemImage: "tray",
                                       description: Text(model.query.isEmpty ? "Choose File > New Item to add one." : ""))
            } else {
                List(items) { item in
                    LabeledContent(item.title) {
                        Text(item.createdAt, format: .dateTime.hour().minute()).monospacedDigit()
                    }
                }
            }
        }
        .searchable(text: $model.query)
        .toolbar {
            Button("New Item", systemImage: "plus") { model.addItem() }
                .help("Add a new item to the list")
        }
    }
}

struct SettingsView: View {
    var body: some View {
        Form {
            Text("No settings yet.").foregroundStyle(.secondary)
        }
        .formStyle(.grouped)
        .frame(width: 420)
        .fixedSize(horizontal: false, vertical: true)
    }
}
