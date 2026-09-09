// bun test runs outside a browser, so the offline layer needs a real IndexedDB
// implementation to test against. fake-indexeddb is the reference one; using it
// keeps TC-601..605 honest instead of testing a mock of our own queue.
import "fake-indexeddb/auto";
