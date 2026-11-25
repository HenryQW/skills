import Foundation
import Testing
@testable import __EXEC__Core

@Test func newestItemIsFirst() {
    var list = ItemList()
    list.add("First", at: Date(timeIntervalSince1970: 1))
    list.add("Second", at: Date(timeIntervalSince1970: 2))
    #expect(list.items.map(\.title) == ["Second", "First"])
}

@Test func filterIgnoresCaseAndDiacritics() {
    var list = ItemList()
    list.add("Café")
    list.add("Tea")
    #expect(list.filtered(by: "CAFE").map(\.title) == ["Café"])
    #expect(list.filtered(by: " ").count == 2)
}
