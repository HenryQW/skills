import Foundation

// Starter model: replace it with the app's domain model. Core has no UI imports.
public struct Item: Identifiable, Equatable, Sendable {
    public let id: UUID
    public var title: String
    public let createdAt: Date

    public init(id: UUID = UUID(), title: String, createdAt: Date = Date()) {
        self.id = id
        self.title = title
        self.createdAt = createdAt
    }
}

public struct ItemList: Equatable, Sendable {
    public private(set) var items: [Item] = []

    public init() {}

    /// Adds an item; the newest item is first.
    public mutating func add(_ title: String, at date: Date = Date()) {
        items.insert(Item(title: title, createdAt: date), at: 0)
    }

    /// Items whose title contains `query`, ignoring case and diacritics; all items for an empty query.
    public func filtered(by query: String) -> [Item] {
        let q = query.trimmingCharacters(in: .whitespaces)
        guard !q.isEmpty else { return items }
        return items.filter { $0.title.range(of: q, options: [.caseInsensitive, .diacriticInsensitive]) != nil }
    }
}
