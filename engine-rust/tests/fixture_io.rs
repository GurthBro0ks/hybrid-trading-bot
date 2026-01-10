//! Fixture I/O helpers for integration tests
//!
//! Provides utilities to load JSON fixtures relative to CARGO_MANIFEST_DIR

use std::path::PathBuf;

/// Load a fixture file as a string
///
/// Path is relative to CARGO_MANIFEST_DIR (engine-rust/)
/// Example: load_fixture("tests/fixtures/venuebook/polymarket/pm_deep.json")
pub fn load_fixture(relative_path: &str) -> String {
    let manifest_dir = env!("CARGO_MANIFEST_DIR");
    let mut path = PathBuf::from(manifest_dir);
    path.push(relative_path);

    std::fs::read_to_string(&path)
        .unwrap_or_else(|e| panic!("Failed to read fixture {}: {}", path.display(), e))
}

/// Load a fixture file as serde_json::Value
pub fn load_fixture_json(relative_path: &str) -> serde_json::Value {
    let content = load_fixture(relative_path);
    serde_json::from_str(&content)
        .unwrap_or_else(|e| panic!("Failed to parse fixture JSON {}: {}", relative_path, e))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_load_fixture() {
        // Verify we can load an existing fixture (crossover_scenario.jsonl)
        let content = load_fixture("tests/fixtures/crossover_scenario.jsonl");
        assert!(!content.is_empty());
    }
}
